# Deployment readiness — no live deployment performed

Step 9 prepares GitHub CI, a Render Blueprint and Vercel settings. Applying
the Blueprint or deploying Vercel remains Cynthia's decision. Automatic Render
and Vercel Git deployments are disabled in the committed configuration.

## Local stack

With the existing 20k database, `data/models` and `OPENAI_API_KEY` in the shell
or ignored `.env`:

```powershell
docker compose up -d --build
```

Web: http://localhost:3000; API: http://localhost:8000. A fresh local database
still needs explicit provisioning, before API startup:

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
docker compose up -d db
uv sync --frozen
uv run python scripts/download_dataset.py
uv run python -m safelens.migrate
uv run python -m safelens.cli reindex --corpus-manifest eval/corpus_manifest_20k.json
```

These are offline operations. Never run a replacement reindex while accepting
Ask traffic. The production lock fails safely rather than exposing mixed builds.

## CI contracts

The PR gate has no provider secrets, external API, model downloads or ASRS data.
It uses a pgvector Postgres service solely for synthetic isolated-schema tests.
`live_corpus`, `live_api` and `model_download` markers are excluded; `postgres`
marks the synthetic integration tests and is included. Existing test assertions
are unchanged. Hermetic tests block external socket connections; HF libraries
are offline. Ruff and the Next.js install/type/lint/build checks are mandatory.

The development eval gate runs on master pushes and manual dispatch. Each run
downloads and checksums the three pinned JSONL files, verifies/reproduces the
20k manifest and builds an entirely fresh index with the production pipeline.
`eval/gates.json` contains the fixed baselines and thresholds. Layer-1 uses all
28 category queries, without category filtering. Layer-2 gates dense on eight
development queries: relevant/judged in each top ten, macro averaged, with
coverage and missing pairs always reported. Unjudged pairs are excluded, never
zero-filled; a query with no judgments fails. This explicitly named judged-only
statistic equals strict P@10 when coverage is complete and must not be described
as a complete pooled comparison when coverage is incomplete.

SQL checks reproduce 98/20,000 runway reports in 2020 and 20,000/20,000 total.
Ask uses three Layer-2 development queries and one development control; the
mechanisms require validated citations and answered/partial outcomes, and the
control requires insufficient evidence with zero citations. A missing
`OPENAI_API_KEY` repository secret still permits retrieval and SQL measurements,
but records Ask as blocked and fails the workflow. It never substitutes mock
answers. The numeric JSON artifact is uploaded even on failure.

To enable the full hosted gate, Cynthia sets the GitHub Actions repository
secret `OPENAI_API_KEY` using GitHub Settings (never a public issue or commit),
then runs:

```powershell
gh workflow run eval.yml --ref master
gh run list --workflow eval.yml
```

CI never invokes the spent final-test evaluator, generates final rankings or
calls Ask with a frozen final question. The web build only reads the already
committed final records to regenerate its sanitized historical snapshot.
Protected source/data hashes are checked before and after evaluation.

## Render Blueprint

After the confirmations below, import this repository's `render.yaml` as a
Blueprint. The API uses the repository-root Docker context and
`deploy/Dockerfile`, Python 3.12, one Pro instance in Oregon, port 10000 and
`/health`. The database is paid Render Postgres 16, `basic-1gb`, in the same
region with 5 GB storage. External DB access is disabled; the API receives the
private connection string through `fromDatabase`. Render supports pgvector;
the existing migration explicitly creates `vector`.
See the [Blueprint reference](https://render.com/docs/blueprint-spec) and
[supported extensions](https://render.com/docs/postgresql-extensions).

Every backend configuration variable is named in the Blueprint. Enter
`OPENAI_API_KEY` into the secret prompt. For the **first provision only**, set
`SAFELENS_BOOTSTRAP=1` at the prompt: this is explicit authorization to run the
existing migration, pinned download and offline 20k reindex in the pre-deploy
phase. The API intentionally cannot serve an empty or mismatched index.
After the first healthy deployment, set `SAFELENS_BOOTSTRAP=0` before any later
deploy. Normal pre-deploy checks verify readiness and never silently rebuild.
`autoDeployTrigger: off` leaves later deployments manual.

The exact bootstrap command is:

```sh
sh deploy/bootstrap.sh
# Equivalent explicit steps:
uv run --no-sync python -m safelens.migrate
uv run --no-sync python scripts/download_dataset.py
uv run --no-sync python -m safelens.cli reindex --corpus-manifest eval/corpus_manifest_20k.json
```

These are also the documented **post-deploy maintenance commands** in a Render
Shell, after entering a maintenance window and draining requests. They replace
the corpus using the existing offline lock; no model/config switch is implicit.
Alternatively explicitly set the bootstrap flag to 1 for a manual maintenance
deployment and reset it to 0 afterward. Never leave it enabled across deploys.

The persistent disk mounts `/app/data` for the runtime model cache and any
explicit maintenance downloads. Render pre-deploy runs on separate compute
and cannot access this disk: initial pre-deploy files are temporary, while the
indexed corpus is durable in Postgres. The runtime downloads the pinned model
once into its own persistent cache. Do not assume pre-deploy downloads appear
on the runtime disk. Disks also limit this design to a single instance and
prevent zero-downtime disk-backed rollouts; plan a maintenance window.
[Render disk lifecycle](https://render.com/docs/disks).

## Vercel web settings

After API readiness is confirmed, import the same repo with Root Directory
`web`, framework Next.js, Node 24, install `npm ci`, build `npm run build` and
the default Next.js output settings. Enable **Include source files outside of
the Root Directory in the Build Step**: prebuild reads committed records under
`../eval`. Do not upload raw `data/` or Python model caches. See
[Vercel's monorepo guidance](https://vercel.com/docs/monorepos/monorepo-faq).

Set `NEXT_PUBLIC_API_BASE_URL=https://<confirmed-api-service>.onrender.com` in
the appropriate Vercel Production/Preview environment **before building**.
Use the actual allocated API URL, never the Docker-only `http://api:8000`.
The existing Next.js route forwards to the API over HTTPS, so backend CORS
changes are unnecessary. This public URL is not a credential; never set an
OpenAI key on Vercel. Public environment variables are build-time values, so
changing the API URL requires a rebuild. The existing proxy duration is 240s;
confirm the chosen Vercel plan supports that duration and the 235s upstream
timeout. [Function limits](https://vercel.com/docs/functions/limitations).

`web/vercel.json` disables automatic Git deployments. Only after approval,
perform the first manual dashboard deployment or deliberately enable Git
deployments. None is performed by the Step 9 workflows.

## Cost, size and operating limits

Budget estimate as of 2026-11-16: Render Pro API is listed at about $85/month;
add the selected paid Postgres tier, DB storage and a 10 GB persistent disk.
Plan roughly **$110–150/month before LLM usage, bandwidth and optional paid
Vercel/workspace features**, then confirm actual checkout prices. This is a
planning estimate, not a provider quote. A 2 GB API tier is cheaper but needs
measured headroom: the warmed local Linux API used about 1.17 GiB during Step 9,
and a single observation is not a peak-load guarantee.
[Render pricing](https://render.com/pricing).

Vercel Hobby is restricted to personal/non-commercial use; select a paid plan
if required by the intended use and verify current usage limits and billing.
[Vercel Hobby](https://vercel.com/docs/plans/hobby).

The corpus is 20,000 reports / 28,306 chunks. Raw pinned downloads total about
333 MB; model weights, Python ML wheels and build caches add substantial disk
and cold-build time. BM25 holds token/frequency structures for the corpus in
process memory and rebuilds its cache on process restart; it is not a remote
search service. BGE runs on CPU, and exact vector scans still use PostgreSQL.
Cold imports/model loading and the first BM25 request are slower than warm
requests. Keep one API worker; additional workers duplicate model/BM25 memory.
Use `/health` for readiness, not an LLM request. Provider requests incur usage
cost even if a caller disconnects; set a project budget with the provider.

Before public access, confirm ingress access control/rate limits and the
expected traffic budget. The frozen API has no authentication or rate limiter;
Step 9 does not add either or fix the recorded ft-cnt-1 routing gap. A public
unauthenticated demo should be an explicit operator choice.

## Post-deploy smoke and rollback

Against an API URL (not the Vercel page URL):

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
uv run python scripts/smoke_production.py https://<confirmed-api-service>.onrender.com --output data/production-smoke.json
```

The script checks ready health on 20k reports, a development airspeed mechanism
with validated citations, and the exact 2020 runway count/filters/denominator.
It fails on any mismatch; it does not run the frozen final test. Then check the
Vercel Ask/report/Results views in a browser. Keep the previous application
image and a provider DB backup. Roll back the application to a compatible
image; do not change model/chunk config without an explicit offline reindex.
Provider disk snapshots do not replace a Postgres backup. Verify backup/restore
policy before approving a live deployment.

## Decisions Cynthia must confirm before any live deploy

1. Render and Vercel account/team ownership, billing and the monthly budget;
   intended commercial/personal use and final plans/region.
2. The public API/frontend URLs or custom domains, HTTPS and which preview
   deployments may call the production API.
3. OpenAI project/key, usage budget and GitHub secret setup. These are separate
   destinations; no credential is transferred automatically by this work.
4. Initial explicit bootstrap flag, maintenance window, provider backup
   retention and an actual restore/rollback owner.
5. Public access versus an access-controlled demo, ingress rate limits and
   expected concurrent traffic. Accept the unchanged documented count-routing
   limitation, or authorize a separate disclosed patch later.

All configuration is prepared; no Render, Vercel or other cloud service is
created, synchronized, deployed or billed by Step 9.
