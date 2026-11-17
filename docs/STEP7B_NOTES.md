# Step 7B — answer-rate calibration

## Phase 1: diagnosis before behavior changes

Observed the eleven existing requests through the unchanged production HTTP Ask path (real provider), and audited the original Step 7 ablation. The production baseline, raw provider outputs before citation validation, and actual packaged passages are stored locally; the versioned diagnosis includes trace pointers and short explanations. No production behavior changed during this phase.

Codes: (a) grader insufficient despite known qrel-relevant retrieval; (b) grader sufficient, generator refused; generator_after_partial = grader allowed partial evidence but generator refused; (d_signal) fewer known positives after rewrite, with coverage reported rather than counting unknowns as irrelevant. (c) requires evidence of a mechanism dropped, not just a relevant label on an excluded report. (e) means validation stripped an answer; flags alone would not prove the removed answer was grounded.

| Query | Production status | Diagnosis | Known relevant top ten, first → final (judged coverage) | Trace evidence |
|---|---|---|---|---|
| ri-l2-1 | insufficient_evidence | b, d_signal | 10 → 9 (100% → 90%) | `eval/experiment_step7b_diagnosis.json/production_before/ri-l2-1/trace/5/detail/output`: Grader sufficient; generation executed but refused; `eval/experiment_step7b_diagnosis.json/production_before/ri-l2-1/trace/4/detail/top10_acns`: Known-positive count 10 -> 9; coverage 100% -> 90%; unknowns not misses; `eval/experiment_step7_ablation.json/per_question/Hybrid + Rewrite/ri-l2-1/trace/5/detail/output`: Grader sufficient but generator refused |
| ri-l2-2 | insufficient_evidence | b, d_signal | 9 → 6 (100% → 60%) | `eval/experiment_step7b_diagnosis.json/production_before/ri-l2-2/trace/5/detail/output`: Grader sufficient; generation executed but refused; `eval/experiment_step7b_diagnosis.json/production_before/ri-l2-2/trace/4/detail/top10_acns`: Known-positive count 9 -> 6; coverage 100% -> 60%; unknowns not misses; `eval/experiment_step7_ablation.json/per_question/Hybrid + Rewrite/ri-l2-2/trace/5/detail/output`: Grader sufficient but generator refused |
| alt-l2-1 | insufficient_evidence | b, d_signal, generator_after_partial | 9 → 3 (90% → 30%) | `eval/experiment_step7b_diagnosis.json/production_before/alt-l2-1/trace/8/detail/output`: Grader partial; generation executed but refused; `eval/experiment_step7b_diagnosis.json/production_before/alt-l2-1/trace/7/detail/top10_acns`: Known-positive count 9 -> 3; coverage 90% -> 30%; unknowns not misses; `eval/experiment_step7_ablation.json/per_question/Full Agentic/alt-l2-1/trace/3/detail/output`: Grader sufficient but generator refused |
| alt-l2-2 | insufficient_evidence | a, d_signal, generator_after_partial | 10 → 5 (100% → 50%) | `eval/experiment_step7b_diagnosis.json/production_before/alt-l2-2/trace/5/detail/output`: 7 known relevant top-ten reports, grader insufficient; `eval/experiment_step7b_diagnosis.json/production_before/alt-l2-2/trace/8/detail/output`: Grader partial; generation executed but refused; `eval/experiment_step7b_diagnosis.json/production_before/alt-l2-2/trace/7/detail/top10_acns`: Known-positive count 10 -> 5; coverage 100% -> 50%; unknowns not misses |
| nmac-l2-1 | insufficient_evidence | b, d_signal, generator_after_partial | 7 → 3 (80% → 30%) | `eval/experiment_step7b_diagnosis.json/production_before/nmac-l2-1/trace/8/detail/output`: Grader partial; generation executed but refused; `eval/experiment_step7b_diagnosis.json/production_before/nmac-l2-1/trace/7/detail/top10_acns`: Known-positive count 7 -> 3; coverage 80% -> 30%; unknowns not misses; `eval/experiment_step7_ablation.json/per_question/Hybrid + Rewrite/nmac-l2-1/trace/5/detail/output`: Grader sufficient but generator refused |
| nmac-l2-2 | insufficient_evidence | a, b, d_signal | 9 → 2 (100% → 20%) | `eval/experiment_step7b_diagnosis.json/production_before/nmac-l2-2/trace/2/detail/output`: 9 known relevant top-ten reports, grader insufficient; `eval/experiment_step7b_diagnosis.json/production_before/nmac-l2-2/trace/8/detail/output`: Grader sufficient; generation executed but refused; `eval/experiment_step7b_diagnosis.json/production_before/nmac-l2-2/trace/7/detail/top10_acns`: Known-positive count 9 -> 2; coverage 100% -> 20%; unknowns not misses |
| equip-l2-1 | partial | already_supported_response, d_signal | 9 → 8 (90% → 80%) | `eval/experiment_step7b_diagnosis.json/production_before/equip-l2-1/trace/7/detail/top10_acns`: Known-positive count 9 -> 8; coverage 90% -> 80%; unknowns not misses |
| equip-l2-2 | insufficient_evidence | b, d_signal, generator_after_partial | 9 → 4 (90% → 40%) | `eval/experiment_step7b_diagnosis.json/production_before/equip-l2-2/trace/8/detail/output`: Grader partial; generation executed but refused; `eval/experiment_step7b_diagnosis.json/production_before/equip-l2-2/trace/7/detail/top10_acns`: Known-positive count 9 -> 4; coverage 90% -> 40%; unknowns not misses; `eval/experiment_step7_ablation.json/per_question/Hybrid + Rewrite/equip-l2-2/trace/5/detail/output`: Grader sufficient but generator refused |
| control-domain | insufficient_evidence | correct_control_refusal | 0 → 0 (0% → 0%) | `eval/experiment_step7b_diagnosis.json/production_before/control-domain/status`: Correct full-path control refusal; zero invented citations |
| control-time | insufficient_evidence | correct_control_refusal | 0 → 0 (0% → 0%) | `eval/experiment_step7b_diagnosis.json/production_before/control-time/status`: Correct full-path control refusal; zero invented citations |
| control-acn | insufficient_evidence | correct_control_refusal | 0 → 0 (0% → 0%) | `eval/experiment_step7b_diagnosis.json/production_before/control-acn/status`: Correct full-path control refusal; zero invented citations |

