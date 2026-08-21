"""Deterministic, professional HTML report generator.

Used as the guaranteed-correct rendering path (the report_writer agent may
also draft prose, but the table/numbers always come from here so figures
in the report can never drift from the scoring engine's output).
"""
from datetime import datetime

from jinja2 import Template

TEMPLATE = Template(r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Procurement Report — {{ category }}</title>
<style>
  :root {
    --navy: #0b3d91; --navy-dark: #082a66; --ink: #1a1f2b; --muted: #5b6472;
    --line: #e4e8ef; --bg: #f6f8fb; --gold: #c9971f; --green: #1a7f45; --red: #b3261e;
  }
  * { box-sizing: border-box; }
  body { margin:0; font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: var(--bg); color: var(--ink); }
  .wrap { max-width: 980px; margin: 0 auto; padding: 40px 28px 80px; }
  header.hero { background: linear-gradient(135deg, var(--navy) 0%, var(--navy-dark) 100%); color: #fff; border-radius: 14px; padding: 36px 40px; margin-bottom: 28px; box-shadow: 0 10px 30px rgba(11,61,145,.18); }
  header.hero .tag { text-transform: uppercase; letter-spacing: .12em; font-size: 12px; opacity: .75; margin-bottom: 8px; }
  header.hero h1 { margin: 0 0 6px; font-size: 28px; }
  header.hero .meta { opacity:.85; font-size: 14px; }
  .card { background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 28px 30px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(20,30,50,.04); }
  .card h2 { margin-top: 0; font-size: 18px; color: var(--navy-dark); border-bottom: 2px solid var(--line); padding-bottom: 10px; }
  .rec-banner { display:flex; align-items:center; gap:16px; background: #fbf6e9; border: 1px solid #eddfb3; border-radius: 10px; padding: 18px 20px; margin: 14px 0 18px; }
  .rec-banner .badge { background: var(--gold); color:#fff; font-weight:700; font-size:12px; padding: 6px 10px; border-radius: 999px; letter-spacing:.05em; }
  .rec-banner strong { font-size: 16px; }
  table { width:100%; border-collapse: collapse; font-size: 13.5px; }
  thead th { text-align:left; background: #f0f3f9; color: var(--navy-dark); font-weight:700; padding: 10px 12px; border-bottom: 2px solid var(--line); white-space: nowrap; }
  tbody td { padding: 10px 12px; border-bottom: 1px solid var(--line); vertical-align: top; }
  tbody tr:hover { background: #f9fbff; }
  .rank1 td:first-child { position: relative; }
  .pill { display:inline-block; padding:2px 9px; border-radius:999px; font-size:11.5px; font-weight:700; }
  .pill.score-high { background:#e7f6ec; color: var(--green); }
  .pill.score-mid { background:#fdf3e3; color:#8a6212; }
  .pill.score-low { background:#fbeae9; color: var(--red); }
  .top3-grid { display:grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 16px; }
  .prod-card { border:1px solid var(--line); border-radius: 10px; padding: 16px; background:#fcfdff; }
  .prod-card .rank { font-size:11px; font-weight:800; letter-spacing:.08em; color: var(--gold); }
  .prod-card h3 { margin: 4px 0 4px; font-size: 15px; }
  .prod-card .price { font-size: 18px; font-weight: 800; color: var(--navy-dark); margin: 6px 0; }
  .prod-card p { font-size: 12.8px; color: var(--muted); margin: 6px 0 0; line-height:1.5; }
  .disq-list { font-size: 13px; color: var(--muted); }
  .disq-list li { margin-bottom: 6px; }
  footer { text-align:center; color: var(--muted); font-size: 12px; margin-top: 30px; }
  @media (max-width: 720px) { .top3-grid { grid-template-columns: 1fr; } table { font-size:12px; } }
</style>
</head>
<body>
<div class="wrap">

  <header class="hero">
    <div class="tag">Procurement Report</div>
    <h1>{{ category }}</h1>
    <div class="meta">{{ company_name }} · {{ quantity }} units · Budget ${{ '{:,}'.format(budget) }}/unit
      · Generated {{ generated_at }}</div>
  </header>

  <div class="card">
    <h2>Executive Summary</h2>
    {% if top %}
    <div class="rec-banner">
      <span class="badge">Recommended</span>
      <div>
        <strong>{{ top.product_name }}</strong> — ${{ '{:,.0f}'.format(top.price_usd) }} from {{ top.vendor }}
        (value score {{ top.value_score }}/100)<br>
        <span style="color:var(--muted); font-size:13px;">{{ top.why }}</span>
      </div>
    </div>
    {% endif %}
    <p>{{ n_ranked }} of {{ n_total }} researched products met every hard requirement (budget, minimum
    specs, vendor rating, warranty). Below is the full ranked comparison, top-3 breakdown, and the reasons
    any product was excluded.</p>
  </div>

  <div class="card">
    <h2>Ranked Comparison</h2>
    <table>
      <thead>
        <tr><th>#</th><th>Product</th><th>Vendor</th><th>Price</th><th>RAM</th><th>Storage</th>
            <th>CPU</th><th>Rating</th><th>Warranty</th><th>Value Score</th></tr>
      </thead>
      <tbody>
        {% for p in ranked %}
        <tr {% if loop.index==1 %}class="rank1"{% endif %}>
          <td>{{ loop.index }}</td>
          <td>{{ p.product_name }}</td>
          <td>{{ p.vendor }}</td>
          <td>${{ '{:,.0f}'.format(p.price_usd) }}</td>
          <td>{{ p.specs.ram_gb }}GB</td>
          <td>{{ p.specs.storage_gb }}GB {{ p.specs.storage_type }}</td>
          <td>{{ p.specs.cpu }}</td>
          <td>{{ p.seller_rating }}★</td>
          <td>{{ p.warranty_months }}mo</td>
          <td>
            <span class="pill {% if p.value_score>=75 %}score-high{% elif p.value_score>=55 %}score-mid{% else %}score-low{% endif %}">
              {{ p.value_score }}
            </span>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Top 3 — Trade-off Notes</h2>
    <div class="top3-grid">
      {% for p in ranked[:3] %}
      <div class="prod-card">
        <div class="rank">#{{ loop.index }} PICK</div>
        <h3>{{ p.product_name }}</h3>
        <div class="price">${{ '{:,.0f}'.format(p.price_usd) }}</div>
        <p>{{ p.why }}. {{ p.specs.ram_gb }}GB RAM / {{ p.specs.storage_gb }}GB {{ p.specs.storage_type }},
        {{ p.specs.battery_life_hours }}h battery, {{ p.vendor }} ({{ p.seller_rating }}★,
        {{ p.warranty_months }}mo warranty).</p>
      </div>
      {% endfor %}
    </div>
  </div>

  {% if disqualified %}
  <div class="card">
    <h2>Excluded From Consideration</h2>
    <ul class="disq-list">
      {% for d in disqualified %}
      <li><strong>{{ d.product_name }}</strong> ({{ d.vendor }}) — {{ d.reason }}</li>
      {% endfor %}
    </ul>
  </div>
  {% endif %}

  <footer>Generated by the Multi-Agent Procurement Assistant (CrewAI) · {{ generated_at }}</footer>
</div>
</body>
</html>
""")


def render_report(company_context: dict, scoring_result: dict) -> str:
    req = company_context["procurement_request"]
    ranked = scoring_result["ranked"]
    return TEMPLATE.render(
        category=req["category"],
        company_name=company_context["company_name"],
        quantity=req["quantity"],
        budget=req["budget_per_unit_usd"],
        generated_at=datetime.now().strftime("%B %d, %Y %H:%M"),
        top=ranked[0] if ranked else None,
        ranked=ranked,
        disqualified=scoring_result["disqualified"],
        n_ranked=len(ranked),
        n_total=len(ranked) + len(scoring_result["disqualified"]),
    )
