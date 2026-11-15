# SafeLens contributor rules

Read `docs/PROJECT1_MINI_WEEKEND_SPEC.md` (frozen v1.3), then
`docs/DATA_NOTES.md`; the spec governs design and the notes record data facts.
Follow the step boundaries and acceptance checks in `CODEX_KICKOFF.md`.
Use English for code, comments, and documentation.

- Use PostgreSQL + pgvector (`pgvector/pgvector:pg16`). Mini vector search is
  exact; defer ANN indexes and other flagship features.
- Rank, fuse, evaluate, and assemble generation context at report level only.
  Collapse chunk hits to unique ACNs using each report's best chunk score before
  RRF. Defaults: 100 candidate chunks, 50 candidate reports, RRF k=60; break
  ties deterministically by ACN and retain winning chunks and component ranks.
- Benchmark runs never apply the category filter. Query categories are labels
  for evaluation; separately label any filtered experiment.
- ACN is the report primary key. Store a normalized content hash and provenance.
  Replace a report and its chunks atomically; skip only when both content and
  active index configuration match. Preserve chunk metadata and uniqueness of
  `(acn, chunk_idx)`.
- Keep document and query embedding methods separate; apply the configured
  query prefix. Models and providers belong behind configuration and interfaces.
- Reindexing is explicit and offline. Never switch models by env change alone.
  Only a fully validated build becomes active; startup must reject configuration
  mismatches, and failures must never expose mixed embeddings.
- Raw data and intermediate exports belong in gitignored `data/`; never commit
  them or `.env`, API keys, or other secrets. Maintain `.env.example`.
- Preserve all reporter narratives with provenance labels. Dates have month
  precision only. Normalize using the documented field mapping and fail loudly
  on unexpected schema changes.
- Version `eval/queries.jsonl` and `eval/qrels.jsonl` like code. Record corpus and
  index configuration, candidate depths, file hashes, and latency per experiment.
  Separate weak-label agreement from judged relevance; do not treat unjudged
  reports as irrelevant or hide negative findings.
- Ground answers in reporter accounts, with exact evidence passages and validated
  ACN citations. Missing evidence requires a qualified refusal. RRF scores are
  not confidence estimates; do not use a score threshold for refusal.
- Use Python 3.12 and uv. Set `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8`
  before Python entry points, locally and in Compose. Specify `encoding="utf-8"`
  explicitly for text file I/O.
