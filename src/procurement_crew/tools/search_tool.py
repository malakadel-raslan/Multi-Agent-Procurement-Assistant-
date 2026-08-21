"""Web search tool used by the Market Research agent.

Wraps Tavily Search. If no TAVILY_API_KEY is configured (or DEMO_MODE=true),
falls back to bundled demo listings so the crew can still run end-to-end
without any external API keys — useful for local testing and CI.
"""
import json
import os

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from procurement_crew.demo_data import DEMO_SEARCH_RESULTS


class ProductSearchInput(BaseModel):
    query: str = Field(..., description="Product category / search query, e.g. 'business laptop 16GB RAM'")
    max_results: int = Field(8, description="Maximum number of listings to return")


class ProductSearchTool(BaseTool):
    name: str = "product_search"
    description: str = (
        "Searches the web for product listings matching a query and returns "
        "candidate product name, vendor, and URL for each result."
    )
    args_schema: type[BaseModel] = ProductSearchInput

    def _run(self, query: str, max_results: int = 8) -> str:
        demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        api_key = os.getenv("TAVILY_API_KEY")

        if demo_mode or not api_key:
            results = DEMO_SEARCH_RESULTS[:max_results]
            return json.dumps({"source": "demo_data", "results": results}, indent=2)

        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=api_key)
            resp = client.search(
                query=f"{query} buy price specifications",
                max_results=max_results,
                search_depth="advanced",
            )
            results = [
                {
                    "product_name": r.get("title", "Unknown product"),
                    "vendor": r.get("url", "").split("/")[2] if r.get("url") else "unknown",
                    "url": r.get("url"),
                }
                for r in resp.get("results", [])
            ]
            return json.dumps({"source": "tavily", "results": results}, indent=2)
        except Exception as exc:  # network / auth failures degrade gracefully
            fallback = DEMO_SEARCH_RESULTS[:max_results]
            return json.dumps(
                {"source": "demo_data_fallback", "error": str(exc), "results": fallback},
                indent=2,
            )
