#!/usr/bin/env python3
"""PayPal Kontoauszug Analyse — HTML + PDF Report"""

import re
import json
import math
import pdfplumber
from collections import defaultdict
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, base64

PDF_IN  = 'paypal.pdf'
HTML_OUT = 'paypal_analyse.html'
PDF_OUT  = 'paypal_analyse.pdf'

# ── Filter: interne PayPal-Buchungen ausblenden ──────────────────────────────
SKIP_KEYWORDS = [
    'Bankgutschrift', 'Abbuchung – Bankkonto', 'Währungsumrec',
    'Rückbuchung allgemeiner', 'Einbehaltung für', 'Allgemeiner Kontoausgleich',
    'Rückbuchung von ACH', 'ACH- Überweisung', 'Freigegebene Zahlung',
    'Käuferschutz', 'Transfer (Abbuchung', 'Transfer (Gutschrift',
]

# ── Namens-Normalisierung ────────────────────────────────────────────────────
NAME_MAP = {
    r'INTERSPAR.*':           'Interspar',
    r'Interspar.*':           'Interspar',
    r'ALDI.*':                'Aldi',
    r'IONOS.*':               '1&1 IONOS',
    r'1&1 IONOS.*':           '1&1 IONOS',
    r'Apple Services':        'Apple Services',
    r'GitHub.*':              'GitHub',
    r'EasyPark.*':            'EasyPark',
    r'DISKONT.*':             'Diskont Supermarkt',
    r'AliExpress.*':          'AliExpress',
    r'Temu.*':                'Temu',
    r'Dogans.*':              "Dogan's Bistro",
    r'Apotheke.*':            'Apotheke',
    r'McDonalds.*':           "McDonald's",
    r'REWE.*':                'REWE',
    r'Lidl.*':                'Lidl',
    r'BayWa.*':               'BayWa',
    r'YUME.*':                'YUME',
    r'Xoom.*':                'Xoom',
    r'Giropay.*':             'Giropay',
    r'Maria Rose.*Beker':     'Maria Beker',
    r'Maria Beker':           'Maria Beker',
    r'Carl Beker':            'Carl Beker',
    r'Harald Beker':          'Harald Beker',
}

def normalize_name(name):
    name = name.strip()
    if not name:
        return '(unbekannt)'
    for pattern, replacement in NAME_MAP.items():
        if re.fullmatch(pattern, name, re.IGNORECASE):
            return replacement
    return name

def parse_amount(s):
    if not s: return None
    s = s.strip().replace('\xa0', '').replace(' ', '')
    s = s.replace('.', '').replace(',', '.')
    try:
        return float(s)
    except:
        return None

# ── PDF einlesen ─────────────────────────────────────────────────────────────
transactions = []
currency = 'EUR'

with pdfplumber.open(PDF_IN) as pdf:
    for page in pdf.pages:
        text = page.extract_text() or ''
        for cur in ['EUR', 'CHF', 'GBP', 'USD']:
            if f'Transaktionsübersicht - {cur}' in text:
                currency = cur
        for table in page.extract_tables():
            for row in table:
                if not row or not row[0]:
                    continue
                date_str = (row[0] or '').strip()
                if not re.match(r'\d{2}\.\d{2}\.\d{2}$', date_str):
                    continue
                typ  = (row[1] or '').replace('\n', ' ').strip()
                name = (row[2] or '').replace('\n', ' ').strip()
                brutto = parse_amount(row[5])
                if brutto is None:
                    continue
                # Interne Buchungen überspringen
                if any(k in typ for k in SKIP_KEYWORDS):
                    continue
                # Datum parsen
                try:
                    date = datetime.strptime(date_str, '%d.%m.%y')
                except:
                    continue
                transactions.append({
                    'date':     date,
                    'date_str': date_str,
                    'type':     typ,
                    'name':     normalize_name(name),
                    'currency': currency,
                    'brutto':   brutto,
                })

print(f"Parsed {len(transactions)} transactions")

# ── Aggregation ──────────────────────────────────────────────────────────────
def year_str(t):
    return str(t['date'].year)

years = sorted(set(year_str(t) for t in transactions))

def agg_by_recipient(txs):
    """Returns dict name -> {ausgaben, einnahmen, count}"""
    d = defaultdict(lambda: {'ausgaben': 0.0, 'einnahmen': 0.0, 'count': 0})
    for t in txs:
        n = t['name']
        d[n]['count'] += 1
        if t['brutto'] < 0:
            d[n]['ausgaben'] += abs(t['brutto'])
        else:
            d[n]['einnahmen'] += t['brutto']
    return dict(d)

