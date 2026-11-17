"""Step 7B Phase 3: one calibrated batch on production HTTP, dense and hybrid."""

import hashlib
import inspect
import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

from fastapi.testclient import TestClient
from run_eval import file_hash, load_queries

from safelens.agent import AgentEngine, AgentOptions
from safelens.app import create_app, indexed_connection
from safelens.config import Settings
from safelens.evaluation import load_qrels
from safelens.generate import select_evidence, validate_citations
from safelens.retrieve import search_hybrid


def citation_stats(qid, response, qrels):
    acns = sorted({c["acn"] for c in response["citations"]})
    judged = [(a, qrels[(qid, a)]) for a in acns if (qid, a) in qrels]
    relevant = sum(g >= 1 for _, g in judged)
    return {"acns": acns, "cited_reports": len(acns), "judged": len(judged), "relevant": relevant,
            "grade_zero_acns": [a for a,g in judged if g == 0], "unknown_acns": [a for a in acns if (qid,a) not in qrels],
            "precision_on_judged": relevant/len(judged) if judged else None,
            "judged_coverage": len(judged)/len(acns) if acns else None}


def supported(response):
    return (response["status"] in ("answered", "partial") and bool(response["citations"])
            and not response["validation"]["flagged"] and not response["validation"]["invalid_acns"])


def summary(queries, responses, qrels):
    normal = [q for q in queries if q["layer"] == 2]
    supported_responses = [citation_stats(q["id"], responses[q["id"]], qrels) for q in normal if supported(responses[q["id"]])]
    judged = sum(r["judged"] for r in supported_responses)
    cited = sum(r["cited_reports"] for r in supported_responses)
    controls = [q for q in queries if q["layer"] == "control"]
    return {"supported_normal_responses": len(supported_responses),
            "normal_statuses": {s: sum(responses[q["id"]]["status"] == s for q in normal)
                                for s in ("answered", "partial", "insufficient_evidence")},
            "controls_passed": sum(responses[q["id"]]["status"] == "insufficient_evidence"
                                   and not responses[q["id"]]["validation"]["invalid_acns"] for q in controls),
            "invented_citations": sum(len(r["validation"]["invalid_acns"]) for r in responses.values()),
            "grade_zero_citations": sum(len(r["grade_zero_acns"]) for r in supported_responses),
            "citation_precision_on_judged": sum(r["relevant"] for r in supported_responses)/judged if judged else None,
            "citation_judged_coverage": judged/cited if cited else None,
            "cited_report_pairs": cited, "judged_report_pairs": judged,
            "mean_input_tokens": mean(r["usage"]["input_tokens"] for r in responses.values()),
            "mean_output_tokens": mean(r["usage"]["output_tokens"] for r in responses.values()),
            "mean_latency_ms": mean(r["usage"]["latency_ms"] for r in responses.values()),
            "mean_model_calls": mean(r["usage"]["model_calls"] for r in responses.values()),
            "mean_retries": mean(r["usage"]["retries"] for r in responses.values())}


