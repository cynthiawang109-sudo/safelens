"""Step 7B Phase 1: observe unchanged Ask behavior and diagnose original traces."""

import hashlib
import inspect
import json
from datetime import UTC, datetime
from pathlib import Path

import psycopg
from fastapi.testclient import TestClient
from run_eval import file_hash, load_queries

from safelens.app import create_app, indexed_connection
from safelens.config import Settings
from safelens.evaluation import load_qrels
from safelens.generate import select_evidence, validate_citations
from safelens.llm import OpenAILLMProvider
from safelens.retrieve import search_hybrid

SOURCES = ["src/safelens/generate.py", "src/safelens/agent.py", "src/safelens/llm.py", "src/safelens/app.py"]


class RecordingProvider(OpenAILLMProvider):
    """Observation only: preserve requests/results, save pre-validation output locally."""
    def __init__(self, settings):
        super().__init__(settings)
        self.records = []

    def generate_with_usage(self, prompt):
        value, usage = super().generate_with_usage(prompt)
        self.records.append({"schema": None, "prompt": prompt, "output": value, "usage": usage})
        return value, usage

    def generate_structured(self, prompt, schema):
        value, usage = super().generate_structured(prompt, schema)
        self.records.append({"schema": schema.__name__, "prompt": prompt, "output": value.model_dump(), "usage": usage})
        return value, usage


def known_counts(qid, acns, qrels):
    acns = list(dict.fromkeys(acns))
    grades = [qrels[(qid, a)] for a in acns if (qid, a) in qrels]
    return {"returned": len(acns), "judged": len(grades), "relevant": sum(g >= 1 for g in grades),
            "direct": sum(g == 2 for g in grades), "coverage": len(grades)/len(acns) if acns else 0}


def diagnose(q, response, calls, qrels, step7, initial, synopses):
    qid = q["id"]
    production_source = "eval/experiment_step7b_diagnosis.json"
    base = f"/production_before/{qid}"
    traces = response["trace"]
    retrievals = [(i, e) for i, e in enumerate(traces) if e["stage"] == "retrieve"]
    grades = [(i, e) for i, e in enumerate(traces) if e["stage"] == "grade"]
    first = retrievals[0][1]["detail"]["top10_acns"]
    last = retrievals[-1][1]["detail"]["top10_acns"]
    counts_first, counts_last = known_counts(qid, first, qrels), known_counts(qid, last, qrels)
    flags, evidence = [], []
    for i, event in grades:
        preceding = next(e for j,e in reversed(retrievals) if j < i)
        positive = known_counts(qid, preceding["detail"]["top10_acns"], qrels)["relevant"]
        grade = event["detail"]["output"]
        if grade["sufficiency"] == "insufficient" and positive:
            flags.append("a")
            evidence.append({"source": production_source, "pointer": f"{base}/trace/{i}/detail/output",
                             "observation": f"{positive} known relevant top-ten reports, grader insufficient", "reason": grade["reason"]})
    generated = [c for c in calls if c["schema"] is None]
    if generated and response["status"] == "insufficient_evidence" and grades:
        grade = grades[-1][1]["detail"]["output"]
        flags.append("b" if grade["sufficiency"] == "sufficient" else "generator_after_partial")
        evidence.append({"source": production_source, "pointer": f"{base}/trace/{grades[-1][0]}/detail/output",
                         "observation": f"Grader {grade['sufficiency']}; generation executed but refused", "reason": generated[-1]["output"][:650]})
    if response["validation"]["flagged"]:
        flags.append("e_flag")
        evidence.append({"source": production_source, "pointer": f"{base}/validation", "observation": response["validation"]})
    if len(retrievals) > 1 and counts_last["relevant"] < counts_first["relevant"]:
        flags.append("d_signal")
        evidence.append({"source": production_source, "pointer": f"{base}/trace/{retrievals[-1][0]}/detail/top10_acns",
                         "first_attempt_pointer": f"{base}/trace/{retrievals[0][0]}/detail/top10_acns",
                         "observation": f"Known-positive count {counts_first['relevant']} -> {counts_last['relevant']}; coverage {counts_first['coverage']:.0%} -> {counts_last['coverage']:.0%}; unknowns not misses"})
    package_audits = []
    for i, call in enumerate(calls):
        if call["schema"] == "QueryRewrite":
            continue
        marker = "REQUEST_AND_EVIDENCE_JSON:\n" if call["schema"] is None else "\nReporter accounts are unverified, not confirmed findings.\n"
        data = json.loads(call["prompt"].split(marker,1)[1])
        acns = sorted({p["acn"] for p in data["passages"]})
        preserved = all(synopses[p["acn"]] in p["passage"] for p in data["passages"])
        package_audits.append({"call_index": i, "schema": call["schema"], "acns": acns,
                               "known": known_counts(qid, acns, qrels), "synopsis_preserved": preserved,
                               "chunk_ids": [p["chunk_id"] for p in data["passages"]]})
    historical = []
    for config, values in step7["per_question"].items():
        item = values[qid]
        events = item["trace"]
        historical.append({"configuration": config, "status": item["status"],
                           "validation": item["validation"], "answer": item["answer"],
                           "grade_decisions": [{"trace_index": i, "output": e["detail"]["output"]} for i,e in enumerate(events) if e["stage"] == "grade"],
                           "generator_executed": any(e["stage"] == "generate" for e in events)})
        grade_events = [(i,e) for i,e in enumerate(events) if e["stage"] == "grade"]
        if item["status"] == "insufficient_evidence" and grade_events and grade_events[-1][1]["detail"]["output"]["sufficiency"] == "sufficient":
            flags.append("b")
            evidence.append({"source": "eval/experiment_step7_ablation.json", "pointer": f"/per_question/{config}/{qid}/trace/{grade_events[-1][0]}/detail/output",
                             "observation": "Grader sufficient but generator refused", "reason": item["answer"][:450]})
    if q["layer"] == "control":
        flags = ["correct_control_refusal"] if response["status"] == "insufficient_evidence" else ["control_failure"]
        evidence.append({"source": production_source, "pointer": f"{base}/status",
                         "observation": f"Control status {response['status']}; validation={response['validation']}"})
    elif response["status"] in ("answered", "partial"):
        flags.append("already_supported_response")
    return {"query_id": qid, "query": q["query"], "layer": q["layer"], "production_status": response["status"],
            "classifications": sorted(set(flags)), "trace_evidence": evidence, "known_first_top10": counts_first,
            "known_final_top10": counts_last, "packaging": package_audits,
            "packaging_conclusion": "Selected report synopses are already present; qrel-relevant selected passages exist. A dropped mechanism is not established by labels alone.",
            "citation_validation_flagged": response["validation"]["flagged"], "historical": historical,
            "initial_hybrid_selected": known_counts(qid, [e["acn"] for e in select_evidence(initial[qid]["hybrid"])], qrels)}


