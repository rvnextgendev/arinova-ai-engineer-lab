"""Streamlit UI calls the real local API, not simulated answers."""
import os
import requests
import streamlit as st

st.set_page_config(page_title="AriNova Debug Studio", layout="wide")
st.title("AriNova AI Architect Debug Studio")
st.warning("Local learning only: demo roles, synthetic PDFs, no production authentication.")
base = os.getenv("API_URL", "http://localhost:8000")
tenant = st.sidebar.text_input("Demo tenant", "acme")
actor = st.sidebar.selectbox("Demo role", ["admin", "reader", "reviewer"])
page = st.sidebar.radio("Module", ["Health", "PDF ingestion", "Embedding explorer", "Hybrid RAG", "AI playground", "Security", "Evaluation", "Workflow and reliability", "Audit and observability", "Human approval", "MCP and fine-tuning", "Chunking lab", "Prompt inspector", "LLM-as-a-Judge", "Live telemetry", "Cost and usage", "Architecture", "Circuit breaker"])
def call(method, path, **kwargs):
    try:
        r = requests.request(method, base + path, timeout=900, **kwargs)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as exc:
        st.error(str(exc))
        if exc.response is not None:
            st.code(exc.response.text)
        return None
def show(value):
    if value is not None:
        st.json(value)
def question(default="How many casual leaves are allowed?"):
    return {"question": st.text_area("Input", default), "tenant": tenant, "actor": actor}
if page == "Health":
    show(call("GET", "/health"))
elif page == "PDF ingestion":
    f = st.file_uploader("Upload a synthetic PDF", type=["pdf"])
    if f and st.button("Extract, chunk, embed and store"):
        show(call("POST", "/ingest", files={"file": (f.name, f.getvalue(), "application/pdf")}, data={"tenant": tenant, "actor": actor}))
    if st.button("Inspect stored chunks"):
        show(call("GET", "/inspect/chunks", params={"tenant": tenant}))
elif page in ["Embedding explorer", "Hybrid RAG", "AI playground", "Security", "Evaluation"]:
    q = question()
    endpoint = {"Embedding explorer": "/embedding", "Hybrid RAG": "/retrieve", "AI playground": "/ask", "Security": "/security", "Evaluation": "/evaluate"}[page]
    if page == "AI playground":
        q["request_id"] = st.text_input("Optional request ID for idempotency") or None
    if st.button("Execute real backend"):
        result = call("POST", endpoint, json=q)
        show(result)
        if page == "AI playground" and result:
            st.session_state["last_answer"] = result.get("answer", "")
    if page == "AI playground" and st.session_state.get("last_answer"):
        rating = st.slider("Feedback rating", 1, 5, 5)
        if st.button("Save feedback"):
            show(call("POST", "/feedback", json={**q, "answer": st.session_state["last_answer"], "rating": rating}))
elif page in ["Workflow and reliability", "Human approval"]:
    st.caption("Inspect persisted workflow state; approval is a separate lab, not a mandatory answer gate.")
    table = st.selectbox("Inspect", ["workflows", "dlq"])
    if st.button("Refresh"):
        show(call("GET", "/inspect/" + table, params={"tenant": tenant}))
    action = st.selectbox("Action", ["cancel", "replay"] if page == "Workflow and reliability" else ["request_approval", "approve"])
    item = st.text_input("Workflow or DLQ ID")
    if item and st.button("Execute action"):
        show(call("POST", "/workflow/" + action + "/" + item, params={"tenant": tenant}))
elif page == "Audit and observability":
    st.caption("Structured audit records; use docker compose logs -f api for runtime logs.")
    show(call("GET", "/inspect/audit", params={"tenant": tenant}))
elif page == "Chunking lab":
    text = st.text_area("Text", "Employees receive 12 casual leaves per year.")
    size = st.slider("Chunk size",50,2000,200)
    overlap = st.slider("Overlap",0,size-1,min(30,size-1))
    if st.button("Chunk"): show(call("POST","/chunk",json={"text":text,"size":size,"overlap":overlap}))
elif page == "Prompt inspector":
    q = question()
    if st.button("Inspect actual prompt"): show(call("POST","/prompt",json=q))
elif page == "LLM-as-a-Judge":
    q = question()
    evidence = st.text_area("Evidence","Employees receive 12 casual leaves per year.")
    answer = st.text_area("Candidate answer","Employees receive 12 casual leaves.")
    if st.button("Run real Ollama judge"):
        show(call("POST","/judge",json={**q,"evidence":evidence,"answer":answer}))
    st.caption("Advisory grounding score, not proof of correctness.")
elif page in ["Live telemetry","Cost and usage"]:
    st.caption("Actual recent API requests; in-memory history resets on restart. Local demo data is shared across demo roles.")
    rows = call("GET","/telemetry") or []
    usage = [e for r in rows for e in r["events"] if e["name"]=="ollama_usage"]
    if page == "Cost and usage":
        st.metric("Observed input tokens",sum(e.get("input_tokens") or 0 for e in usage))
        st.metric("Observed output tokens",sum(e.get("output_tokens") or 0 for e in usage))
        st.caption("Missing token counts are not measured. No paid API charges for local Ollama; electricity excluded.")
        show(usage)
    else:
        if rows:
            st.metric("Recent requests",len(rows))
            st.metric("Mean latency (ms)",round(sum(r["milliseconds"] for r in rows)/len(rows),2))
            st.line_chart([r["milliseconds"] for r in rows])
            chosen = st.selectbox("Trace",list(reversed(rows)),format_func=lambda r:r["trace_id"]+" "+r["route"])
            show(chosen)
        st.markdown("[Prometheus](http://localhost:9090) | [Grafana](http://localhost:3000)")
    if st.button("Refresh"): st.rerun()
elif page == "Architecture":
    st.graphviz_chart("digraph { UI -> API; API -> LangGraph; LangGraph -> Retrieve; Retrieve -> Validate; Validate -> Generate; Generate -> Evaluate; Retrieve -> pgvector; Generate -> Ollama; Evaluate -> Ollama; API -> Prometheus }")
    st.caption("Local architecture; optional judge uses the same configured model.")
elif page == "Circuit breaker":
    show(call("GET","/circuit"))
    st.caption("Actual process-local breaker. Stop Ollama and ask a question with retrieved evidence to observe failures.")
else:
    if st.button("Discover configured MCP tools"): show(call("GET","/mcp/tools"))
    if st.button("Export training candidates"): show(call("GET","/training/candidates",params={"tenant":tenant}))
    st.info("MCP and LoRA are separate optional CLI learning examples. No arbitrary command execution is exposed by this UI.")
    st.code("python learning/arinova_architect_master_annotated.py --help")
