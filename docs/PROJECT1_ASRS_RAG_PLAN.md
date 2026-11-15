# Project 1 — SafeLens (working name): NASA ASRS Aviation Safety RAG

**Status: DECIDED 2026-11-14 (Cynthia).** This spec replaces the FilingLens (SEC filings) draft in `PROJECT_LIST.md`. The domain changed; the portfolio purpose, the three differentiators, and the stack did not.

**Benchmark target:** UC Berkeley School of Information, MIDS Capstone Spring 2026 — *Aviation Safety Search Engine* (https://www.ischool.berkeley.edu/programs/mids/capstone/2026a-spring/aviation-safety). Strategy: replicate its retrieval core on the same public corpus, then extend it in the three places it stops short — a grounded generation layer, continuous ingestion, and a stricter evaluation protocol.

**Amendment v1.3 (2026-11-15, Sunny self-review of the Mini spec, propagated here):** leftover "BM25" wording in the query-path diagram, M2 row, and interview story corrected to "lexical"; chunk metadata date is month-granularity; the embedding bake-off now mandates vendor-recommended query/document prefixes per candidate (§6).

**Amendment v1.2 (2026-11-15, from an external architecture review of the Mini spec):** the lexical baseline is correctly identified as PostgreSQL FTS, not BM25 (true BM25 via `pg_search` becomes a bake-off variant, §6); the retrieval benchmark gains the Mini's pooled judged-relevance layer alongside label recall (§8); a synopsis-vs-narrative text ablation is added (§8).

**Amendment v1.1 (2026-11-14, from external review suggestions Cynthia shared):** adopted — source-typed citations with an explicit evidence-tier rule (§7), Citation Accuracy and latency as named metrics (§8), a thin-evidence control question (§8), and a scoped Phase 2 multi-source expansion (§14). Not adopted for MVP: NTSB and regulatory corpora (sequenced to Phase 2 to protect the 3–4 week scope).

---

## 1. Purpose (why this project exists)

Portfolio Project 1 closes Cynthia's largest evidence gap: a **traditional RAG system** — chunking → embeddings → vector retrieval → hybrid search / rerank → grounded generation → evaluation in CI. Her production AI work (Entmoot) is index + on-demand fetch, not embeddings/vector search, and Project 2's doc-search proves retrieval only at small, clean-corpus scale. This project proves it at 47k messy real-world documents, in a domain adjacent to her aviation-tracking career, without re-proving strengths her resume already covers (backend scale, AWS, complex SQL, real-time ingestion).

The three differentiators carried over from the FilingLens draft:

1. **Agentic self-correction loop** — retrieval grading → query rewrite & retry → explicit abstention when evidence is insufficient; the loop is visible in the UI as a trace.
2. **Evaluation in CI** — a label-grounded retrieval benchmark plus a golden Q&A set, RAGAS/DeepEval gates, and a published ablation table. Scores drive design changes; that loop is the interview story.
3. **Incremental ingestion** — reports keyed by ACN + content hash; new NASA batches re-index only what changed. (The Berkeley team's own roadmap lists continuous ingestion as unbuilt future work — building it is one of our three extensions.)

## 2. The benchmark: what Berkeley built, and our extensions

Berkeley system (verified from the project page, 2026-11-14):

- Corpus: 47,723 de-identified NASA ASRS reports over a decade → 112,997 overlapping chunks.
- Query path: LLM query expansion → parallel keyword + semantic search (top 50 each) → rank-position fusion → LLM relevance filtering in iterative batches with automatic stopping → ranked list (up to 500 results). **It is a search engine: no answer generation.**
- Embedding model (GTE Large) chosen by benchmarking 16 candidates / 7 families on 200 synthetic queries; a purpose-built aviation model (SafeAeroBERT) ranked only 12th.
- Evaluation: NASA's own 92 expert-assigned anomaly categories as ground truth. Reported results: ~7 of top 10 results directly relevant for common incident types; rare-type recall more than 2× keyword-only, reaching 41% recall across the full relevant pool.
- Deployment: Kubernetes on AWS, S3 + PostgreSQL. (Infrastructure is *not* something Cynthia needs to prove; we deliberately ship Docker Compose — see §9.)

Our three extensions beyond the benchmark:

| Extension | Why |
|---|---|
| **Grounded generation layer** ("Ask" mode) | Completes the RAG story Berkeley omits: cross-report pattern synthesis with per-claim citations and abstention; adds faithfulness evaluation. |
| **Continuous ingestion** | Their stated future work; demonstrates the document-lifecycle answer every RAG interview asks about. |
| **Stricter evaluation** | Their model selection used synthetic queries only. Ours combines label-based recall (primary), paraphrased + human-authored queries, and generation metrics, all gated in CI. |

## 3. Users and core scenarios

Persona: an airline **SMS (Safety Management System) analyst** — the Berkeley persona; a real role in Cynthia's industry.

1. **Search mode** — "runway incursion with a vehicle on the active runway" → ranked reports, filterable by date, anomaly category, flight phase, aircraft category; each hit shows why it matched.
2. **Ask mode** — "What human factors recur in fatigue-related altitude deviations?" → a synthesized pattern summary; every claim carries citations to specific reports (ACN); the system abstains when retrieved evidence is thin.
3. **Precedent lookup** — after a new incident, find whether it has happened before and how often (count + trend over time from metadata, not from the LLM).

Out of scope for the persona: any airworthiness/safety determination. The UI carries the same caveat NASA does — ASRS reports are unverified reporter narratives; this is a research demo, not an operational safety tool.

## 4. Data

**Source:** NASA Aviation Safety Reporting System (ASRS), public, de-identified.

Acquisition (all three routes verified 2026-11-14):

1. **Primary — ASRS Database Online** (asrs.arc.nasa.gov/search/database.html): query by date range and export CSV; **10,000 records per export** → ~5 exports by year slice for a 2015–2025 corpus of ~48k reports.
2. **Bootstrap/fallback — Hugging Face** `elihoole/asrs-aviation-reports`: 38,655 reports (Jan 2012 – Mar 2022), 111 fields. Use to start M1 before manual exports are done; final corpus should come from the official source.
3. **Not needed at this scale:** formal ASRS data request (precedent exists for 385k documents, but 48k via exports is enough and matches the benchmark).

Schema notes (verified quirks to design around):

- Export CSV has ~125 physical columns with a **mirrored schema** (Aircraft 1/2, Person 1/2) producing ~48 duplicate column names across ~77 unique fields. The loader must disambiguate explicitly (`aircraft_1.*`, `aircraft_2.*`) — no silent pandas dedup.
- Fields we keep: ACN (document id), report date, synopsis, narrative(s), anomaly codes, flight phase, aircraft category/make, reporter function, environment (WX, airport), human factors codes. Everything else is dropped at normalize time and documented.
- **Anomaly codes are the evaluation ground truth** — they ship inside the export (expert-coded by ASRS analysts). Multi-label is normal; a report can carry several anomaly codes.
- Dedupe key: ACN. Change detection: SHA-256 over the normalized report record.

## 5. Ingestion and chunking

Pipeline: `download (manual CSV drops) → normalize → dedupe (ACN) → assemble document text (synopsis + narrative) → chunk → embed → index`. Idempotent end to end; re-running on the same exports changes nothing.

- Chunking: narrative-aware. Split on paragraph boundaries first, then pack to **400–600 tokens with 15–20% overlap** (Berkeley's 47,723 → 112,997 chunks implies ~2.4 chunks/report; we validate our ratio against that). Synopsis is prepended to each chunk as context (it is the analyst-written summary of the same event). Metadata (ACN, report month — ASRS public data is month-granularity — anomaly codes, phase, aircraft) is stored on every chunk and used for filtering — never embedded as text, except a short header line (`Phase: Landing | Anomaly: Runway Incursion`) whose value is A/B-tested in the ablation.
- Incremental: a monthly job re-exports the latest date slice, diffs by ACN + content hash, and inserts/updates/deletes only the delta. Deletions are rare in ASRS but handled.

## 6. Indexing and the embedding bake-off

- **Store:** PostgreSQL + pgvector (chunk embeddings + all metadata + full-text). The lexical baseline is PostgreSQL FTS (`ts_rank_cd`) with a configuration that preserves aviation acronyms/codes as single tokens (TCAS, RA, ACN-style codes must not be stemmed away) — note `ts_rank_cd` is **not** BM25, and the docs must never call it that. A true BM25 engine (ParadeDB `pg_search`) is included as a compared variant in the M3 retrieval bake-off; whichever lexical engine wins becomes the hybrid's lexical leg.
- **Embedding model is an experiment, not a default.** Bake-off on the label-based eval (§8) across 4–6 candidates spanning families: `gte-large-en-v1.5`, `bge-large-en-v1.5`, `e5-large-v2`, one code/API model (`text-embedding-3-small`), and `SafeAeroBERT`-class domain model if readily available — replicating Berkeley's "domain model loses" finding (or refuting it) with our own numbers is a deliberate story beat. Winner is chosen by rare-category recall, not overall recall. Every candidate is evaluated **with its vendor-recommended query/document prefixes and pooling** (asymmetric models are handicapped without them — the Mini self-review caught this), and the exact settings are recorded in the experiment config.
- Local inference via sentence-transformers is the default (one-time cost for ~113k chunks); an API-embedding config switch is kept for comparison runs.

## 7. Query path (LangGraph)

Two modes share one retrieval core:

```
query → classify (search | ask)
      → expand: LLM adds synonym/acronym variants from an aviation glossary
        (e.g. runway incursion → ground incursion, vehicle on the active)
      → hybrid retrieve: dense top-50 + lexical top-50 (metadata filters applied)
      → fuse: Reciprocal Rank Fusion
      → rerank: cross-encoder (bge-reranker-large) over fused top-100
      → LLM relevance filter: batched grading, stop when batch precision collapses
      → grade evidence: sufficient?
          ├─ no, retries left → rewrite query (narrow/broaden) → loop (max 2)
          └─ no, exhausted → ABSTAIN with reason
      → search mode: ranked list
        ask mode: generate pattern summary, every claim cited [ACN],
                  claims without support are dropped by a faithfulness check
```

Streaming responses; every stage emits trace events (expansion terms, per-stage hit counts, grading decisions, retries) that the UI renders — the self-correction loop must be *visible*, not just implemented.

**Citations are source-typed, and evidence tiers are never blurred.** Every citation carries its source type — in MVP `[ASRS report, ACN …]`; in Phase 2 also `[NTSB investigation …]` and `[Regulation/Guidance …]`. The three tiers mean different things — voluntary unverified reporter narratives, formal investigation conclusions, and current regulatory requirements — and generation prompts, UI badges, and answer structure must keep them visibly separate. A narrative can never be cited as if it were a rule; a regulation can never be summarized from incident reports.

Cost controls: the LLM filter uses a small/cheap model, batches of ~20, hard cap on judged candidates per query; all LLM calls behind a provider interface (OpenAI first; local model optional).

## 8. Evaluation (the core deliverable)

**Retrieval benchmark (label-grounded).** For a stratified set of anomaly categories (all 92 if pool sizes allow; minimum 30 spanning common and rare):

- Query set per category: (a) template queries from the category definition, (b) LLM paraphrases in analyst language, (c) ~15 human-authored queries by Cynthia. Synthetic-only evaluation is the benchmark's known weakness; (c) exists to counter it.
- Gold pool: all reports carrying that category's anomaly code. Metrics: **Recall@50/100/500, Precision@10, nDCG@10**, reported **split by common vs rare categories** — rare-category recall vs the lexical-only baseline is the headline number (Berkeley reference: >2× keyword, 41% absolute; P@10 ≈ 0.7 on common types). Label recall at large K measures *category coverage* (that is what makes it Berkeley-comparable); it is complemented by the **pooled judged-relevance layer inherited from ASRS Mini** (`qrels.jsonl`: human grades over pooled top-K, Precision@K / MRR / nDCG) for query-level relevance — the two layers are always reported separately, never blended.

**Ablation table (published in README):** lexical only → dense only → hybrid → + expansion → + rerank → + LLM filter. Each row: common/rare recall + P@10. Any stage that doesn't earn its latency gets cut, and the cut is documented. One additional text-construction ablation: **narrative only vs synopsis + narrative** — the synopsis is expert-written and may be inflating retrieval scores; the size of that effect is reported, not assumed away.

**Generation evaluation (Ask mode).** ~30 golden questions authored from the corpus (pattern/factor questions with known supporting reports, plus 5 unanswerable controls). RAGAS: faithfulness, answer relevancy, context precision/recall. The unanswerable controls must abstain — a confident answer to any of them fails the gate. Two named metrics are tracked separately: **Citation Accuracy** (sampled human/RAGAS check that each cited report actually supports the claim attached to it) and **latency** (p50/p95 per pipeline stage, shown on the evaluation dashboard — the LLM filter must justify its latency in the ablation, not just its recall).

One probe question is fixed by name: *"GPS interference during approach near Canadian airports — compare contributing factors and identify relevant regulatory guidance."* ASRS is a U.S. corpus, so evidence is structurally thin and the regulatory half is out of corpus in MVP. This is a **thin-evidence probe, not an abstention control**: the corpus may legitimately contain matching reports, so a sourced partial answer is a *pass* — correct behavior is to answer only what the evidence supports, flag the thin evidence explicitly, and abstain on the rest. (True abstention controls are verifiably-absent facts, per the Mini spec's three control types: out-of-domain, precision the record cannot contain, fabricated identifier.) This question becomes fully answerable only in Phase 2 (§14) — it is the acceptance test for the multi-source expansion.

**CI gate (DeepEval / pytest):** PRs run the retrieval benchmark + generation eval against a cached 5k-report subset index; thresholds = no regression >2 points on rare recall, faithfulness ≥ 0.85 on the subset. Full-corpus eval runs manually/nightly and updates the README table.

## 9. Stack and deployment

- Backend: Python, FastAPI, LangGraph, PostgreSQL + pgvector, sentence-transformers, Docker Compose.
- Frontend: Next.js + TypeScript + React — search/ask UI, filters, full-report view, trace panel, and an **evaluation dashboard page** rendering the ablation and bake-off tables from committed eval artifacts.
- Deployment: Docker Compose locally; public demo on a single small host (Fly.io/Render-class). No Kubernetes — deliberate scope decision, documented in the README as such (the portfolio does not need another infrastructure proof).
- Repo hygiene: English docs and code comments (Cynthia's standing rule), README with architecture diagram, trade-offs, how-to-run, and the eval tables; tests for loader, chunker, fusion, and the abstain path.

**Execution note (2026-11-15):** M0–M2 are front-run by **ASRS Mini**, a one-weekend prototype build specified in `PROJECT1_MINI_WEEKEND_SPEC.md` — same repo, HF-dataset subset (~5k reports, 4 categories), five hard seams (pgvector from day one, ACN + content hash, metadata-rich chunks, provider interfaces, standalone eval harness) so the prototype upgrades into this plan instead of being discarded.

## 10. Milestones

| Milestone | Contents | Exit criteria |
|---|---|---|
| **M0 Data spike** (2–3 days) | One official 10k export + HF dataset check; loader handles mirrored schema; field inventory doc | 10k reports parsed, anomaly-code coverage counted, go/no-go on official route |
| **M1 Retrieval v1** (2–3 days) | Full ingest + chunk + pgvector/FTS indexes; CLI search; one default embedding model | End-to-end search over ~48k reports from CLI |
| **M2 Eval harness** (3–4 days) | Label-based benchmark, lexical/dense baselines, stratified reporting | Baseline table exists *before* any tuning — measure-first is a rule |
| **M3 Hybrid pipeline** (1 week) | Expansion, RRF, rerank, LLM filter; embedding bake-off | Full ablation table; model choice documented with numbers |
| **M4 Agentic + generation** (1 week) | LangGraph loop (grade/rewrite/abstain), Ask mode with citations, golden Q&A, RAGAS, CI gate | Abstain controls pass; CI gate live on PRs |
| **M5 Product surface** (3–5 days) | Next.js UI + trace + filters, incremental ingestion job, demo deploy, README + case study | Public demo URL; a new monthly batch ingests as a delta-only run |

Total: ~3–4 weeks at portfolio pace (evenings/weekends, Codex-assisted).

## 11. Explicit non-goals

No fine-tuning in MVP (Phase 2 experiment: fine-tune a small embedder on ASRS pairs and re-run the bake-off). No GraphRAG. No multi-tenancy/auth beyond a demo login wall if the host requires one. No real-time flight/NOTAM data. No safety or airworthiness conclusions anywhere in the product copy. No company data, systems, or names — the corpus is 100% public NASA data. No NTSB or regulatory corpora in MVP — they are Phase 2 (§14), deliberately sequenced after the single-corpus system is measured.

## 12. Risks and mitigations

- **Manual exports are tedious** (5 × 10k through a web UI) → HF dataset bootstraps M1; official exports land before M2 baselines are frozen.
- **Label noise / multi-label skew** → stratify by category size, report per-category, never a single blended recall number.
- **LLM filter cost/latency** → small model, batching, early stop, per-query cap; the ablation must show the filter earns its cost or it ships off by default.
- **Synthetic-query bias** → human-authored queries in the eval set; paraphrases reviewed, not raw-generated.
- **Narrative quality varies wildly** (shorthand, all-caps era reports) → normalization documented; chunking validated on samples from different decades.

## 13. Interview story (what this proves, in one breath each)

- Why hybrid retrieval is not optional in jargon-heavy domains: acronyms need lexical search, paraphrases need embeddings, and the ablation table shows each failing alone.
- Model selection by measurement: a domain-specific model lost to general models — twice (Berkeley's result, our bake-off).
- Rare-event recall is the metric that matters in safety domains, and optimizing for it changes design choices (recall-first fusion, filter tuned to not over-prune).
- The full lifecycle: ingestion deltas, eval gates in CI, abstention as a designed behavior — not a chatbot with a vector DB attached.

## 14. Phase 2 — multi-source expansion (post-MVP, scoped)

Sequenced after M5, in this order, each gated by the §8 evaluation before the next starts:

1. **Regulatory guidance mini-corpus** — a *bounded* set (~10–15 documents) mapped to the highest-volume anomaly categories: FAA Advisory Circulars and guidance relevant to those categories (e.g., SMS, runway safety, GNSS/GPS interference), plus the matching Transport Canada guidance where it exists. Not "all of 14 CFR" — the corpus boundary is the category map, and the map is published in the README. Adds a second retrieval index with its own chunking (section-structured, like regulations demand) and cross-corpus Ask questions to the golden set.
2. **NTSB investigation corpus** — formal accident/incident investigations (public NTSB data: narratives, findings, probable cause), ingested as a third source type. Enables the highest-value cross-source question class: *has this near-miss pattern ever become an investigated accident, and what did the investigation conclude?*
3. **Geo/temporal enrichment** — airport/state filters already exist in MVP metadata; Phase 2 adds an airport reference join (public airport data) for map display and region-level aggregation. Full GIS analysis is out of scope.

Phase 2 is what turns SafeLens from a single-corpus RAG into a multi-source evidence system; it is also the easiest place to lose the plot, so it stays out of MVP and each step must re-run the full benchmark before it counts as done.

## 15. Open decisions (Cynthia, before M0)

1. **Name** — SafeLens is a working title; alternatives welcome before the repo is created.
2. **LLM provider** for expansion/filter/generation — OpenAI API (pay-per-use, simplest) vs local models (free, slower filter). Default in this spec: OpenAI for generation/filter, local for embeddings.
3. **Corpus window** — 2015–2025 (~48k, matches Berkeley) is the default; a smaller 20k corpus is the fallback if M0 shows exports are slower than expected.
