"use client";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { presets } from "@/lib/presets";
import type { AskResponse, Health } from "@/lib/types";
import StatusBadge from "./status-badge";
import TracePanel from "./trace-panel";
function CitedAnswer({ text }: { text: string }) {
  return (
    <div className="answer-text">
      {text.split(/(\[(?:ACN\s*[:#]?\s*)?\d+\])/gi).map((part, i) => {
        const match = part.match(/^\[(?:ACN\s*[:#]?\s*)?(\d+)\]$/i);
        return match ? (
          <Link
            className="acn-chip"
            href={`/report/${match[1]}`}
            key={i}
            aria-label={`Open ASRS report ${match[1]}`}
          >
            ACN {match[1]} ↗
          </Link>
        ) : (
          <span key={i}>{part}</span>
        );
      })}
    </div>
  );
}
export default function AskWorkspace() {
  const [question, setQuestion] = useState("");
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState(false);
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [pending, setPending] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api<Health>("health")
      .then((v) => {
        if (active) setHealth(v);
      })
      .catch(() => {
        if (active) setHealthError(true);
      });
    return () => {
      active = false;
    };
  }, []);
  useEffect(() => {
    if (!pending) return;
    const timer = setInterval(() => setElapsed((v) => v + 1), 1000);
    return () => clearInterval(timer);
  }, [pending]);
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (pending || !question.trim()) return;
    setPending(true);
    setElapsed(0);
    setError("");
    setAnswer(null);
    try {
      setAnswer(
        await api<AskResponse>("ask", {
          method: "POST",
          body: JSON.stringify({ question: question.trim() }),
        }),
      );
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "This request could not be completed.",
      );
    } finally {
      setPending(false);
    }
  }
  return (
    <>
      <div className="hero">
        <div>
          <p className="eyebrow">THE REPORTER’S PERSPECTIVE</p>
          <h1>
            Find the account.
            <br />
            <span className="text-[#72846d]">Understand the context.</span>
          </h1>
          <p className="lead">
            Explore aviation safety reports with answers you can trace back to
            the source. What the accounts support—and what they don’t.
          </p>
        </div>
        <div className="health-pill" aria-live="polite">
          <span className="tiny-dot" />
          {health
            ? "Corpus ready"
            : healthError
              ? "Service unavailable"
              : "Connecting to corpus…"}
          <strong>
            {health
              ? `${health.reports.toLocaleString()} reports`
              : "ASRS collection"}
          </strong>
          <span className="subtle">
            {health
              ? `Build ${health.index_id} · ${health.chunks.toLocaleString()} passages`
              : "Reporter accounts · month-level dates"}
          </span>
        </div>
      </div>
      <div className="workspace">
        <div>
          <section className="card card-pad">
            <div className="card-head">
              <h2>Ask the reports</h2>
              <span className="subtle">01 / EXPLORE</span>
            </div>
            <form onSubmit={submit}>
              <label htmlFor="question" className="sr-only">
                Your question
              </label>
              <textarea
                id="question"
                className="question-box"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                maxLength={2000}
                required
                disabled={pending}
                placeholder="Which situations or contributing factors are you exploring?"
              />
              <div className="composer-bottom">
                <span className="subtle">
                  Answers grounded in cited reporter accounts.
                </span>
                <button
                  className="primary-button"
                  disabled={pending || !question.trim()}
                  type="submit"
                >
                  {pending ? "Reviewing evidence…" : "Find evidence ↗"}
                </button>
              </div>
            </form>
            <div className="presets" aria-label="Example questions">
              {presets.map((p) => (
                <button
                  type="button"
                  className="chip"
                  key={p.label}
                  disabled={pending}
                  onClick={() => setQuestion(p.question)}
                >
                  {p.label} ↗
                </button>
              ))}
            </div>
            {pending && (
              <div className="loading-box" role="status" aria-live="polite">
                <strong>Reviewing the reporter accounts · {elapsed}s</strong>
                <p className="subtle mt-2 mb-0">
                  The backend may grade evidence and try up to two query
                  rewrites. Runs can take 15–60 seconds. The actual stage
                  timeline arrives with the completed response.
                </p>
                <div className="progress-bar" aria-hidden="true">
                  <span />
                </div>
              </div>
            )}
            {error && (
              <div className="error-box" role="alert">
                {error}
                <br />
                <span className="subtle">
                  Your question is kept above. No automatic retry was sent.
                </span>
              </div>
            )}
            {!answer && !pending && !error && (
              <div className="empty-state">
                <div className="empty-symbol" aria-hidden="true">
                  ⌕
                </div>
                <h3>A useful answer starts with the evidence.</h3>
                <p>
                  Ask about a situation, use an example above,
                  <br />
                  or visit the evaluation lab to see how the system performs.
                </p>
              </div>
            )}
            {answer && (
              <div className="section-divider" data-testid="answer">
                <div className="card-head">
                  <h3>What the accounts support</h3>
                  <StatusBadge status={answer.status} />
                </div>
                {answer.aggregate && (
                  <div className="aggregate" data-testid="aggregate">
                    <span className="eyebrow">MATCHING REPORTS</span>
                    <div className="aggregate-value">
                      {answer.aggregate.count.toLocaleString()}{" "}
                      <span className="text-sm tracking-normal text-[#687c60]">
                        of {answer.aggregate.denominator.toLocaleString()}{" "}
                        indexed reports
                      </span>
                    </div>
                    <pre>
                      Filters:{" "}
                      {JSON.stringify(answer.aggregate.filters, null, 2)}
                    </pre>
                    <p className="subtle mt-3 mb-0">
                      {answer.aggregate.caveat}
                    </p>
                    <details className="subtle mt-3">
                      <summary>View count provenance</summary>
                      <pre>
                        {answer.aggregate.sql}
                        <br />
                        Parameters:{" "}
                        {JSON.stringify(answer.aggregate.parameters)}
                      </pre>
                    </details>
                  </div>
                )}
                <CitedAnswer text={answer.answer} />
                {answer.validation.flagged && (
                  <div className="error-box">
                    Citation validation flagged this response. Unsupported
                    citations are excluded and the answer is treated as
                    insufficient evidence.
                  </div>
                )}
                {answer.citations.length > 0 && (
                  <div className="section-divider">
                    <h3>
                      Follow the evidence{" "}
                      <span className="subtle">/ exact indexed passages</span>
                    </h3>
                    {answer.citations.map((c) => (
                      <details
                        className="evidence-item"
                        key={`${c.acn}-${c.chunk_id}`}
                      >
                        <summary>
                          <Link className="acn-chip" href={`/report/${c.acn}`}>
                            ACN {c.acn} ↗
                          </Link>
                          <span className="subtle"> Passage {c.chunk_id}</span>
                        </summary>
                        <blockquote className="evidence-quote">
                          {c.passage}
                        </blockquote>
                      </details>
                    ))}
                  </div>
                )}
                {answer.results.length > 0 && (
                  <details className="section-divider">
                    <summary className="subtle cursor-pointer">
                      Explore {answer.results.length} retrieved reports
                    </summary>
                    <div className="result-list">
                      {answer.results.map((h, i) => (
                        <Link
                          className="result-link"
                          href={`/report/${h.acn}`}
                          key={h.acn}
                        >
                          <div>
                            <span className="result-number">
                              {String(i + 1).padStart(2, "0")}
                            </span>
                            <strong>ACN {h.acn}</strong>
                            <p>{h.text.split("\n")[0]}</p>
                          </div>
                          <span>↗</span>
                        </Link>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            )}
          </section>
        </div>
        <aside>
          <TracePanel events={answer?.trace} usage={answer?.usage} />
          <div className="aside-note">
            <strong>Evidence has limits.</strong>ASRS records are voluntary,
            de-identified accounts. Dates usually identify a month, not an exact
            time. A partial answer states what is supported; a refusal keeps an
            unsupported premise from becoming a finding.
            <Link href="/results" className="block mt-3 text-[#176c5b]">
              Explore the evaluation story →
            </Link>
          </div>
        </aside>
      </div>
    </>
  );
}
