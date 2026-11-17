# Step 8 — Next.js web UI

Scope: frontend only. Ask, report details and the evaluation lab are implemented
in `web/` with Next.js App Router, TypeScript and Tailwind. Gradio, retrieval,
generation, grading, aggregate routing and the frozen evaluation assets are
unchanged. Step 9 was not started.

## Run

With the existing indexed database, cached embedding model and an
`OPENAI_API_KEY` in the shell or gitignored `.env`:

```powershell
docker compose up -d --build
```

The web service is at http://localhost:3000; FastAPI is at
http://localhost:8000. Stop standalone servers occupying these ports first.
A fresh database must still be populated using the existing explicit offline
migration/ingest/reindex instructions. Startup never changes the index.

For a local production build against the already-running API:

```powershell
cd web
npm ci
npm run build
npx tsc --noEmit
npm run lint
npm start
# In another shell:
npx playwright install chromium
npm run smoke
```

The smoke makes live development-example requests (with LLM usage) and writes
`docs/STEP8_SMOKE.json` plus screenshots. It does not rerun the frozen final test.
Node 26.13.1 / npm 11.20.0 were used locally; containers use Node 24 Alpine.

## HTTP boundary and states

`NEXT_PUBLIC_API_BASE_URL` defaults to `http://localhost:8000`; the Compose build
uses `http://api:8000`. The frozen API has no CORS middleware. The browser
therefore uses a narrow same-origin Next.js forwarding route for `GET /health`,
`GET /report/{numeric-acn}` and `POST /ask`. It forwards the existing payloads
without reproducing backend logic or injecting credentials. No keys are built
into the frontend or Docker images.

Ask shows real elapsed waiting time while a request is pending. It does not
invent live stages: the API returns a completed trace, which is rendered in
order with verdicts, per-report grades, rewrite queries, timings and tokens.
The trace opens by default and can be collapsed. Counts show filters,
denominator, caveat and expandable SQL provenance. ACN chips open the original
synopsis/narrative and indexed metadata. All API calls have loading/error
states; failed Ask requests preserve the question and are never auto-retried.

## Evaluation snapshot

`web/scripts/generate-evaluation.mjs` runs before builds and commits its output
at `web/src/data/evaluation.json`. It selects only summaries, numerical count
outcomes and source digests from:

- `eval/experiment.json`: development Layer 1 and Layer 2 on 20k; the historical
  hybrid is FTS/equal-weight, explicitly distinct from the production default.
- `eval/experiment_step7_ablation.json`: five variants, supported responses,
  controls, judgment coverage, latency and token costs. The rewrite variant has
  one supported response; the UI does not claim all five variants refused all
  eight requests. Incomplete judgments are visible and no full relevance
  comparison is inferred.
- `eval/experiment_step7b.json`: each configuration's before/after outcomes,
  citation precision with coverage, controls and measured costs.
- `eval/experiment_step7d.json`: recorded final retrieval summaries, mechanism
  outcomes, controls, citation coverage, costs and count failures.

No frozen question wording, recorded final answers, raw final traces or raw
experiment records are shipped to the UI. The generator explicitly checks for
frozen question leakage. The final count failure `ft-cnt-1` is displayed as
recorded: expected 272, no system aggregate, filters or denominator returned;
the routing gap is unchanged. Final retrieval coverage is complete; citation
precision is explicitly limited to judged pairs, with unknown pairs separate.

## Acceptance evidence

`npm run build`, `npx tsc --noEmit`, and `npm run lint` pass.
`uv run pytest` passes all **60 tests** with `PYTHONUTF8=1` and
`PYTHONIOENCODING=utf-8`. `docker compose config --quiet` passes, and the web
and API Docker images build successfully. After building the images, the final
startup check used `docker compose up -d --no-build --wait --wait-timeout 300`:
the existing database and API are healthy, and web is running on port 3000.
The smoke also passed against this containerized stack; the final screenshots
and `STEP8_SMOKE.json` reflect that run. Its mechanism request took 20.33s and
the SQL count took 0.28s (backend usage timings, not an SLA).

The scripted built-app smoke passed against the real 20k API:

| Development example | Rendered status | Observed result |
| --- | --- | --- |
| Unreliable airspeed mechanism | `partial` | Validated clickable citations; route/retrieve/grade/generate/finalize trace |
| Runway-incursion count, 2020 | `answered` | **98 / 20,000**, year 2020 and `Ground Incursion Runway` metadata filters; route/aggregate_sql trace |

The smoke also verifies report navigation, evaluation rendering, backend-down
and report-not-found states using browser-only intercepted errors, question
retention, and mobile width. There are no browser page errors. Error fixtures
do not change API behavior or substitute for the live answer checks.

Screenshots (Ask trace is opened):

- [Mechanism answer and trace](STEP8_ASK_TRACE.png)
- [Count and trace](STEP8_COUNT_TRACE.png)
- [Mobile Ask](STEP8_ASK_MOBILE.png)
- [Loading/progress](STEP8_LOADING.png)
- [Source report](STEP8_REPORT.png)
- [Evaluation lab](STEP8_RESULTS.png)

Integrity checks compare 73 protected backend/config/evaluation files with
their pre-Step-8 SHA-256 values: no changes. Scanning frontend source and
production browser/server page artifacts finds no frozen question strings.
Only frontend, Compose, README and Step 8 documentation are changed. Raw data,
model caches, build outputs and secrets remain ignored.

`STEP8_VALIDATION.json` records the baseline commit, check results and protected
hashes. All 26 packaged backend source files also match their host baseline
byte-for-byte inside the API container. Raw evaluation records are absent from
the final web runtime image; only the sanitized snapshot is included.