def render_phase1(record):
    lines = ["# Step 7B — answer-rate calibration", "", "## Phase 1: diagnosis before behavior changes", "",
             ("Observed the eleven existing requests through the unchanged production HTTP Ask path (real provider), and audited the original "
             "Step 7 ablation. The production baseline, raw provider outputs before citation validation, and actual packaged passages are stored "
             "locally; the versioned diagnosis includes trace pointers and short explanations. No production behavior changed during this phase."), "",
             ("Codes: (a) grader insufficient despite known qrel-relevant retrieval; (b) grader sufficient, generator refused; "
             "generator_after_partial = grader allowed partial evidence but generator refused; (d_signal) fewer known positives after rewrite, "
             "with coverage reported rather than counting unknowns as irrelevant. (c) requires evidence of a mechanism dropped, not just a relevant "
             "label on an excluded report. (e) means validation stripped an answer; flags alone would not prove the removed answer was grounded."), "",
             "| Query | Production status | Diagnosis | Known relevant top ten, first → final (judged coverage) | Trace evidence |",
             "|---|---|---|---|---|"]
    for row in record["diagnosis"]:
        first,last=row["known_first_top10"],row["known_final_top10"]
        refs = "; ".join(f"`{e['source']}{e['pointer']}`: {str(e['observation']).replace('|','/')}" for e in row["trace_evidence"][:3]) or "Correct refusal; see saved per-query production trace."
        lines.append(f"| {row['query_id']} | {row['production_status']} | {', '.join(row['classifications']) or 'generator/answerability bar; see original no-grader refusal'} | {first['relevant']} → {last['relevant']} ({first['coverage']:.0%} → {last['coverage']:.0%}) | {refs} |")
    lines += ["", "### Mechanism-level findings", "",
              "- The original no-grader Dense-only and Hybrid-10:1 runs refused all eight normal queries, so grading/rewrite cannot be the sole cause. Their answers often describe relevant accounts but demand an exact conjunction or proven cause before answering.",
              "- The generator explicitly requires all requested conditions in one account and says to begin with insufficient evidence otherwise. The grader similarly requires ALL conditions. This conflates useful mechanism-level reporter evidence with complete proof of a premise.",
              "- The current status classifier also treats the phrase 'insufficient evidence' anywhere in a qualified answer as full refusal. An explicit outcome must distinguish a grounded partial answer from no supporting answer.",
              "- All inspected selected passages retain their source synopsis, and relevant accounts already reach the selected evidence. Packaging exclusion may hide additional details, but no diagnosed dropped mechanism justifies changing the caps or packaging in this calibration.",
              "- Citation validation flags and raw pre-validation outputs are checked separately; validation is not to be relaxed. Qrels indicate report relevance, not proof that every sentence in a passage supports every premise.", "",
              "Phase 2 will change only the implicated generation outcome/prompt and grader sufficiency definitions, preserving exact citation validation, packaging/caps, retrieval, and all frozen evaluation assets. One calibration batch will then be measured against the pre-registered criteria; no iterative loosening.", ""]
    return "\n".join(lines)


