# Step 7D — single frozen final evaluation

<!-- frozen-final-test-step7d -->
## Final test (frozen)

Run date: **2026-11-16 (America/New_York)**; started 2026-11-17T03:22:23.626873+00:00, completed 2026-11-17T03:24:12.880808+00:00. These are **single-run frozen final-test results**, not development numbers. One run was made, with no tuning or second execution to check scores. Disappointing results are retained.

Freeze commit: `1b8d294bba143dec42b7e76b63787dc1f334fec1`. Production-design commit recorded at construction: `67a80ab230da8e32d4cf384215b34c8e596dce17`. Query SHA-256: `2160adf50cb818fce182c8c431e1005587acecd63261005241bef3a90a4ec2de`. Final qrels SHA-256: `b7288db09abe8525168a49a1f717900a06d89797309b8355d058e296424d62f3`.

Pre-flight query, pool identity, production code/configuration, installed software, index and corpus checks all matched the sealed record. No post-freeze production changes were made. The 89 human judgments were validated by the existing importer through a temporary in-memory/file Layer-2 schema adapter; frozen final queries and development qrels were not altered.

### Strict mechanism retrieval

Eight mechanism queries; dense and production dense:BM25 10:1 hybrid, report-level RRF k=60. 100 chunk candidates → best chunk per ACN → 50 reports per leg; deterministic ACN ties; no category filter. **100% judgment coverage of both retrievers' top tens**, no unknowns zero-filled. P@10 denominator 10; relevance grade ≥1; MRR over top ten; nDCG@10 uses linear gains 2/1/0 and each query's complete frozen pooled ideal.

| Retriever | P@10 | MRR | nDCG@10 | Judged top-ten coverage |
|---|---:|---:|---:|---:|
| dense | 0.9375 | 1.0000 | 0.8487 | 100% |
| hybrid | 0.9625 | 1.0000 | 0.8945 | 100% |

| Query | Retriever | P@10 | MRR | nDCG@10 | Coverage |
|---|---|---:|---:|---:|---:|
| ft-ri-1 | dense | 1.0000 | 1.0000 | 0.8569 | 100% |
| ft-ri-1 | hybrid | 1.0000 | 1.0000 | 0.9485 | 100% |
| ft-ri-2 | dense | 1.0000 | 1.0000 | 0.8478 | 100% |
| ft-ri-2 | hybrid | 1.0000 | 1.0000 | 0.9604 | 100% |
| ft-alt-1 | dense | 1.0000 | 1.0000 | 0.9959 | 100% |
| ft-alt-1 | hybrid | 1.0000 | 1.0000 | 0.9579 | 100% |
| ft-alt-2 | dense | 0.9000 | 1.0000 | 0.7653 | 100% |
| ft-alt-2 | hybrid | 1.0000 | 1.0000 | 0.8797 | 100% |
| ft-nmac-1 | dense | 0.9000 | 1.0000 | 0.8836 | 100% |
| ft-nmac-1 | hybrid | 0.9000 | 1.0000 | 0.8737 | 100% |
| ft-nmac-2 | dense | 1.0000 | 1.0000 | 0.9172 | 100% |
| ft-nmac-2 | hybrid | 1.0000 | 1.0000 | 0.8830 | 100% |
| ft-eq-1 | dense | 1.0000 | 1.0000 | 0.8689 | 100% |
| ft-eq-1 | hybrid | 1.0000 | 1.0000 | 0.8611 | 100% |
| ft-eq-2 | dense | 0.7000 | 1.0000 | 0.6541 | 100% |
| ft-eq-2 | hybrid | 0.8000 | 1.0000 | 0.7919 | 100% |

### Production Ask outcomes and cost

Each of all twelve questions was sent once to the frozen production HTTP Ask path, including its conditional grading/rewrite workflow and SQL routing. No caller-specific flags or category filters were supplied. Costs are actual provider usage and measured HTTP request wall latency (local FastAPI TestClient); graph-only latency is also in the record. Model/index initialization and non-final warmup are excluded. Provider retries remain disabled. No request was reissued.

| Query | Kind | Status | Validated cited reports | Input tokens | Output tokens | Latency s | Calls | Retries |
|---|---|---|---:|---:|---:|---:|---:|---:|
| ft-ri-1 | mechanism | partial | 2 | 4894 | 347 | 9.06 | 2 | 0 |
| ft-ri-2 | mechanism | answered | 2 | 4234 | 361 | 5.83 | 2 | 0 |
| ft-alt-1 | mechanism | partial | 2 | 5515 | 358 | 6.46 | 2 | 0 |
| ft-alt-2 | mechanism | partial | 2 | 4840 | 350 | 8.08 | 2 | 0 |
| ft-nmac-1 | mechanism | partial | 2 | 5075 | 364 | 5.51 | 2 | 0 |
| ft-nmac-2 | mechanism | partial | 2 | 4343 | 322 | 5.64 | 2 | 0 |
| ft-eq-1 | mechanism | partial | 2 | 8218 | 588 | 13.30 | 4 | 1 |
| ft-eq-2 | mechanism | answered | 1 | 6680 | 550 | 10.31 | 4 | 1 |
| ft-ctl-1 | control | insufficient_evidence | 0 | 7514 | 675 | 13.54 | 5 | 2 |
| ft-ctl-2 | control | insufficient_evidence | 0 | 7048 | 608 | 14.40 | 5 | 2 |
| ft-cnt-1 | count | partial | 2 | 7051 | 519 | 10.41 | 4 | 1 |
| ft-cnt-2 | count | answered | 0 | 0 | 0 | 0.08 | 0 | 0 |

