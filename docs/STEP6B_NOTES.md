<!-- fusion-bakeoff-step6b -->
## Step 6B: fusion-weight mini bake-off (development)

Corpus: 20,000 reports, 28,306 embedded chunks; ready build 4. All 28 category queries; no category filter, label retrieval features, query edits, or generation calls. These are development results, not final-test estimates.

### Fixed protocol

The eight dense:lexical ratios and two families were fixed in `eval/step6b_design.json` before results. Each leg retains at most 50 reports after fetching 100 chunks and max-score aggregation by ACN. Weighted RRF uses wd/(60+rank_dense) + wl/(60+rank_lexical), missing components contribute zero; ties break by ACN. Normalized fusion applies per-query min-max to each complete candidate leg, then wd*d + wl*l; absent reports and constant-score legs contribute zero. Zero-weight legs are excluded, and pure-leg endpoints preserve the exact source ranking.

Select maximum Category P@10, then Hit@10, then smaller relative lexical weight wl/(wd+wl). Remaining exact ties are reported as co-winners; fixed family order only picks a display representative. No extra weights were tried. P@10 uses denominator 10, including underfill. Category agreement is not judged relevance.

Candidate cache: reused complete Step 6B candidate recapture; original Step 6 cache contains only top ten, so both legs were captured once at full depth. The original Step 6 cache is preserved. The full-depth recapture matches all original top-ten ACN orders and representative chunk IDs; equal-weight hybrid ACN orders also match Step 6. All grid trials subsequently use the identical cached lists; no retrieval per weight.

### Full grid

| Family | Dense:BM25 | Category P@10 | Hit@10 | Delta P@10 vs dense |
|---|---:|---:|---:|---:|
| weighted_rrf | 1:0 | 0.6286 | 0.9643 | +0.0000 |
| weighted_rrf | 10:1 | 0.6429 | 1.0000 | +0.0143 |
| weighted_rrf | 5:1 | 0.6429 | 1.0000 | +0.0143 |
| weighted_rrf | 3:1 | 0.6107 | 1.0000 | -0.0179 |
| weighted_rrf | 2:1 | 0.6107 | 1.0000 | -0.0179 |
| weighted_rrf | 1:1 | 0.5786 | 1.0000 | -0.0500 |
| weighted_rrf | 1:2 | 0.5964 | 1.0000 | -0.0321 |
| weighted_rrf | 0:1 | 0.5714 | 1.0000 | -0.0571 |
| normalized_scores | 1:0 | 0.6286 | 0.9643 | +0.0000 |
| normalized_scores | 10:1 | 0.6250 | 0.9643 | -0.0036 |
| normalized_scores | 5:1 | 0.6214 | 0.9643 | -0.0071 |
| normalized_scores | 3:1 | 0.6321 | 0.9643 | +0.0036 |
| normalized_scores | 2:1 | 0.6214 | 0.9643 | -0.0071 |
| normalized_scores | 1:1 | 0.6179 | 0.9643 | -0.0107 |
| normalized_scores | 1:2 | 0.5786 | 1.0000 | -0.0500 |
| normalized_scores | 0:1 | 0.5714 | 1.0000 | -0.0571 |

### Best configuration and recommendation

Display representative: **weighted_rrf 10:1**. Co-winners under the complete selection rule: weighted_rrf:10:1. Category P@10 **0.6429**, dense **0.6286**, margin **+0.0143** (+4 matching reports across 280 slots). Per-query **8 wins / 5 losses / 15 ties** versus dense.

Recommend adopting weighted_rrf 10:1 as the flagship default under the fixed primary selection rule: Category P@10 improves by +0.0143 on this development set. Adoption remains a separate decision.

Although 8/28 queries improve and 5/28 worsen, the net gain is only 4 matching reports. The two largest positive flips (equip-l2-2, ri-l1-2) contribute 4 matches; excluding those queries leaves +0 net matches. The overall win therefore does rest on two query flips in aggregate; it is a fragile development margin, not broad evidence of superiority.

Boundary-grid winner: **True** (dense-heaviest mixed ratio tested; pure-leg endpoints also evaluated). The grid was not extended. Production defaults and all production code paths remain unchanged; adopting any recommendation needs Cynthia's separate decision. Step 7 has not started.

### Per-query comparison versus dense

| Query | Dense Category P@10 | Best Category P@10 | Delta | Outcome |
|---|---:|---:|---:|---|
| ri-l1-1 | 0.900 | 0.900 | +0.000 | tie |
| ri-l1-2 | 0.700 | 0.900 | +0.200 | win |
| ri-l1-3 | 0.000 | 0.100 | +0.100 | win |
| ri-l1-4 | 0.200 | 0.200 | +0.000 | tie |
| ri-l1-5 | 1.000 | 0.900 | -0.100 | loss |
| alt-l1-1 | 0.900 | 0.800 | -0.100 | loss |
| alt-l1-2 | 0.200 | 0.300 | +0.100 | win |
| alt-l1-3 | 0.600 | 0.700 | +0.100 | win |
| alt-l1-4 | 0.400 | 0.400 | +0.000 | tie |
| alt-l1-5 | 0.200 | 0.200 | +0.000 | tie |
| nmac-l1-1 | 1.000 | 1.000 | +0.000 | tie |
| nmac-l1-2 | 1.000 | 1.000 | +0.000 | tie |
| nmac-l1-3 | 0.700 | 0.800 | +0.100 | win |
| nmac-l1-4 | 0.400 | 0.400 | +0.000 | tie |
| nmac-l1-5 | 0.800 | 0.800 | +0.000 | tie |
| equip-l1-1 | 0.900 | 0.900 | +0.000 | tie |
| equip-l1-2 | 0.500 | 0.500 | +0.000 | tie |
| equip-l1-3 | 0.700 | 0.800 | +0.100 | win |
| equip-l1-4 | 0.900 | 0.900 | +0.000 | tie |
| equip-l1-5 | 0.700 | 0.700 | +0.000 | tie |
| ri-l2-1 | 0.900 | 0.900 | +0.000 | tie |
| ri-l2-2 | 0.600 | 0.500 | -0.100 | loss |
| alt-l2-1 | 0.400 | 0.300 | -0.100 | loss |
| alt-l2-2 | 0.600 | 0.700 | +0.100 | win |
| nmac-l2-1 | 0.500 | 0.300 | -0.200 | loss |
| nmac-l2-2 | 0.600 | 0.600 | +0.000 | tie |
| equip-l2-1 | 0.800 | 0.800 | +0.000 | tie |
| equip-l2-2 | 0.500 | 0.700 | +0.200 | win |