def year_summary(year):
    txs = [t for t in transactions if year_str(t) == year]
    ausgaben  = sum(abs(t['brutto']) for t in txs if t['brutto'] < 0)
    einnahmen = sum(t['brutto'] for t in txs if t['brutto'] > 0)
    return txs, ausgaben, einnahmen

# ── Pie Chart als Base64 ─────────────────────────────────────────────────────
COLORS_PIE = [
    '#4e79a7','#f28e2b','#e15759','#76b7b2','#59a14f',
    '#edc948','#b07aa1','#ff9da7','#9c755f','#bab0ac',
    '#6b6ecf','#8ca252','#bd9e39','#ad494a','#a55194',
]

def make_pie(labels, values, title, dark=False):
    bg = '#1e2129' if dark else '#ffffff'
    fg = '#e0e0e0' if dark else '#333333'
    fig, ax = plt.subplots(figsize=(5, 4))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    # limit to top 12 + Sonstige
    if len(labels) > 12:
        combined = sorted(zip(values, labels), reverse=True)
        top = combined[:12]
        rest = combined[12:]
        labels = [l for _, l in top] + ['Sonstige']
        values = [v for v, _ in top] + [sum(v for v, _ in rest)]
    wedges, texts, autotexts = ax.pie(
        values, labels=None, autopct='%1.1f%%',
        colors=COLORS_PIE[:len(values)], startangle=140,
        pctdistance=0.8,
        wedgeprops={'linewidth': 0.5, 'edgecolor': bg}
    )
    for at in autotexts:
        at.set_fontsize(7)
        at.set_color(fg)
    ax.legend(wedges, labels, loc='center left', bbox_to_anchor=(1, 0.5),
              fontsize=7, frameon=False, labelcolor=fg)
    ax.set_title(title, color=fg, fontsize=10, pad=8)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', facecolor=bg)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

