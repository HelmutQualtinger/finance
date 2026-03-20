#!/usr/bin/env python3
"""
build_pdf_analyse.py
Generate pdf_analyse.html from hardcoded transaction data.
Style matches ubstrans_analyse.html (dark/light/blue/green themes,
year tabs via JS, summary cards, inline SVG doughnut charts,
counterparty table with details/summary monthly breakdown, search bar).
"""

import math
from collections import defaultdict

# ── Transaction data ─────────────────────────────────────────────────────────
# (date_str YYYY-MM-DD, counterparty, amount, is_credit)
RAW = [
    # 2026
    ('2026-03-02','Strassenverkehrsamt Kanton St. Gallen',441.00,False),
    ('2026-03-02','Gebäudeversicherung St.Gallen',278.60,False),
    ('2026-02-27','UBS Kontogebühren',15.00,False),
    ('2026-02-27','Europäische Patentorganisation',10956.42,True),
    ('2026-02-26','Endokrinologie-Diabetologie Rheintal',499.50,False),
    ('2026-02-25','UBS Card Center',29.65,False),
    ('2026-02-25','Sunrise GmbH',82.70,False),
    ('2026-02-19','Arztpraxis Knierim',16.50,False),
    ('2026-02-13','Gemeindeverwaltung Rebstein',199.75,False),
    ('2026-02-10','Dr. Risch Ostschweiz AG',164.60,False),
    ('2026-01-30','UBS Kontogebühren',15.00,False),
    ('2026-01-29','HOCH Health Ostschweiz',231.60,False),
    ('2026-01-28','Sunrise GmbH',81.00,False),
    ('2026-01-27','UBS Card Center',78.00,False),
    ('2026-01-28','Europäische Patentorganisation',13191.52,True),
    ('2026-01-13','Endokrinologie-Diabetologie Rheintal',61.70,False),
    ('2026-01-08','Apotheke zur Sonne GmbH',449.05,False),
    ('2026-01-08','Strassenverkehrsamt Kanton St. Gallen',14.00,False),
    ('2026-01-05','Arztpraxis Knierim',49.50,False),
    # 2025
    ('2025-12-31','Schweizerische Mobiliar',675.50,False),
    ('2025-12-31','UBS Kontogebühren',15.00,False),
    ('2025-12-25','UBS Card Center',92.05,False),
    ('2025-12-29','Sunrise GmbH',81.00,False),
    ('2025-12-23','Europäische Patentorganisation',12218.87,True),
    ('2025-12-16','Arztpraxis Knierim',243.70,False),
    ('2025-12-11','Herr Carl Harald Leopold Beker',9328.75,True),
    ('2025-12-04','Dr. Risch Ostschweiz AG',54.70,False),
    ('2025-12-02','HOCH Health Ostschweiz',231.60,False),
    ('2025-12-01','Apotheke zur Sonne GmbH',184.50,False),
    ('2025-11-28','HOCH Health Ostschweiz',944.55,False),
    ('2025-11-28','UBS Kontogebühren',15.00,False),
    ('2025-11-28','Europäische Patentorganisation',12779.29,True),
    ('2025-11-26','Sunrise GmbH',87.00,False),
    ('2025-11-25','UBS Card Center',26.95,False),
    ('2025-11-25','Serafe AG',335.00,False),
    ('2025-11-07','Politische Gemeinde Rebstein',136.05,True),
    ('2025-11-07','Politische Gemeinde Rebstein',698.85,True),
    ('2025-11-07','Politische Gemeinde Rebstein',1485.25,True),
    ('2025-10-31','UBS Kontogebühren',15.00,False),
    ('2025-10-29','Europäische Patentorganisation',12789.77,True),
    ('2025-10-28','Sunrise GmbH',81.00,False),
    ('2025-10-23','Apotheke zur Sonne GmbH',276.90,False),
    ('2025-10-07','Melioration der Rheinebene',294.80,False),
    ('2025-10-01','Clark Switzerland AG',304.00,False),
    ('2025-09-30','Politische Gemeinde Rebstein',3480.00,False),
    ('2025-09-30','UBS Kontogebühren',15.00,False),
    ('2025-09-30','Europäische Patentorganisation',12785.26,True),
    ('2025-09-26','Sunrise GmbH',81.00,False),
    ('2025-09-24','UBS Card Center',237.15,False),
    ('2025-09-23','HOCH Health Ostschweiz',257.45,False),
    ('2025-09-17','Arztpraxis Knierim',68.20,False),
    ('2025-09-01','Apotheke zur Sonne GmbH',459.00,False),
    ('2025-08-29','UBS Kontogebühren',15.00,False),
    ('2025-08-28','Sunrise GmbH',82.50,False),
    ('2025-08-27','UBS Card Center',12.60,False),
    ('2025-08-28','Europäische Patentorganisation',12785.26,True),
    ('2025-08-18','Arztpraxis Knierim',120.40,False),
    ('2025-08-06','Amt für Finanzdienstleistungen Kt SG',71.00,False),
    ('2025-07-31','Politische Gemeinde Rebstein',3460.00,False),
    ('2025-07-31','Schweizerische Mobiliar',461.45,False),
    ('2025-07-31','UBS Kontogebühren',15.00,False),
    ('2025-07-29','UBS Card Center',424.05,False),
    ('2025-07-29','Europäische Patentorganisation',12786.67,True),
    ('2025-07-28','Allianz Suisse',873.10,False),
    ('2025-07-28','Sunrise GmbH',81.00,False),
    ('2025-06-30','UBS Kontogebühren',15.00,False),
    ('2025-06-29','Europäische Patentorganisation',12788.69,True),
    ('2025-06-26','Sunrise GmbH',81.00,False),
    ('2025-06-26','Strassenverkehrsamt Kanton St. Gallen',20.00,False),
    ('2025-06-25','UBS Card Center',5.85,False),
    ('2025-06-25','Zollgarage Rheintal AG',2100.80,False),
    ('2025-06-20','Dr. Risch Ostschweiz AG',111.70,False),
    ('2025-06-12','Strassenverkehrsamt Kanton St. Gallen',60.00,False),
    ('2025-06-10','Arztpraxis Knierim',276.30,False),
    ('2025-06-05','Politische Gemeinde Rebstein',521.50,False),
    ('2025-06-03','Zentrum für Labormedizin',23.90,False),
    ('2025-05-30','Politische Gemeinde Rebstein',3460.00,False),
    ('2025-05-30','UBS Kontogebühren',15.00,False),
    ('2025-05-27','Apotheke zur Sonne GmbH',184.50,False),
    ('2025-05-27','Europäische Patentorganisation',12794.38,True),
    ('2025-05-27','Sunrise GmbH',116.00,False),
    ('2025-05-24','UBS Card Center',26.05,False),
    ('2025-05-23','Spitalregion RWS',831.50,False),
    ('2025-05-21','Arztpraxis Knierim',218.55,False),
    ('2025-05-15','Politische Gemeinde Rebstein',521.50,False),
    ('2025-04-30','UBS Kontogebühren',15.00,False),
    ('2025-04-30','Marie-Noel Arnold',100.00,True),
    ('2025-04-29','Arztpraxis Knierim',420.75,False),
    ('2025-04-28','UBS Card Center',214.40,False),
    ('2025-04-29','Europäische Patentorganisation',12809.92,True),
    ('2025-04-28','Sunrise GmbH',81.00,False),
    ('2025-04-25','Arztpraxis Knierim',33.00,False),
    ('2025-04-23','Dr. Risch Ostschweiz AG',96.70,False),
    ('2025-04-12','Apotheke zur Sonne GmbH',179.75,False),
    ('2025-04-07','Kantonsspital St. Gallen',442.40,False),
    ('2025-04-01','Arztpraxis Knierim',435.30,False),
    ('2025-03-31','Politische Gemeinde Rebstein',700.00,False),
    ('2025-03-31','UBS Kontogebühren',15.00,False),
    ('2025-03-28','Sunrise GmbH',81.00,False),
    ('2025-03-28','UBS Card Center',319.35,True),
    ('2025-03-28','Europäische Patentorganisation',12794.96,True),
    ('2025-03-26','UBS Card Center',319.35,False),
    ('2025-03-26','UBS Card Center',319.35,False),
    ('2025-03-26','Spitalregion RWS',822.45,False),
    ('2025-03-26','Herzpraxis Rheintal AG',771.15,False),
    ('2025-03-24','Gemeindeverwaltung Rebstein',1588.85,False),
    ('2025-03-10','Buttinette Textil-Versandhaus GmbH',76.95,False),
    ('2025-02-28','Strassenverkehrsamt Kanton St. Gallen',728.00,False),
    ('2025-02-28','Strassenverkehrsamt Kanton St. Gallen',468.00,False),
    ('2025-02-28','Gebäudeversicherung St.Gallen',276.10,False),
    ('2025-02-28','UBS Kontogebühren',15.00,False),
    ('2025-02-26','UBS Card Center',609.45,False),
    ('2025-02-27','Dr. Risch Ostschweiz AG',32.20,False),
    ('2025-02-26','Europäische Patentorganisation',12801.49,True),
    ('2025-02-26','Sunrise GmbH',80.25,False),
    ('2025-02-26','Strassenverkehrsamt Kanton St. Gallen',60.00,False),
    ('2025-01-31','UBS Kontogebühren',15.00,False),
    ('2025-01-29','Europäische Patentorganisation',12797.11,True),
    ('2025-01-27','KSSG / ZA',115.00,False),
    ('2025-01-28','Sunrise GmbH',79.55,False),
    ('2025-01-27','UBS Card Center',21.90,False),
    ('2025-01-21','Clark Switzerland AG',304.00,False),
    ('2025-01-07','Arztpraxis Knierim',103.35,False),
    ('2025-01-03','KSSG / ZA',437.15,False),
    ('2025-01-03','Arztpraxis Dr. Geiger AG',127.85,False),
    ('2025-01-03','Dr. med. Oliver Schuff',126.60,False),
    # 2024
    ('2024-12-31','Schweizerische Mobiliar',834.10,False),
    ('2024-12-31','UBS Kontogebühren',15.00,False),
    ('2024-12-24','UBS Card Center',380.60,False),
    ('2024-12-27','Sunrise GmbH',78.75,False),
    ('2024-12-23','Europäische Patentorganisation',12762.59,True),
    ('2024-12-04','Edelmetallbestellung UBS',469.00,False),
    ('2024-11-29','UBS Kontogebühren',15.00,False),
    ('2024-11-28','Europäische Patentorganisation',15416.29,True),
    ('2024-11-26','UBS Card Center',247.30,False),
    ('2024-11-27','Sunrise GmbH',79.00,False),
    ('2024-11-25','Serafe AG',335.00,False),
    ('2024-10-31','UBS Kontogebühren',15.00,False),
    ('2024-10-28','UBS Card Center',4.55,False),
    ('2024-10-29','Europäische Patentorganisation',12691.46,True),
    ('2024-10-28','Sunrise GmbH',79.00,False),
    ('2024-10-07','Melioration der Rheinebene',294.80,False),
    ('2024-10-01','Arztpraxis Knierim',297.35,False),
    ('2024-10-01','Arztpraxis Knierim',130.20,False),
    ('2024-09-30','UBS Kontogebühren',15.00,False),
    ('2024-09-28','Europäische Patentorganisation',12694.02,True),
    ('2024-09-27','Sunrise GmbH',81.65,False),
    ('2024-09-25','UBS Card Center',10.00,False),
    ('2024-09-13','Cigna International Health',26.40,True),
    ('2024-09-12','Arztpraxis Knierim',33.00,False),
    ('2024-09-09','Dr. Risch Ostschweiz AG',71.10,False),
    ('2024-09-03','Schweizerische Mobiliar',650.00,True),
    ('2024-08-30','UBS Kontogebühren',15.00,False),
    ('2024-08-27','UBS Card Center',505.25,False),
    ('2024-08-28','Europäische Patentorganisation',12699.36,True),
    ('2024-08-27','Sunrise GmbH',79.55,False),
    ('2024-08-22','Endokrinologie-Diabetologie Rheintal',447.00,False),
    ('2024-07-31','UBS Kontogebühren',15.00,False),
    ('2024-07-30','Europäische Patentorganisation',12725.14,True),
    ('2024-07-29','Sunrise GmbH',78.75,False),
    ('2024-07-24','UBS Card Center',5.60,False),
    ('2024-07-16','Arztpraxis Knierim',69.70,False),
    ('2024-07-05','Allianz Suisse',873.10,False),
    ('2024-07-01','Schweizerische Mobiliar',415.75,False),
    ('2024-06-28','UBS Kontogebühren',15.00,False),
    ('2024-06-28','Europäische Patentorganisation',12740.12,True),
    ('2024-06-27','Sunrise GmbH',82.65,False),
    ('2024-06-21','Politische Gemeinde Rebstein',521.50,False),
    ('2024-06-21','Politische Gemeinde Rebstein',521.50,False),
    ('2024-06-05','Dr. Risch Ostschweiz AG',86.70,False),
    ('2024-06-03','Endokrinologie-Diabetologie Rheintal',350.00,False),
    ('2024-05-31','UBS Kontogebühren',15.00,False),
    ('2024-05-30','Politische Gemeinde Rebstein',3782.50,False),
    ('2024-05-29','Europäische Patentorganisation',12736.52,True),
    ('2024-05-27','UBS Card Center',810.15,False),
    ('2024-05-28','Sunrise GmbH',78.75,False),
    ('2024-05-06','Norm Elektro GmbH',1593.75,False),
    ('2024-04-30','UBS Kontogebühren',15.00,False),
    ('2024-04-30','Marie-Noel Arnold',100.00,True),
    ('2024-04-30','Europäische Patentorganisation',12734.09,True),
    ('2024-04-29','Andreas Bölsterli',2000.00,False),
    ('2024-04-26','Oviva AG',83.15,False),
    ('2024-04-26','Sunrise GmbH',79.95,False),
    ('2024-04-05','Waldburger & Rutishauser AG',1180.80,False),
    ('2024-04-02','Gemeindeverwaltung Rebstein',738.00,False),
    ('2024-03-29','UBS Kontogebühren',15.00,False),
    ('2024-03-28','Politische Gemeinde Rebstein',700.00,False),
    ('2024-03-28','Europäische Patentorganisation',12712.72,True),
    ('2024-03-26','UBS Card Center',183.25,False),
    ('2024-03-26','Sunrise GmbH',79.50,False),
    ('2024-03-13','Herr Carl Harald Leopold Beker',2325.00,True),
    ('2024-03-11','Oviva AG',106.90,False),
    ('2024-02-29','Gemeindeverwaltung Rebstein',3693.65,False),
    ('2024-02-29','Strassenverkehrsamt Kanton St. Gallen',468.00,False),
    ('2024-02-29','Gebäudeversicherung St.Gallen',270.95,False),
    ('2024-02-29','UBS Kontogebühren',15.00,False),
    ('2024-02-27','UBS Card Center',258.50,False),
    ('2024-02-28','Endokrinologie-Diabetologie Rheintal',234.00,False),
    ('2024-02-27','Europäische Patentorganisation',12684.14,True),
    ('2024-02-26','Sunrise GmbH',79.05,False),
    ('2024-01-31','Sunrise GmbH',80.25,False),
    ('2024-01-31','UBS Kontogebühren',15.00,False),
    ('2024-01-30','Europäische Patentorganisation',12622.32,True),
    ('2024-01-24','UBS Card Center',409.80,False),
    ('2024-01-22','Gemeindeverwaltung Rebstein',628.20,False),
    ('2024-01-22','Dr. Risch Ostschweiz AG',81.70,False),
    ('2024-01-18','Strassenverkehrsamt Kanton St. Gallen',728.00,False),
    ('2024-01-05','Endokrinologie-Diabetologie Rheintal',145.75,False),
    ('2024-01-03','Schweizerische Mobiliar',651.00,False),
    ('2024-01-03','Sunrise GmbH',79.95,False),
]

