# Post-freeze cnt-1 routing fix

Date: 2026-11-17 (America/New_York). This is **post-freeze development**,
motivated by the recorded frozen ft-cnt-1 failure. The frozen results stand
unrevised: the frozen question was not run through Ask or rescored, and its
sealed answer was never used as a test target.

## Change and boundaries

Only `src/safelens/aggregate.py` changes production behavior. Exact known
category/alias phrases are consumed first. A token-set containment fallback
then recognizes reordered category words, with conservative plural handling
limited to known category vocabulary. For example, the pure string mapping
case `NMAC conflicts` now resolves to `Conflict NMAC`; previously the short
`nmac` alias could match while the leftover `conflicts` made the grammar reject
the request. The same mechanism handles reordered runway, altitude and
critical-equipment labels.

Unknown qualifiers, partial words, conflicting category parameters and multiple
categories still reject. The category word `from` is consumed separately from
an actual `from YEAR` connector, so reordered labels cannot manufacture a date
range. Count SQL, year parsing, retrieval, generation, grading and prompts are
unchanged. No special case for a frozen query ID, year or sealed count is added.

The validation API runs patched source on temporary local port 8001 against
the existing 20k index. Existing Docker images are not silently patched or
deployed; ordinary service rebuild/restart is needed to adopt the repository
change. No cloud deployment is performed.

## Validation

`uv run pytest`: **80 passed**, including 17 new mapper cases covering reordered
and plural category words, exact phrases, safe range connectors, ambiguities,
substrings and unsupported qualifiers. Ruff passes.

The full local development gate was rerun against the patched API with the
real configured provider. Baselines reproduce:

| Development gate | Measured | Outcome |
| --- | ---: | --- |
| Dense Category P@10, 28 queries | 0.628571 | Pass, unchanged |
| Production hybrid Category P@10, 28 queries | 0.642857 | Pass, unchanged |
| Dense Layer-2 P@10 on judged pairs | 0.950000 | Pass, 100% coverage |
| 2020 runway count | 98 / 20,000 | Exact |
| Corpus total | 20,000 / 20,000 | Exact |
| Development mechanisms | 3 / 3 supported | Pass |
| Development control | insufficient_evidence, zero citations | Pass |

New development counts use separately authored SQL
`SELECT count(*) FROM reports WHERE report_year = %s AND %s = ANY(anomaly_codes)`
as the oracle, plus a separate corpus denominator query. They do not call the
production mapper or production count SQL to compute expected answers:

| New phrasing | Independent SQL | API | Trace / model calls |
| --- | ---: | --- | --- |
| Count reports in 2018 about NMAC conflicts | 112 / 20,000 | answered, exact filters | route → aggregate_sql; 0 |
| How many reports in 2017 about incursions runway? | 147 / 20,000 | answered, exact filters | route → aggregate_sql; 0 |
| Count reports in 2021 about problems critical equipment | 513 / 20,000 | answered, exact filters | route → aggregate_sql; 0 |

`POST_FREEZE_FIX_CNT1_VALIDATION.json` records these real HTTP/SQL checks.
The full local gate record is retained with its metrics, provenance, index,
retrieval configuration, timing and Ask statuses in
`POST_FREEZE_FIX_CNT1_DEV_GATE.json`. These are development measurements only.

## Protected-hash reissue process

`scripts/reissue_protected.py` is the explicit, narrowly authorized process.
It archives the prior manifest byte-for-byte, permits only this routing module
plus the four development assets authorized by the five-judgment import, and
records before/after hashes and this disclosure. Every other protected entry
must still match its original seal. It checks original qrel-prefix preservation
and verifies that all results outside the Step 7 Part 1 development section,
including the frozen Step 7D section, remain byte-identical. It refuses to
overwrite an existing archive/audit.

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
uv run python scripts/reissue_protected.py --disclosure docs/POST_FREEZE_FIX_CNT1.md --judgment-completion docs/POST_FREEZE_STEP7_JUDGMENTS.json
uv run python scripts/check_protected.py
```

The archived seal and audit live under `eval/protected_hash_history/`; the
active manifest remains `eval/step9_protected_hashes.json`. Known repository
and Windows checkout byte forms are sealed explicitly, as in Step 9. Frozen
assets are never reissued. The enclosing `results.md` hash changes solely for
its development section; the frozen section retains its separately verified
byte hash. No frozen query, qrel, freeze document, experiment,
run-once marker or final-results section changes.

## Part B

The five grades were initially blank and became fully human-filled while this
task was running. The completed pool was then validated and imported; qrels
grow 134 → 139 with every prior line byte-unchanged. The hybrid development
row and its judgment-version caveat are recorded in
[the Part B addendum](POST_FREEZE_STEP7_JUDGMENTS.md). No historical final score
was recalculated to measure this patch.