Mean across all 12 questions: **5451.0 input tokens**, **420.2 output tokens**, **8.55s**, 2.83 provider calls and 0.58 retries per question. A SQL-only answer has zero provider tokens. Local embedding latency is included in request wall time, not provider-token counts.

### Frozen controls

| Control | Status | Invented ACNs detected | Pass |
|---|---|---:|---|
| ft-ctl-1 | insufficient_evidence | 0 | True |
| ft-ctl-2 | insufficient_evidence | 0 | True |

### Frozen aggregate counts

Expected counts were sealed during construction using the production SQL executor with explicit metadata filters. The run did not substitute those answers for the system's natural-language routing. `null` means the system did not return that aggregate field; it is reported as a failed comparison rather than guessed or silently repaired.

| Query | Status | Expected count | System count | Expected filters | System-stated filters | Expected denominator | System-stated denominator | Exact match |
|---|---|---:|---:|---|---|---:|---:|---|
| ft-cnt-1 | partial | 272 | null | `{"anomaly_category": "Conflict NMAC", "year_end": 2019, "year_start": 2019}` | `null` | 20000 | null | False |
| ft-cnt-2 | answered | 2469 | 2469 | `{"anomaly_category": null, "year_end": 2015, "year_start": 2015}` | `{"anomaly_category": null, "year_end": 2015, "year_start": 2015}` | 20000 | 20000 | True |

Exact match above requires the numeric count, filters, and denominator to match; separate numeric/filter/denominator flags and complete system answers/routing traces are in the experiment record. Counts are voluntary ASRS reports, not incident rates.

### Citation precision against frozen qrels

Scored responses are only `answered` or `partial`. Each cited ACN counts once per response. A known pair supports when grade ≥1; grade 0 is non-support. Outside-pool pairs are **unknown**, never scored as wrong. Refusals are listed but excluded from citation precision; count questions have no final relevance judgments, so any narrative citations they produce are unknown. Report-level relevance does not prove every generated claim.

| Scope | Supporting / judged pairs | Precision on judged | Judged / cited pairs | Coverage | Unknown pairs |
|---|---:|---:|---:|---:|---:|
| all answered/partial | 14/14 | 100.00% | 14/17 | 82.35% | 3 |
| mechanism answered/partial | 14/14 | 100.00% | 14/15 | 93.33% | 1 |

| Query | Status | Known supporting / judged citations | Precision | Judged coverage | Grade-0 ACNs | Unknown ACNs |
|---|---|---:|---:|---:|---|---|
| ft-ri-1 | partial | 2/2 | 100.00% | 100.00% | — | — |
| ft-ri-2 | answered | 2/2 | 100.00% | 100.00% | — | — |
| ft-alt-1 | partial | 2/2 | 100.00% | 100.00% | — | — |
| ft-alt-2 | partial | 2/2 | 100.00% | 100.00% | — | — |
| ft-nmac-1 | partial | 2/2 | 100.00% | 100.00% | — | — |
| ft-nmac-2 | partial | 2/2 | 100.00% | 100.00% | — | — |
| ft-eq-1 | partial | 2/2 | 100.00% | 100.00% | — | — |
| ft-eq-2 | answered | 0/0 | N/A | 0.00% | — | 1286823 |
| ft-ctl-1 | insufficient_evidence | 0/0 | N/A (refusal) | N/A | — | — |
| ft-ctl-2 | insufficient_evidence | 0/0 | N/A (refusal) | N/A | — | — |
| ft-cnt-1 | partial | 0/0 | N/A | 0.00% | — | 1691217, 1692218 |
| ft-cnt-2 | answered | 0/0 | N/A | N/A | — | — |

### Observations and limitations

- Mechanism responses: {'partial': 6, 'answered': 2}. These statuses are observed outputs, not independent claim-level faithfulness judgments.
- Controls: 2/2 passed; aggregate counts: 1/2 exact matches. Failures were not corrected or retried.
- Both strict retrieval tables have complete frozen judgment coverage. Citation coverage can be lower because the production workflow can rewrite queries or cite reports outside the original frozen pool; those pairs remain unknown.
- Eight authored mechanism questions and two controls are a small single frozen sample; no broad superiority or safety conclusions follow.
- ft-cnt-1 did not return the sealed aggregate result. System aggregate payload: None. The unchanged routing behavior is disclosed, not patched.

Complete per-query answers, trace grades/queries, actual usage, import provenance, source/config hashes, and this run's single-run marker are in `eval/experiment_step7d.json`. Passage-bearing response data stay under ignored `data/`. Results were not used to tune the system or to request another run. Development assets remain separate; only this labeled section is appended to the existing results document. Step 8 has not started.

### Final integrity and acceptance audit

The one-shot ledger records exactly 16 requested retrieval calls and 12 distinct production Ask requests, all completed under one run ID. No question was reissued and no second evaluation or automatic resume was attempted. All 89 final qrels match Cynthia's supplied grades; development queries/qrels and production files retain their frozen byte hashes. The original results document remains an exact byte prefix of the appended publication. All returned citation passages match their DB chunks.

The pre-run suite passed **60 tests**, including all 57 prior tests plus three one-shot/reporting safeguards on synthetic fixtures. Ruff and `git diff --check` pass. Post-run checks inspected saved artifacts and DB evidence only; they did not recompute final scores or rerun any final request. The NMAC count-routing failure is preserved. See `docs/STEP7D_VALIDATION.json`. Step 8 was not started.
