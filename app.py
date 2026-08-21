"""
Multi-Agent Procurement Assistant — Streamlit deployment
Run with:  streamlit run app.py
"""
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))
load_dotenv()

from procurement_crew.pipeline import run_pipeline  # noqa: E402

st.set_page_config(
    page_title="Procurement Assistant · CrewAI",
    page_icon="🧭",
    layout="wide",
)

# ---------- styling ----------
st.markdown("""
<style>
.stApp { background: #f6f8fb; }
.hero { background: linear-gradient(135deg,#0b3d91 0%,#082a66 100%); color:#fff;
        border-radius:16px; padding:28px 32px; margin-bottom:8px; }
.hero h1 { margin:0 0 4px; font-size:26px; }
.hero p { margin:0; opacity:.85; font-size:14px; }
.agent-log { background:#0f172a; color:#a3f7bf; font-family: "SF Mono", Menlo, monospace;
             font-size:13px; border-radius:10px; padding:16px 18px; height:260px; overflow-y:auto; }
.metric-card { background:#fff; border:1px solid #e4e8ef; border-radius:12px; padding:16px 18px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🧭 Multi-Agent Procurement Assistant</h1>
  <p>4 CrewAI agents — Market Research → Data Extraction → Comparison & Ranking → Report Writer</p>
</div>
""", unsafe_allow_html=True)

# ---------- sidebar: company context editor ----------
with st.sidebar:
    st.header("⚙️ Configuration")

    demo_default = not bool(os.getenv("OPENAI_API_KEY"))
    demo_mode = st.toggle(
        "Demo mode (no API keys needed)",
        value=demo_default,
        help="Runs the exact same 4-stage pipeline on bundled realistic sample data — "
             "great for testing the deployment without paying for API calls.",
    )
    os.environ["DEMO_MODE"] = "true" if demo_mode else "false"

    if not demo_mode:
        st.text_input("OpenAI API key", type="password", key="openai_key",
                       value=os.getenv("OPENAI_API_KEY", ""))
        st.text_input("Tavily API key", type="password", key="tavily_key",
                       value=os.getenv("TAVILY_API_KEY", ""))
        if st.session_state.get("openai_key"):
            os.environ["OPENAI_API_KEY"] = st.session_state["openai_key"]
        if st.session_state.get("tavily_key"):
            os.environ["TAVILY_API_KEY"] = st.session_state["tavily_key"]
        st.caption("Keys are kept only in this session's memory, never written to disk.")

    st.divider()
    st.subheader("Company & Request")

    default_path = Path(__file__).parent / "company_context.json"
    ctx = json.loads(default_path.read_text())

    ctx["company_name"] = st.text_input("Company name", ctx["company_name"])
    req = ctx["procurement_request"]
    req["category"] = st.text_input("Product category", req["category"])
    req["quantity"] = st.number_input("Quantity", min_value=1, value=req["quantity"])
    req["budget_per_unit_usd"] = st.number_input(
        "Budget per unit (USD)", min_value=1, value=req["budget_per_unit_usd"])

    with st.expander("Required specs"):
        specs = req["required_specs"]
        specs["ram_gb_min"] = st.number_input("Min RAM (GB)", value=specs["ram_gb_min"])
        specs["storage_gb_min"] = st.number_input("Min storage (GB)", value=specs["storage_gb_min"])
        specs["battery_life_hours_min"] = st.number_input(
            "Min battery life (h)", value=specs["battery_life_hours_min"])

    with st.expander("Vendor policy"):
        pol = ctx["vendor_policy"]
        pol["min_seller_rating"] = st.slider("Min seller rating", 0.0, 5.0, float(pol["min_seller_rating"]), 0.1)
        pol["require_warranty_months"] = st.number_input(
            "Min warranty (months)", value=pol["require_warranty_months"])

    run_clicked = st.button("🚀 Run Procurement Crew", type="primary", use_container_width=True)

# ---------- main run area ----------
if "result" not in st.session_state:
    st.session_state.result = None

if run_clicked:
    log_lines = []
    col_log, col_status = st.columns([3, 1])
    with col_log:
        st.markdown("**Agent execution log**")
        log_box = st.empty()
    with col_status:
        st.markdown("**Status**")
        status_box = st.empty()

    def log(msg):
        log_lines.append(msg)
        log_box.markdown(f'<div class="agent-log">{"<br>".join(log_lines)}</div>', unsafe_allow_html=True)
        status_box.info("Running…")
        time.sleep(0.15)

    with st.spinner("Agents at work..."):
        try:
            result = run_pipeline(ctx, log=log)
            st.session_state.result = result
            status_box.success("Complete ✅")
        except Exception as e:
            status_box.error("Failed ❌")
            st.exception(e)

result = st.session_state.result
if result:
    scoring = result["scoring"]
    ranked = scoring["ranked"]
    disq = scoring["disqualified"]

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Products researched", len(ranked) + len(disq))
    m2.metric("Qualified", len(ranked))
    m3.metric("Disqualified", len(disq))
    m4.metric("Top value score", f"{ranked[0]['value_score']}/100" if ranked else "—")

    tab_report, tab_chart, tab_table, tab_raw = st.tabs(
        ["📄 Report", "📊 Comparison Chart", "🗂️ Raw Data", "🧠 Agent Output"]
    )

    with tab_report:
        st.components.v1.html(result["html"], height=900, scrolling=True)
        st.download_button(
            "⬇️ Download HTML report",
            data=result["html"],
            file_name="procurement_report.html",
            mime="text/html",
            use_container_width=True,
        )

    with tab_chart:
        if ranked:
            df = pd.DataFrame(ranked)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df["product_name"], y=df["value_score"],
                marker_color="#0b3d91", name="Value score",
                text=df["value_score"], textposition="outside",
            ))
            fig.add_trace(go.Scatter(
                x=df["product_name"], y=df["price_usd"],
                mode="lines+markers", name="Price (USD)", yaxis="y2",
                marker_color="#c9971f",
            ))
            fig.update_layout(
                yaxis=dict(title="Value score (0-100)"),
                yaxis2=dict(title="Price (USD)", overlaying="y", side="right"),
                legend=dict(orientation="h", y=1.1),
                margin=dict(t=20), height=420,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No qualifying products to chart.")

    with tab_table:
        if ranked:
            st.markdown("**Qualified products**")
            st.dataframe(pd.json_normalize(ranked), use_container_width=True)
        if disq:
            st.markdown("**Disqualified products**")
            st.dataframe(pd.json_normalize(disq), use_container_width=True)

    with tab_raw:
        st.json(result)

else:
    st.info("Set your procurement request in the sidebar and click **Run Procurement Crew** to start. "
            "Demo mode is on by default so you can try it instantly, with zero API keys.")
