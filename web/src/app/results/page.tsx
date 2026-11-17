import data from "@/data/evaluation.json";
const pct = (v: number | null) =>
  v === null ? "—" : `${(v * 100).toFixed(2)}%`;
const num = (v: number) => v.toFixed(4);
const seconds = (v: number) => `${(v / 1000).toFixed(2)}s`;
const label = (s: string) =>
  s === "lexical" ? "PostgreSQL FTS" : s === "hybrid" ? "Hybrid" : "Dense";
export default function Results() {
  return (
    <>
      <div className="hero">
        <div>
          <p className="eyebrow">THE EVALUATION LAB</p>
          <h1>
            Evidence you
            <br />
            <span className="text-[#72846d]">can inspect.</span>
          </h1>
          <p className="lead">
            From retrieval experiments to a single frozen test. Measured
            results, with their limitations visible.
          </p>
        </div>
        <span className="health-pill">
          {data.corpus.reports.toLocaleString()}-report corpus<strong>Report-level evaluation</strong>
          <span className="subtle">Committed experiment snapshots</span>
        </span>
      </div>
      <div className="metric-grid">
        <div className="metric">
          <p>Final hybrid P@10</p>
          <strong>{pct(data.final.retrieval.hybrid.precision_at_10)}</strong>
          <span className="subtle">Dense : BM25 = 10 : 1</span>
        </div>
        <div className="metric">
          <p>Final controls refused</p>
          <strong>
            {data.final.controlsPassed}/{data.final.controlsTotal}
          </strong>
          <span className="subtle">Zero invented citations</span>
        </div>
        <div className="metric">
          <p>Citation precision on judged</p>
          <strong>
            {pct(
              data.final.citation["all answered/partial"].precision_on_judged,
            )}
          </strong>
          <span className="subtle">
            Judged coverage{" "}
            {pct(data.final.citation["all answered/partial"].judged_coverage)}
          </span>
        </div>
      </div>
      <section className="card card-pad mt-8">
        <p className="eyebrow">01 / DEVELOPMENT</p>
        <h2>Retrieval before the production default</h2>
        <p className="subtle">
          Layer 1 measures weak-label category agreement across 28 queries, not
          human relevance. Layer 2 uses 8 judged queries. This historical hybrid
          uses FTS and equal weights; it is distinct from production BM25 10:1.
        </p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Retriever</th>
                <th>L1 category P@10</th>
                <th>L1 Hit@10</th>
                <th>L2 P@10</th>
                <th>L2 MRR</th>
                <th>L2 nDCG@10</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.development.layer1).map(([name, s]) => {
                const j =
                  data.development.layer2[
                    name as keyof typeof data.development.layer2
                  ];
                return (
                  <tr key={name}>
                    <td>{label(name)}</td>
                    <td>{pct(s.category_precision_at_10)}</td>
                    <td>{pct(s.hit_at_10)}</td>
                    <td>{num(j.precision_at_10)}</td>
                    <td>{num(j.mrr)}</td>
                    <td>{num(j.ndcg_at_10)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
      <section className="card card-pad mt-8">
        <p className="eyebrow">02 / STEP 7 ABLATION</p>
        <h2>More stages did not solve answerability</h2>
        <p className="subtle">
          Before calibration, supported answers were rare despite strong retrieval;
          every configuration passed its controls. Judgments are incomplete for several
          variants, so no full relevance comparison is implied.
        </p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Configuration</th>
                <th>Supported / 8</th>
                <th>Controls / 3</th>
                <th>Judged coverage</th>
                <th>Fully judged / 8</th>
                <th>Mean time</th>
                <th>Tokens in / out</th>
                <th>Retries</th>
              </tr>
            </thead>
            <tbody>
              {data.ablation.map((s) => (
                <tr key={s.name}>
                  <td>{s.name}</td>
                  <td>{s.statuses.answered + s.statuses.partial}</td>
                  <td>{s.controls}</td>
                  <td>{pct(s.coverage)}</td>
                  <td>{s.fullyJudged}</td>
                  <td>{seconds(s.latency)}</td>
                  <td>
                    {s.input.toFixed(0)} / {s.output.toFixed(0)}
                  </td>
                  <td>{s.retries.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="card card-pad mt-8">
        <p className="eyebrow">03 / STEP 7B CALIBRATION</p>
        <h2>Answer what the evidence supports</h2>
        <p className="subtle">
          Mechanism-level prompt and sufficiency calibration; citations remain
          fail-closed. Supported means answered or partial. Before measurements
          come from the calibration record, which is separate from the earlier
          ablation.
        </p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Configuration / phase</th>
                <th>Answered / partial / refused</th>
                <th>Supported / 8</th>
                <th>Controls / 3</th>
                <th>Citation precision</th>
                <th>Judged coverage</th>
                <th>Mean time</th>
                <th>Tokens in / out</th>
              </tr>
            </thead>
            <tbody>
              {data.calibration.flatMap((s) =>
                (["before", "after"] as const).map((phase) => {
                  const x = s[phase];
                  return (
                    <tr key={s.name + phase}>
                      <td>
                        {s.name} · {phase}
                      </td>
                      <td>
                        {x.statuses.answered} / {x.statuses.partial} /{" "}
                        {x.statuses.insufficient_evidence}
                      </td>
                      <td>{x.supported}</td>
                      <td>{x.controls}</td>
                      <td>{pct(x.precision)}</td>
                      <td>{pct(x.coverage)}</td>
                      <td>{seconds(x.latency)}</td>
                      <td>
                        {x.input.toFixed(0)} / {x.output.toFixed(0)}
                      </td>
                    </tr>
                  );
                }),
              )}
            </tbody>
          </table>
        </div>
      </section>
      <section className="card card-pad mt-8">
        <p className="eyebrow">04 / FROZEN FINAL TEST</p>
        <h2>One run. The failure stays visible.</h2>
        <p className="subtle">Mechanism outcomes: {Object.entries(data.final.statuses).map(([status, count]) => `${count} ${status.replaceAll('_', ' ')}`).join(' · ')}.</p>
        <p className="subtle">
          Eight mechanism queries, two controls and two counts. Both retrievers
          have complete top-ten judgment coverage. P@10 uses denominator 10;
          relevance is grade ≥ 1; nDCG uses linear gains 2 / 1 / 0 and the
          pooled ideal.
        </p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Retriever</th>
                <th>P@10</th>
                <th>MRR</th>
                <th>nDCG@10</th>
                <th>Judged coverage</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.final.retrieval).map(([name, s]) => (
                <tr key={name}>
                  <td>{name === "hybrid" ? "Hybrid · BM25 10:1" : "Dense"}</td>
                  <td>{num(s.precision_at_10)}</td>
                  <td>{num(s.mrr)}</td>
                  <td>{num(s.ndcg_at_10)}</td>
                  <td>{pct(data.final.retrievalCoverage[name as keyof typeof data.final.retrievalCoverage])}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="table-wrap mt-6">
          <table className="count-table">
            <thead>
              <tr>
                <th>Count check</th>
                <th>Expected</th>
                <th>System count / denominator</th>
                <th>Stated filters</th>
                <th>Outcome</th>
              </tr>
            </thead>
            <tbody>
              {data.final.counts.map((c) => (
                <tr key={c.id}>
                  <td>{c.id}</td>
                  <td>
                    {c.expected.toLocaleString()} /{" "}
                    {c.expectedDenominator.toLocaleString()}
                    <br />
                    <span className="subtle">
                      {JSON.stringify(c.expectedFilters)}
                    </span>
                  </td>
                  <td>
                    {c.actual === null
                      ? "No aggregate returned"
                      : `${c.actual.toLocaleString()} / ${c.denominator?.toLocaleString()}`}
                  </td>
                  <td>
                    {c.filters ? JSON.stringify(c.filters) : "None returned"}
                  </td>
                  <td>{c.exact ? "Exact match" : `Failed · ${c.status}`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="error-box mt-5">
          ft-cnt-1: the count intent was detected, but filters could not be
          mapped. The system returned no aggregate count or denominator. This
          documented routing gap is unchanged.
        </div>
        <p className="subtle mt-5">
          Final citation precision covers{" "}
          {data.final.citation["all answered/partial"].judged_report_pairs} of{" "}
          {data.final.citation["all answered/partial"].cited_report_pairs} cited
          pairs (
          {pct(data.final.citation["all answered/partial"].judged_coverage)}).
          Unjudged citations remain unknown. Mechanism-only judged coverage:{" "}
          {pct(
            data.final.citation["mechanism answered/partial"].judged_coverage,
          )}
          . Mean Ask time: {seconds(data.final.cost.latency_ms)};{" "}
          {data.final.cost.input_tokens.toFixed(0)} input /{" "}
          {data.final.cost.output_tokens.toFixed(0)} output tokens.
        </p>
      </section>
      <section className="card card-pad mt-8">
        <h2>Source trail</h2>
        <p className="subtle">
          Each source digest identifies the exact committed experiment record
          behind these tables.
        </p>
        {data.sources.map((s) => (
          <div className="source-row" key={s.path}>
            <strong>{s.path}</strong>
            <p className="mono subtle break-all">SHA-256 {s.sha256}</p>
          </div>
        ))}
      </section>
    </>
  );
}
