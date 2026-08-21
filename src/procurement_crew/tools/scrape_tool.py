"""Product page scraping tool used by the Data Extraction agent.

Tries ScrapeGraphAI (LLM-driven structured extraction) first. If that fails
(no key, network error, unsupported page) falls back to a plain
requests + BeautifulSoup heuristic scrape. If DEMO_MODE is on, or a URL is
one of the bundled demo URLs, returns realistic canned data instead so the
whole pipeline can be exercised without hitting the network or any API.
"""
import json
import os

import requests
from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from procurement_crew.demo_data import DEMO_PRODUCT_RECORDS

EMPTY_RECORD = {
    "price_usd": None,
    "specs": {},
    "seller_rating": None,
    "warranty_months": None,
}


class ProductScrapeInput(BaseModel):
    url: str = Field(..., description="Product page URL to scrape")
    product_name: str = Field(..., description="Product name, for logging/matching")
    vendor: str = Field("unknown", description="Vendor / retailer name")


class ProductScrapeTool(BaseTool):
    name: str = "product_scrape"
    description: str = (
        "Scrapes a single product page URL and returns structured data: "
        "price_usd, specs (dict), seller_rating, warranty_months."
    )
    args_schema: type[BaseModel] = ProductScrapeInput

    def _run(self, url: str, product_name: str, vendor: str = "unknown") -> str:
        demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"

        if demo_mode or url in DEMO_PRODUCT_RECORDS:
            record = DEMO_PRODUCT_RECORDS.get(url, {**EMPTY_RECORD})
            return json.dumps(
                {
                    "product_name": product_name,
                    "vendor": vendor,
                    "url": url,
                    "source": "demo_data",
                    **record,
                },
                indent=2,
            )

        record = self._scrape_with_scrapegraph(url)
        if record is None:
            record = self._scrape_with_requests(url)
        if record is None:
            record = {**EMPTY_RECORD}

        return json.dumps(
            {"product_name": product_name, "vendor": vendor, "url": url, **record},
            indent=2,
        )

    # -- strategies -------------------------------------------------

    def _scrape_with_scrapegraph(self, url: str):
        try:
            from scrapegraphai.graphs import SmartScraperGraph

            graph_config = {
                "llm": {
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "model": os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
                },
                "verbose": False,
                "headless": True,
            }
            scraper = SmartScraperGraph(
                prompt=(
                    "Extract: price in USD as a number, a dict of specs "
                    "(ram_gb, storage_gb, storage_type, cpu, battery_life_hours, "
                    "screen_size_inches, weight_kg), seller_rating (0-5 float), "
                    "warranty_months (int). Use null for anything not found."
                ),
                source=url,
                config=graph_config,
            )
            result = scraper.run()
            if isinstance(result, str):
                result = json.loads(result)
            return {
                "price_usd": result.get("price_usd") or result.get("price"),
                "specs": result.get("specs", {}),
                "seller_rating": result.get("seller_rating"),
                "warranty_months": result.get("warranty_months"),
                "source": "scrapegraphai",
            }
        except Exception:
            return None

    def _scrape_with_requests(self, url: str):
        try:
            resp = requests.get(
                url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (ProcurementBot/1.0)"}
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text(" ", strip=True)
            return {
                "price_usd": None,
                "specs": {"raw_text_snippet": text[:300]},
                "seller_rating": None,
                "warranty_months": None,
                "source": "requests_bs4_fallback",
                "note": "Structured fields unavailable; manual review recommended.",
            }
        except Exception:
            return None