### Mechanism-level findings

- The original no-grader Dense-only and Hybrid-10:1 runs refused all eight normal queries, so grading/rewrite cannot be the sole cause. Their answers often describe relevant accounts but demand an exact conjunction or proven cause before answering.
- The generator explicitly requires all requested conditions in one account and says to begin with insufficient evidence otherwise. The grader similarly requires ALL conditions. This conflates useful mechanism-level reporter evidence with complete proof of a premise.
- The current status classifier also treats the phrase 'insufficient evidence' anywhere in a qualified answer as full refusal. An explicit outcome must distinguish a grounded partial answer from no supporting answer.
- All inspected selected passages retain their source synopsis, and relevant accounts already reach the selected evidence. Packaging exclusion may hide additional details, but no diagnosed dropped mechanism justifies changing the caps or packaging in this calibration.
- Citation validation flags and raw pre-validation outputs are checked separately; validation is not to be relaxed. Qrels indicate report relevance, not proof that every sentence in a passage supports every premise.

Phase 2 will change only the implicated generation outcome/prompt and grader sufficiency definitions, preserving exact citation validation, packaging/caps, retrieval, and all frozen evaluation assets. One calibration batch will then be measured against the pre-registered criteria; no iterative loosening.

<!-- answer-calibration-step7b -->
## Step 7B — answer-rate calibration (development)

Phase 1 diagnosed the generator's all-conditions requirement and the grader's complete-coverage requirement, not retrieval or citation validation. Fresh unchanged production responses and all five original Step 7 configurations were audited. Selected passages already contained each selected report's synopsis; packaging was not changed. See `docs/STEP7B_NOTES.md` for per-query trace references.

### One implicated calibration batch

Generation now uses explicit structured `answered` / `partial` / `insufficient_evidence` outcomes: report a supported mechanism with qualifications instead of requiring every condition or independently proven causality. Grader sufficiency means at least one relevant account addressing the mechanism, not all reports or all topic details. A partial status is read from the structured outcome rather than the occurrence of 'insufficient evidence' anywhere in a qualified answer. Unavailable precise dates/times, absent named identifiers, and out-of-domain questions still refuse.

Citation validation and evidence packaging functions are unchanged by hash. Reporter-account framing, passage-only claims, caps, query set, qrels, corpus, weights, and retrieval code remain fixed. There are no query-ID rules or qrel-based production filters. Qrels are used only after generation for evaluation; the 82 additions remain unjudged.

### Before/after summary

