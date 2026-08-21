#!/usr/bin/env python3
"""CLI entrypoint.

Usage:
    python main.py                      # demo mode by default if no OPENAI_API_KEY
    DEMO_MODE=true python main.py       # force demo mode
    python main.py --context path.json  # custom company context
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv

load_dotenv()

from procurement_crew.pipeline import run_pipeline  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Procurement Assistant")
    parser.add_argument("--context", default="company_context.json", help="Path to company context JSON")
    parser.add_argument("--out", default="outputs/procurement_report.html", help="Output HTML path")
    args = parser.parse_args()

    ctx = json.loads(Path(args.context).read_text())

    def log(msg):
        print(msg)

    result = run_pipeline(ctx, log=log)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result["html"])

    print(f"\nReport saved to {out_path}")
    ranked = result["scoring"]["ranked"]
    if ranked:
        print(f"Top recommendation: {ranked[0]['product_name']} (${ranked[0]['price_usd']}, "
              f"score {ranked[0]['value_score']}/100)")


if __name__ == "__main__":
    main()
