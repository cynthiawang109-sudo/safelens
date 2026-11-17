export type Status = "answered" | "partial" | "insufficient_evidence";
export interface Evidence {
  acn: string;
  chunk_id: number;
  passage: string;
}
export interface Hit {
  acn: string;
  chunk_id: number;
  text: string;
  score: number;
  ranks: Record<string, number | null>;
}
export interface TraceEvent {
  stage: string;
  latency_ms: number;
  input_tokens: number | null;
  output_tokens: number | null;
  model_calls: number;
  detail: Record<string, unknown>;
}
export interface Usage {
  input_tokens: number;
  output_tokens: number;
  model_calls: number;
  retries: number;
  latency_ms: number;
  query_attempts: string[];
}
export interface Aggregate {
  count: number;
  denominator: number;
  filters: Record<string, unknown>;
  caveat: string;
  sql: string;
  parameters: unknown[];
}
export interface AskResponse {
  status: Status;
  answer: string;
  citations: Evidence[];
  results: Hit[];
  trace: TraceEvent[];
  usage: Usage;
  aggregate: Aggregate | null;
  validation: {
    flagged: boolean;
    invalid_acns: string[];
    missing_citations: boolean;
  };
  index_id: number;
}
export interface Health {
  status: string;
  reports: number;
  chunks: number;
  index_id: number;
  categories: string[];
}
export interface Report {
  acn: string;
  synopsis: string | null;
  narrative: string | null;
  report_month: string | null;
  report_year: number | null;
  aircraft_category: string | null;
  flight_phase: string | null;
  anomaly_codes: string[] | null;
  source_dataset: string;
  source_revision: string | null;
  content_hash: string;
  index_id: number;
}