Production before = fresh unchanged HTTP Ask run; Dense-only and Hybrid-10:1 before = original Step 7 real-provider ablation with matching old generation/grader hashes. After uses the same eleven requests; production is through HTTP. All costs are actual provider tokens and request latency, mean over eleven requests, excluding warmup. Historical baseline latency versus current latency is descriptive, not a controlled provider-speed benchmark.

| Configuration | Supported normal / 8, before → after | Controls / 3, before → after | Citation precision on judged (coverage), after | Grade-0 supports |
|---|---:|---:|---:|---:|
| Production Ask | 1 → 8 | 3 → 3 | 100.0% (81.2%) | 0 |
| Dense-only | 0 → 8 | 3 → 3 | 100.0% (100.0%) | 0 |
| Hybrid-10:1 | 0 → 8 | 3 → 3 | 100.0% (100.0%) | 0 |

Unique cited reports count once per response. Precision = existing qrel grade ≥1 / judged cited reports. Coverage = judged / all cited reports. Unknown pairs are listed separately, never scored as irrelevant or assigned grades. These report-level qrels do not independently prove every generated claim. Precision before and all per-query counts are in the experiment record.

### Cost deltas

| Configuration | Mean input tokens, before → after (delta) | Mean output tokens, before → after (delta) | Mean latency seconds, before → after (delta) | Mean retries, before → after |
|---|---:|---:|---:|---:|
| Production Ask | 8775.5 → 6449.5 (-2326.0) | 659.5 → 479.3 (-180.3) | 14.20 → 9.74 (-4.46) | 1.82 → 0.82 |
| Dense-only | 2551.5 → 2826.5 (+275.0) | 99.8 → 117.4 (+17.5) | 2.40 → 2.60 (+0.20) | 0.00 → 0.00 |
| Hybrid-10:1 | 2618.3 → 2893.3 (+275.0) | 98.4 → 124.1 (+25.7) | 2.43 → 2.79 (+0.36) | 0.00 → 0.00 |

### Per-query status, citation precision and cost

