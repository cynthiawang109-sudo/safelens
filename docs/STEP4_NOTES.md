# Step 4 — implementation and acceptance status

**Step 4 acceptance passed after API credit was replenished.** The final five
live HTTP checks used `gpt-4o-mini`, temperature **0**, and ready build **3**.
Controls were reviewed for the actual claims, not merely for a refusal string.

## Implemented

- `generate.py`: hybrid top-five reports; best chunk first, then a distinct
  alternate component chunk only for a top-five component rank. At most two
  chunks per report and eight total. Passages are reporter accounts, not
  confirmed findings. Prompts require source support, validated numeric ACN
  citations, uncertainty, and refusal of absent facts or unavailable date precision.
- Citation validation checks the supplied context, not the whole corpus.
  Fabricated ACNs are dropped, the answer is flagged, and fabricated/uncited
  answers fail closed to `insufficient evidence.` Citation membership alone
  does not establish that a claim is supported; no RRF confidence threshold is used.
- FastAPI: typed `/ask`, `/report/{acn}`, `/health` contracts; startup and each
  request require a matching ready index. A shared offline lock pins the build
  through generation. OpenAI text generation uses the configured provider/model.
- Gradio: HTTP calls to FastAPI only, displaying answers, structured evidence,
  report rankings, validation flags, and a source-report viewer.
- Human judgment import and relevance metrics: validated CSV conversion, strict
  top-ten qrel coverage, per-query and averaged P@10, MRR, and nDCG@10. Existing
  human-filled sheets and qrels are protected from accidental overwriting.

## Required live generation smoke tests

| Query | Final outcome | Cited ACNs | Time (ms) |
|---|---|---|---:|
| `control-domain` | Insufficient evidence; no invented marine incident or findings | None | 4470.18 |
| `control-time` | Correctly gives November 2021 only; explicitly says exact day/time unavailable | 1857031 | 2122.37 |
| `control-acn` | Explicitly says the requested report has no supplied account; other cited examples are clearly identified as different reports | 1728715, 1577269 | 2862.98 |
| `alt-l2-1` | Qualified refusal of the exact causal premise; quotes reported contributing factors | 1298683 | 2574.53 |
| `nmac-l2-1` | Conservative insufficient-evidence response for the requested RA/unseen-traffic combination | None | 4519.35 |

All five returned HTTP 200; all citation IDs belonged to supplied passages and
every returned passage matched the indexed chunk exactly. No invalid ACNs or
citation flags occurred. No exact day/time, fabricated report account, or marine
findings were invented. The two normal queries are recorded honestly as qualified
or refused, rather than being forced into affirmative answers.

A supplemental `equip-l2-1` request also gave a qualified refusal: its context
described hydraulic failures but did not establish the complete flight-control
degradation premise. A separate positive-path follow-up asked what the CE680
crew reported doing after the main hydraulic failure. It returned a substantive
answer with validated citation **[1124233]**: lowering the gear, using the
checklist, declaring an emergency/diverting, and reporting post-landing damage
and maintenance actions. Those details were checked against the cited passage.
Supplemental checks are separate from the required five and from relevance metrics.

During review an earlier normal response conflated a traffic advisory with a
resolution advisory and reversed a visual-contact/maneuver sequence. The prompt
now explicitly preserves technical labels, negation, and event order, requires
all requested conditions in the same account, and corrects unsupported premises.
Uncited refusals are reduced to a bare refusal so they cannot carry unverified
factual paragraphs. The final five were rerun after these changes. Citation
membership still does not prove claim support; this small smoke set is not a
general grounding guarantee, and conservative refusals remain a limitation.

To reproduce the required five with the API running:

```powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
uv run python scripts/smoke_step4.py
```

The script calls all five queries over HTTP, verifies every citation passage
against the indexed chunk, and checks `/report` against the stored source.
Full answers/passages are saved only to ignored `data/step4_smoke.json` after
all requests finish; partial diagnostics use `data/step4_smoke_partial.json`.
Supplemental outputs use `data/step4_positive_check.json` and
`data/step4_positive_actions.json`. Read the three control answers in full before recording
pass/fail: an invented day, ACN account, or marine finding is a failed check
even if the answer also says “insufficient evidence.”

## Completed local checks

- **34 tests passed**, including prior tests, fabricated-ACN rejection, exact
  citation passages, context bounds, API/source contracts, quota-error handling,
  toy metric arithmetic, strict unjudged-document rejection, validated import,
  and an end-to-end evaluator run with temporary **synthetic** qrels. The latter
  also verifies that a filled synthetic judging sheet is not overwritten.
- Ruff passes. Lexical semantics in `retrieve.py` were not changed.
- Live `/health`: ready build **3**, **5,000 reports**, **6,998 chunks**.
- Live `/report/1857031` and the smoke-selected `/report/1298683`: all
  source/provenance/hash fields and exact indexed chunk texts match PostgreSQL.
  Typed OpenAPI contracts are present.
- Gradio at `http://127.0.0.1:7860` returns HTTP 200. Its real report callback
  matches the FastAPI response, demonstrating the HTTP-only source path.
- The retrieval evaluator ran successfully. Primary Layer-1 category precision
  remains **0.090 lexical / 0.895 dense / 0.885 hybrid**. All **88** pool rows
  remain ungraded with blank notes, and **`eval/qrels.jsonl` does not exist**.
  No real report relevance labels were assigned.

Aggregate local verification is in ignored `data/step4_local_checks.json`.
API documentation: `http://127.0.0.1:8000/docs`. Health describes the ready index;
it does not make a paid generation request or certify external quota.

## Human judging and metric definitions

After Cynthia grades the sheet, `eval/import_judgments.py` checks unique query/ACN
pairs, known Layer-2 queries, subset membership, complete current pool coverage,
and grades 0/1/2 before creating qrels. It rejects blank grades and refuses to
overwrite existing qrels. It was tested using temporary synthetic files only.

When qrels exist, `eval/run_eval.py` appends a separate judged-relevance section
with per-query and macro averages. **P@10 uses denominator 10**; **MRR** uses
the first grade>=1 report within the returned top ten; **nDCG@10** uses linear
gains **2/1/0**, log2 discounts, and the ideal ranking over the judged pool.
Unjudged top-ten documents cause an error rather than receiving grade zero.
No judgments, qrels, or actual Layer-2 relevance scores were fabricated in Step 4.

No work beyond Step 4 was started.