# ── HTML generieren ───────────────────────────────────────────────────────────
def fmt(amount, currency='EUR'):
    sym = {'EUR': '€', 'CHF': 'CHF ', 'USD': '$', 'GBP': '£'}.get(currency, currency + ' ')
    return f"{sym}{amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def build_year_section(year, dark=False):
    txs, ausgaben, einnahmen = year_summary(year)
    recipients = agg_by_recipient(txs)

    # Ausgaben-Pie
    aus_data = {n: v['ausgaben'] for n, v in recipients.items() if v['ausgaben'] > 0}
    pie_aus_b64 = make_pie(list(aus_data.keys()), list(aus_data.values()), 'Ausgaben nach Empfänger', dark=dark) if aus_data else None

    # Tabelle Ausgaben
    sorted_aus = sorted(aus_data.items(), key=lambda x: x[1], reverse=True)

    # Einnahmen-Pie
    ein_data = {n: v['einnahmen'] for n, v in recipients.items() if v['einnahmen'] > 0}
    pie_ein_b64 = make_pie(list(ein_data.keys()), list(ein_data.values()), 'Einnahmen nach Quelle', dark=dark) if ein_data else None

    sorted_ein = sorted(ein_data.items(), key=lambda x: x[1], reverse=True)

    # Transaktionsliste pro Empfänger (aufklappbar)
    by_name = defaultdict(list)
    for t in sorted(txs, key=lambda x: x['date']):
        by_name[t['name']].append(t)

    html = f'<div class="year-section" id="year-{year}">'

    # Summary Cards
    html += f'''
    <div class="summary-cards">
      <div class="card card-out">
        <div class="card-label">Ausgaben {year}</div>
        <div class="card-value">-{fmt(ausgaben)}</div>
      </div>
      <div class="card card-in">
        <div class="card-label">Einnahmen {year}</div>
        <div class="card-value">+{fmt(einnahmen)}</div>
      </div>
      <div class="card card-net">
        <div class="card-label">Saldo {year}</div>
        <div class="card-value {"neg" if einnahmen-ausgaben < 0 else ""}">{fmt(einnahmen - ausgaben)}</div>
      </div>
      <div class="card card-count">
        <div class="card-label">Transaktionen</div>
        <div class="card-value">{len(txs)}</div>
      </div>
    </div>'''

    # Charts
    html += '<div class="charts-row">'
    if pie_aus_b64:
        html += f'<div class="chart-box"><img src="data:image/png;base64,{pie_aus_b64}" /></div>'
    if pie_ein_b64:
        html += f'<div class="chart-box"><img src="data:image/png;base64,{pie_ein_b64}" /></div>'
    html += '</div>'

    # Ausgaben-Tabelle
    if sorted_aus:
        html += '<h3>Ausgaben nach Empfänger</h3>'
        html += '<table class="data-table"><thead><tr><th>Empfänger</th><th>Betrag</th><th>Transaktionen</th></tr></thead><tbody>'
        for name, amt in sorted_aus:
            cnt = recipients[name]['count']
            html += f'<tr><td>{name}</td><td class="amount-neg">-{fmt(amt)}</td><td class="center">{cnt}</td></tr>'
        html += f'<tr class="total-row"><td><strong>Gesamt</strong></td><td class="amount-neg"><strong>-{fmt(ausgaben)}</strong></td><td></td></tr>'
        html += '</tbody></table>'

    # Einnahmen-Tabelle
    if sorted_ein:
        html += '<h3>Einnahmen nach Quelle</h3>'
        html += '<table class="data-table"><thead><tr><th>Quelle</th><th>Betrag</th><th>Transaktionen</th></tr></thead><tbody>'
        for name, amt in sorted_ein:
            cnt = recipients[name]['count']
            html += f'<tr><td>{name}</td><td class="amount-pos">+{fmt(amt)}</td><td class="center">{cnt}</td></tr>'
        html += f'<tr class="total-row"><td><strong>Gesamt</strong></td><td class="amount-pos"><strong>+{fmt(einnahmen)}</strong></td><td></td></tr>'
        html += '</tbody></table>'

    # Aufklappbare Detailtransaktionen
    html += '<h3>Alle Transaktionen</h3>'
    for name in sorted(by_name.keys()):
        txlist = by_name[name]
        total_aus = sum(abs(t['brutto']) for t in txlist if t['brutto'] < 0)
        total_ein = sum(t['brutto'] for t in txlist if t['brutto'] > 0)
        summary = f"-{fmt(total_aus)}" if total_aus else f"+{fmt(total_ein)}"
        html += f'''
    <details class="tx-details">
      <summary>{name} <span class="tx-summary">({len(txlist)} Transaktionen &nbsp;|&nbsp; {summary})</span></summary>
      <table class="tx-table">
        <thead><tr><th>Datum</th><th>Typ</th><th>Betrag</th><th>Währung</th></tr></thead>
        <tbody>'''
        for t in txlist:
            cls = 'amount-neg' if t['brutto'] < 0 else 'amount-pos'
            sign = '' if t['brutto'] >= 0 else ''
            html += f'<tr><td>{t["date_str"]}</td><td>{t["type"]}</td><td class="{cls}">{t["brutto"]:+,.2f}</td><td>{t["currency"]}</td></tr>'
        html += '</tbody></table></details>'

    html += '</div>'
    return html


