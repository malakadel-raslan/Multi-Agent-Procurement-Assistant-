# 🧭 Multi-Agent Procurement Assistant (CrewAI)

A 4-agent CrewAI system that researches products across multiple vendor
sites, scrapes price/specs, ranks them against your company's budget and
policy, and writes a professional HTML procurement report — with a
Streamlit deployment on top and Docker packaging for one-command hosting.

Built to satisfy the INSTANT project brief: *"Multi-Agent Procurement
Assistant using CrewAI."*

## How it maps to the brief

| Requirement | Where it lives |
|---|---|
| Set up CrewAI and define the agent workflow | `src/procurement_crew/crew.py` (`Process.sequential`, 4 agents) |
| Create a company context for the agents | `company_context.json` (editable live from the sidebar) |
| Agents for search, data collection/scraping, report generation | `config/agents.yaml`: `market_researcher`, `data_extractor`, `procurement_analyst`, `report_writer` |
| Tools like Tavily Search and ScrapeGraph | `tools/search_tool.py` (Tavily), `tools/scrape_tool.py` (ScrapeGraphAI + BeautifulSoup fallback) |
| Compare and rank by price, specs, and value | `tools/scoring_tool.py` — deterministic 0–100 value score, hard disqualifiers, weighted scoring |
| Run agents sequentially, generate a final HTML report | `pipeline.py` + `report.py` (Jinja2, self-contained styled HTML) |

## Architecture

```
Market Researcher  ──▶  Data Extractor  ──▶  Procurement Analyst  ──▶  Report Writer
 (Tavily search)        (ScrapeGraphAI/       (deterministic          (professional
                          BS4 fallback)         scoring tool)           HTML report)
```

Every agent has one job and one tool. The scoring math is a **deterministic
Python tool** (not left to the LLM to eyeball), so rankings are reproducible
and auditable — the report's numbers can never drift from the analyst's
actual computation.

## Demo mode — run it with zero API keys

The project ships with realistic bundled sample data (8 candidate laptops
across 8 vendors). With `DEMO_MODE=true` (the default when no
`OPENAI_API_KEY` is set), the exact same 4-stage pipeline runs directly in
Python — same search → scrape → score → report flow, same output shape —
without calling any LLM or hitting the network. This is what lets you
verify the whole system works before spending anything on API calls.

```bash
pip install -r requirements.txt
python main.py                    # writes outputs/procurement_report.html
# or
streamlit run app.py              # interactive UI, opens on localhost:8501
```

## Live mode (real agents, real web data)

1. Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY` (required)
   and `TAVILY_API_KEY` (recommended — without it, search falls back to
   demo data even in live mode).
2. Set `DEMO_MODE=false`.
3. `streamlit run app.py` or `python main.py`.

## Deployment

### Docker (recommended)

```bash
cp .env.example .env        # fill in keys, or leave DEMO_MODE=true
docker compose up --build
# open http://localhost:8501
```

### Bare metal / VM

```bash
pip install -r requirements.txt
streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

Put this behind any reverse proxy (Caddy/nginx) with TLS for a public
deployment; the container also ships a `/_stcore/health` healthcheck for
orchestrators (Docker, k8s, ECS, etc.).

## Testing

```bash
DEMO_MODE=true python -m pytest tests/ -v
```

7 tests cover: full pipeline execution, budget disqualification, spec
disqualification, ranking order, missing-data handling, report content,
and re-scoring under a changed budget.

## Project structure

```
procurement-crew/
├── app.py                     # Streamlit deployment (this is the "product")
├── main.py                    # CLI entrypoint
├── company_context.json       # editable company/procurement profile
├── config/
│   ├── agents.yaml             # 4 agent role/goal/backstory definitions
│   └── tasks.yaml               # 4 task descriptions, sequential context chain
├── src/procurement_crew/
│   ├── crew.py                  # wires agents + tasks into a CrewAI Crew
│   ├── pipeline.py              # demo-mode / live-mode entrypoint used by CLI & UI
│   ├── report.py                # Jinja2 professional HTML report renderer
│   ├── demo_data.py             # bundled realistic sample data
│   └── tools/
│       ├── search_tool.py       # Tavily-backed product search
│       ├── scrape_tool.py       # ScrapeGraphAI + requests/BS4 fallback
│       └── scoring_tool.py      # deterministic ranking engine
├── tests/test_pipeline.py     # 7 automated tests
├── Dockerfile / docker-compose.yml
└── requirements.txt
```

---
*ملاحظة: المشروع بيشتغل فورًا في "Demo Mode" من غير أي API keys (بيانات
عينة واقعية بتمر فعليًا على كل مراحل الـ pipeline). لو عايز بيانات حقيقية
من الإنترنت، ضيف `OPENAI_API_KEY` و `TAVILY_API_KEY` في ملف `.env` واطفي
Demo Mode.*
