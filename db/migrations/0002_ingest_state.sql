-- Per-report ingestion bookkeeping; this is not a ready vector index.
CREATE TABLE ingest_state (
    acn text PRIMARY KEY REFERENCES reports ON DELETE CASCADE,
    config jsonb NOT NULL
);