# ── Gesamt-Übersicht ─────────────────────────────────────────────────────────
def build_overview(dark=False):
    by_year = {}
    for year in years:
        txs, a, e = year_summary(year)
        by_year[year] = {'ausgaben': a, 'einnahmen': e, 'count': len(txs)}

    total_aus = sum(v['ausgaben'] for v in by_year.values())
    total_ein = sum(v['einnahmen'] for v in by_year.values())

    # Gesamt Empfänger
    all_recipients = agg_by_recipient(transactions)
    top_aus = sorted(all_recipients.items(), key=lambda x: x[1]['ausgaben'], reverse=True)[:20]
    top_pie_labels = [n for n, _ in top_aus if _['ausgaben'] > 0]
    top_pie_values = [v['ausgaben'] for _, v in top_aus if v['ausgaben'] > 0]
    pie_b64 = make_pie(top_pie_labels, top_pie_values, 'Top Empfänger gesamt', dark=dark) if top_pie_labels else None

    html = '<div class="year-section" id="year-alle">'
    html += f'''
    <div class="summary-cards">
      <div class="card card-out"><div class="card-label">Gesamt Ausgaben</div><div class="card-value">-{fmt(total_aus)}</div></div>
      <div class="card card-in"><div class="card-label">Gesamt Einnahmen</div><div class="card-value">+{fmt(total_ein)}</div></div>
      <div class="card card-net"><div class="card-label">Gesamt Saldo</div><div class="card-value {"neg" if total_ein-total_aus < 0 else ""}">{ fmt(total_ein - total_aus)}</div></div>
      <div class="card card-count"><div class="card-label">Transaktionen</div><div class="card-value">{len(transactions)}</div></div>
    </div>'''

    # Jahres-Vergleichstabelle
    html += '<h3>Jahresübersicht</h3>'
    html += '<table class="data-table"><thead><tr><th>Jahr</th><th>Ausgaben</th><th>Einnahmen</th><th>Saldo</th><th>Transaktionen</th></tr></thead><tbody>'
    for year in years:
        v = by_year[year]
        saldo = v['einnahmen'] - v['ausgaben']
        scls = 'amount-neg' if saldo < 0 else 'amount-pos'
        html += f'<tr><td>{year}</td><td class="amount-neg">-{fmt(v["ausgaben"])}</td><td class="amount-pos">+{fmt(v["einnahmen"])}</td><td class="{scls}">{fmt(saldo)}</td><td class="center">{v["count"]}</td></tr>'
    html += f'<tr class="total-row"><td><strong>Gesamt</strong></td><td class="amount-neg"><strong>-{fmt(total_aus)}</strong></td><td class="amount-pos"><strong>+{fmt(total_ein)}</strong></td><td class="{"amount-neg" if total_ein-total_aus < 0 else "amount-pos"}"><strong>{fmt(total_ein-total_aus)}</strong></td><td></td></tr>'
    html += '</tbody></table>'

    if pie_b64:
        html += f'<div class="charts-row"><div class="chart-box"><img src="data:image/png;base64,{pie_b64}" /></div></div>'

    # Top 20 Empfänger
    html += '<h3>Top 20 Empfänger (gesamt)</h3>'
    html += '<table class="data-table"><thead><tr><th>Empfänger</th><th>Ausgaben</th><th>Einnahmen</th><th>Transaktionen</th></tr></thead><tbody>'
    for name, v in top_aus:
        html += f'<tr><td>{name}</td><td class="amount-neg">-{fmt(v["ausgaben"])}</td><td class="amount-pos">+{fmt(v["einnahmen"])}</td><td class="center">{v["count"]}</td></tr>'
    html += '</tbody></table>'

    html += '</div>'
    return html


# ── HTML zusammenbauen ────────────────────────────────────────────────────────
tab_labels = ['Alle'] + years

year_sections_dark  = [build_overview(dark=True)]  + [build_year_section(y, dark=True)  for y in years]
year_sections_light = [build_overview(dark=False)] + [build_year_section(y, dark=False) for y in years]
year_ids = ['alle'] + years

tabs_html = ''.join(
    f'<button class="tab-btn" onclick="showYear(\'{yid}\')" id="btn-{yid}">{lbl}</button>'
    for yid, lbl in zip(year_ids, tab_labels)
)

dark_sections_html  = ''.join(f'<div class="theme-dark"  id="dark-{yid}"  style="display:none">{sec}</div>'
                               for yid, sec in zip(year_ids, year_sections_dark))
light_sections_html = ''.join(f'<div class="theme-light" id="light-{yid}" style="display:none">{sec}</div>'
                               for yid, sec in zip(year_ids, year_sections_light))

HTML = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>PayPal Analyse 2023–2026</title>
<style>
:root {{
  --bg-dark:#1e2129; --bg-card-dark:#2a2d3e; --text-dark:#e0e0e0; --border-dark:#3a3d4e;
  --bg-light:#f4f6fb; --bg-card-light:#ffffff; --text-light:#333; --border-light:#dde3ef;
  --accent:#4e79a7; --red:#e15759; --green:#59a14f; --yellow:#f28e2b;
}}
* {{ box-sizing: border-box; margin:0; padding:0; }}
body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size:14px; transition: background .3s; }}
body.dark  {{ background:var(--bg-dark);  color:var(--text-dark); }}
body.light {{ background:var(--bg-light); color:var(--text-light); }}