COLORS = [
    '#3b82f6','#ef4444','#10b981','#f59e0b',
    '#8b5cf6','#ec4899','#06b6d4','#f97316','#64748b',
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def chf(v):
    """Format number as CHF with thousands separator (Swiss style)."""
    return f"{v:,.2f}".replace(',', "'")


def fmt_chf(v, sign=False):
    s = chf(abs(v))
    if sign:
        return f"+{s}" if v >= 0 else f"-{s}"
    return s


def make_pie_svg(labels, values, colors, size=260):
    """
    Build a compact inline SVG doughnut chart with a legend to the right.
    Returns an HTML string containing the <svg> element.
    """
    total = sum(values)
    if total == 0:
        return '<p style="color:var(--faint);font-size:0.8rem;">Keine Daten</p>'

    cx, cy, r_outer, r_inner = 90, 90, 80, 48
    svg_w = 340
    svg_h = max(size, len(labels) * 22 + 20)

    def polar(cx, cy, r, angle_deg):
        a = math.radians(angle_deg)
        return cx + r * math.sin(a), cy - r * math.cos(a)

    parts = []
    start = 0.0
    for i, (lbl, val, col) in enumerate(zip(labels, values, colors)):
        pct = val / total
        sweep = pct * 360
        end = start + sweep
        large = 1 if sweep > 180 else 0
        x1, y1 = polar(cx, cy, r_outer, start)
        x2, y2 = polar(cx, cy, r_outer, end)
        x3, y3 = polar(cx, cy, r_inner, end)
        x4, y4 = polar(cx, cy, r_inner, start)
        path = (
            f'M {x1:.2f} {y1:.2f} '
            f'A {r_outer} {r_outer} 0 {large} 1 {x2:.2f} {y2:.2f} '
            f'L {x3:.2f} {y3:.2f} '
            f'A {r_inner} {r_inner} 0 {large} 0 {x4:.2f} {y4:.2f} Z'
        )
        title = f'{lbl}: CHF {chf(val)} ({pct*100:.1f}%)'
        parts.append(f'<path d="{path}" fill="{col}" stroke="var(--bg2)" stroke-width="1.5"><title>{title}</title></path>')
        start = end

    # Legend
    legend_x = cx * 2 + 16
    legend_items = []
    for i, (lbl, val, col) in enumerate(zip(labels, values, colors)):
        ly = 14 + i * 22
        pct = val / total * 100
        short = lbl if len(lbl) <= 22 else lbl[:21] + '…'
        legend_items.append(
            f'<rect x="{legend_x}" y="{ly}" width="10" height="10" rx="2" fill="{col}"/>'
            f'<text x="{legend_x+14}" y="{ly+9}" font-size="10" fill="var(--text2)">{short}</text>'
            f'<text x="{svg_w-4}" y="{ly+9}" font-size="9.5" fill="var(--muted)" text-anchor="end">{pct:.1f}%</text>'
        )

    svg = (
        f'<svg viewBox="0 0 {svg_w} {svg_h}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;max-height:{svg_h}px;overflow:visible">'
        + ''.join(parts)
        + ''.join(legend_items)
        + '</svg>'
    )
    return svg


# ── Data aggregation ──────────────────────────────────────────────────────────

def aggregate(transactions):
    """
    Returns per-year dict:
      year -> {
        'total_credit', 'total_debit', 'count',
        'counterparties': {cp -> {'debit', 'credit', 'count', 'months': {YYYY-MM -> {'debit','credit','count'}}}}
      }
    """
    years = defaultdict(lambda: {
        'total_credit': 0.0, 'total_debit': 0.0, 'count': 0,
        'counterparties': defaultdict(lambda: {
            'debit': 0.0, 'credit': 0.0, 'count': 0,
            'months': defaultdict(lambda: {'debit': 0.0, 'credit': 0.0, 'count': 0})
        })
    })
    for date_str, cp, amount, is_credit in transactions:
        year = int(date_str[:4])
        month = date_str[:7]
        y = years[year]
        y['count'] += 1
        cps = y['counterparties'][cp]
        cps['count'] += 1
        m = cps['months'][month]
        m['count'] += 1
        if is_credit:
            y['total_credit'] += amount
            cps['credit'] += amount
            m['credit'] += amount
        else:
            y['total_debit'] += amount
            cps['debit'] += amount
            m['debit'] += amount
    return years


def top8_plus_rest(cp_dict, key):
    """Sort by key descending, take top 8, rest -> 'Sonstige'."""
    items = [(cp, data[key]) for cp, data in cp_dict.items() if data[key] > 0]
    items.sort(key=lambda x: x[1], reverse=True)
    if len(items) <= 8:
        return items, []
    top = items[:8]
    rest = items[8:]
    rest_total = sum(v for _, v in rest)
    return top, [('Sonstige', rest_total)]


# ── HTML generation ───────────────────────────────────────────────────────────

CSS = """
  /* ── Themes via CSS variables ── */
  [data-theme="dark"] {
    --bg: #0f1117; --bg2: #1a1f35; --border: #2d3748; --border2: #1e2a3a;
    --text: #e2e8f0; --text2: #cbd5e1; --muted: #94a3b8; --faint: #64748b;
    --thead: #0f1117; --detail-bg: #0f1117; --bar-bg: #0f1117;
    --accent: #3b82f6; --hover: rgba(59,130,246,0.06);
    --h1: #fff; --input-bg: #1a1f35;
  }
  [data-theme="light"] {
    --bg: #f1f5f9; --bg2: #ffffff; --border: #e2e8f0; --border2: #e2e8f0;
    --text: #1e293b; --text2: #334155; --muted: #64748b; --faint: #94a3b8;
    --thead: #f8fafc; --detail-bg: #f1f5f9; --bar-bg: #e2e8f0;
    --accent: #2563eb; --hover: rgba(37,99,235,0.05);
    --h1: #0f172a; --input-bg: #ffffff;
  }
  [data-theme="blue"] {
    --bg: #0a1628; --bg2: #0f2040; --border: #1e3a5f; --border2: #162e4d;
    --text: #e2f0ff; --text2: #bcd6f5; --muted: #7aa8d8; --faint: #4e7aa8;
    --thead: #071120; --detail-bg: #071120; --bar-bg: #071120;
    --accent: #38bdf8; --hover: rgba(56,189,248,0.07);
    --h1: #fff; --input-bg: #0f2040;
  }
  [data-theme="green"] {
    --bg: #071612; --bg2: #0d2318; --border: #1a4030; --border2: #122e22;
    --text: #d1fae5; --text2: #a7f3d0; --muted: #6ee7b7; --faint: #34d399;
    --thead: #051009; --detail-bg: #051009; --bar-bg: #051009;
    --accent: #10b981; --hover: rgba(16,185,129,0.07);
    --h1: #ecfdf5; --input-bg: #0d2318;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         background: var(--bg); color: var(--text); min-height: 100vh; transition: background 0.25s, color 0.25s; }
  .header { background: var(--bg2); border-bottom: 1px solid var(--border); padding: 1.5rem 2rem; }
  .header-inner { max-width: 1400px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem; }
  .header h1 { font-size: 1.6rem; font-weight: 700; color: var(--h1); }
  .header p { color: var(--muted); margin-top: 0.3rem; font-size: 0.875rem; }

  /* Theme switcher */
  .theme-switcher { display: flex; gap: 0.4rem; align-items: center; }
  .pdf-link { display:inline-flex; align-items:center; padding:0.45rem 1rem;
    background:var(--accent); color:#fff; border-radius:8px; text-decoration:none;
    font-size:0.8rem; font-weight:600; transition:opacity 0.2s; white-space:nowrap; }
  .pdf-link:hover { opacity:0.85; }
  .theme-switcher span { font-size: 0.75rem; color: var(--faint); margin-right: 0.3rem; }
  .theme-btn { width: 28px; height: 28px; border-radius: 50%; border: 2px solid transparent;
               cursor: pointer; transition: border-color 0.2s, transform 0.15s; }
  .theme-btn:hover { transform: scale(1.15); }
  .theme-btn.active { border-color: var(--text); }
  .theme-btn[data-t="dark"]  { background: linear-gradient(135deg, #0f1117 50%, #1a1f35 50%); }
  .theme-btn[data-t="light"] { background: linear-gradient(135deg, #f1f5f9 50%, #e2e8f0 50%); border-color: #cbd5e1; }
  .theme-btn[data-t="blue"]  { background: linear-gradient(135deg, #0a1628 50%, #38bdf8 50%); }
  .theme-btn[data-t="green"] { background: linear-gradient(135deg, #071612 50%, #10b981 50%); }

  .container { max-width: 1400px; margin: 0 auto; padding: 1.5rem 2rem; }

  /* Year tabs */
  .tabs { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
  .tab { padding: 0.5rem 1.2rem; border-radius: 20px; cursor: pointer; font-size: 0.85rem; font-weight: 600;
         border: 1px solid var(--border); background: var(--bg2); color: var(--muted); transition: all 0.2s; }
  .tab:hover { color: var(--text); border-color: var(--accent); }
  .tab.active { background: var(--accent); border-color: var(--accent); color: #fff; }

  /* Summary cards */
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
  .card { background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; padding: 1.2rem; }
  .card-label { font-size: 0.75rem; color: var(--faint); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem; }
  .card-value { font-size: 1.4rem; font-weight: 700; }
  .card-value.green { color: #10b981; }
  .card-value.red { color: #ef4444; }
  .card-value.blue { color: var(--accent); }
  .card-value.neutral { color: var(--text); }

  /* Table */
  .section { display: none; }
  .section.active { display: block; }
  .table-wrapper { background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
  table { width: 100%; border-collapse: collapse; }
  thead { background: var(--thead); }
  th { padding: 0.45rem 1rem; text-align: left; font-size: 0.75rem; color: var(--faint); text-transform: uppercase; letter-spacing: 0.05em; }
  th.right { text-align: right; }
  tbody tr { border-top: 1px solid var(--border2); transition: background 0.15s; }
  tbody tr:hover { background: var(--hover); }
  td { padding: 0.35rem 1rem; font-size: 0.875rem; }
  td.right { text-align: right; font-variant-numeric: tabular-nums; }
  td.cp-name { font-weight: 500; color: var(--text2); max-width: 280px; }
  td.count { color: var(--muted); }
  td.debit { color: #ef4444; }
  td.credit { color: #10b981; }
  td.net-pos { color: #10b981; font-weight: 600; }
  td.net-neg { color: #ef4444; font-weight: 600; }
  td.bar-cell { width: 120px; }
  .bar-wrap { background: var(--bar-bg); border-radius: 4px; height: 8px; overflow: hidden; }
  .bar { height: 8px; border-radius: 4px; }
  .bar.debit-bar { background: #ef4444; }
  .bar.credit-bar { background: #10b981; }

  /* Month breakdown (details/summary) */
  details { cursor: pointer; }
  details summary { list-style: none; display: inline; }
  details summary::-webkit-details-marker { display: none; }
  .expand-arrow { color: var(--faint); font-size: 0.75rem; margin-left: 4px; user-select: none; }
  .detail-row { display: none; }
  .detail-row.open { display: table-row; }
  .detail-inner { background: var(--detail-bg); padding: 0.75rem 1rem 0.75rem 2rem; }
  .detail-inner table { font-size: 0.8rem; }
  .detail-inner th { font-size: 0.7rem; }

  .search-bar { margin-bottom: 1rem; }
  .search-bar input { background: var(--input-bg); border: 1px solid var(--border); border-radius: 8px; color: var(--text);
    padding: 0.5rem 1rem; font-size: 0.875rem; width: 300px; outline: none; transition: border-color 0.2s; }
  .search-bar input:focus { border-color: var(--accent); }
  .search-bar input::placeholder { color: var(--faint); }

  .tag { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 600; margin-left: 4px; }
  .tag.income  { background: rgba(16,185,129,0.15); color: #10b981; }
  .tag.expense { background: rgba(239,68,68,0.15);  color: #ef4444; }
  .tag.mixed   { background: rgba(59,130,246,0.15);  color: #3b82f6; }

  /* SVG pie charts */
  .charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; }
  .chart-box { background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; padding: 1.2rem; }
  .chart-box h3 { font-size: 0.8rem; color: var(--faint); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.8rem; }

  @media (max-width: 700px) {
    .charts-row { grid-template-columns: 1fr; }
    .header-inner { flex-direction: column; align-items: flex-start; }
  }
"""

JS = """
function showYear(year) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('year-' + year).classList.add('active');
  document.getElementById('tab-' + year).classList.add('active');
}

function toggleDetail(id) {
  var row = document.getElementById(id);
  row.classList.toggle('open');
}

function filterTable(year, query) {
  var q = query.toLowerCase();
  var rows = document.querySelectorAll('#table-' + year + ' .cp-row');
  rows.forEach(function(row) {
    var cp = row.getAttribute('data-cp') || '';
    var match = cp.includes(q);
    row.style.display = match ? '' : 'none';
    var nextRow = row.nextElementSibling;
    if (nextRow && nextRow.classList.contains('detail-row')) {
      nextRow.style.display = match ? '' : 'none';
    }
  });
}

function setTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  document.querySelectorAll('.theme-btn').forEach(function(btn) {
    btn.classList.toggle('active', btn.getAttribute('data-t') === t);
  });
  try { localStorage.setItem('pdf-analyse-theme', t); } catch(e) {}
}

(function() {
  try {
    var saved = localStorage.getItem('pdf-analyse-theme');
    if (saved) setTheme(saved);
  } catch(e) {}
})();
"""

PDF_ICON = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'style="margin-right:5px;vertical-align:-2px">'
    '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
    '<polyline points="14 2 14 8 20 8"/>'
    '<line x1="12" y1="18" x2="12" y2="12"/>'
    '<line x1="9" y1="15" x2="15" y2="15"/>'
    '</svg>'
)