def render_results(record):
    lines = ["<!-- answer-calibration-step7b -->", "## Step 7B — answer-rate calibration (development)", "",
             ("Phase 1 diagnosed the generator's all-conditions requirement and the grader's complete-coverage requirement, "
             "not retrieval or citation validation. Fresh unchanged production responses and all five original Step 7 configurations "
             "were audited. Selected passages already contained each selected report's synopsis; packaging was not changed. "
             "See `docs/STEP7B_NOTES.md` for per-query trace references."), "",
             "### One implicated calibration batch", "",
             ("Generation now uses explicit structured `answered` / `partial` / `insufficient_evidence` outcomes: report a "
             "supported mechanism with qualifications instead of requiring every condition or independently proven causality. "
             "Grader sufficiency means at least one relevant account addressing the mechanism, not all reports or all topic details. "
             "A partial status is read from the structured outcome rather than the occurrence of 'insufficient evidence' anywhere "
             "in a qualified answer. Unavailable precise dates/times, absent named identifiers, and out-of-domain questions still refuse."), "",
             ("Citation validation and evidence packaging functions are unchanged by hash. Reporter-account framing, passage-only "
             "claims, caps, query set, qrels, corpus, weights, and retrieval code remain fixed. There are no query-ID rules or "
             "qrel-based production filters. Qrels are used only after generation for evaluation; the 82 additions remain unjudged."), "",
             "### Before/after summary", "",
             ("Production before = fresh unchanged HTTP Ask run; Dense-only and Hybrid-10:1 before = original Step 7 real-provider "
             "ablation with matching old generation/grader hashes. After uses the same eleven requests; production is through HTTP. "
             "All costs are actual provider tokens and request latency, mean over eleven requests, excluding warmup. Historical "
             "baseline latency versus current latency is descriptive, not a controlled provider-speed benchmark."), "",
             "| Configuration | Supported normal / 8, before → after | Controls / 3, before → after | Citation precision on judged (coverage), after | Grade-0 supports |",
             "|---|---:|---:|---:|---:|"]
    def metric(v):
        return "N/A" if v is None else f"{v:.1%}"
    for name, values in record["summaries"].items():
        b,a=values["before"],values["after"]
        lines.append(f"| {name} | {b['supported_normal_responses']} → {a['supported_normal_responses']} | {b['controls_passed']} → {a['controls_passed']} | {metric(a['citation_precision_on_judged'])} ({metric(a['citation_judged_coverage'])}) | {a['grade_zero_citations']} |")
    lines += ["", ("Unique cited reports count once per response. Precision = existing qrel grade ≥1 / judged cited reports. "
              "Coverage = judged / all cited reports. Unknown pairs are listed separately, never scored as irrelevant or assigned "
              "grades. These report-level qrels do not independently prove every generated claim. Precision before and all per-query "
              "counts are in the experiment record."), "",
              "### Cost deltas", "",
              "| Configuration | Mean input tokens, before → after (delta) | Mean output tokens, before → after (delta) | Mean latency seconds, before → after (delta) | Mean retries, before → after |",
              "|---|---:|---:|---:|---:|"]
    for name, values in record["summaries"].items():
        b,a=values["before"],values["after"]
        lines.append(f"| {name} | {b['mean_input_tokens']:.1f} → {a['mean_input_tokens']:.1f} ({a['mean_input_tokens']-b['mean_input_tokens']:+.1f}) | {b['mean_output_tokens']:.1f} → {a['mean_output_tokens']:.1f} ({a['mean_output_tokens']-b['mean_output_tokens']:+.1f}) | {b['mean_latency_ms']/1000:.2f} → {a['mean_latency_ms']/1000:.2f} ({(a['mean_latency_ms']-b['mean_latency_ms'])/1000:+.2f}) | {b['mean_retries']:.2f} → {a['mean_retries']:.2f} |")
    lines += ["", "### Per-query status, citation precision and cost", "",
              "| Configuration | Query | Before → after | Judged-relevant / judged cited; unknown | Input tokens before → after | Output tokens before → after | Latency seconds before → after (delta) |",
              "|---|---|---|---|---:|---:|---:|"]
    for name, rows in record["per_query"].items():
        for qid,row in rows.items():
            b,a=row["before"],row["after"]
            cs=row["citation_after"]
            signal=f"{cs['relevant']}/{cs['judged']}; {len(cs['unknown_acns'])} unknown" if row["layer"]==2 and a["status"] in ("answered","partial") else "N/A (refusal/control)"
            lines.append(f"| {name} | {qid} | {b['status']} → {a['status']} | {signal} | {b['usage']['input_tokens']} → {a['usage']['input_tokens']} | {b['usage']['output_tokens']} → {a['usage']['output_tokens']} | {b['usage']['latency_ms']/1000:.2f} → {a['usage']['latency_ms']/1000:.2f} ({(a['usage']['latency_ms']-b['usage']['latency_ms'])/1000:+.2f}) |")
    success=record["success"]
    lines += ["", "### Pre-registered outcome and stopping rule", "",
              (f"**Success criteria met: {success['passed']}.** Production supported answers: {success['production_supported']}/8 "
              "(required ≥6); every measured configuration controls 3/3 with zero invented citations: "
              f"{success['controls_all_passed']}; no answered/partial response cites a known grade-0 support: {success['no_grade_zero_support']}."), "",
              "One calibration batch was tested. " + ("No further loosening was attempted." if success["passed"] else "The criteria failed; calibration stopped without further loosening. See failure details in the experiment record."), "",
              ("Full record: `eval/experiment_step7b.json`. Diagnosis: `eval/experiment_step7b_diagnosis.json`. "
              "Raw prompts, pre-validation outputs, and passage-bearing responses stay in ignored `data/`. "
              "Run `uv run python eval/diagnose_answer_rate.py` on the original pre-calibration source to capture diagnosis; "
              "run `uv run python eval/remeasure_answer_rate.py` for the registered calibrated source (matching checkpoints reused). "
              "No final-test queries or Step 8 work."), ""]
    return "\n".join(lines)


