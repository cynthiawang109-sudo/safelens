# Step 3 judging handoff

`judging_pool.csv` is the blinded union of all three retrievers' top-ten reports
for the eight queries below. Rows are shuffled; retriever identities, scores,
and ranks are absent. Grade and note are intentionally blank. No automated
or assistant judgments have been assigned.

| Query ID | Question to judge against |
|---|---|
| ri-l2-1 | A pilot mistook a taxi instruction for permission to cross the runway. |
| ri-l2-2 | Low visibility or confusing airport signs led a crew into the departure path. |
| alt-l2-1 | An incorrectly set altitude selector caused the aircraft to pass through the cleared level. |
| alt-l2-2 | A readback misunderstanding led the crew to stop the climb at a different level than the controller intended. |
| nmac-l2-1 | A TCAS resolution advisory required avoiding traffic that the pilots had not seen. |
| nmac-l2-2 | An aircraft without radio contact passed very close to an airplane in the airport traffic pattern. |
| equip-l2-1 | Hydraulic failure degraded flight controls and forced an emergency diversion. |
| equip-l2-2 | Unreliable airspeed indications left the pilots uncertain about the airplane's actual energy state. |

Read the synopsis first; consult the full indexed narrative only if ambiguous.
Judge relevance to the question, not just agreement with its coarse category.
Use **2 = directly relevant**, **1 = partially relevant**, **0 = irrelevant**.
Notes are optional; record when the narrative was needed. Reports are reporter
accounts, not independently confirmed findings.

To read a narrative without seeing retrieval provenance, replace the ACN below:

```powershell
docker compose exec -T db psql -U safelens -d safelens -c "SELECT acn, synopsis, narrative FROM reports WHERE acn = 'REPLACE_WITH_ACN';"
```

During blinded judging, use this guide, the query file, the CSV, and indexed
source reports. Avoid the development retrieval logs in `data/`.
The evaluator refuses to overwrite a judging CSV with any filled grade or note.

Target reading budget is approximately two hours. If it overruns, a later
explicit decision can reduce the judged set to six queries; do not thin the
judgments within a query. Every top-ten report of every compared retriever
must be judged before fair relevance comparisons can be reported.

Completed qrels and relevance metrics belong to a later step. Step 3 ends with
this ungraded pool; unjudged reports are not treated as irrelevant.
