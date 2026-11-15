# DATA_NOTES — ASRS Corpus

Status: **full-corpus inspection finalized on 2026-11-15** for Step 1.
Counts below cover all three pinned files. The 1,000-report validation slice
is imported. Step 1 evidence below records its pre-index state; Step 2 indexes
the same slice (see `STEP2_VALIDATION.json`). Final ~5,000 selection is deferred.

## Source and reproduction

- Hugging Face dataset: `elihoole/asrs-aviation-reports`.
- Revision: `f1e681e92cddae20d01fc498d685f1cf6a052d34` (2022-07-15).
- Download URL pattern:
  `https://huggingface.co/datasets/elihoole/asrs-aviation-reports/resolve/f1e681e92cddae20d01fc498d685f1cf6a052d34/asrs-aviation-reports-{split}.jsonl`.
- License: Apache-2.0 according to the dataset card; underlying reports are
  NASA ASRS public data.
- Corpus decision: concatenate train, validation, test, deduplicate by normalized
  ACN before selecting reports. There is no ML training here. The full corpus
  is **47,723 reports**; 38,655 is the train split alone.
- Raw JSONL and inspection output remain in gitignored `data/`.
  [STEP1_VALIDATION.json](STEP1_VALIDATION.json) records file SHA-256s and slice
  checks. [FULL_CORPUS_STATS.json](FULL_CORPUS_STATS.json) records aggregate
  counts and schema metadata only, with no source report text.
- Run `scripts/inspect_dataset.py` with all three paths. Its final `SUMMARY_JSON`
  line contains machine-readable full-corpus statistics. README has commands.

| File | Rows | Bytes |
|---|---:|---:|
| `asrs-aviation-reports-train.jsonl` | 38,655 | 270,248,264 |
| `asrs-aviation-reports-validation.jsonl` | 4,295 | 29,941,842 |
| `asrs-aviation-reports-test.jsonl` | 4,773 | 33,260,860 |
| Total | 47,723 | 333,450,966 |

## Verified schema facts

- **111 columns**, flattened names of the form `<Section>[.n]_<Field>`.
  Every row matches `src/safelens/source_columns.json`; all 47,723 rows pass
  normalization.
- `acn_num_ACN`: present on every row, **47,723 unique**, **zero duplicates**
  across splits.
- `Time_Date`: valid `YYYYMM` on every row, **201201–202203**, **111 months**.
  Store `report_month=YYYY-MM`, `report_year=YYYY`; never invent a day.
- Correction to the draft: `Time.1_Local Time Of Day` exists and contains broad
  bands: `0001-0600` (5,182), `0601-1200` (12,338), `1201-1800` (15,737),
  `1801-2400` (9,511), `ZZZ` (14), or empty (4,941). The Mini drops this field.
  There is no structured exact day/timestamp. Prose may mention times: verify
  the chosen record's text before using an exact-day/time abstention control.
- `Events_Anomaly`: nonempty **47,701/47,723**; **36,846** multi-label reports
  (77.2%), **97 distinct exact labels**. Split on `;`, trim whitespace, preserve
  spelling/case. Fragments `Critical` / `Less Severe` remain separate labels.
  Match exact strings, never substrings.
- Narrative columns are exactly `Report 1_Narrative` and `Report 2_Narrative`.
  Report 1: **47,723/47,723**, average **1,584 chars**. Report 2:
  **11,228/47,723 (23.5%)**, average **961 chars** among nonempty accounts.
  **Zero** reports have all narratives empty; the loader still drops/counts
  that case. Callback columns are not narratives and are dropped.
- Only synopsis column: `Report 1.2_Synopsis`, **47,723/47,723**, average
  **171 chars**, maximum **959 chars**. No Report 2 synopsis exists.
- Source document lengths (synopsis + narratives, excluding separators):
  average **1,981 chars**, p90 **3,768 chars**. These are character counts,
  not measured token/chunk counts.
- Narrative normalization trims outer whitespace and joins nonempty accounts
  in report order with `\n\n`, preceded by `— Report 1 —\n` / `— Report 2 —\n`.
  Preserve synopsis verbatim. Planned document construction is
  `synopsis + "\n\n" + narrative`; later chunking prepends synopsis per chunk
  and uses the embedding model's tokenizer.

## Field mapping (spec §5 → actual export)

