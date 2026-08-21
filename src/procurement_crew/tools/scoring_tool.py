"""Deterministic comparison/ranking engine.

Exposed both as a plain Python function (used directly by tests and by the
Streamlit app) and as a CrewAI tool (used by the procurement_analyst agent)
so ranking math is never left to the LLM to eyeball.
"""
import json

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


def score_products(products: list[dict], company_context: dict) -> dict:
    req = company_context["procurement_request"]
    specs_req = req["required_specs"]
    policy = company_context["vendor_policy"]
    weights = company_context["evaluation_weights"]
    budget = req["budget_per_unit_usd"]

    ranked, disqualified = [], []

    prices = [p["price_usd"] for p in products if p.get("price_usd")]
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 1

    for p in products:
        specs = p.get("specs") or {}
        price = p.get("price_usd")
        rating = p.get("seller_rating")
        warranty = p.get("warranty_months")

        # --- hard disqualifiers ---
        if price is None:
            disqualified.append({**p, "reason": "No price data available"})
            continue
        if price > budget:
            disqualified.append({**p, "reason": f"Over budget (${price} > ${budget})"})
            continue
        if specs.get("ram_gb") is not None and specs["ram_gb"] < specs_req["ram_gb_min"]:
            disqualified.append({**p, "reason": f"RAM below minimum ({specs.get('ram_gb')}GB < {specs_req['ram_gb_min']}GB)"})
            continue
        if specs.get("storage_gb") is not None and specs["storage_gb"] < specs_req["storage_gb_min"]:
            disqualified.append({**p, "reason": f"Storage below minimum ({specs.get('storage_gb')}GB < {specs_req['storage_gb_min']}GB)"})
            continue
        if rating is not None and rating < policy["min_seller_rating"]:
            disqualified.append({**p, "reason": f"Seller rating below minimum ({rating} < {policy['min_seller_rating']})"})
            continue
        if warranty is not None and warranty < policy["require_warranty_months"]:
            disqualified.append({**p, "reason": f"Warranty below minimum ({warranty}mo < {policy['require_warranty_months']}mo)"})
            continue

        # --- scoring (0-100) ---
        price_score = 100 * (1 - (price - min_price) / max((max_price - min_price), 1))

        spec_points, spec_total = 0, 0
        for key, minimum in (("ram_gb", specs_req["ram_gb_min"]), ("storage_gb", specs_req["storage_gb_min"])):
            spec_total += 1
            val = specs.get(key)
            if val is not None and val >= minimum:
                spec_points += 1 + min((val - minimum) / minimum, 1) * 0.5  # bonus for exceeding
        battery = specs.get("battery_life_hours")
        if battery is not None:
            spec_total += 1
            if battery >= specs_req["battery_life_hours_min"]:
                spec_points += 1 + min((battery - specs_req["battery_life_hours_min"]) / specs_req["battery_life_hours_min"], 1) * 0.5
        nice = req.get("nice_to_have", [])
        nice_hits = 0
        for tag, flag_key in [
            ("Backlit keyboard", "backlit_keyboard"),
            ("Fingerprint reader", "fingerprint_reader"),
        ]:
            if tag in nice and specs.get(flag_key):
                nice_hits += 1
        spec_score = min(100, (spec_points / max(spec_total, 1)) * 85 + nice_hits * 7.5)

        value_score = (price / max(specs.get("ram_gb", 1) * specs.get("storage_gb", 1), 1)) if price else None
        value_for_money_score = price_score * 0.5 + spec_score * 0.5  # blended proxy

        vendor_score = min(100, (rating or 0) / 5 * 80 + (min(warranty or 0, 36) / 36) * 20)

        total = (
            price_score * weights["price"]
            + spec_score * weights["specs_match"]
            + value_for_money_score * weights["value_for_money"]
            + vendor_score * weights["vendor_reliability"]
        )

        why_bits = []
        if price <= budget * 0.85:
            why_bits.append("comfortably under budget")
        if specs.get("ram_gb", 0) > specs_req["ram_gb_min"]:
            why_bits.append("RAM exceeds requirement")
        if warranty and warranty >= 24:
            why_bits.append(f"{warranty}-month warranty")
        if rating and rating >= 4.5:
            why_bits.append("top-rated seller")

        ranked.append({
            **p,
            "value_score": round(total, 1),
            "why": "; ".join(why_bits) if why_bits else "Meets all hard requirements.",
        })

    ranked.sort(key=lambda x: x["value_score"], reverse=True)
    return {"ranked": ranked, "disqualified": disqualified}


class ScoringInput(BaseModel):
    products_json: str = Field(..., description="JSON list of scraped product records")
    company_context_json: str = Field(..., description="JSON of the company_context object")


class ProductScoringTool(BaseTool):
    name: str = "score_and_rank_products"
    description: str = (
        "Deterministically scores and ranks a list of scraped product records "
        "against the company context (budget, required specs, vendor policy, "
        "evaluation weights). Returns {ranked: [...], disqualified: [...]}."
    )
    args_schema: type[BaseModel] = ScoringInput

    def _run(self, products_json: str, company_context_json: str) -> str:
        products = json.loads(products_json)
        context = json.loads(company_context_json)
        result = score_products(products, context)
        return json.dumps(result, indent=2)
