import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
os.environ["DEMO_MODE"] = "true"

from procurement_crew.pipeline import run_demo_pipeline
from procurement_crew.tools.scoring_tool import score_products

ROOT = Path(__file__).parents[1]


def load_context():
    return json.loads((ROOT / "company_context.json").read_text())


def test_full_demo_pipeline_runs_end_to_end():
    ctx = load_context()
    result = run_demo_pipeline(ctx)
    assert result["html"].startswith("\n<!DOCTYPE html>") or "<!DOCTYPE html>" in result["html"]
    assert len(result["records"]) == 8
    assert len(result["scoring"]["ranked"]) + len(result["scoring"]["disqualified"]) == 8


def test_over_budget_products_are_disqualified():
    ctx = load_context()
    result = run_demo_pipeline(ctx)
    disq_names = {d["product_name"] for d in result["scoring"]["disqualified"]}
    assert "Lenovo ThinkPad T14 Gen 5" in disq_names  # $1299 > $1200 budget
    assert "Microsoft Surface Laptop 6" in disq_names  # $1399 > $1200 budget


def test_ranking_is_sorted_descending():
    ctx = load_context()
    result = run_demo_pipeline(ctx)
    scores = [p["value_score"] for p in result["scoring"]["ranked"]]
    assert scores == sorted(scores, reverse=True)


def test_low_ram_products_disqualified():
    ctx = load_context()
    result = run_demo_pipeline(ctx)
    disq_reasons = " ".join(d["reason"] for d in result["scoring"]["disqualified"])
    assert "RAM below minimum" in disq_reasons


def test_scoring_handles_missing_price_gracefully():
    ctx = load_context()
    products = [{"product_name": "No Price Item", "vendor": "x", "price_usd": None, "specs": {}}]
    result = score_products(products, ctx)
    assert result["ranked"] == []
    assert result["disqualified"][0]["reason"] == "No price data available"


def test_report_html_contains_top_pick_and_table():
    ctx = load_context()
    result = run_demo_pipeline(ctx)
    top_name = result["scoring"]["ranked"][0]["product_name"]
    assert top_name in result["html"]
    assert "<table>" in result["html"]
    assert "Excluded From Consideration" in result["html"]


def test_relaxed_budget_changes_ranking():
    ctx = load_context()
    ctx["procurement_request"]["budget_per_unit_usd"] = 5000
    result = run_demo_pipeline(ctx)
    # with a huge budget nothing should be disqualified for price
    price_disq = [d for d in result["scoring"]["disqualified"] if "budget" in d["reason"].lower()]
    assert price_disq == []


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