| Stored field | Source column | Rule |
|---|---|---|
| `acn` | `acn_num_ACN` | Trim; require a nonempty numeric string. Dedicated report key wins over mirrored Person 1 accession. |
| `report_month`, `report_year` | `Time_Date` | Validate `YYYYMM`; preserve month precision. |
| `anomaly_codes` | `Events_Anomaly` | Split on `;`, trim, discard empty fragments; exact labels. |
| `flight_phase` | `Aircraft 1.9_Flight Phase` | Nonempty 46,104/47,723. Aircraft 1 represents the primary aircraft; drop Aircraft 2, no fallback. |
| `aircraft_category` | `Aircraft 1.2_Make Model Name` | Nonempty 47,594/47,723; preserve make/model verbatim. Drop Aircraft 2, no fallback. |
| `synopsis` | `Report 1.2_Synopsis` | Only synopsis column, preserved verbatim. |
| `narrative` | `Report 1_Narrative` + `Report 2_Narrative` | Both accounts, explicit provenance labels. |
| `source_dataset`, `source_revision` | Pinned download identity | Dataset ID and full revision SHA. |
| `content_hash` | Normalized report | SHA-256 of compact UTF-8 JSON in `Report` dataclass field order, including provenance, `ensure_ascii=False`. |

The eight mapped source keys must exist; empty/null optional text is allowed.
All 111 known columns are allowlisted, but only mapped fields enter the report.
Unknown columns or missing required keys fail with file/line context.
`Assessments.1_Primary Problem`, `Person 1.7_Human Factors`, other Person 1/2
twins, callbacks, and every remaining column are intentionally dropped.

## Full-corpus candidate categories

Counts are label assignments, not disjoint report sets.

| Exact label | Reports | Rationale |
|---|---:|---|
| `Ground Incursion Runway` | 1,245 | Jargon/acronym-heavy incursions and hold-short clearances. |
| `Deviation - Altitude Excursion From Assigned Altitude` | 2,413 | Paraphrase-heavy altitude deviations. |
| `Conflict NMAC` | 2,934 | NMAC / TCAS RA vocabulary and varied descriptions. |
| `Aircraft Equipment Problem Critical` | 8,822 | Technical vocabulary and ample volume. |

Union: **14,994 unique reports (31.4%)**; **14,574** carry exactly one selected
label, **420** exactly two, none three or four. The broad
`Deviation / Discrepancy - Procedural Published Material / Policy` label is
not selected: **24,171** reports would dominate the subset.

## Year distribution and validation slice

| Year | Full corpus | Step 1 slice |
|---|---:|---:|
| 2012 | 5,056 | 111 |
| 2013 | 4,475 | 99 |
| 2014 | 4,577 | 94 |
| 2015 | 5,971 | 116 |
| 2016 | 2,823 | 54 |
| 2017 | 5,216 | 115 |
| 2018 | 3,071 | 70 |
| 2019 | 6,427 | 132 |
| 2020 | 4,974 | 102 |
| 2021 | 4,536 | 101 |
| 2022 | 597 | 6 |

Selection: first **1,000 unique nonempty-narrative ACNs** in file order
train → validation → test, first occurrence retained. All 1,000 come from train.
This is deterministic, with **no random sampling/seed**, category filter, or
recent-years-first sort. It validates ingestion; it is not the final balanced
evaluation corpus. The future ~5,000 selection must use a fixed seed and
document selection order, temporal skew, label counts, and overlap.

Slice selected-label counts: runway **20**, altitude **68**, NMAC **75**,
critical equipment **193**. **657** reports have no selected label, **330**
exactly one, **13** exactly two; selected-label union **343**.

## Step 1 acceptance evidence

- Initial import: **1,000 inserted**, 0 skipped/updated/failed/dropped/duplicates.
- Repeat: **1,000 skipped**, 0 inserted/updated/failed/dropped/duplicates;
  report hashes/counts unchanged, zero duplicate keys/chunk pairs.
- Spot checks: **1574675**, **1437983**, **1701562** match raw source for all
  stored fields/hash. Narrative order/labels, month parsing, anomaly splitting
  independently verified. The first and third include Report 2.
- At Step 1 completion: **0 chunks, 0 index builds**. Auxiliary `ingest_state` records the
  report-only stage/configuration and never claims an active vector index.
  Report-only CLI rejects changes to existing indexed content; unchanged rows
  skip only when their hash and active configuration match. The prepared-chunk
  write seam supports atomic replacement without implementing chunking/models.
- PostgreSQL integration tests check successful replacement, exception rollback,
  and **process kill after replacement report/chunk writes but before commit**.
  Prior report, chunks, ingestion state, and index metadata remain intact.
  Tests use isolated temporary schemas and synthetic vectors, not the slice.
- Configuration changes invalidate skips; ready-index mismatches fail loudly.
  Initial vector dimension is the default model's **384**; future model changes
  require explicit offline reindex/migration.

Full-file inspection does not import all 47,723 reports into PostgreSQL.
