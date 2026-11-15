# ASRS Mini — Weekend Build Spec (SafeLens prototype)

**Status: APPROVED by Cynthia, 2026-11-15; v1.1 the same day** after an external architecture review (ChatGPT, `SAFELENS_MINI_SPEC_REVIEW.md`); **v1.3 after a second external review of v1.2** (aggregation/fusion order and candidate depth pinned down, benchmark runs explicitly unfiltered, abstention controls replaced with verifiably-absent facts, active-index state defined — spec is **frozen** after this round; remaining unknowns are data facts for Saturday's schema inspection, not design questions); **v1.2 after Sunny's self-review** — fixes: retrieval results are aggregated to report level before ranking/evaluation (chunk-level top-K was undefined against report-level metrics); Layer-2 judging scoped to 8 queries (the original 16–20 × ~20 documents was 4–15 hours of reading — not weekend-feasible); the embedding provider splits `embed_documents`/`embed_query` with per-model prefixes (bge-class models underperform measurably without the query instruction, which would have corrupted the FTS-vs-dense comparison); ASRS dates are month-granularity, so `report_date: date` became `report_month text` + `report_year int`; FTS configuration, the pgvector Compose image, ANN-index deferral, abstention control queries, and secrets hygiene are now explicit. Material changes: evaluation redesigned into two layers (weak-label category agreement + pooled human judgments — the original single-layer Recall@10 against the whole category pool was not a valid relevance metric); the lexical baseline is correctly named **PostgreSQL FTS** (`ts_rank_cd` is not BM25 — true BM25 via ParadeDB `pg_search` is deferred to the flagship retrieval lab); the RRF-score refusal threshold was removed (RRF scores are ranks, not calibrated confidence); schema gained chunk uniqueness, provenance, and index-version contracts. A one-weekend, working RAG over a subset of NASA ASRS reports. This is **not a separate throwaway project**: it is the SafeLens flagship repo in its first milestone state. Everything built here carries forward per the flagship spec (`PROJECT1_ASRS_RAG_PLAN.md`); only the prototype UI and the subset data are disposable.

**Repo name from day one:** `safelens` (working name, same as flagship).

---

## 1. Weekend goal (definition of done)

By Sunday night, all of these are true:

- [ ] `docker compose up` starts PostgreSQL + pgvector; ingest runs end-to-end and is idempotent (re-running changes nothing; changed reports replace their chunks atomically, never duplicate them).
- [ ] The pipeline is validated on **1,000 reports first**, then scaled to **~5,000 ASRS reports** (4 anomaly categories), chunked, embedded, and indexed (dense + full-text). The indexed report count is recorded with every experiment.
- [ ] A question returns a grounded answer whose `[ACN]` citations are validated against the documents actually supplied to generation; when support is missing the system answers "insufficient evidence" instead of bluffing. Latency is *measured and reported* (retrieval p95 target < 1s locally; end-to-end generation p95 reported, no hard SLA) — not promised.
- [ ] `eval/results.md` contains a committed comparison table — PostgreSQL FTS vs dense vs hybrid — with **both** evaluation layers from §6 (weak-label category agreement and judged relevance), metric definitions, and stated limitations.
- [ ] README documents architecture, how to run, the results table, and the flagship roadmap. Repo is public.
- [ ] Fallback honesty rule: if the generation/UI layer is not finished by Sunday night, the repo is labeled a *retrieval + evaluation milestone*, not a complete RAG — and finishing it is the immediate next step, not a quiet omission.

## 2. Scope

**In:** data load + normalize, chunking, one embedding model, pgvector + Postgres FTS indexes, lexical(FTS)/dense/RRF retrieval, one generation endpoint with validated citations and an insufficient-evidence response, a Gradio page, the two-layer eval harness.

**Out (flagship territory, do not touch this weekend):** LangGraph and any agent loop, query expansion, cross-encoder rerank, LLM relevance filter, Next.js UI, official NASA exports (10k CSV downloads), incremental ingestion *job* (hash is stored, the job is not built), auth, deployment beyond localhost.

## 3. The five seams (hard rules — breaking one means rework later)

1. **PostgreSQL + pgvector from day one**, via Docker Compose using the **`pgvector/pgvector:pg16` image** (the stock `postgres` image does not ship the extension — do not burn weekend time discovering this). No in-memory vector stores, no Chroma/SQLite detours.
2. **ACN is the primary key**, and every report row stores a `content_hash` (SHA-256 of the normalized record) even though nothing reads it yet — the flagship's incremental ingestion depends on both.
3. **Chunk rows carry full metadata columns** (report month/year, anomaly codes, flight phase, aircraft category) even if the weekend UI only filters by category.
4. **Embedding model and LLM sit behind config + a thin provider interface** (`EMBEDDING_MODEL`, `LLM_PROVIDER`/`LLM_MODEL` env vars; functions: `embed_documents(texts)`, `embed_query(text)`, `generate(prompt)`). Documents and queries are embedded **separately**: asymmetric models (bge/e5 class) require a query instruction prefix (config: `EMBED_QUERY_PREFIX`), and skipping it silently degrades dense retrieval. The flagship bake-off must be a config change plus a re-embed command, not a refactor.
5. **The eval harness is a standalone script with a versioned query file** (`eval/queries.jsonl`), so the flagship only adds rows and metrics — never rewrites the harness.

## 4. Data

- **Source:** Hugging Face dataset `elihoole/asrs-aviation-reports` (38,655 reports, Jan 2012 – Mar 2022, 111 fields), loaded with the `datasets` library. No NASA website interaction this weekend.
- **First task is schema inspection, not coding:** print all columns, identify the fields for ACN, report date, synopsis, narrative, anomaly codes, flight phase, aircraft category; record the mapping in `docs/DATA_NOTES.md`. The export's mirrored/duplicate column names (~48 duplicates across Aircraft 1/2, Person 1/2) must be resolved explicitly in the loader — write down which twin wins and why.
- **Subset selection:** count reports per anomaly category; pick **4 categories** with healthy volume and contrasting retrieval behavior (at least one acronym-heavy, e.g. runway incursion; at least one paraphrase-heavy, e.g. fatigue/human factors). Target **~5,000 reports total**; sampling uses a **fixed seed** and a documented selection order (dedupe by ACN first, then sample), and DATA_NOTES.md reports the outcome honestly: unique ACN count, per-label counts, year distribution, and multi-label overlap — recent-years-first sampling skews the corpus temporally, and that skew is recorded, not hidden. Anomaly codes are **multi-label** (semicolon-joined in the export): per-category counts are label assignments, not disjoint report sets, and one report may belong to several selected categories — that is expected, not a data error.
- **Raw data stays out of Git.** The HF download and any intermediate CSVs live in a gitignored `data/` directory; the repo ships the loader script + DATA_NOTES so the corpus is reproducible, not redistributed.
- **Document text:** `synopsis + "\n\n" + narrative`. ASRS records can carry **two** reporter narratives (Report 1 / Report 2) describing the same event from different seats — schema inspection must enumerate every narrative and synopsis column, count how many rows have a second narrative, and record the decision in DATA_NOTES.md. Mini default: concatenate all narrative fields in report order with explicit provenance labels (`— Report 1 —`, `— Report 2 —`) as separators (never silently drop the second perspective, and citations can later distinguish the accounts). Reports with all narratives empty are dropped and counted. Note for the flagship: synopsis text is expert-written and may make retrieval measurably easier — a narrative-only vs synopsis+narrative ablation is scheduled there; the Mini records which construction it used in every experiment config.

## 5. Build plan

### Data model (PostgreSQL)

```sql
reports(
  acn            text primary key,       -- validated nonempty + normalized at ingest
  report_month   text,                   -- 'YYYY-MM': ASRS public data is month-granularity
  report_year    int,                    -- (de-identification strips exact dates; do not fake a day)
  synopsis       text,
  narrative      text,                   -- all narrative fields concatenated per DATA_NOTES
  anomaly_codes  text[],
  flight_phase   text,
  aircraft_category text,
  content_hash   text not null,          -- SHA-256 over the canonical serialization of the
                                         -- normalized record (fixed field order, defined in code)
  source_dataset text not null,          -- e.g. elihoole/asrs-aviation-reports
  source_revision text                   -- dataset revision / export batch id
)
chunks(
  id             bigserial primary key,
  acn            text references reports,
  chunk_idx      int,
  text           text,
  embedding      vector(<dim>),          -- dim follows the configured model
  tsv            tsvector,               -- generated with the 'simple' text-search config
                                         -- (no stemming; queries use websearch_to_tsquery with
                                         -- the same config; GIN index on this column. Whether
                                         -- 'simple' actually beats 'english' on aviation text is
                                         -- a hypothesis — a flagship ablation, not a premise)
  anomaly_codes  text[],                 -- denormalized from reports for eval/filter
  flight_phase   text,
  aircraft_category text,
  report_month   text,
  report_year    int,
  unique (acn, chunk_idx)                -- reruns replace, never duplicate
)
index_meta(                              -- one row per index build
  id             bigserial primary key,
  status         text not null,          -- building | ready | failed; exactly one 'ready' row
                                         -- is the active index, and serving requires it
  embedding_model text not null,
  embedding_dim  int not null,
  embed_query_prefix text,               -- the prefix the build's query embeddings used
  chunk_config   jsonb not null,         -- size/overlap/text construction/lexical config
  report_count   int not null,
  built_at       timestamptz not null
)
```

**Vector search is exact in the Mini** (no HNSW/IVFFlat index): at ~12k chunks a sequential scan is fast, and exact scores keep the evaluation honest. ANN indexing is a flagship scale decision, made with measurements at 113k chunks.

**Model switching is a reindex, not an env change.** A new embedding model can change dimensionality and always changes the vector space: switching requires an explicit `python -m safelens.cli reindex --model <name>` run. **Reindexing is an offline operation in the Mini**: it builds with `index_meta.status='building'`, flips to `'ready'` only after every chunk is embedded and counts validate, and marks the previous build superseded. At startup the API verifies that the configured model, dimension, query prefix, and chunk config match the single active `ready` build — a mismatch is a hard error, not a silent degradation. A failed reindex must never expose mixed embeddings. Schema changes ship as ordered SQL files under `db/migrations/`, applied in filename order.

### Pipeline modules (`src/safelens/`)

| Module | Job |
|---|---|
| `config.py` | Env-driven settings (DB URL, model names, chunk params). Nothing else hardcodes a model name. |
| `ingest.py` | Load HF dataset → normalize per DATA_NOTES mapping → upsert reports. Per-ACN transaction: skip only when `content_hash` matches **and** the active index config (model + chunking) is unchanged; a changed report's chunks are prepared first, then report + chunks swap in one transaction (rollback preserves the old valid state). Logs skipped/inserted/updated/failed counts per run. |
| `chunk.py` | Paragraph-aware packing to 400–600 tokens, 15% overlap; synopsis prepended to every chunk of its report. Token counting uses the **embedding model's tokenizer** (via the provider); parameters recorded in `index_meta.chunk_config`. |
| `embed.py` | `embed_documents(texts)` / `embed_query(text)` provider functions (query side applies `EMBED_QUERY_PREFIX`); batch-embeds chunks, writes vectors. Re-runnable per model. |
| `retrieve.py` | `search_lexical(q, k)` (PostgreSQL FTS, `ts_rank_cd` — **not** BM25; true BM25 via ParadeDB `pg_search` is a flagship retrieval-lab comparison), `search_dense(q, k)`, `search_hybrid(q, k)` (RRF, k=60). Optional category filter. **Aggregation and fusion are defined exactly** (no implementer's choice left): each retriever first fetches `candidate_chunks` chunk hits (default **100**), collapses them to unique ACNs keeping each report's best chunk score, and keeps its top `candidate_reports` (default **50**). RRF is computed over these **report-level rankings** (`score(d) = Σ 1/(60 + rank_r(d))`), never over chunk ranks. Output is at most one row per ACN; ties break deterministically by ACN. The winning chunk ID/text and each component rank are retained per report for generation and debugging. `candidate_chunks`, `candidate_reports`, fusion k, and the aggregation policy are recorded in every experiment config; if doubling `candidate_chunks` changes results materially, that candidate starvation is reported, not silently tuned away. Every metric in §6 and the generation context are defined over these report rankings. Pure functions, no UI imports — the flagship LangGraph nodes will wrap these. |
| `generate.py` | Builds the grounded prompt, calls `generate()`, returns answer + cited ACNs. **No score-threshold refusal**: RRF scores are rank artifacts, not calibrated confidence. Instead: (1) the prompt instructs the model to answer only from the supplied evidence and to reply "insufficient evidence" when support is missing; (2) every cited ACN is validated against the documents actually supplied — fabricated citations are dropped and the answer flagged. This is a safeguard, not a confidence estimator; calibrated abstention (cross-encoder grading, threshold set on judged data) is flagship M4 work. |
| `generate.py` (grounding) | The prompt must present retrieved passages as **reporter accounts, not confirmed findings** (no causal certainty the narrative doesn't support). `/ask` returns structured evidence per citation — `{acn, chunk_id, passage}` — not bare ACNs, so any claim can be traced to the exact text. Citation validation proves a passage exists, not that a claim is true; unsupported-claim detection is flagship evaluation work. |
| `app.py` | FastAPI: `POST /ask {question, category?}` → `{answer, citations[{acn, chunk_id, passage}], results[]}`; `GET /report/{acn}` returns exactly the indexed source text + provenance (dataset, revision) used for generation; `GET /health`. Response fields are a stable contract — the Next.js UI will replace Gradio against the same shapes. |
| `ui.py` | Gradio page calling the API over HTTP (never importing retrieve directly — API is the seam the Next.js UI will replace). |
| `eval/run_eval.py` | Reads `eval/queries.jsonl` (+ `eval/qrels.jsonl` when present), runs all three retrievers, writes `eval/results.md` **and** a full experiment record alongside it: corpus source + revision + selection seed + unique report count, chunk count + chunk config, embedding model + revision + query prefix, lexical config, candidate depths + RRF k + aggregation policy, query/qrels file hashes, per-retriever latency, hardware note, timestamp. |

### Defaults (chosen for weekend speed, all config-switchable)

- Embedding: **`BAAI/bge-small-en-v1.5`** locally via sentence-transformers (384-dim, fast on CPU, good enough to show the dense-vs-lexical contrast), with `EMBED_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "` (the vendor-recommended instruction for this model family). The flagship bake-off re-decides; expect a re-embed.
- LLM: **OpenAI `gpt-4o-mini`** (or current equivalent mini model) via the provider interface — cheap, fast, sufficient for grounded answers over 5–8 chunks of context.
- Context for generation: the best chunk of each of the top 5 reports from the hybrid report ranking, plus a second chunk per report when it ranks highly (max 8 chunks total).
- Secrets: the API key lives in `.env` (gitignored); a committed `.env.example` documents every variable. No key ever enters the repo, the eval artifacts, or the README.

## 6. Evaluation (do not cut — this is the point)

An anomaly code is a **coarse category label, not query-level relevance**: not every runway-incursion report is relevant to a specific runway-incursion question, and "Recall@10" against a 1,200-report category pool measures category coverage, not retrieval quality. The Mini therefore evaluates in **two explicitly separated layers**.

**Benchmark runs are unfiltered.** The `category` field on a query is an evaluation label, never a retrieval filter — running the benchmark with the category filter on would mechanically inflate Layer-1 precision and invalidate the comparison. (A filtered-retrieval experiment may be reported separately, clearly named.) All runs record the corpus snapshot, query-file hash, and qrels-file hash.

**Layer 1 — weak-label category agreement (automatic, all queries).** For each query, the fraction of top-10 results carrying the query's anomaly code: **Category Precision@10** and **Hit@10** (≥1 in-category result). This measures coarse topical alignment only, and results.md must say so.

**Layer 2 — judged relevance (manual, pooled, scoped).** Judging is real reading work, so it is deliberately scoped: **8 of the queries (2 per category) get full judgments**; the rest are Layer-1 only. For each judged query, pool the top-10 *reports* from all three retrievers, deduplicate (~15–20 reports), and grade each `relevant` / `partially relevant` / `irrelevant`. Judging protocol: read the synopsis first; open the full narrative only when the synopsis is ambiguous — and record that this protocol was used. Budget ≈ 2 hours; if it overruns, drop to 6 queries rather than thinning judgments. Judgments are stored in **`eval/qrels.jsonl`** (`{"query_id": ..., "acn": ..., "grade": 2|1|0, "note": optional}`), versioned like code. Grade semantics are fixed: **2 = directly relevant, 1 = partially relevant, 0 = irrelevant**. Metrics per retriever, computed over the report-level rankings: **Precision@10 and MRR treat grade ≥ 1 as relevant; nDCG@10 uses the graded gains (2/1/0)**. Results are reported **per query as well as averaged** — with 8 judged queries, no broad superiority claims. Judging is **blinded**: the judging sheet hides which retriever proposed each report and randomizes display order. Every top-10 report from each compared retriever must have a qrel; adding a new retriever later requires re-pooling and extending the judgments before any comparison is fair. These 8 queries are a development/judgment set — tuning against them is allowed, but results.md must not present them as an independent held-out test (the flagship builds one). Unjudged documents are *not* assumed irrelevant; recall is reported only against the judged pool and the pooling limitation is stated in results.md.

**Abstention controls.** Three additional queries with `"category": null, "expect": "insufficient_evidence"`, each targeting a *verifiably* absent fact (absence is checked against the frozen subset before scoring — a merely-unlikely topic is not a control, since the corpus might legitimately contain it): (1) an out-of-domain request (e.g. a marine equipment incident); (2) a precision the corpus cannot contain — the **exact day and time** of an event whose record stores only year-month; (3) a **fabricated ACN**, verified absent from the subset, asked about as if real. Scoring judges the *claim*, not the literal string "insufficient evidence": a qualified answer ("the record identifies only the month") passes; inventing a date, a report, or findings for the fake ACN fails.

Files:

- `eval/queries.jsonl` — one object per line: `{"id": "ri-1", "query": "aircraft entered the active runway without clearance while another was on final", "category": "runway_incursion"}`. 16–20 category queries, **4–5 per selected category**, mixing (a) plain-language descriptions, (b) paraphrases that avoid the category's obvious keywords, (c) one acronym/jargon-heavy query per category — plus the 3 abstention controls.
- `eval/results.md` — generated by the script and committed, with both layers, the abstention-control outcomes, metric definitions, corpus counts, and limitations. Numbers first, tuning second: if hybrid does not beat both singles, that is a finding to write up, not a table to hide.

## 7. Weekend schedule

**Saturday AM — data.** Repo + compose + config skeleton; schema inspection → DATA_NOTES.md; ingest + chunk + embed running, **validated end-to-end on 1,000 reports before scaling** to the ~5,000 subset.
**Saturday PM — retrieval.** Indexes, the three search functions, CLI smoke tests; eval query file drafted; Layer-1 (category agreement) numbers; start Layer-2 judging on the pooled results.
**Sunday AM — product.** FastAPI `/ask` with citation validation + insufficient-evidence behavior; Gradio page.
**Sunday PM — proof.** Judging finished, full eval run, results.md committed; README (architecture sketch, run instructions, results, flagship roadmap link); repo public; final check against §1.

**Priority order if time runs short:** data + ingestion → retrieval → two-layer evaluation → `/ask` → Gradio → README polish. Cut from the bottom; never cut evaluation to save the UI.

**Minimum tests (all must pass before calling it done):**

- Ingest twice on unchanged data → identical report/chunk counts, no duplicates, same active index.
- Force a failure mid-replacement of a changed report → old report and chunks intact after rollback.
- Change chunk config or embedding model → skip logic does not treat stale vectors as current; startup config check fails loudly.
- A report with several matching chunks → appears exactly once in report-level top-K.
- Benchmark run with `category` present in query metadata → retrieval is demonstrably unfiltered.
- Ask about the fabricated ACN and the exact-day control → qualified refusal, no invented citation or date.
- Restart Docker, rerun evaluation → same results under the pinned corpus/config.

**Stretch (only if §1 is fully green):** a static glossary expansion for ~20 aviation acronyms applied to the lexical query (TCAS, RA, NMAC, CFIT…) — a taste of flagship M3, kept behind a config flag so the ablation stays honest.

## 8. Upgrade path (why nothing here is wasted)

| Mini piece | Flagship future |
|---|---|
| ingest + content_hash | M5 incremental job diffs on exactly this hash |
| chunk + metadata schema | unchanged at 48k scale; only the corpus source swaps (HF → official exports) |
| retrieve.py functions | become LangGraph tool nodes in M4; expansion/rerank/filter slot in as additional stages in M3 |
| eval harness + queries.jsonl + qrels.jsonl | grows into the flagship §8 benchmark (label-recall at large K *plus* this judged layer, RAGAS, CI gate) |
| Gradio UI | **thrown away**, replaced by Next.js (M5) — the API contract survives |
| bge-small embeddings | replaced by the bake-off winner; one config change + re-embed |