def build_year_section(year, y_data, is_first):
    cps = y_data['counterparties']
    total_credit = y_data['total_credit']
    total_debit  = y_data['total_debit']
    netto        = total_credit - total_debit
    n_txn        = y_data['count']
    n_cp         = len(cps)

    netto_cls   = 'green' if netto >= 0 else 'red'
    netto_sign  = '+' if netto >= 0 else '-'
    active_cls  = ' active' if is_first else ''

    # ── Cards ──────────────────────────────────────────────────────────────
    cards_html = f"""
  <div class="cards">
    <div class="card"><div class="card-label">Einnahmen</div><div class="card-value green">CHF {chf(total_credit)}</div></div>
    <div class="card"><div class="card-label">Ausgaben</div><div class="card-value red">CHF {chf(total_debit)}</div></div>
    <div class="card"><div class="card-label">Netto</div><div class="card-value {netto_cls}">CHF {netto_sign}{chf(abs(netto))}</div></div>
    <div class="card"><div class="card-label">Transaktionen</div><div class="card-value neutral">{n_txn}</div></div>
    <div class="card"><div class="card-label">Gegenparteien</div><div class="card-value blue">{n_cp}</div></div>
  </div>"""

    # ── SVG Doughnut charts ────────────────────────────────────────────────
    def make_chart(cp_dict, key, title):
        top, rest = top8_plus_rest(cp_dict, key)
        all_items = top + rest
        if not all_items:
            return f'<div class="chart-box"><h3>{title}</h3><p style="color:var(--faint);font-size:0.8rem;padding:1rem 0">Keine Daten</p></div>'
        labels = [lbl for lbl, _ in all_items]
        values = [v   for _, v   in all_items]
        colors = COLORS[:len(all_items)]
        n_rows = len(labels)
        svg_h  = max(200, n_rows * 22 + 20)
        svg    = make_pie_svg(labels, values, colors, size=svg_h)
        return f'<div class="chart-box"><h3>{title}</h3>{svg}</div>'

    chart_out = make_chart(cps, 'debit',  'Ausgaben nach Gegenpartei')
    chart_in  = make_chart(cps, 'credit', 'Einnahmen nach Gegenpartei')

    charts_html = f"""
  <div class="charts-row">
    {chart_out}
    {chart_in}
  </div>"""

    # ── Sort counterparties: debit desc, then credit desc ──────────────────
    sorted_cps = sorted(
        cps.items(),
        key=lambda x: (x[1]['debit'], x[1]['credit']),
        reverse=True
    )

    max_debit = max((d['debit'] for _, d in sorted_cps), default=1) or 1

    # ── Table rows ─────────────────────────────────────────────────────────
    rows_html = ''
    for idx, (cp, d) in enumerate(sorted_cps):
        detail_id = f'd-{year}-{idx}'
        debit  = d['debit']
        credit = d['credit']
        net    = credit - debit
        count  = d['count']

        if debit > 0 and credit > 0:
            tag = '<span class="tag mixed">beides</span>'
        elif debit > 0:
            tag = '<span class="tag expense">ausgang</span>'
        else:
            tag = '<span class="tag income">eingang</span>'

        debit_str  = f'-{chf(debit)}'   if debit  > 0 else '—'
        credit_str = chf(credit)         if credit > 0 else '—'
        net_cls    = 'net-pos' if net >= 0 else 'net-neg'
        net_str    = ('+' if net >= 0 else '-') + chf(abs(net))

        bar_pct = int(debit / max_debit * 100) if max_debit else 0

        debit_cls  = 'debit'  if debit  > 0 else ''
        credit_cls = 'credit' if credit > 0 else ''

        # Monthly breakdown inside <details><summary>
        months_sorted = sorted(d['months'].items())
        month_rows = ''
        for month, md in months_sorted:
            m_deb = f'-{chf(md["debit"])}'   if md['debit']  > 0 else ''
            m_cre = chf(md['credit'])          if md['credit'] > 0 else ''
            m_cnt = f'{md["count"]} Buchg.'
            month_rows += (
                f'<tr>'
                f'<td>{month}</td>'
                f'<td class="right debit">{m_deb}</td>'
                f'<td class="right credit">{m_cre}</td>'
                f'<td>{m_cnt}</td>'
                f'</tr>\n'
            )

        # Use <details><summary> for expand in first cell
        cp_cell = (
            f'<details>'
            f'<summary>{cp}{tag}<span class="expand-arrow">&#9660;</span></summary>'
            f'</details>'
        )

        rows_html += f"""
      <tr class="cp-row" data-cp="{cp.lower()}">
        <td class="cp-name">{cp_cell}</td>
        <td class="right count">{count}</td>
        <td class="right {debit_cls}">{debit_str}</td>
        <td class="right {credit_cls}">{credit_str}</td>
        <td class="right {net_cls}">{net_str}</td>
        <td class="bar-cell"><div class="bar-wrap"><div class="bar debit-bar" style="width:{bar_pct}%"></div></div></td>
      </tr>
      <tr class="detail-row" id="{detail_id}">
        <td colspan="6"><div class="detail-inner"><table>
          <thead><tr><th>Monat</th><th class="right">Ausgaben</th><th class="right">Einnahmen</th><th>Anzahl</th></tr></thead>
          <tbody>{month_rows}</tbody></table></div></td>
      </tr>"""

    table_html = f"""
  <div class="search-bar"><input type="text" placeholder="Gegenpartei suchen..." onkeyup="filterTable({year}, this.value)" id="search-{year}"></div>
  <div class="table-wrapper">
  <table id="table-{year}">
    <thead>
      <tr>
        <th>Gegenpartei</th>
        <th class="right">Anzahl</th>
        <th class="right">Ausgaben (CHF)</th>
        <th class="right">Einnahmen (CHF)</th>
        <th class="right">Netto (CHF)</th>
        <th class="right">Ausgaben</th>
      </tr>
    </thead>
    <tbody>{rows_html}
    </tbody>
  </table>
  </div>"""

    return f"""
<div class="section{active_cls}" id="year-{year}">
  {cards_html}
  {charts_html}
  {table_html}
</div>"""


