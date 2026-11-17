"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Report } from "@/lib/types";
export default function ReportView({ acn }: { acn: string }) {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    api<Report>(`report/${encodeURIComponent(acn)}`)
      .then((v) => {
        if (active) {
          setReport(v);
          setError("");
        }
      })
      .catch((e) => {
        if (active)
          setError(e instanceof Error ? e.message : "Could not load report.");
      });
    return () => {
      active = false;
    };
  }, [acn, retry]);
  return (
    <div className="report-body">
      <Link href="/" className="subtle">
        ← Back to Ask
      </Link>
      <p className="eyebrow mt-8">INDEXED SOURCE ACCOUNT</p>
      <h1>Report {acn}</h1>
      <p className="lead">
        The original reporter narrative, with its provenance and month-level
        metadata.
      </p>
      {error ? (
        <div className="error-box" role="alert">
          {error}
          <button
            className="quiet-button block mt-3"
            onClick={() => {
              setError("");
              setRetry((v) => v + 1);
            }}
          >
            Retry report
          </button>
        </div>
      ) : !report ? (
        <div className="loading-box" role="status">
          Loading the indexed source report…
          <div className="progress-bar">
            <span />
          </div>
        </div>
      ) : (
        <>
          <dl className="metadata-grid">
            {[
              ["Report month", report.report_month],
              ["Flight phase", report.flight_phase],
              ["Aircraft", report.aircraft_category],
              ["Source", report.source_dataset],
              ["Index build", String(report.index_id)],
              ["Anomaly labels", report.anomaly_codes?.join("; ")],
            ].map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{value || "Not recorded"}</dd>
              </div>
            ))}
          </dl>
          <section className="card card-pad mb-5">
            <p className="eyebrow">SYNOPSIS</p>
            <p className="report-text mb-0">
              {report.synopsis || "No synopsis recorded."}
            </p>
          </section>
          <section className="card card-pad">
            <p className="eyebrow">REPORTER NARRATIVE</p>
            <div className="report-text">
              {report.narrative || "No narrative recorded."}
            </div>
            <div className="section-divider subtle">
              Source revision:{" "}
              <span className="break-all font-mono">
                {report.source_revision || "Not recorded"}
              </span>
              <br />
              Content hash:{" "}
              <span className="break-all font-mono">{report.content_hash}</span>
              <br />
              These are voluntary reporter accounts, not confirmed findings.
            </div>
          </section>
        </>
      )}
    </div>
  );
}
