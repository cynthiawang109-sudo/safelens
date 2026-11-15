"""Gradio client: all application data comes from FastAPI over HTTP."""

import os

import gradio as gr
import httpx


def request_api(method, path, body=None, *, base_url=None, transport=None):
    base_url = base_url or os.getenv("SAFELENS_API_URL", "http://127.0.0.1:8000")
    try:
        with httpx.Client(base_url=base_url, timeout=90, transport=transport) as client:
            response = client.request(method, path, json=body)
            if response.status_code == 502:
                detail = response.json().get("detail", {})
                if isinstance(detail, dict) and detail.get("code") == "credit_balance_exhausted":
                    raise gr.Error("Generation is unavailable because the OpenAI account has no remaining API credit.")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError:
        raise gr.Error("The SafeLens API could not complete this request. Check that it is running and its index is ready.") from None


def ask_http(question, category):
    data = request_api("POST", "/ask", {"question": question, "category": category or None})
    results = [[i, hit["acn"], hit["chunk_id"], hit["score"], hit["ranks"].get("lexical"), hit["ranks"].get("dense")]
               for i, hit in enumerate(data["results"], 1)]
    return data["answer"], data["citations"], results, data["validation"]


def report_http(acn):
    if not acn.strip().isdigit():
        raise gr.Error("Enter a numeric ACN.")
    return request_api("GET", f"/report/{acn.strip()}")


def build_ui():
    health = request_api("GET", "/health")
    with gr.Blocks(title="SafeLens Mini") as demo:
        gr.Markdown("# SafeLens Mini\nAsk about ASRS reporter accounts and read the cited passages. These accounts are not confirmed findings.")
        question = gr.Textbox(label="Question", lines=3)
        category = gr.Dropdown(choices=health["categories"], label="Category (optional)", value=None)
        submit = gr.Button("Ask")
        answer = gr.Markdown(label="Answer", sanitize_html=True)
        citations = gr.JSON(label="Citations and exact evidence passages")
        results = gr.Dataframe(headers=["Rank", "ACN", "Chunk", "RRF score", "Lexical rank", "Dense rank"],
                               interactive=False, label="Report-level results")
        validation = gr.JSON(label="Citation validation")
        submit.click(ask_http, inputs=[question, category], outputs=[answer, citations, results, validation], api_name="ask")
        acn = gr.Textbox(label="Open a source report by ACN")
        open_report = gr.Button("Read report")
        report = gr.JSON(label="Indexed source report and provenance")
        open_report.click(report_http, inputs=acn, outputs=report, api_name="report")
    return demo


def main():
    build_ui().launch(server_name="127.0.0.1", server_port=7860, share=False, inbrowser=False)


if __name__ == "__main__":
    main()