def build_html(years_data):
    sorted_years = sorted(years_data.keys(), reverse=True)
    total_txn = sum(y['count'] for y in years_data.values())

    # Tab buttons
    tabs_html = ''
    for i, yr in enumerate(sorted_years):
        active = ' active' if i == 0 else ''
        tabs_html += f'    <div class="tab{active}" onclick="showYear({yr})" id="tab-{yr}">{yr}</div>\n'

    # Sections
    sections_html = ''
    for i, yr in enumerate(sorted_years):
        sections_html += build_year_section(yr, years_data[yr], i == 0)

    html = f"""<!DOCTYPE html>
<html lang="de" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UBS Privatkonto Analyse</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="header">
  <div class="header-inner" style="gap:0.8rem;">
    <div>
      <h1>UBS Privatkonto Analyse</h1>
      <p>CH65 0022 5225 8077 6105 B &mdash; Zeitraum 03.01.2024&ndash;02.03.2026 &mdash; {total_txn} Transaktionen</p>
    </div>
    <div class="theme-switcher">
      <span>Thema:</span>
      <button class="theme-btn active" data-t="dark"  onclick="setTheme('dark')"  title="Dunkel"></button>
      <button class="theme-btn"        data-t="light" onclick="setTheme('light')" title="Hell"></button>
      <button class="theme-btn"        data-t="blue"  onclick="setTheme('blue')"  title="Blau"></button>
      <button class="theme-btn"        data-t="green" onclick="setTheme('green')" title="Grün"></button>
    </div>
    <a href="pdf_analyse.pdf" class="pdf-link" title="PDF öffnen / drucken" download>
      {PDF_ICON}Drucken / PDF
    </a>
  </div>
</div>
<div class="container">
  <div class="tabs" id="tabsContainer">
{tabs_html}  </div>
{sections_html}
</div>
<script>
{JS}
// Details/summary toggle — clicking a <details> row shows the detail-row below
document.addEventListener('DOMContentLoaded', function() {{
  document.querySelectorAll('td.cp-name details').forEach(function(det) {{
    var tr = det.closest('tr');
    var detailRow = tr && tr.nextElementSibling;
    if (detailRow && detailRow.classList.contains('detail-row')) {{
      det.addEventListener('toggle', function() {{
        detailRow.classList.toggle('open', det.open);
      }});
    }}
  }});
}});
</script>
</body>
</html>"""
    return html


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    years_data = aggregate(RAW)
    html = build_html(years_data)
    out_path = '/Users/haraldbeker/finance/pdf_analyse.html'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Written {len(html):,} chars to {out_path}')

    # Quick sanity
    for yr in sorted(years_data.keys(), reverse=True):
        y = years_data[yr]
        netto = y['total_credit'] - y['total_debit']
        print(f"  {yr}: {y['count']:3d} Txn | Einnahmen {chf(y['total_credit'])} | "
              f"Ausgaben {chf(y['total_debit'])} | Netto {'+' if netto>=0 else ''}{chf(netto)}")