def main():
    diagnosis=json.loads(Path("eval/experiment_step7b_diagnosis.json").read_text(encoding="utf-8"))
    design=json.loads(Path("eval/step7b_design.json").read_text(encoding="utf-8"))
    frozen=diagnosis["frozen_hashes"]
    if frozen!={p:file_hash(p) for p in frozen}:
        raise ValueError("Frozen evaluation/retrieval assets changed")
    for fn in (select_evidence,validate_citations):
        if hashlib.sha256(inspect.getsource(fn).encode()).hexdigest()!=diagnosis["protected_function_hashes"][fn.__name__]:
            raise ValueError("Citation validation or evidence packaging changed")
    sources={p:file_hash(p) for p in diagnosis["source_hashes_before_calibration"]}
    attempt={"batch":1,"sources":sources,"design_sha256":file_hash("eval/step7b_design.json")}
    register=Path("eval/step7b_calibration_batch.json")
    if register.exists() and json.loads(register.read_text(encoding="utf-8"))!=attempt:
        raise ValueError("One calibration batch is already registered; no further tuning is allowed")
    register.write_text(json.dumps(attempt,indent=2),encoding="utf-8")
    queries=[q for q in load_queries(Path("eval/queries.jsonl")) if q["layer"] in (2,"control")]
    qrels=load_qrels("eval/qrels.jsonl",{q["id"] for q in queries if q["layer"]==2})
    before_prod=json.loads(Path(diagnosis["local_baseline"]).read_text(encoding="utf-8"))["responses"]
    step7=json.loads(Path("eval/experiment_step7_ablation.json").read_text(encoding="utf-8"))
    for path in ("src/safelens/generate.py","src/safelens/agent.py"):
        assert step7["source_hashes"][path]==diagnosis["source_hashes_before_calibration"][path]
    before_old=json.loads(Path(step7["local_checkpoint"]).read_text(encoding="utf-8"))
    before={"Production Ask":before_prod,"Dense-only":before_old["Dense-only"],"Hybrid-10:1":before_old["Hybrid-10:1"]}
    fingerprint=hashlib.sha256(json.dumps(attempt,sort_keys=True).encode()).hexdigest()
    checkpoint=Path(f"data/step7b_after_{fingerprint[:16]}.json")
    after=json.loads(checkpoint.read_text(encoding="utf-8")) if checkpoint.exists() else {}
    settings=Settings.from_env()
    with TestClient(create_app(settings)) as client:
        with indexed_connection(settings) as conn:
            search_hybrid("aviation safety",10,conn=conn,settings=settings,provider=client.app.state.embedding)
        for name in design["configurations"]:
            after.setdefault(name,{})
            for q in queries:
                if q["id"] not in after[name]:
                    if name=="Production Ask":
                        response=client.post("/ask",json={"question":q["query"]})
                        response.raise_for_status()
                        result=response.json()
                    else:
                        options=AgentOptions(dense_only=name=="Dense-only",rerank=False,rewrite=False,grading=False)
                        with indexed_connection(settings) as conn:
                            result=AgentEngine(conn,settings,client.app.state.embedding,client.app.state.llm,options=options).run(q["query"])
                    after[name][q["id"]]=result
                    checkpoint.write_text(json.dumps(after,indent=2),encoding="utf-8")
                result=after[name][q["id"]]
                print(json.dumps({"configuration":name,"query_id":q["id"],"status":result["status"],
                                  "citation_acns":sorted({c['acn'] for c in result['citations']}),
                                  "retries":result["usage"]["retries"]}),flush=True)
    summaries={name:{"before":summary(queries,before[name],qrels),"after":summary(queries,after[name],qrels)} for name in after}
    success={"production_supported":summaries["Production Ask"]["after"]["supported_normal_responses"],
             "controls_all_passed":all(v["after"]["controls_passed"]==3 and v["after"]["invented_citations"]==0 for v in summaries.values()),
             "no_grade_zero_support":all(v["after"]["grade_zero_citations"]==0 for v in summaries.values())}
    success["passed"]=success["production_supported"]>=6 and success["controls_all_passed"] and success["no_grade_zero_support"]
    per_query={name:{q["id"]:{"layer":q["layer"],
                            "before":{k:before[name][q["id"]][k] for k in ("status","answer","usage","validation","trace")},
                            "after":{k:after[name][q["id"]][k] for k in ("status","answer","usage","validation","trace")},
                            "citation_before":citation_stats(q["id"],before[name][q["id"]],qrels),
                            "citation_after":citation_stats(q["id"],after[name][q["id"]],qrels)} for q in queries} for name in after}
    assert frozen=={p:file_hash(p) for p in frozen}
    record={"timestamp":datetime.now(UTC).isoformat(),"split":"development","design":design,"batch":attempt,
            "diagnosis_sha256":file_hash("eval/experiment_step7b_diagnosis.json"),"frozen_hashes":frozen,
            "protected_function_hashes":diagnosis["protected_function_hashes"],"local_after_checkpoint":str(checkpoint),
            "summaries":summaries,"success":success,"per_query":per_query}
    Path("eval/experiment_step7b.json").write_text(json.dumps(record,indent=2),encoding="utf-8")
    from diagnose_answer_rate import render_phase1
    notes=render_phase1(diagnosis)+"\n"+render_results(record)
    Path("docs/STEP7B_NOTES.md").write_text(notes,encoding="utf-8")
    results=Path("eval/results.md")
    previous=results.read_text(encoding="utf-8").split("<!-- answer-calibration-step7b -->")[0]
    results.write_text(previous.rstrip()+"\n\n"+render_results(record),encoding="utf-8")
    print(json.dumps({"success":success,"summaries":summaries},indent=2))


if __name__=="__main__":
    main()
