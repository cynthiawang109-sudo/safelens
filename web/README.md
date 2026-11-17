# SafeLens web

Next.js App Router, TypeScript and Tailwind. Requires Node.js 24+ and the
existing SafeLens API. No retrieval or generation runs in the frontend.

```powershell
npm ci
npm run dev
```

Copy `.env.example` to `.env.local` to override the default API URL
`http://localhost:8000`. The browser uses `/api/backend/*`, a same-origin,
uncached forwarding route restricted to health, Ask and report reads. It keeps
the frozen backend unchanged and avoids requiring CORS changes. Runtime API
credentials stay with FastAPI.

```powershell
npm run build
npx tsc --noEmit
npm run lint
npm start
# In a second shell, with the API running:
npx playwright install chromium
npm run smoke
```

The smoke submits development examples to the real API (LLM usage), records
rendered statuses and screenshots in `../docs/`, and checks citation navigation,
mobile layout and frontend errors. It never evaluates frozen final questions.
`SMOKE_BASE_URL` may override `http://127.0.0.1:3000`.

`npm run snapshot` deterministically regenerates `src/data/evaluation.json`
from four committed experiment records; `prebuild` runs it automatically.
Only whitelisted summaries and provenance hashes are included. Frozen question
text, final answers, raw traces and raw experiment files are excluded from
the browser and final Docker image. Final-test scores are read, never rerun.

The root README documents `docker compose up -d --build` for the full stack.