### Layer-2 partial-coverage development signals

Uses the runtime `eval/qrels.jsonl` (51b93d1b97c873dbf6b6489a436bcde3cd0724b7e30f4acafc0bff0f78029465). Same Step 6 condensed protocol: remove unknown pairs from the original top ten; precision proxy is relevant/judged, MRR and DCG use condensed ranks, linear gains 2/1/0, ideal over known qrels at the same judged depth. No judged hits means undefined, excluded from macro means (query counts printed). Coverage = judged/10 including underfill; coverage of returned results is separately recorded in JSON. Unknowns never receive grade zero. These are **partial-coverage development signals**, not full-coverage scores and not used for selection. Condensation and the historical pooling can favor the original retrievers.

| Configuration | Precision proxy (coverage) | Condensed MRR (coverage) | Condensed nDCG (coverage) | Defined queries / 8 |
|---|---:|---:|---:|---:|
| best | 0.9594 (93.8%) | 1.0000 (93.8%) | 0.8491 (93.8%) | 8 |
| dense | 0.9500 (100.0%) | 1.0000 (100.0%) | 0.8457 (100.0%) | 8 |

| Query | Configuration | Judged / returned | Precision proxy (coverage) | MRR (coverage) | nDCG (coverage) |
|---|---|---:|---:|---:|---:|
| ri-l2-1 | best | 10 / 10 | 1.0000 (100.0%) | 1.0000 (100.0%) | 0.8353 (100.0%) |
| ri-l2-2 | best | 10 / 10 | 0.9000 (100.0%) | 1.0000 (100.0%) | 0.8028 (100.0%) |
| alt-l2-1 | best | 9 / 10 | 1.0000 (90.0%) | 1.0000 (90.0%) | 0.9298 (90.0%) |
| alt-l2-2 | best | 10 / 10 | 1.0000 (100.0%) | 1.0000 (100.0%) | 0.9477 (100.0%) |
| nmac-l2-1 | best | 8 / 10 | 0.8750 (80.0%) | 1.0000 (80.0%) | 0.7378 (80.0%) |
| nmac-l2-2 | best | 10 / 10 | 0.9000 (100.0%) | 1.0000 (100.0%) | 0.7278 (100.0%) |
| equip-l2-1 | best | 9 / 10 | 1.0000 (90.0%) | 1.0000 (90.0%) | 0.9646 (90.0%) |
| equip-l2-2 | best | 9 / 10 | 1.0000 (90.0%) | 1.0000 (90.0%) | 0.8471 (90.0%) |
| ri-l2-1 | dense | 10 / 10 | 1.0000 (100.0%) | 1.0000 (100.0%) | 0.8494 (100.0%) |
| ri-l2-2 | dense | 10 / 10 | 0.9000 (100.0%) | 1.0000 (100.0%) | 0.8550 (100.0%) |
| alt-l2-1 | dense | 10 / 10 | 1.0000 (100.0%) | 1.0000 (100.0%) | 0.9334 (100.0%) |
| alt-l2-2 | dense | 10 / 10 | 0.9000 (100.0%) | 1.0000 (100.0%) | 0.8263 (100.0%) |
| nmac-l2-1 | dense | 10 / 10 | 0.9000 (100.0%) | 1.0000 (100.0%) | 0.7629 (100.0%) |
| nmac-l2-2 | dense | 10 / 10 | 0.9000 (100.0%) | 1.0000 (100.0%) | 0.7457 (100.0%) |
| equip-l2-1 | dense | 10 / 10 | 1.0000 (100.0%) | 1.0000 (100.0%) | 0.9376 (100.0%) |
| equip-l2-2 | dense | 10 / 10 | 1.0000 (100.0%) | 1.0000 (100.0%) | 0.8552 (100.0%) |

### Reproduction and acceptance

Run `uv run python eval/run_fusion_bakeoff.py` with `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8`; set `HF_HUB_OFFLINE=1` for the already cached embedding model. Full configuration, all 448 grid/query rows, input and protected hashes, cache provenance, historical equivalence checks, and runtime qrels version are in `eval/experiment_step6b.json`. Detailed evidence stays in ignored `data/eval_rankings_step6b_candidates.json`. No corpus writes, reindexing, new judgments, production default changes, or additional grid trials.

Acceptance checks: **46 tests passed** (all 42 prior tests plus four new fusion tests), Ruff and `git diff --check` passed. Weighted-RRF 1:1 matches Step 6 hybrid rankings, and zero lexical weight reproduces dense rankings exactly. Both full grid families are reported; all protected hashes and prior results sections are unchanged.