/* Header */
.header {{ padding:20px 30px; display:flex; align-items:center; justify-content:space-between;
           border-bottom:2px solid var(--accent); background:var(--accent); color:#fff; }}
.header h1 {{ font-size:22px; }}
.header .subtitle {{ font-size:13px; opacity:.85; }}

/* Theme toggle */
.theme-toggles {{ display:flex; gap:8px; }}
.theme-btn {{ padding:6px 14px; border:none; border-radius:4px; cursor:pointer;
              font-size:12px; font-weight:bold; opacity:.7; transition:.2s; }}
.theme-btn.active {{ opacity:1; box-shadow:0 0 0 2px #fff; }}
.theme-btn.t-dark  {{ background:#1e2129; color:#e0e0e0; }}
.theme-btn.t-light {{ background:#f4f6fb; color:#333; }}
.theme-btn.t-blue  {{ background:#1a3a5c; color:#7eb3e0; }}
.theme-btn.t-green {{ background:#1a2e1a; color:#7ec87e; }}

/* Tabs */
.tabs {{ display:flex; gap:4px; padding:16px 30px 0; flex-wrap:wrap; }}
.tab-btn {{ padding:8px 20px; border:none; border-radius:6px 6px 0 0; cursor:pointer;
            font-size:13px; font-weight:600; transition:.2s; }}
body.dark  .tab-btn {{ background:#2a2d3e; color:#a0a8c0; }}
body.light .tab-btn {{ background:#e2e8f5; color:#555; }}
.tab-btn.active {{ background:var(--accent)!important; color:#fff!important; }}

/* Content */
.content {{ padding:20px 30px; max-width:1400px; margin:0 auto; }}

/* Summary cards */
.summary-cards {{ display:flex; gap:16px; margin-bottom:24px; flex-wrap:wrap; }}
.card {{ padding:16px 22px; border-radius:10px; min-width:160px; flex:1; }}
body.dark  .card {{ background:var(--bg-card-dark); border:1px solid var(--border-dark); }}
body.light .card {{ background:var(--bg-card-light); border:1px solid var(--border-light);
                    box-shadow:0 2px 8px rgba(0,0,0,.07); }}
.card-label {{ font-size:11px; text-transform:uppercase; letter-spacing:.5px; opacity:.6; margin-bottom:6px; }}
.card-value  {{ font-size:22px; font-weight:700; }}
.card-out .card-value {{ color:var(--red); }}
.card-in  .card-value {{ color:var(--green); }}
.card-net .card-value {{ color:var(--accent); }}
.card-net .card-value.neg {{ color:var(--red); }}
.card-count .card-value {{ color:var(--yellow); }}

/* Charts */
.charts-row {{ display:flex; gap:20px; margin:20px 0; flex-wrap:wrap; }}
.chart-box  {{ flex:1; min-width:280px; text-align:center; }}
.chart-box img {{ max-width:100%; border-radius:8px; }}

/* Tables */
h3 {{ margin:24px 0 10px; font-size:16px; color:var(--accent); }}
.data-table {{ width:100%; border-collapse:collapse; margin-bottom:20px; font-size:13px; }}
.data-table th {{ padding:10px 14px; text-align:left; font-weight:600; font-size:12px;
                  text-transform:uppercase; letter-spacing:.3px; }}
body.dark  .data-table th {{ background:#353850; color:#9aa0c0; border-bottom:2px solid var(--border-dark); }}
body.light .data-table th {{ background:#e8edf8; color:#555;    border-bottom:2px solid var(--border-light); }}
.data-table td {{ padding:9px 14px; border-bottom:1px solid; }}
body.dark  .data-table td {{ border-color:var(--border-dark); }}
body.light .data-table td {{ border-color:var(--border-light); }}
body.dark  .data-table tr:hover td {{ background:#2f3245; }}
body.light .data-table tr:hover td {{ background:#f0f4fc; }}
.total-row td {{ font-weight:700; }}
body.dark  .total-row td {{ background:#2e3040; border-top:2px solid var(--border-dark); }}
body.light .total-row td {{ background:#eef2fc; border-top:2px solid var(--border-light); }}
.amount-neg {{ color:var(--red);   text-align:right; font-variant-numeric:tabular-nums; }}
.amount-pos {{ color:var(--green); text-align:right; font-variant-numeric:tabular-nums; }}
.center {{ text-align:center; }}

/* Details / Transaktionen */
details.tx-details {{ margin-bottom:8px; border-radius:6px; overflow:hidden; }}
body.dark  details.tx-details {{ border:1px solid var(--border-dark); }}
body.light details.tx-details {{ border:1px solid var(--border-light); }}
details.tx-details summary {{
  padding:10px 14px; cursor:pointer; font-weight:600; font-size:13px;
  list-style:none; display:flex; align-items:center; gap:8px;
}}
body.dark  details.tx-details summary {{ background:#2a2d3e; }}
body.light details.tx-details summary {{ background:#eef2fc; }}
details.tx-details summary:hover {{ opacity:.85; }}
.tx-summary {{ font-weight:400; opacity:.65; font-size:12px; }}
.tx-table {{ width:100%; border-collapse:collapse; font-size:12px; }}
.tx-table th {{ padding:7px 12px; text-align:left; font-size:11px; font-weight:600; text-transform:uppercase; }}
body.dark  .tx-table th {{ background:#353850; color:#9aa0c0; }}
body.light .tx-table th {{ background:#f4f6fb; color:#666; }}
.tx-table td {{ padding:7px 12px; border-bottom:1px solid; }}
body.dark  .tx-table td {{ border-color:#2d3040; }}
body.light .tx-table td {{ border-color:#eee; }}

/* Blue theme */
body.blue {{ background:#0f1c2e; color:#c8dff5; }}
body.blue .card  {{ background:#1a2d44; border-color:#2a4060; }}
body.blue .header {{ background:#1a3a5c; }}
body.blue .tab-btn {{ background:#1a2d44; color:#8ab0d0; }}
body.blue .data-table th {{ background:#1a2d44; color:#8ab0d0; border-color:#2a4060; }}
body.blue .data-table td {{ border-color:#2a4060; }}
body.blue .data-table tr:hover td {{ background:#1f3550; }}
body.blue .total-row td {{ background:#1a2d44; border-color:#2a4060; }}
body.blue details.tx-details {{ border-color:#2a4060; }}
body.blue details.tx-details summary {{ background:#1a2d44; }}
body.blue .tx-table th {{ background:#1a2d44; color:#8ab0d0; }}
body.blue .tx-table td {{ border-color:#2a4060; }}

/* Green theme */
body.green {{ background:#0f1e0f; color:#c8e8c0; }}
body.green .card  {{ background:#1a2e1a; border-color:#2a4a2a; }}
body.green .header {{ background:#1a4a1a; }}
body.green .tab-btn {{ background:#1a2e1a; color:#8ac880; }}
body.green .data-table th {{ background:#1a2e1a; color:#8ac880; border-color:#2a4a2a; }}
body.green .data-table td {{ border-color:#2a4a2a; }}
body.green .data-table tr:hover td {{ background:#1f381f; }}
body.green .total-row td {{ background:#1a2e1a; border-color:#2a4a2a; }}
body.green details.tx-details {{ border-color:#2a4a2a; }}
body.green details.tx-details summary {{ background:#1a2e1a; }}
body.green .tx-table th {{ background:#1a2e1a; color:#8ac880; }}
body.green .tx-table td {{ border-color:#2a4a2a; }}
</style>
</head>
<body class="dark">

<div class="header">
  <div>
    <div class="header h1">PayPal Analyse</div>
    <div class="subtitle">01.04.2023 – 22.03.2026 &nbsp;|&nbsp; {len(transactions)} Transaktionen</div>
  </div>
  <div style="display:flex;align-items:center;gap:16px;">
    <a href="paypal_analyse.pdf" target="_blank" style="color:#fff;background:rgba(255,255,255,.15);padding:7px 16px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:600;border:1px solid rgba(255,255,255,.3);">📄 PDF</a>
  <div class="theme-toggles">
    <button class="theme-btn t-dark  active" onclick="setTheme('dark')">🌙 Dark</button>
    <button class="theme-btn t-light"        onclick="setTheme('light')">☀️ Light</button>
    <button class="theme-btn t-blue"         onclick="setTheme('blue')">🔵 Blue</button>
    <button class="theme-btn t-green"        onclick="setTheme('green')">🟢 Green</button>
  </div>
  </div>
</div>

<div class="tabs">
{tabs_html}
</div>

<div class="content">
{dark_sections_html}
{light_sections_html}
</div>

<script>
var currentYear = 'alle';
var currentTheme = 'dark';
var darkThemes = ['dark','blue','green'];

function setTheme(t) {{
  document.body.className = t;
  currentTheme = t;
  document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
  document.querySelector('.t-' + t).classList.add('active');
  showYear(currentYear);
}}

function showYear(year) {{
  currentYear = year;
  // hide all
  document.querySelectorAll('[id^="dark-"],[id^="light-"]').forEach(el => el.style.display='none');
  // show correct
  var isDark = darkThemes.includes(currentTheme);
  var prefix = isDark ? 'dark-' : 'light-';
  var el = document.getElementById(prefix + year);
  if (el) el.style.display = 'block';
  // update tabs
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  var btn = document.getElementById('btn-' + year);
  if (btn) btn.classList.add('active');
}}

// init
showYear('alle');
document.getElementById('btn-alle').classList.add('active');
</script>
</body>
</html>
"""

with open(HTML_OUT, 'w', encoding='utf-8') as f:
    f.write(HTML)
print(f"HTML gespeichert: {HTML_OUT}")

# ── PDF Report ────────────────────────────────────────────────────────────────
def build_pdf():
    doc = SimpleDocTemplate(PDF_OUT, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    DARK  = colors.HexColor('#1e2129')
    ACCENT= colors.HexColor('#4e79a7')
    RED   = colors.HexColor('#e15759')
    GREEN = colors.HexColor('#59a14f')
    LIGHT = colors.HexColor('#f0f4fc')
    LGREY = colors.HexColor('#e8edf8')
    WHITE = colors.white
    GREY  = colors.HexColor('#666666')

    title_style = ParagraphStyle('Title2', fontSize=18, textColor=ACCENT,
                                 spaceAfter=6, fontName='Helvetica-Bold')
    h2_style    = ParagraphStyle('H2', fontSize=13, textColor=ACCENT,
                                 spaceAfter=4, spaceBefore=14, fontName='Helvetica-Bold')
    h3_style    = ParagraphStyle('H3', fontSize=11, textColor=GREY,
                                 spaceAfter=4, spaceBefore=10, fontName='Helvetica-Bold')
    body_style  = ParagraphStyle('Body2', fontSize=9, spaceAfter=4)
    sub_style   = ParagraphStyle('Sub', fontSize=8, textColor=GREY)

    story = []

    # Titelseite
    story.append(Paragraph("PayPal Kontoauszug Analyse", title_style))
    story.append(Paragraph("01.04.2023 – 22.03.2026 | REDACTED", sub_style))
    story.append(Spacer(1, 0.5*cm))

    # Gesamt-Übersicht
    total_aus = sum(abs(t['brutto']) for t in transactions if t['brutto'] < 0)
    total_ein = sum(t['brutto'] for t in transactions if t['brutto'] > 0)

    story.append(Paragraph("Gesamt-Übersicht", h2_style))
    overview_data = [
        ['Jahr', 'Ausgaben (EUR)', 'Einnahmen (EUR)', 'Saldo', 'Transaktionen'],
    ]
    for year in years:
        txs, a, e = year_summary(year)
        saldo = e - a
        overview_data.append([
            year,
            f"-{a:,.2f}",
            f"+{e:,.2f}",
            f"{saldo:+,.2f}",
            str(len(txs)),
        ])
    overview_data.append([
        'Gesamt',
        f"-{total_aus:,.2f}",
        f"+{total_ein:,.2f}",
        f"{total_ein-total_aus:+,.2f}",
        str(len(transactions)),
    ])

    col_w = [2.5*cm, 4*cm, 4*cm, 4*cm, 3*cm]
    t = Table(overview_data, colWidths=col_w)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), ACCENT),
        ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('ALIGN',      (1,0), (-1,-1), 'RIGHT'),
        ('ALIGN',      (0,0), (0,-1), 'LEFT'),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [LIGHT, WHITE]),
        ('BACKGROUND', (0,-1), (-1,-1), LGREY),
        ('FONTNAME',   (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('GRID',       (0,0), (-1,-1), 0.3, colors.HexColor('#cccccc')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    # Pie als PNG für PDF
    all_recipients = agg_by_recipient(transactions)
    top_aus = sorted(all_recipients.items(), key=lambda x: x[1]['ausgaben'], reverse=True)[:15]
    pie_labels = [n for n, v in top_aus if v['ausgaben'] > 0]
    pie_values = [v['ausgaben'] for _, v in top_aus if v['ausgaben'] > 0]

    if pie_labels:
        fig, ax = plt.subplots(figsize=(7, 4))
        fig.patch.set_facecolor('white')
        if len(pie_labels) > 10:
            combined = sorted(zip(pie_values, pie_labels), reverse=True)
            top = combined[:10]
            rest = combined[10:]
            pie_labels2 = [l for _, l in top] + ['Sonstige']
            pie_values2 = [v for v, _ in top] + [sum(v for v, _ in rest)]
        else:
            pie_labels2, pie_values2 = pie_labels, pie_values
        wedges, texts, autotexts = ax.pie(pie_values2, labels=None,
            autopct='%1.1f%%', colors=COLORS_PIE[:len(pie_values2)],
            startangle=140, pctdistance=0.8)
        for at in autotexts: at.set_fontsize(7)
        ax.legend(wedges, pie_labels2, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=7, frameon=False)
        ax.set_title('Top Empfänger (gesamt)', fontsize=11)
        fig.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        plt.close(fig)
        buf.seek(0)
        from reportlab.platypus import Image as RLImage
        img = RLImage(buf, width=14*cm, height=8*cm)
        story.append(img)

    story.append(PageBreak())

    # Je Jahr eine Sektion
    for year in years:
        story.append(Paragraph(f"Jahr {year}", h2_style))
        txs, ausgaben, einnahmen = year_summary(year)
        saldo = einnahmen - ausgaben
        story.append(Paragraph(
            f"Ausgaben: <font color='#e15759'>-{ausgaben:,.2f} EUR</font> &nbsp;&nbsp; "
            f"Einnahmen: <font color='#59a14f'>+{einnahmen:,.2f} EUR</font> &nbsp;&nbsp; "
            f"Saldo: <b>{saldo:+,.2f} EUR</b> &nbsp;&nbsp; Transaktionen: {len(txs)}",
            body_style
        ))

        recipients = agg_by_recipient(txs)
        sorted_aus_r = sorted([(n, v) for n, v in recipients.items() if v['ausgaben'] > 0],
                              key=lambda x: x[1]['ausgaben'], reverse=True)
        sorted_ein_r = sorted([(n, v) for n, v in recipients.items() if v['einnahmen'] > 0],
                              key=lambda x: x[1]['einnahmen'], reverse=True)

        if sorted_aus_r:
            story.append(Paragraph("Ausgaben nach Empfänger", h3_style))
            table_data = [['Empfänger', 'Ausgaben (EUR)', 'Anz.']]
            for name, v in sorted_aus_r[:30]:
                table_data.append([name, f"{v['ausgaben']:,.2f}", str(v['count'])])
            table_data.append(['Gesamt', f"{ausgaben:,.2f}", ''])
            cw = [9*cm, 4.5*cm, 2*cm]
            tab = Table(table_data, colWidths=cw)
            tab.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), ACCENT),
                ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
                ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE',   (0,0), (-1,-1), 8),
                ('ALIGN',      (1,0), (-1,-1), 'RIGHT'),
                ('ROWBACKGROUNDS', (0,1), (-1,-2), [LIGHT, WHITE]),
                ('BACKGROUND', (0,-1), (-1,-1), LGREY),
                ('FONTNAME',   (0,-1), (-1,-1), 'Helvetica-Bold'),
                ('GRID',       (0,0), (-1,-1), 0.3, colors.HexColor('#cccccc')),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(tab)

        if sorted_ein_r:
            story.append(Paragraph("Einnahmen nach Quelle", h3_style))
            table_data = [['Quelle', 'Einnahmen (EUR)', 'Anz.']]
            for name, v in sorted_ein_r[:20]:
                table_data.append([name, f"{v['einnahmen']:,.2f}", str(v['count'])])
            table_data.append(['Gesamt', f"{einnahmen:,.2f}", ''])
            cw = [9*cm, 4.5*cm, 2*cm]
            tab = Table(table_data, colWidths=cw)
            tab.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#59a14f')),
                ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
                ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE',   (0,0), (-1,-1), 8),
                ('ALIGN',      (1,0), (-1,-1), 'RIGHT'),
                ('ROWBACKGROUNDS', (0,1), (-1,-2), [LIGHT, WHITE]),
                ('BACKGROUND', (0,-1), (-1,-1), LGREY),
                ('FONTNAME',   (0,-1), (-1,-1), 'Helvetica-Bold'),
                ('GRID',       (0,0), (-1,-1), 0.3, colors.HexColor('#cccccc')),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(tab)

        story.append(PageBreak())

    doc.build(story)
    print(f"PDF gespeichert: {PDF_OUT}")

build_pdf()