| Configuration | Query | Before → after | Judged-relevant / judged cited; unknown | Input tokens before → after | Output tokens before → after | Latency seconds before → after (delta) |
|---|---|---|---|---:|---:|---:|
| Production Ask | ri-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 8136 → 5057 | 485 → 346 | 11.94 → 9.13 (-2.80) |
| Production Ask | ri-l2-2 | insufficient_evidence → partial | 2/2; 0 unknown | 8133 → 5273 | 525 → 330 | 14.10 → 6.30 (-7.80) |
| Production Ask | alt-l2-1 | insufficient_evidence → partial | 1/1; 1 unknown | 9481 → 8452 | 661 → 517 | 14.19 → 11.42 (-2.77) |
| Production Ask | alt-l2-2 | insufficient_evidence → partial | 2/2; 0 unknown | 9703 → 4752 | 743 → 344 | 13.72 → 6.26 (-7.45) |
| Production Ask | nmac-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 9719 → 5559 | 755 → 381 | 16.47 → 7.30 (-9.17) |
| Production Ask | nmac-l2-2 | insufficient_evidence → answered | 1/1; 1 unknown | 10980 → 7574 | 726 → 570 | 16.41 → 11.88 (-4.53) |
| Production Ask | equip-l2-1 | partial → answered | 1/1; 1 unknown | 9789 → 7696 | 755 → 541 | 17.65 → 10.89 (-6.76) |
| Production Ask | equip-l2-2 | insufficient_evidence → partial | 2/2; 0 unknown | 9531 → 4464 | 717 → 351 | 13.64 → 7.34 (-6.30) |
| Production Ask | control-domain | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 8027 → 8405 | 616 → 605 | 12.02 → 11.54 (-0.48) |
| Production Ask | control-time | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 6026 → 6327 | 640 → 647 | 14.46 → 12.87 (-1.59) |
| Production Ask | control-acn | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 7005 → 7385 | 632 → 640 | 11.55 → 12.18 (+0.63) |
| Dense-only | ri-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 2655 → 2930 | 96 → 121 | 2.98 → 2.69 (-0.29) |
| Dense-only | ri-l2-2 | insufficient_evidence → partial | 2/2; 0 unknown | 2923 → 3198 | 107 → 132 | 2.35 → 2.28 (-0.07) |
| Dense-only | alt-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 2493 → 2768 | 102 → 146 | 2.27 → 2.30 (+0.04) |
| Dense-only | alt-l2-2 | insufficient_evidence → answered | 2/2; 0 unknown | 2531 → 2806 | 92 → 168 | 2.27 → 4.94 (+2.67) |
| Dense-only | nmac-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 2815 → 3090 | 119 → 143 | 2.42 → 2.81 (+0.39) |
| Dense-only | nmac-l2-2 | insufficient_evidence → partial | 2/2; 0 unknown | 2655 → 2930 | 108 → 137 | 2.52 → 2.42 (-0.09) |
| Dense-only | equip-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 2577 → 2852 | 102 → 133 | 2.34 → 3.20 (+0.87) |
| Dense-only | equip-l2-2 | insufficient_evidence → partial | 2/2; 0 unknown | 2477 → 2752 | 122 → 121 | 3.30 → 2.69 (-0.61) |
| Dense-only | control-domain | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 2720 → 2995 | 61 → 72 | 1.77 → 2.11 (+0.34) |
| Dense-only | control-time | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 2018 → 2293 | 83 → 56 | 2.02 → 1.40 (-0.61) |
| Dense-only | control-acn | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 2202 → 2477 | 106 → 62 | 2.22 → 1.73 (-0.49) |
| Hybrid-10:1 | ri-l2-1 | insufficient_evidence → partial | 1/1; 0 unknown | 3046 → 3321 | 92 → 141 | 2.88 → 2.96 (+0.08) |
| Hybrid-10:1 | ri-l2-2 | insufficient_evidence → partial | 2/2; 0 unknown | 2926 → 3201 | 99 → 135 | 2.11 → 4.22 (+2.12) |
| Hybrid-10:1 | alt-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 2773 → 3048 | 105 → 150 | 2.93 → 4.14 (+1.20) |
| Hybrid-10:1 | alt-l2-2 | insufficient_evidence → partial | 2/2; 0 unknown | 2531 → 2806 | 114 → 148 | 2.94 → 2.43 (-0.51) |
| Hybrid-10:1 | nmac-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 2815 → 3090 | 119 → 141 | 2.59 → 3.62 (+1.02) |
| Hybrid-10:1 | nmac-l2-2 | insufficient_evidence → answered | 2/2; 0 unknown | 2577 → 2852 | 99 → 137 | 2.27 → 2.31 (+0.05) |
| Hybrid-10:1 | equip-l2-1 | insufficient_evidence → partial | 2/2; 0 unknown | 2823 → 3098 | 126 → 133 | 2.44 → 2.78 (+0.33) |
| Hybrid-10:1 | equip-l2-2 | insufficient_evidence → partial | 3/3; 0 unknown | 2477 → 2752 | 110 → 149 | 2.80 → 2.88 (+0.09) |
| Hybrid-10:1 | control-domain | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 2720 → 2995 | 61 → 78 | 2.15 → 1.69 (-0.45) |
| Hybrid-10:1 | control-time | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 1970 → 2245 | 102 → 110 | 1.78 → 2.38 (+0.61) |
| Hybrid-10:1 | control-acn | insufficient_evidence → insufficient_evidence | N/A (refusal/control) | 2143 → 2418 | 55 → 43 | 1.86 → 1.26 (-0.60) |

### Pre-registered outcome and stopping rule

**Success criteria met: True.** Production supported answers: 8/8 (required ≥6); every measured configuration controls 3/3 with zero invented citations: True; no answered/partial response cites a known grade-0 support: True.

One calibration batch was tested. No further loosening was attempted.

Full record: `eval/experiment_step7b.json`. Diagnosis: `eval/experiment_step7b_diagnosis.json`. Raw prompts, pre-validation outputs, and passage-bearing responses stay in ignored `data/`. Run `uv run python eval/diagnose_answer_rate.py` on the original pre-calibration source to capture diagnosis; run `uv run python eval/remeasure_answer_rate.py` for the registered calibrated source (matching checkpoints reused). No final-test queries or Step 8 work.

## Final validation

All 57 tests passed, including the 53 prior tests and four calibration tests pinning mechanism-level prompts, explicit partial outcomes, and fail-closed fabricated/uncited answers. Ruff and `git diff --check` passed. All returned citation passages match their indexed DB chunks. Citation validation and evidence selection functions retain their original hashes; retrieval defaults and corpus snapshots, queries, qrels, and all 82 blank ablation additions are unchanged. All per-query diagnosis references resolve. See `docs/STEP7B_VALIDATION.json`.

The production citation precision is 13/13 judged report citations at 13/16 judgment coverage. The other three cited report pairs remain unknown, not incorrect or automatically labeled. These development results meet the specified criteria; they do not constitute independent claim-level faithfulness judgments or final-test accuracy. No further loosening or Step 8 work was performed.
