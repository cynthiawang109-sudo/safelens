"""Local FastAPI contract for grounded ASRS answers and indexed source reports."""

import threading
from contextlib import asynccontextmanager, contextmanager

import psycopg
from fastapi import FastAPI, HTTPException
from psycopg.rows import dict_row
from pydantic import BaseModel, Field, field_validator

from safelens.config import Settings
from safelens.embed import LocalEmbeddingProvider
from safelens.generate import generate_answer
from safelens.ingest import require_active_index
from safelens.llm import GenerationUnavailable, OpenAILLMProvider
from safelens.reindex import LOCK
from safelens.retrieve import search_hybrid
from safelens.subset import CATEGORIES


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    category: str | None = None

    @field_validator("question")
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError("Question cannot be blank")
        return value.strip()

    @field_validator("category")
    @classmethod
    def known_category(cls, value):
        if value is not None and value not in CATEGORIES:
            raise ValueError("Unknown category")
        return value


class Evidence(BaseModel):
    acn: str
    chunk_id: int
    passage: str


class CitationValidation(BaseModel):
    flagged: bool
    invalid_acns: list[str]
    missing_citations: bool


class ReportHit(BaseModel):
    acn: str
    chunk_id: int
    text: str
    score: float
    ranks: dict[str, int | None]
    components: dict


class AskResponse(BaseModel):
    answer: str
    citations: list[Evidence]
    results: list[ReportHit]
    validation: CitationValidation
    index_id: int


class SourceChunk(BaseModel):
    chunk_id: int
    chunk_idx: int
    text: str


class ReportResponse(BaseModel):
    acn: str
    report_month: str | None
    report_year: int | None
    synopsis: str | None
    narrative: str | None
    anomaly_codes: list[str] | None
    flight_phase: str | None
    aircraft_category: str | None
    content_hash: str
    source_dataset: str
    source_revision: str | None
    text: str
    chunks: list[SourceChunk]
    index_id: int


class HealthResponse(BaseModel):
    status: str
    index_id: int
    reports: int
    chunks: int
    embedding_model: str
    llm_model: str
    categories: list[str]


@contextmanager
def indexed_connection(settings):
    """Pin one ready build throughout retrieval, evidence assembly, and generation."""
    with psycopg.connect(settings.database_url, autocommit=True, connect_timeout=10) as conn:
        if not conn.execute("SELECT pg_try_advisory_lock_shared(%s)", (LOCK,)).fetchone()[0]:
            raise HTTPException(503, "Offline reindex/ingest is active")
        try:
            try:
                require_active_index(conn, settings)
            except ValueError:
                raise HTTPException(503, "No ready index matches the configured model and chunk policy") from None
            yield conn
        finally:
            conn.execute("SELECT pg_advisory_unlock_shared(%s)", (LOCK,))


def create_app(settings=None, embedding_factory=LocalEmbeddingProvider, llm_factory=OpenAILLMProvider):
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(application):
        with indexed_connection(settings):
            pass
        application.state.embedding = embedding_factory(settings)
        application.state.llm = llm_factory(settings)
        application.state.embedding_lock = threading.Lock()
        yield

    api = FastAPI(title="SafeLens Mini", version="0.1.0", lifespan=lifespan)

    @api.exception_handler(psycopg.Error)
    async def database_unavailable(request, exc):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})

    @api.get("/health", response_model=HealthResponse)
    def health():
        with indexed_connection(settings) as conn:
            index_id, report_count = conn.execute("SELECT id, report_count FROM index_meta WHERE status='ready'").fetchone()
            chunks = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
            return {"status": "ready", "index_id": index_id, "reports": report_count, "chunks": chunks,
                    "embedding_model": settings.embedding_model, "llm_model": settings.llm_model,
                    "categories": list(CATEGORIES)}

    @api.get("/report/{acn}", response_model=ReportResponse)
    def report(acn: str):
        if not acn.isdigit():
            raise HTTPException(404, "Report not found")
        with indexed_connection(settings) as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                row = cursor.execute("SELECT * FROM reports WHERE acn=%s", (acn,)).fetchone()
                if row is None:
                    raise HTTPException(404, "Report not found")
                chunks = cursor.execute("SELECT id AS chunk_id, chunk_idx, text FROM chunks WHERE acn=%s ORDER BY chunk_idx", (acn,)).fetchall()
            return {**row, "text": (row["synopsis"] or "") + "\n\n" + (row["narrative"] or ""), "chunks": chunks,
                    "index_id": conn.execute("SELECT id FROM index_meta WHERE status='ready'").fetchone()[0]}

    @api.post("/ask", response_model=AskResponse)
    def ask(body: AskRequest):
        with indexed_connection(settings) as conn:
            with api.state.embedding_lock:
                results = search_hybrid(body.question, 5, conn=conn, settings=settings,
                                        provider=api.state.embedding, category=body.category)
            with conn.cursor(row_factory=dict_row) as cursor:
                reports = {row["acn"]: row for row in cursor.execute(
                    "SELECT acn, report_month, source_dataset, source_revision FROM reports WHERE acn=ANY(%s)",
                    ([hit["acn"] for hit in results],),
                ).fetchall()}
            try:
                generated = generate_answer(body.question, results, reports, api.state.llm)
            except GenerationUnavailable as error:
                raise HTTPException(502, {"message": "LLM generation unavailable", "code": error.code}) from None
            return {**generated, "results": results,
                    "index_id": conn.execute("SELECT id FROM index_meta WHERE status='ready'").fetchone()[0]}

    return api


app = create_app()
