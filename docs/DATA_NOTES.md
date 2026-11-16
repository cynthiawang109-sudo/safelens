# DATA_NOTES — ASRS Corpus

Status: **full-corpus inspection finalized on 2026-11-15** for Step 1.
Counts below cover all three pinned files. The 1,000-report validation slice
is imported. Step 1 evidence below records its pre-index state; Step 2 indexes
the same slice (see `STEP2_VALIDATION.json`). Step 3 supersedes that slice with
the 5,000-report subset documented below; earlier figures remain historical.

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
evaluation corpus. Step 3 selection records the seed, order, temporal skew,
label counts, and overlap below.

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

## Step 3 — final Mini subset (5,000 reports)

The versioned selection is [eval/subset_manifest.json](../eval/subset_manifest.json),
created by `uv run python -m safelens.subset` with **seed 20261115**.
Deduplicate ACNs first, retaining the first occurrence in train → validation →
test order. Sort ACNs as strings before using a private Python 3.12
`random.Random(seed)` and `sample`. No recent-years-first sorting is used.

In the fixed category order runway → altitude → NMAC → critical equipment,
sample up to **1,250 previously unselected reports per pass**. The runway pool
has only 1,245 reports, all selected. Later passes each add 1,250; fill the final
five places from the sorted remaining union with the same RNG. ACNs in the
manifest are sorted; overlapping categories count a report only once.

| Exact selected label | Final label assignments |
|---|---:|
| `Ground Incursion Runway` | 1,245 |
| `Deviation - Altitude Excursion From Assigned Altitude` | 1,305 |
| `Conflict NMAC` | 1,352 |
| `Aircraft Equipment Problem Critical` | 1,390 |

**4,708** reports carry exactly one selected label; **292** carry exactly two;
none carry three or four. The **5,292 assignments** therefore describe exactly
**5,000 unique reports**. This is a category-balanced development corpus, not a
random sample of ASRS as a whole; all available runway reports are included.

| Year | Selected reports | Subset share | Full-corpus share |
|---|---:|---:|---:|
| 2012 | 630 | 12.60% | 10.59% |
| 2013 | 509 | 10.18% | 9.38% |
| 2014 | 490 | 9.80% | 9.59% |
| 2015 | 574 | 11.48% | 12.51% |
| 2016 | 262 | 5.24% | 5.92% |
| 2017 | 482 | 9.64% | 10.93% |
| 2018 | 295 | 5.90% | 6.44% |
| 2019 | 572 | 11.44% | 13.47% |
| 2020 | 455 | 9.10% | 10.42% |
| 2021 | 668 | 13.36% | 9.50% |
| 2022 | 63 | 1.26% | 1.25% |

Category selection produces temporal skew even without date-based sampling:
2021 is overrepresented by about **3.86 percentage points**, while 2019 is
underrepresented by about **2.03 points**. Do not generalize evaluation numbers
to the original corpus distribution.

### Superseding the first-1,000 corpus

Run `uv run python -m safelens.cli reindex --subset-manifest eval/subset_manifest.json`.
The command reproduces the manifest from the pinned files before building.
It stages all selected normalized reports and their chunks under the offline
lock. The final transaction deletes old chunks and reports, inserts exactly the
5,000 selected reports, installs the staged embeddings, replaces ingestion
state, supersedes the old ready build, and publishes the new ready build.
Deleting non-subset reports from `reports` and `chunks` ensures they cannot
appear in retrieval; they are not merely hidden by an optional search filter.
Only **122** reports overlap the former first-1,000 slice: **878** old slice
reports are excluded and **4,878** selected reports are newly included.
Failure before commit restores the entire previous corpus/index. Tests exercise
both rollback and successful exclusion of old reports.

The selected corpus snapshot is SHA-256 of sorted `acn:content_hash\n` pairs:
`df6c66bb1efd9beba7bf3fd07de19446a0639db2228bed4d079b3d4201349e09`.
The evaluation runner checks the active ACN set and this hash against the
manifest before running unfiltered benchmarks. The final index counts and
configuration are recorded in `eval/experiment.json`.

## Step 5 — flagship 20,000-report selection

The new manifest is `eval/corpus_manifest_20k.json`; the Mini manifest above
remains unchanged. Selection seed: **20261120**. Retain all **5,000** Mini
ACNs, deduplicate the pinned full source by ACN first (train → validation → test,
first occurrence wins), and remove those Mini ACNs from the sampling frame.
There are **42,723** remaining unique reports. Sample **15,000 additions**
across all anomaly categories without a category filter.

Year quotas use Hamilton/largest-remainder allocation: floor each remaining
year population's proportional share of 15,000, then distribute the residual
to the largest fractional remainders, ties by ascending year. Within each year,
sort ACNs as strings and use a private Python 3.12 `random.Random(seed).sample`;
process years in ascending order. The manifest records both final and added
ACN lists, quota populations, per-year counts, all observed label counts, and
the normalized-record snapshot hash.

| Year | Remaining population | Added | Final corpus |
|---|---:|---:|---:|
| 2012 | 4,426 | 1,554 | 2,184 |
| 2013 | 3,966 | 1,392 | 1,901 |
| 2014 | 4,087 | 1,435 | 1,925 |
| 2015 | 5,397 | 1,895 | 2,469 |
| 2016 | 2,561 | 899 | 1,161 |
| 2017 | 4,734 | 1,662 | 2,144 |
| 2018 | 2,776 | 975 | 1,270 |
| 2019 | 5,855 | 2,056 | 2,628 |
| 2020 | 4,519 | 1,587 | 2,042 |
| 2021 | 3,868 | 1,358 | 2,026 |
| 2022 | 534 | 187 | 250 |
| Total | 42,723 | 15,000 | 20,000 |

The final corpus contains **75 distinct observed exact anomaly labels**.
The sampling frame permits every label, but very rare labels are not guaranteed
to appear. Four original category counts become runway **1,245**, altitude
**1,693**, NMAC **1,917**, and critical equipment **4,005**. Counts remain
multi-label assignments. Retaining the category-balanced Mini means the final
20k is not a fresh proportional sample of the whole corpus: only the additions
are proportional to the remaining year populations.

Snapshot SHA-256:
`c47c73dae040d26dba7221e50c6cbeb457859632f6ef385e7fdf338b03db850b`.
Incremental indexing reuses existing chunks only when the report content hash,
active index configuration, and ingestion state match and embeddings are
complete. Only added/changed reports are chunked and embedded; an atomic ready
build switch publishes the union. No absence-based deletion is allowed by the
incremental growth command. The baseline 5k experiment/results are archived as
`eval/experiment_5k.json` and `eval/results_5k.md`.

All Mini queries, the human-filled judging pool, and qrels are retained.
This preserves the meaning of those labels, but does not label newly retrieved
20k top-ten candidates. The evaluator checks exact query/ACN judgment coverage
and must leave full Layer-2 scores pending when that coverage is incomplete.

Step 3 contains **20 dedicated Layer-1 queries + 8 additional Layer-2 pool
queries + 3 controls**. Category agreement is reported for the 20 primary
queries and for all 28 category queries. No human relevance labels or
generation outcomes are assigned in Step 3. The only redistributed source
excerpts are the synopsis cells explicitly requested for the blinded judging
CSV; raw files and full retrieved passages stay in ignored `data/`.
