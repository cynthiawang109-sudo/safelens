CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE reports (
    acn text PRIMARY KEY CHECK (length(btrim(acn)) > 0),
    report_month text,
    report_year int,
    synopsis text,
    narrative text,
    anomaly_codes text[],
    flight_phase text,
    aircraft_category text,
    content_hash text NOT NULL,
    source_dataset text NOT NULL,
    source_revision text
);

CREATE TABLE chunks (
    id bigserial PRIMARY KEY,
    acn text REFERENCES reports,
    chunk_idx int,
    text text,
    embedding vector(384),
    tsv tsvector GENERATED ALWAYS AS (to_tsvector('simple', coalesce(text, ''))) STORED,
    anomaly_codes text[],
    flight_phase text,
    aircraft_category text,
    report_month text,
    report_year int,
    UNIQUE (acn, chunk_idx)
);
CREATE INDEX chunks_tsv_gin ON chunks USING gin (tsv);

CREATE TABLE index_meta (
    id bigserial PRIMARY KEY,
    status text NOT NULL CHECK (status IN ('building', 'ready', 'failed', 'superseded')),
    embedding_model text NOT NULL,
    embedding_dim int NOT NULL,
    embed_query_prefix text,
    chunk_config jsonb NOT NULL,
    report_count int NOT NULL,
    built_at timestamptz NOT NULL
);
CREATE UNIQUE INDEX index_meta_one_ready ON index_meta ((status)) WHERE status = 'ready';