def main():
    design=json.loads(Path("eval/step7b_design.json").read_text(encoding="utf-8"))
    frozen={p:file_hash(p) for p in design["frozen"]}
    sources={p:file_hash(p) for p in SOURCES}
    settings=Settings.from_env()
    queries=[q for q in load_queries(Path("eval/queries.jsonl")) if q["layer"] in (2,"control")]
    qrels=load_qrels("eval/qrels.jsonl",{q["id"] for q in queries if q["layer"]==2})
    checkpoint=Path("data/step7b_before_production.json")
    saved=json.loads(checkpoint.read_text(encoding="utf-8")) if checkpoint.exists() else {"sources":sources,"responses":{},"calls":{}}
    if saved["sources"]!=sources:
        raise ValueError("Diagnosis baseline source mismatch; preserve the original snapshot")
    with TestClient(create_app(settings,llm_factory=RecordingProvider)) as client:
        with indexed_connection(settings) as conn:
            search_hybrid("aviation safety",10,conn=conn,settings=settings,provider=client.app.state.embedding)
        for q in queries:
            if q["id"] not in saved["responses"]:
                llm=client.app.state.llm
                start=len(llm.records)
                response=client.post("/ask",json={"question":q["query"]})
                response.raise_for_status()
                saved["responses"][q["id"]]=response.json()
                saved["calls"][q["id"]]=llm.records[start:]
                checkpoint.write_text(json.dumps(saved,indent=2),encoding="utf-8")
            r=saved["responses"][q["id"]]
            print(json.dumps({"phase":"unchanged_baseline","query_id":q["id"],"status":r["status"],"retries":r["usage"]["retries"]}),flush=True)
    with psycopg.connect(settings.database_url,autocommit=True) as conn:
        synopses=dict(conn.execute("SELECT acn,synopsis FROM reports").fetchall())
    step7=json.loads(Path("eval/experiment_step7_ablation.json").read_text(encoding="utf-8"))
    initial=json.loads(Path("data/eval_rankings_step7.json").read_text(encoding="utf-8"))
    diagnosis=[diagnose(q,saved["responses"][q["id"]],saved["calls"][q["id"]],qrels,step7,initial,synopses) for q in queries]
    assert sources=={p:file_hash(p) for p in SOURCES}
    assert frozen=={p:file_hash(p) for p in frozen}
    record={"timestamp":datetime.now(UTC).isoformat(),"phase":"diagnosis_before_changes","split":"development",
            "design":design,"frozen_hashes":frozen,"source_hashes_before_calibration":sources,
            "step7_record_sha256":file_hash("eval/experiment_step7_ablation.json"),"local_baseline":str(checkpoint),
            "local_baseline_sha256":file_hash(checkpoint),"diagnosis":diagnosis,
            "protected_function_hashes": {fn.__name__:hashlib.sha256(inspect.getsource(fn).encode("utf-8")).hexdigest()
                                          for fn in (select_evidence, validate_citations)},
            "all_selected_synopses_preserved": all(p["synopsis_preserved"] for row in diagnosis for p in row["packaging"]),
            "fresh_validation_flags": sum(v["validation"]["flagged"] for v in saved["responses"].values()),
            "historical_validation_flags": sum(v["validation"]["flagged"] for values in step7["per_question"].values() for v in values.values()),
            "production_before":{qid:{k:r[k] for k in ("status","answer","validation","trace","usage")} for qid,r in saved["responses"].items()}}
    Path("eval/experiment_step7b_diagnosis.json").write_text(json.dumps(record,indent=2),encoding="utf-8")
    Path("docs/STEP7B_NOTES.md").write_text(render_phase1(record),encoding="utf-8")
    print("Diagnosis recorded; production source hashes unchanged.",flush=True)


if __name__=="__main__":
    main()
