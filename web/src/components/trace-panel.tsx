"use client";
import { useState } from "react";
import type { TraceEvent, Usage } from "@/lib/types";
function object(v: unknown): Record<string, unknown> {
  return v && typeof v === "object" ? (v as Record<string, unknown>) : {};
}
function Detail({ event }: { event: TraceEvent }) {
  const d = event.detail,
    output = object(d.output);
  const query =
    typeof d.query === "string"
      ? d.query
      : typeof output.query === "string"
        ? output.query
        : null;
  return (
    <div className="trace-detail">
      {query && <div className="trace-query">“{query}”</div>}
      {d.attempt !== undefined && (
        <span>
          Retrieval attempt {Number(d.attempt) + 1} · {String(d.reports)}{" "}
          reports
        </span>
      )}
      {typeof output.sufficiency === "string" && (
        <>
          <span className="trace-verdict">{output.sufficiency}</span>
          <p>{String(output.reason)}</p>
        </>
      )}
      {Array.isArray(output.reports) && (
        <details>
          <summary>
            Model relevance checks · {output.reports.length} reports
          </summary>
          {output.reports.map((v, i) => {
            const r = object(v);
            return (
              <div key={i} className="trace-query">
                ACN {String(r.acn)} · relevance {String(r.relevance)}
                <br />
                {String(r.reason)}
              </div>
            );
          })}
        </details>
      )}
      {typeof d.strategy === "string" && (
        <p>
          Retry {String(d.retry)} · {d.strategy}
        </p>
      )}
      {event.stage === "route" && (
        <span>
          {d.count_intent
            ? d.unmapped_aggregate
              ? "Count request · filters could not be mapped"
              : "Count request · metadata filters mapped"
            : "Reporter-account evidence path"}
        </span>
      )}
      {event.stage === "aggregate_sql" && (
        <span>
          Auditable metadata count · denominator {String(d.denominator)}
        </span>
      )}
      {event.stage === "finalize" && (
        <span>Outcome: {String(d.status).replaceAll("_", " ")}</span>
      )}
    </div>
  );
}
export default function TracePanel({
  events,
  usage,
}: {
  events?: TraceEvent[];
  usage?: Usage;
}) {
  const [open, setOpen] = useState(true);
  return (
    <section className="card" aria-label="Evidence trace">
      <button
        className="trace-title"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-controls="trace-timeline"
      >
        <span>
          <strong>Behind the answer</strong>
          <span className="subtle">Every check. Every query. In sequence.</span>
        </span>
        <span aria-hidden="true">{open ? "−" : "+"}</span>
      </button>
      {!events?.length ? (
        <div className="trace-idle">
          The completed backend trace will appear here after you ask a question.
          Stage timings and token usage come directly from the API.
        </div>
      ) : (
        open && (
          <div
            className="trace-content"
            id="trace-timeline"
            data-testid="trace-timeline"
          >
            <ol className="timeline">
              {events.map((e, i) => (
                <li key={i} className="timeline-item">
                  <span className="timeline-dot" />
                  <div className="timeline-top">
                    <span className="timeline-stage">
                      {e.stage.replaceAll("_", " ")}
                    </span>
                    <span className="timeline-cost">
                      {e.latency_ms.toFixed(0)} ms ·{" "}
                      {(e.input_tokens ?? 0) + (e.output_tokens ?? 0)} tok
                    </span>
                  </div>
                  <Detail event={e} />
                  {e.model_calls > 0 && (
                    <span className="subtle">
                      {e.input_tokens ?? "—"} in / {e.output_tokens ?? "—"} out
                      · {e.model_calls} model call
                    </span>
                  )}
                </li>
              ))}
            </ol>
            {usage && (
              <div className="usage-strip">
                <span>{(usage.latency_ms / 1000).toFixed(2)}s total</span>
                <span>
                  {usage.input_tokens.toLocaleString()} in /{" "}
                  {usage.output_tokens.toLocaleString()} out
                </span>
                <span>
                  {usage.retries} retries · {usage.model_calls} model calls
                </span>
              </div>
            )}
          </div>
        )
      )}
    </section>
  );
}
