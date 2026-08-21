"""Assembles the 4-agent sequential CrewAI crew."""
import json
import os
from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task

from procurement_crew.tools import ProductSearchTool, ProductScrapeTool, ProductScoringTool

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def _load_yaml(name: str) -> dict:
    with open(CONFIG_DIR / name, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class ProcurementCrew:
    """Builds and runs the search -> extract -> compare -> report crew."""

    def __init__(self, company_context: dict, min_results: int = 6):
        self.company_context = company_context
        self.min_results = min_results
        self.agents_cfg = _load_yaml("agents.yaml")
        self.tasks_cfg = _load_yaml("tasks.yaml")

        self.search_tool = ProductSearchTool()
        self.scrape_tool = ProductScrapeTool()
        self.scoring_tool = ProductScoringTool()

    def _build_agents(self):
        a = self.agents_cfg
        self.market_researcher = Agent(**a["market_researcher"], tools=[self.search_tool])
        self.data_extractor = Agent(**a["data_extractor"], tools=[self.scrape_tool])
        self.procurement_analyst = Agent(**a["procurement_analyst"], tools=[self.scoring_tool])
        self.report_writer = Agent(**a["report_writer"])

    def _build_tasks(self):
        t = self.tasks_cfg
        category = self.company_context["procurement_request"]["category"]
        ctx_json = json.dumps(self.company_context, indent=2)

        self.t_search = Task(
            description=t["search_task"]["description"].format(
                category=category, company_context=ctx_json, min_results=self.min_results
            ),
            expected_output=t["search_task"]["expected_output"].format(min_results=self.min_results),
            agent=self.market_researcher,
        )
        self.t_extract = Task(
            description=t["extract_task"]["description"],
            expected_output=t["extract_task"]["expected_output"],
            agent=self.data_extractor,
            context=[self.t_search],
        )
        self.t_compare = Task(
            description=t["compare_task"]["description"].format(company_context=ctx_json),
            expected_output=t["compare_task"]["expected_output"],
            agent=self.procurement_analyst,
            context=[self.t_extract],
        )
        self.t_report = Task(
            description=t["report_task"]["description"],
            expected_output=t["report_task"]["expected_output"],
            agent=self.report_writer,
            context=[self.t_compare],
        )

    def build(self) -> Crew:
        self._build_agents()
        self._build_tasks()
        return Crew(
            agents=[self.market_researcher, self.data_extractor, self.procurement_analyst, self.report_writer],
            tasks=[self.t_search, self.t_extract, self.t_compare, self.t_report],
            process=Process.sequential,
            verbose=True,
        )

    def kickoff(self) -> str:
        crew = self.build()
        result = crew.kickoff()
        return str(result)
