# Step 9 — CI gates and deployment readiness

Scope: CI gates in full, deployment configuration and instructions only. No live
deployment is performed; the ft-cnt-1 routing gap and frozen production code
remain unchanged. The final test is not rerun.

## Local validation

- Ruff: passed. Both workflow files: actionlint passed.
- Hermetic pytest selection: **63 passed** (60 prior tests plus three gate
  contract tests). Existing test assertions are unchanged; fixture/marker
  additions block external networking and identify synthetic Postgres tests.
- `npm ci`, `npx tsc --noEmit`, `npm run lint`, `npm run build`: passed.
- Render Blueprint: validates against the current Render JSON Schema. Vercel
  configuration: validates against its published property rules with Draft 7;
  the provider's schema contains unrelated meta-schema-invalid definitions,
  so instance validation was used rather than schema self-validation.
- Deployment Dockerfile: `docker build --check` passed; all three shell scripts
  pass `sh -n` in the existing Linux image. No cloud build/deploy was attempted.
- Production smoke against the existing local API: healthy 20k corpus,
  mechanism `partial` with validated citations, count `answered`, 98/20,000.

Full local development gate (`data/step9_local_eval.json`):

| Check | Measured | Threshold/outcome |
| --- | ---: | --- |
| Dense Category P@10, all 28 | 0.628571 | ≥ 0.60, pass |
| Production hybrid Category P@10, all 28 | 0.642857 | ≥ 0.62, pass |
| Dense Layer-2 relevance on judged pairs | 0.950000 | ≥ 0.90, pass |
| Dense top-ten judgment coverage | 100% | Eight development queries |
| 2020 runway SQL count | 98 / 20,000 | Exact, pass |
| Total SQL count | 20,000 / 20,000 | Exact, pass |
| Mechanism Ask | 3 / 3 supported | Pass |
| Development control | insufficient_evidence, 0 citations | Pass |

The full local gate used the existing local provider key. GitHub's repository
secret list is empty; no key is transferred by this step. The hosted eval gate
will still measure retrieval/SQL and fail explicitly on the blocked Ask smoke.
Actual GitHub run links and artifact numbers are added after execution below.

## Integrity and portability

`eval/step9_protected_hashes.json` seals 76 existing production, migration,
configuration and evaluation assets. The checker recognizes the committed blob
hash and the pre-existing Windows checkout hash where those differ solely in
checkout line endings. It does not normalize a changed file or accept arbitrary
content. Frozen final assets retain the existing `-text` attributes and have
identical sealed bytes across checkouts. Local original bytes remain unchanged.
Web prebuild provenance hashes naturally reflect the record bytes in that
checkout; numeric summaries are generated from the same committed records.

Deployment details, verified provider references, realistic resource/billing
limits and Cynthia's required decisions are in [DEPLOYMENT.md](DEPLOYMENT.md).
Both providers' automatic Git deployments are disabled. No credentials are
committed or copied to a hosting service.

## GitHub execution

Pending the step's push and explicit workflow dispatch.
