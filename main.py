#!/usr/bin/env python3
"""Full project runner — runs the entire Multi-Agent Procurement Assistant.

By default this single command does everything end-to-end:
  1. Runs the 4-agent pipeline (search -> extract -> compare -> report)
  2. Prints a full console summary (ranked table + disqualified list)
  3. Saves the HTML report to disk
  4. Opens the report automatically in your browser

Usage:
    python main.py                        # run everything, demo mode by default
    DEMO_MODE=true python main.py         # force demo mode (no API keys needed)
    python main.py --context path.json    # use a custom company context
    python main.py --no-open              # don't auto-open the report in a browser
    python main.py --app                  # also launch the full Streamlit web app
"""
import argparse
import json
import subprocess
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv

load_dotenv()

from procurement_crew.pipeline import run_pipeline  # noqa: E402

ROOT = Path(__file__).parent


def print_ranked_table(ranked):
    if not ranked:
        print("\nNo qualifying products.")
        return
    headers = ["#", "Product", "Vendor", "Price", "RAM", "Storage", "Rating", "Warranty", "Score"]
    rows = []
    for i, p in enumerate(ranked, 1):
        s = p.get("specs", {})
        rows.append([
            str(i),
            p.get("product_name", "")[:28],
            p.get("vendor", "")[:16],
            f"${p.get('price_usd', 0):,.0f}",
            f"{s.get('ram_gb', '-')}GB",
            f"{s.get('storage_gb', '-')}GB",
            f"{p.get('seller_rating', '-')}\u2605",
            f"{p.get('warranty_months', '-')}mo",
            f"{p.get('value_score', '-')}",
        ])
    widths = [max(len(str(h)), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print("\n" + line)
    print("-" * len(line))
    for r in rows:
        print("  ".join(c.ljust(w) for c, w in zip(r, widths)))


def print_disqualified(disqualified):
    if not disqualified:
        return
    print("\nDisqualified:")
    for d in disqualified:
        print(f"  - {d.get('product_name')} ({d.get('vendor')}): {d.get('reason')}")


def run_full_pipeline(args):
    ctx = json.loads(Path(args.context).read_text())

    def log(msg):
        print(msg)

    print("=" * 60)
    print(" MULTI-AGENT PROCUREMENT ASSISTANT — full run")
    print("=" * 60)
    result = run_pipeline(ctx, log=log)

    scoring = result["scoring"]
    ranked = scoring["ranked"]

    print_ranked_table(ranked)
    print_disqualified(scoring["disqualified"])

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result["html"])
    print(f"\nReport saved to: {out_path.resolve()}")

    if ranked:
        top = ranked[0]
        print(f"\nTop recommendation: {top['product_name']} "
              f"(${top['price_usd']:,.0f}, score {top['value_score']}/100)")

    if not args.no_open:
        webbrowser.open(f"file://{out_path.resolve()}")
        print("Opened report in your default browser.")

    return result


def launch_streamlit_app():
    print("\nLaunching the full Streamlit web app (Ctrl+C to stop)...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py")])


def main():
    parser = argparse.ArgumentParser(description="Run the whole Multi-Agent Procurement Assistant project")
    parser.add_argument("--context", default="company_context.json", help="Path to company context JSON")
    parser.add_argument("--out", default="outputs/procurement_report.html", help="Output HTML path")
    parser.add_argument("--no-open", action="store_true", help="Don't auto-open the report in a browser")
    parser.add_argument("--app", action="store_true", help="Also launch the full Streamlit web app afterwards")
    args = parser.parse_args()

    run_full_pipeline(args)

    if args.app:
        launch_streamlit_app()
    else:
        print("\nTip: run `python main.py --app` to also launch the interactive web dashboard.")


if __name__ == "__main__":
    main()
