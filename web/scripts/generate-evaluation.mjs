import { readFile, mkdir, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
const names = [
  "experiment.json",
  "experiment_step7_ablation.json",
  "experiment_step7b.json",
  "experiment_step7d.json",
];
const records = [],
  sources = [];
for (const name of names) {
  const raw = await readFile(
    new URL(`../../eval/${name}`, import.meta.url),
    "utf8",
  );
  records.push(JSON.parse(raw));
  sources.push({
    path: `eval/${name}`,
    sha256: createHash("sha256").update(raw).digest("hex"),
  });
}
const [dev, ablation, calibration, final] = records;
// Explicit allowlist: never ship final questions, answers, traces, or raw records.
const snapshot = {
  sources,
  corpus: { reports: dev.corpus.reports, chunks: dev.corpus.chunks },
  development: {
    layer1: dev.all_category_queries,
    layer2: dev.judged_relevance.averages,
  },
  ablation: Object.entries(ablation.summaries).map(([name, s]) => ({
    name,
    statuses: s.normal_answer_statuses,
    controls: s.controls_passed,
    fullyJudged: s.fully_judged_queries,
    coverage: s.partial_signals.coverage_at_10,
    latency: s.mean_latency_ms,
    input: s.mean_input_tokens,
    output: s.mean_output_tokens,
    retries: s.mean_retries,
  })),
  calibration: Object.entries(calibration.summaries).map(([name, s]) => ({
    name,
    ...Object.fromEntries(
      ["before", "after"].map((phase) => {
        const x = s[phase];
        return [
          phase,
          {
            supported: x.supported_normal_responses,
            statuses: x.normal_statuses,
            controls: x.controls_passed,
            precision: x.citation_precision_on_judged,
            coverage: x.citation_judged_coverage,
            latency: x.mean_latency_ms,
            input: x.mean_input_tokens,
            output: x.mean_output_tokens,
          },
        ];
      }),
    ),
  })),
  final: {
    retrieval: final.retrieval_metrics.averages,
    retrievalCoverage: final.retrieval_judgment_coverage,
    controlsPassed: final.controls.filter((c) => c.passed).length,
    controlsTotal: final.controls.length,
    citation: final.citation_summary,
    cost: final.ask_mean_cost,
    counts: final.counts.map((c) => ({
      id: c.query_id,
      status: c.status,
      expected: c.expected.count,
      expectedDenominator: c.expected.denominator,
      expectedFilters: c.expected.filters,
      actual: c.system_aggregate?.count ?? null,
      denominator: c.system_aggregate?.denominator ?? null,
      filters: c.system_aggregate?.filters ?? null,
      exact: c.exact_match,
    })),
    statuses: Object.values(final.ask)
      .filter((a) => a.kind === "mechanism")
      .reduce((out, a) => {
        const status = a.response?.status ?? a.status;
        out[status] = (out[status] ?? 0) + 1;
        return out;
      }, {}),
  },
};
const serialized = JSON.stringify(snapshot, null, 2) + "\n";
for (const row of (
  await readFile(
    new URL("../../eval/queries_final.jsonl", import.meta.url),
    "utf8",
  )
)
  .trim()
  .split("\n")
  .map(JSON.parse))
  if (serialized.includes(row.question))
    throw new Error("Frozen question leaked");
const target = new URL("../src/data/evaluation.json", import.meta.url);
await mkdir(new URL("../src/data/", import.meta.url), { recursive: true });
await writeFile(target, serialized, "utf8");
console.log(
  "Generated sanitized evaluation snapshot from four committed records.",
);
