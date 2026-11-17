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
measured retrieval/SQL and failed explicitly on the blocked Ask smoke.
The hosted run and its downloaded artifact are recorded below.

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

Tested code commit: `4d7101f89db580a9a1db6892982976d395cb9e75`.

- [PR gate: success](https://github.com/cynthiawang109-sudo/safelens/actions/runs/44020104275):
  Ruff, protected hashes, **63 tests in 12.78s**, npm install, TypeScript, lint
  and the production web build all pass on GitHub's Linux runner. The original
  implementation also passed the preceding push run; the linked run includes
  the final configuration/timing provenance instrumentation.
- [Explicit workflow_dispatch evaluation](https://github.com/cynthiawang109-sudo/safelens/actions/runs/44020105195):
  completed in **50m36s**. All three pinned source downloads verified,
  migrations passed, and the production pipeline built a new ready index:
  **20,000 reports / 28,306 chunks**.
  Index logs confirm 20,000 processed reports, zero skipped, 28,306 embedded
  chunks and zero reused chunks: this was a full fresh build.
  Both bookend protected-hash checks passed. No final-test evaluation ran.
- [Workflow artifact](https://github.com/cynthiawang109-sudo/safelens/actions/runs/44020105195/artifacts/14302743392): `development-evaluation-44020105195`.
  The downloaded numeric JSON is also preserved as `docs/STEP9_CI_EVAL.json`.
  JSON SHA-256: `ea37dfeb9c85dde861c1863103af4961be6c010da48929d71d72cc5c6d2ba6b4`.

Actual artifact measurements (development queries only):

| Gate | Hosted measurement | Required | Outcome |
| --- | ---: | ---: | --- |
| Dense Category P@10, 28 queries | 0.628571 | 0.60 | Pass |
| Production hybrid Category P@10, 28 queries | 0.642857 | 0.62 | Pass |
| Dense Layer-2 precision on judged pairs | 0.950000 | 0.90 | Pass |
| Dense Layer-2 judgment coverage | 100% | Report explicitly | Eight queries, all 80 top-ten pairs judged |
| 2020 runway SQL count | 98 / 20,000 | Exact | Pass |
| Total SQL count | 20,000 / 20,000 | Exact | Pass |
| Hosted Ask smoke | Blocked | Three supported mechanisms + one zero-citation refusal | **Fail: repository secret absent** |

**Remaining blocker:** the repository secret `OPENAI_API_KEY` is absent.
The workflow therefore skipped API startup, made **zero hosted Ask calls**, and
failed the Ask gate explicitly; it did not report skipped generation as success.
After Cynthia sets that secret, dispatch `eval.yml` again. No credential was
transferred automatically. The full local gate did execute the three mechanism
requests plus the control successfully, using the existing local provider key.
Those local outcomes are separate from this hosted failure.

The artifact records a ready BGE-small index (384 dimensions, pinned revision,
500-token chunks / 15% overlap / synopsis plus all labeled narratives),
100 candidate chunks, 50 candidate reports, report-level RRF k=60,
dense:BM25 weights 10:1 and no category filter. It also records software,
4 logical CPUs, per-query timings, cold-cache timing scope and mean/p95 retrieval
latencies. Unjudged pairs are excluded; none were missing for this dense run.

Cloud bootstrap must account for the observed duration: this 4-CPU hosted run
exceeded Render's 30-minute pre-deploy window. Use the documented external
bootstrap route by default, or first confirm faster pipeline compute and a
measured duration that fits. The API instance plan alone does not control the
pre-deploy compute tier. No cloud deployment was performed.

Final evidence-only documentation commits use `[skip ci]` to avoid rerunning
an unchanged 20k evaluation just to publish its own result. The linked tested
commit contains the final executable workflow/gate logic. Both production code
and all frozen/development assets remain unchanged.
