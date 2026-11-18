# Deploy / teardown checklist — SafeLens live demo

Purpose: spin the public demo up for a defined window (interviews, a link in
an application), then tear it down to stop billing. This is the one-page
operator version; `docs/DEPLOYMENT.md` is the full reference and wins on any
disagreement. Expected cost while live: roughly **$110–150/month** (Render
Pro API ~$85 + paid Postgres/disk) plus small OpenAI usage. Nothing here
runs the frozen final test.

## Before you start

- [ ] Render account with billing set up; Vercel account
- [ ] OpenAI key at hand to paste into Render (never commit it)
- [ ] Demo window dates chosen, **teardown date put on the calendar**
- [ ] Accepted: the API has no authentication or rate limiting — a public
      demo is unauthenticated for the window

## Phase 1 — Render: database + API (bootstrap OFF)

- [ ] Render Dashboard → New → Blueprint → select this repo (`render.yaml`)
- [ ] Prompts: `OPENAI_API_KEY` = your key; `SAFELENS_BOOTSTRAP=0`
- [ ] Apply. Postgres provisions; the API's first readiness check **fails on
      the empty database — expected**. Do not flip the bootstrap flag to fix
      it: Render pre-deploy is capped at 30 minutes and the 20k build takes
      ~50

## Phase 2 — External bootstrap (from your PC, ~1 hour)

- [ ] Render Postgres page → temporarily add your current IP to the
      database allowlist
- [ ] Local repo checkout, PowerShell:
  - `$env:PYTHONUTF8 = '1'` and `$env:PYTHONIOENCODING = 'utf-8'`
  - `$env:DATABASE_URL` = the Render **external** connection string with
    `sslmode=require` — double-check it points at the Render database,
    not your local one
- [ ] `uv sync --frozen`
- [ ] `uv run python -m safelens.migrate`
- [ ] `uv run python scripts/download_dataset.py`
- [ ] `uv run python -m safelens.cli reindex --corpus-manifest eval/corpus_manifest_20k.json`
- [ ] Confirm the build reports ready: 20,000 reports / 28,306 chunks
- [ ] Remove your IP from the database allowlist (back to empty)

## Phase 3 — API go-live + smoke

- [ ] Render API service → Manual Deploy (bootstrap flag still 0)
- [ ] `https://<api-service>.onrender.com/health` reports ready, 20k corpus
- [ ] `uv run python scripts/smoke_production.py https://<api-service>.onrender.com`
      passes (mechanism citations + 2020 runway count 98 / 20,000)

## Phase 4 — Vercel: web

- [ ] Vercel → Add New Project → import this repo
- [ ] Root Directory = `web`; enable **Include source files outside of the
      Root Directory in the Build Step**
- [ ] Environment: `NEXT_PUBLIC_API_BASE_URL=https://<api-service>.onrender.com`
      (Production), set **before** the first build
- [ ] Deploy manually from the dashboard (`web/vercel.json` disables
      automatic Git deployments)
- [ ] Browser check: Ask a mechanism question, open a cited report, open
      `/results`

## While live

- [ ] Check OpenAI project spend weekly (no rate limit on the demo)
- [ ] No API pushes without a maintenance window (single instance +
      persistent disk); first request after idle is slow (model + BM25
      warm-up)

## Teardown — on the scheduled date, in this order

- [ ] Vercel: delete the project (on Hobby it bills nothing, but it would
      point at a dead API)
- [ ] Render: delete the API web service (stops the instance + disk charges)
- [ ] Render: delete the Postgres database (stops DB billing; the corpus is
      rebuildable from the pinned dataset — nothing unique lives only there)
- [ ] Render Billing page: confirm no billable services remain
- [ ] The GitHub `OPENAI_API_KEY` secret can stay (CI uses it); remove it
      only if you retire the key itself
- [ ] Your local stack is unaffected: `docker compose up` still runs
      everything on your PC

## Accepted limitations during a live window

- Count questions whose wording does not map to a category name can fall
  back to narrative answers (the documented ft-cnt-1 finding; not fixed)
- Cold starts are slow; `/health` is the readiness signal, not an Ask call
