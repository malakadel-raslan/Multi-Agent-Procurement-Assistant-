"""Single entrypoint used by both the CLI and the Streamlit app.

- DEMO_MODE=true (or no OPENAI_API_KEY): runs the exact same
  search -> scrape -> score -> report pipeline, but drives it directly in
  Python (no LLM calls) using the bundled demo data, so it always produces
  a real, fully-populated report.
- Otherwise: builds and kicks off the real CrewAI crew (agents reasoning +
  tool calls via an LLM), then still renders the final HTML deterministically
  from the analyst's structured output so numbers can't drift.
"""
import json
import os

from procurement_crew.demo_data import DEMO_SEARCH_RESULTS, DEMO_PRODUCT_RECORDS
from procurement_crew.report import render_report
from procurement_crew.tools.scoring_tool import score_products


def run_demo_pipeline(company_context: dict, log=lambda *_: None) -> dict:
    """Runs the full 4-stage pipeline directly, no LLM/network required."""
    log("🔎 Market Research Agent: searching for candidate products...")
    candidates = DEMO_SEARCH_RESULTS
    log(f"   found {len(candidates)} candidates across "
        f"{len({c['vendor'] for c in candidates})} vendors")

    log("🕸️ Data Extraction Agent: scraping each product page...")
    records = []
    for c in candidates:
        rec = DEMO_PRODUCT_RECORDS.get(c["url"], {})
        records.append({**c, **rec})
    log(f"   extracted structured data for {len(records)} products")

    log("📊 Procurement Analyst: scoring & ranking against company policy...")
    result = score_products(records, company_context)
    log(f"   {len(result['ranked'])} qualified, {len(result['disqualified'])} disqualified")

    log("📝 Report Writer: rendering final HTML report...")
    html = render_report(company_context, result)
    log("✅ Done.")

    return {"records": records, "scoring": result, "html": html}


def run_live_pipeline(company_context: dict, log=lambda *_: None) -> dict:
    """Runs the real CrewAI crew (requires OPENAI_API_KEY, ideally TAVILY_API_KEY)."""
    from procurement_crew.crew import ProcurementCrew

    log("🚀 Building crew (4 agents, sequential process)...")
    crew_wrapper = ProcurementCrew(company_context)
    crew = crew_wrapper.build()

    log("🔎 Running: research → extract → compare → write...")
    raw_result = crew.kickoff()

    # The analyst task output is the structured JSON we trust for the table;
    # the report_writer's prose/html is offered too, but we re-render the
    # numeric table deterministically so it can never disagree with the score.
    try:
        compare_output = crew_wrapper.t_compare.output.raw
        scoring_result = json.loads(compare_output)
    except Exception:
        scoring_result = {"ranked": [], "disqualified": []}

    if scoring_result.get("ranked"):
        html = render_report(company_context, scoring_result)
    else:
        html = str(raw_result)

    return {"records": None, "scoring": scoring_result, "html": html, "raw_crew_output": str(raw_result)}


def run_pipeline(company_context: dict, log=lambda *_: None) -> dict:
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    has_key = bool(os.getenv("OPENAI_API_KEY"))
    if demo_mode or not has_key:
        return run_demo_pipeline(company_context, log)
    return run_live_pipeline(company_context, log)
