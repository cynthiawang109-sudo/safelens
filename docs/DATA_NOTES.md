# DATA_NOTES — ASRS Corpus (draft, pre-filled from live inspection)

Status: **draft prepared by Sunny on 2026-11-15** by actually downloading and
inspecting the dataset (test + validation splits, 9,068 reports). Numbers marked
*(sample)* come from that 19% sample and must be re-confirmed on the full ingest
run; field names and formats below are verified facts, not assumptions.

Final home of this file: `docs/DATA_NOTES.md` in the `safelens` repo. Update the
*(sample)* figures with full-corpus counts during the first ingest and flip the
status line to final.

## Source

- Hugging Face dataset: `elihoole/asrs-aviation-reports`
- Revision (commit sha): `f1e681e92cddae20d01fc498d685f1cf6a052d34` (last modified 2022-07-15)
- License: Apache-2.0 (dataset card); underlying reports are U.S. government (NASA ASRS) public data
- Format: JSONL, three files — train 270 MB / validation 30 MB / test 33 MB
- Total reports per dataset card: **47,723** (the train split alone is 38,655 —
  earlier third-party citations of "38,655 reports" refer to the train split, and
  Berkeley's "47,723" matches this dataset's full size, i.e. this is the corpus
  the reference project used)
- **Corpus decision:** the Mini/flagship corpus is all three splits concatenated,
  deduplicated by ACN. There is no ML training here, so split boundaries carry no
  meaning for retrieval; record the decision, do not silently use train only.
- Raw JSONL files stay out of Git (`data/` is gitignored); this file + the loader
  script are the reproducibility record.

## Verified schema facts (sample: 9,068 reports)

- **111 columns**, flattened export names of the form `<Section>[.n]_<Field>`.
- `acn_num_ACN`: present on every row, **unique in sample (0 duplicates)** → primary key.
- `Time_Date`: string `YYYYMM` (e.g. `201510`), range in sample 201201–202203,
  111 distinct months. There is **no day/time anywhere** in the record — this is
  what makes the "exact day and time" abstention control valid.
  → `report_month = YYYY-MM`, `report_year = YYYY`.
- `Events_Anomaly`: present on 9,062/9,068 rows. Semicolon-joined **multi-label**:
  78% of reports carry more than one label; 75 distinct labels in the sample
  (Berkeley cites 92 across the full corpus). Split on `;`, trim whitespace.
  Some labels are fragments of a controlled vocabulary split (e.g. a bare
  `Critical` / `Less Severe` alongside `Aircraft Equipment Problem Critical`) —
  match labels by exact string, never by substring.
- Narratives: `Report 1_Narrative` present on **100%** of rows, avg 1,574 chars.
  `Report 2_Narrative` present on **2,117/9,068 (23%)**, avg 945 chars.
  → Chunking text concatenates both with `— Report 1 —` / `— Report 2 —`
  provenance labels, per spec §4. Dropping Report 2 would lose a second
  perspective on nearly a quarter of the corpus.
- Synopsis: `Report 1.2_Synopsis` present on 100% of rows, avg 170 chars,
  max 898. There is **no Report 2 synopsis**.
- Document text (synopsis + narratives): avg 1,964 chars, p90 3,731 chars
  → at 400–600 token chunks with the synopsis prepended, expect roughly
  1–2 chunks per report (~7,500 chunks for the 5,000-report Mini subset).

## Field mapping (spec §5 → actual export columns)

| Spec field | Source column | Notes |
|---|---|---|
| `acn` | `acn_num_ACN` | Also mirrored in `Person 1.10_ASRS Report Number.Accession Number`; use `acn_num_ACN` |
| `report_month`, `report_year` | `Time_Date` | `YYYYMM` string, month granularity only |
| `anomalies[]` | `Events_Anomaly` | Split on `;`, exact-string labels |
| `flight_phase` | `Aircraft 1.9_Flight Phase` | Nonempty 8,757/9,068 *(sample)*; `Aircraft 2.9_Flight Phase` exists for the second aircraft — Mini stores Aircraft 1 only |
| `aircraft_category` | `Aircraft 1.2_Make Model Name` | Nonempty 9,047/9,068 *(sample)*; values mix make/model strings (e.g. `B737-800`, `A320`); store verbatim |
| `synopsis` | `Report 1.2_Synopsis` | 100% coverage |
| `narrative` | `Report 1_Narrative` + `Report 2_Narrative` | Concatenate with provenance labels (see above) |
| (metadata, optional) | `Assessments.1_Primary Problem`, `Person 1.7_Human Factors` | Not in the Mini schema; candidates for flagship metadata |

Everything not listed is dropped at ingest for the Mini (the loader keeps a
column allowlist, so export surprises fail loudly instead of leaking in).

## Mini subset — category selection (decided from sample counts)

Full-corpus estimates scale the sample by ≈ ×5.26.

| Category (exact label) | Sample | Est. full | Why selected |
|---|---|---|---|
| `Ground Incursion Runway` | 252 | ~1,326 | Jargon/acronym-dense (runway incursion, hold short, LUAW); the flagship's headline category |
| `Deviation - Altitude Excursion From Assigned Altitude` | 481 | ~2,530 | Paraphrase-heavy ("busted the altitude", "climbed through assigned") — stresses dense retrieval |
| `Conflict NMAC` | 557 | ~2,930 | Defined by an acronym (NMAC, TCAS RA); mixed keyword/dense behavior |
| `Aircraft Equipment Problem Critical` | 1,662 | ~8,740 | Large technical-vocabulary pool; anchors volume |

Union of the four labels: **2,875 unique reports in the sample (31.7%)** →
~15,100 in the full corpus. Sampling 5,000 is comfortable for every category
except Ground Incursion Runway, where the sample will take most of the pool —
expected and recorded, not a problem.

Explicitly **not** selected: `Deviation / Discrepancy - Procedural Published
Material / Policy` (4,625 in sample — 51% of all reports carry it; as a subset
category it would swamp the corpus and its queries are mostly checklist/policy
disputes, a different retrieval problem).

## Open items to confirm on the full ingest run

- [ ] Full-corpus counts replace every *(sample)* figure above
- [ ] ACN uniqueness across all three splits after concatenation
- [ ] Distinct anomaly label count on the full corpus (expect ~92)
- [ ] Any rows with empty `Report 1_Narrative` at full scale (0 in sample)
- [ ] Final subset counts per label + year distribution + multi-label overlap,
      recorded per spec §4 (fixed seed, documented selection order)
