#!/usr/bin/env python3
"""build_kreditkarten_analyse.py — UBS Kreditkarten-Analyse (transactions-KreditKarten.pdf)"""
import math, collections

# ── All 105 transactions (date, counterparty, debit_chf, credit_chf) ─────────
TRANSACTIONS = [
    # 2026 — Page 1
    ("2026-03-15", "Google One",                  9.36,    0),
    ("2026-02-26", "LSV-Zahlung",                 0,      29.65),
    ("2026-02-15", "Google One",                  9.46,    0),
    ("2026-01-28", "LSV-Zahlung",                 0,      78.00),
    ("2026-01-20", "ALDI mobile",                20.00,    0),
    ("2026-01-15", "Google One",                  9.65,    0),
    ("2026-01-05", "Anthropic",                  22.27,    0),
    ("2026-01-01", "Google Cloud",               37.98,    0),
    # 2025 — Pages 2–6
    ("2025-12-31", "Anthropic",                  17.76,    0),
    ("2025-12-30", "LSV-Zahlung",                 0,      92.05),
    ("2025-12-01", "Google Cloud",                2.50,    0),
    ("2025-12-01", "Anthropic",                  22.51,    0),
    ("2025-11-27", "Google Play",                 1.44,    0),
    ("2025-11-26", "LSV-Zahlung",                 0,      26.95),
    ("2025-11-26", "Devisenzuschlag 1.75%",       0.18,    0),
    ("2025-11-26", "PayPal *Alipay",             10.46,    0),
    ("2025-11-24", "Google One",                  9.64,    0),
    ("2025-11-20", "Google One",                  3.84,    0),
    ("2025-11-18", "Anthropic",                  17.89,    0),
    ("2025-11-15", "PayPal *Digitec",            23.60,    0),
    ("2025-11-02", "Anthropic",                  22.50,    0),
    ("2025-11-01", "Anthropic",                   0.47,    0),
    ("2025-10-27", "KSSG Parking H07A",           4.00,    0),
    ("2025-09-25", "LSV-Zahlung",                 0,     237.15),
    ("2025-09-11", "Temu.com",                   45.27,    0),
    ("2025-08-30", "Temu.com",                   23.86,    0),
    ("2025-08-28", "LSV-Zahlung",                 0,      12.60),
    ("2025-08-15", "Pizolbahnen AG",            168.00,    0),
    ("2025-08-13", "Sportplatz Bützel",           4.60,    0),
    ("2025-07-30", "LSV-Zahlung",                 0,     424.05),
    ("2025-07-21", "Caffè Sette K2",              8.00,    0),
    ("2025-07-10", "Anthropic",                   4.47,    0),
    ("2025-07-10", "Anthropic",                   4.47,    0),
    ("2025-06-26", "Apotheke zur Sonne",        415.10,    0),
    ("2025-06-26", "LSV-Zahlung",                 0,       5.85),
    ("2025-05-27", "LSV-Zahlung",                 0,      26.05),
    ("2025-05-15", "Google Play",                 5.84,    0),
    ("2025-05-09", "KSSG Parking H07A",           2.50,    0),
    ("2025-05-09", "KSSG Campus",                22.60,    0),
    ("2025-05-08", "Apple.com/CHDE",            998.00,    0),
    ("2025-04-30", "Apple.com/CHDE",              0,     998.00),
    ("2025-04-29", "LSV-Zahlung",                 0,     214.40),
    ("2025-04-15", "Google Play",                 0.95,    0),
    ("2025-04-11", "Apotheke zur Sonne",        203.55,    0),
    ("2025-03-27", "LSV-Zahlung",                 0,     319.35),
    ("2025-03-20", "Interspar Restaurant",        7.33,    0),
    ("2025-03-14", "KSSG Parking H07A",           3.50,    0),
    ("2025-03-11", "Interspar Filiale",         136.77,    0),
    ("2025-02-27", "LSV-Zahlung",                 0,     609.45),
    ("2025-02-25", "Olivetano Feinkost",         13.58,    0),
    ("2025-02-25", "ALDI Süd Lindau",           119.50,    0),
    ("2025-02-18", "Manga Quick Restaurant",     45.55,    0),
    ("2025-02-18", "IKEA St. Gallen",             3.95,    0),
    ("2025-02-13", "Apotheke zur Sonne",        440.25,    0),
    ("2025-02-04", "ALDI Süd Lindau",           130.96,    0),
    ("2025-01-28", "LSV-Zahlung",                 0,      21.90),
    ("2025-01-27", "Manga Quick Restaurant",     21.82,    0),
    ("2025-01-16", "KSSG Campus",               16.40,    0),
    ("2025-01-14", "Selecta Merchant",            1.90,    0),
    ("2025-01-08", "ALDI mobile",               20.00,    0),
    # 2024 — Pages 7–10
    ("2024-12-27", "LSV-Zahlung",                 0,     380.60),
    ("2024-12-04", "Zentral Apotheke Heerbrugg",272.45,    0),
    ("2024-12-04", "Reichelt Electronics",       61.17,    0),
    ("2024-12-04", "Devisenzuschlag 1.75%",       1.07,    0),
    ("2024-12-04", "Zentral Apotheke Heerbrugg",  3.20,    0),
    ("2024-11-27", "AliExpress",                  9.79,    0),
    ("2024-11-27", "Devisenzuschlag 1.75%",       0.17,    0),
    ("2024-11-27", "LSV-Zahlung",                 0,     247.30),
    ("2024-11-27", "EasyPark Schweiz",            1.15,    0),
    ("2024-11-22", "PayPal *Digitec",            31.60,    0),
    ("2024-11-11", "EasyPark Schweiz",            6.40,    0),
    ("2024-11-02", "AliExpress",                  6.26,    0),
    ("2024-11-02", "Devisenzuschlag 1.75%",       0.11,    0),
    ("2024-10-29", "LSV-Zahlung",                 0,       4.55),
    ("2024-10-26", "EasyPark Schweiz",            1.63,    0),
    ("2024-10-25", "EasyPark Schweiz",            4.98,    0),
    ("2024-10-24", "EasyPark Schweiz",            0.67,    0),
    ("2024-10-23", "Night Inn Hotel Feldkirch", 225.92,    0),
    ("2024-10-16", "EasyPark Schweiz",            1.31,    0),
    ("2024-09-26", "LSV-Zahlung",                 0,      10.00),
    ("2024-09-11", "Devisenzuschlag 1.75%",       0.08,    0),
    ("2024-09-11", "PayPal *Temu",                4.47,    0),
    ("2024-09-02", "ALDI mobile",               10.00,    0),
    ("2024-08-28", "LSV-Zahlung",                 0,     505.25),
    ("2024-08-06", "Devisenzuschlag 1.75%",       0.29,    0),
    ("2024-08-06", "PayPal *Wiener Linien",      16.70,    0),
    ("2024-08-06", "EasyPark Schweiz",            3.44,    0),
    ("2024-08-05", "Zentral Apotheke Heerbrugg",477.20,    0),
    ("2024-07-25", "Devisenzuschlag 1.75%",       0.13,    0),
    ("2024-07-25", "LSV-Zahlung",                 0,       5.60),
    ("2024-07-25", "PayPal *Temu",                7.47,    0),
    ("2024-07-25", "PayPal *Temu",                0.02,    0),
    ("2024-07-12", "Devisenzuschlag 1.75%",       0.10,    0),
    ("2024-07-12", "PayPal *Temu",                5.48,    0),
    ("2024-05-28", "LSV-Zahlung",                 0,     810.15),
    ("2024-05-09", "NYX Anker Snack Vienna",      3.24,    0),
    ("2024-04-19", "Endokrinologie Altstätten", 188.15,    0),
    ("2024-04-15", "Devisenzuschlag 1.75%",       1.38,    0),
    ("2024-04-15", "PayPal *Trainline",          78.79,    0),
    ("2024-04-15", "PayPal *Digitec",           538.60,    0),
    ("2024-03-27", "LSV-Zahlung",                 0,     183.25),
    ("2024-02-28", "LSV-Zahlung",                 0,     258.50),
    ("2024-02-23", "Apotheke zur Sonne",        173.45,    0),
    ("2024-02-21", "Devisenzuschlag 1.75%",       0.17,    0),
    ("2024-02-21", "PayPal *Alipay",              9.65,    0),
]

PIE_COLORS = ['#3b82f6','#ef4444','#10b981','#f59e0b','#8b5cf6',
              '#ec4899','#06b6d4','#f97316','#84cc16','#64748b']

def fmt(v):
    return f"{v:,.2f}".replace(',', "'")

def make_pie_svg(items):
    TOP_N = 8
    top = items[:TOP_N]
    rest = items[TOP_N:]
    labels = [cp for cp, _ in top]
    vals   = [v  for _, v  in top]
    if rest:
        labels.append('Sonstige')
        vals.append(round(sum(v for _, v in rest), 2))
    total = sum(vals)
    if total <= 0:
        return '<svg viewBox="0 0 340 60"><text x="170" y="35" text-anchor="middle" font-size="12" fill="#94a3b8">Keine Ausgaben</text></svg>'
    colors = list(PIE_COLORS[:len(labels)])
    if rest:
        colors[-1] = '#64748b'

    cx, cy, r, ri = 90, 90, 80, 48
    rows = len(labels)
    h = max(200, rows * 22 + 14)
    paths = []
    angle = -math.pi / 2

    for i, (lbl, v) in enumerate(zip(labels, vals)):
        pct = v / total
        da  = 2 * math.pi * pct
        display_lbl = lbl[:22] + '…' if len(lbl) > 22 else lbl
        ly = 14 + i * 22

        if pct >= 0.9999:
            # Full circle: two semicircles
            path = (
                f'<path d="M {cx} {cy-r:.2f} A {r} {r} 0 1 1 {cx} {cy+r:.2f} '
                f'A {r} {r} 0 1 1 {cx} {cy-r:.2f} '
                f'L {cx} {cy-ri:.2f} A {ri} {ri} 0 1 0 {cx} {cy+ri:.2f} '
                f'A {ri} {ri} 0 1 0 {cx} {cy-ri:.2f} Z" '
                f'fill="{colors[i]}" stroke="var(--bg2)" stroke-width="1.5">'
                f'<title>{lbl}: CHF {fmt(v)} (100.0%)</title></path>'
            )
        else:
            x1  = cx + r  * math.cos(angle);       y1  = cy + r  * math.sin(angle)
            x2  = cx + r  * math.cos(angle + da);  y2  = cy + r  * math.sin(angle + da)
            xi1 = cx + ri * math.cos(angle);        yi1 = cy + ri * math.sin(angle)
            xi2 = cx + ri * math.cos(angle + da);   yi2 = cy + ri * math.sin(angle + da)
            large = 1 if da > math.pi else 0
            path = (
                f'<path d="M {x1:.2f} {y1:.2f} A {r} {r} 0 {large} 1 {x2:.2f} {y2:.2f} '
                f'L {xi2:.2f} {yi2:.2f} A {ri} {ri} 0 {large} 0 {xi1:.2f} {yi1:.2f} Z" '
                f'fill="{colors[i]}" stroke="var(--bg2)" stroke-width="1.5">'
                f'<title>{lbl}: CHF {fmt(v)} ({pct*100:.1f}%)</title></path>'
            )

        legend = (
            f'<rect x="196" y="{ly}" width="10" height="10" rx="2" fill="{colors[i]}"/>'
            f'<text x="210" y="{ly+9}" font-size="10" fill="var(--text2)">{display_lbl}</text>'
            f'<text x="336" y="{ly+9}" font-size="9.5" fill="var(--muted)" text-anchor="end">{pct*100:.1f}%</text>'
        )
        paths.append(path + legend)
        angle += da

    return (f'<svg viewBox="0 0 340 {h}" xmlns="http://www.w3.org/2000/svg" '
            f'style="width:100%;max-height:{h}px;overflow:visible">{"".join(paths)}</svg>')


def build_year_section(year, txns):
    cp_debit  = collections.defaultdict(float)
    cp_credit = collections.defaultdict(float)
    cp_count  = collections.defaultdict(int)
    # cp -> month -> [debit, credit, count]
    cp_months = collections.defaultdict(lambda: collections.defaultdict(lambda: [0.0, 0.0, 0]))

    for date, cp, debit, credit in txns:
        month = date[:7]
        cp_debit[cp]  += debit
        cp_credit[cp] += credit
        cp_count[cp]  += 1
        cp_months[cp][month][0] += debit
        cp_months[cp][month][1] += credit
        cp_months[cp][month][2] += 1

    total_debit  = round(sum(cp_debit.values()),  2)
    total_credit = round(sum(cp_credit.values()), 2)
    total_net    = round(total_credit - total_debit, 2)
    n_txn = len(txns)
    n_cp  = len(set(cp for _, cp, _, _ in txns))

    cps_by_debit = sorted(cp_debit.keys(), key=lambda cp: cp_debit[cp], reverse=True)

    # Pie: expenses only (no LSV-Zahlung)
    expense_items = [(cp, cp_debit[cp]) for cp in cps_by_debit
                     if cp_debit[cp] > 0 and cp != 'LSV-Zahlung']
    pie_svg = make_pie_svg(expense_items)

    net_cls  = 'green' if total_net >= 0 else 'red'
    net_sign = '+' if total_net >= 0 else ''
    cards = f"""
  <div class="cards">
    <div class="card"><div class="card-label">Ausgaben</div><div class="card-value red">CHF {fmt(total_debit)}</div></div>
    <div class="card"><div class="card-label">Kartenzahlungen</div><div class="card-value green">CHF {fmt(total_credit)}</div></div>
    <div class="card"><div class="card-label">Saldo</div><div class="card-value {net_cls}">CHF {net_sign}{fmt(total_net)}</div></div>
    <div class="card"><div class="card-label">Transaktionen</div><div class="card-value neutral">{n_txn}</div></div>
    <div class="card"><div class="card-label">Gegenparteien</div><div class="card-value blue">{n_cp}</div></div>
  </div>"""

    pie_section = f"""
  <div class="charts-row" style="grid-template-columns:1fr;">
    <div class="chart-box"><h3>Ausgaben nach Gegenpartei</h3>{pie_svg}</div>
  </div>"""

    max_debit = max((cp_debit[cp] for cp in cps_by_debit if cp_debit[cp] > 0), default=1)
    rows = []
    for cp in cps_by_debit:
        d   = round(cp_debit[cp], 2)
        cr  = round(cp_credit[cp], 2)
        net = round(cr - d, 2)
        cnt = cp_count[cp]
        net_cls2 = 'net-pos' if net >= 0 else 'net-neg'
        net_str  = f'+{fmt(net)}' if net >= 0 else fmt(net)
        bar_pct  = int(d / max_debit * 100) if max_debit > 0 and d > 0 else 0

        if d > 0 and cr > 0:
            tag = '<span class="tag mixed">gemischt</span>'
        elif d > 0:
            tag = '<span class="tag expense">ausgang</span>'
        else:
            tag = '<span class="tag income">eingang</span>'

        months_sorted = sorted(cp_months[cp].keys())
        month_rows = ''.join(
            f'<tr><td>{m}</td>'
            f'<td class="right debit">{("-" + fmt(cp_months[cp][m][0])) if cp_months[cp][m][0] > 0 else ""}</td>'
            f'<td class="right credit">{fmt(cp_months[cp][m][1]) if cp_months[cp][m][1] > 0 else ""}</td>'
            f'<td>{cp_months[cp][m][2]} Buchg.</td></tr>'
            for m in months_sorted
        )
        detail = (f'<div class="detail-inner"><table>'
                  f'<thead><tr><th>Monat</th><th class="right">Ausgaben</th>'
                  f'<th class="right">Einnahmen</th><th>Anzahl</th></tr></thead>'
                  f'<tbody>{month_rows}</tbody></table></div>')

        rows.append(
            f'      <tr class="cp-row" data-cp="{cp.lower()}">\n'
            f'        <td class="cp-name"><details><summary>{cp}{tag}'
            f'<span class="expand-arrow">&#9660;</span></summary>{detail}</details></td>\n'
            f'        <td class="right count">{cnt}</td>\n'
            f'        <td class="right debit">{("-" + fmt(d)) if d > 0 else "—"}</td>\n'
            f'        <td class="right {"credit" if cr > 0 else ""}">{fmt(cr) if cr > 0 else "—"}</td>\n'
            f'        <td class="right {net_cls2}">{net_str}</td>\n'
            f'        <td class="bar-cell"><div class="bar-wrap">'
            f'<div class="bar debit-bar" style="width:{bar_pct}%"></div></div></td>\n'
            f'      </tr>'
        )

    table = (f'  <div class="table-wrapper">\n'
             f'  <table id="table-{year}">\n'
             f'    <thead><tr>'
             f'<th>Gegenpartei</th>'
             f'<th class="right">Anzahl</th>'
             f'<th class="right">Ausgaben (CHF)</th>'
             f'<th class="right">Einnahmen (CHF)</th>'
             f'<th class="right">Netto (CHF)</th>'
             f'<th class="right">Ausgaben</th>'
             f'</tr></thead>\n'
             f'    <tbody>\n{"".join(rows)}\n    </tbody>\n  </table>\n  </div>')

    return cards + pie_section + '\n' + table


def build_html():
    txns_by_year = collections.defaultdict(list)
    for txn in TRANSACTIONS:
        txns_by_year[int(txn[0][:4])].append(txn)

    years = sorted(txns_by_year.keys(), reverse=True)

    tabs = ''.join(
        f'<div class="tab{" active" if i==0 else ""}" onclick="showYear({y})" id="tab-{y}">{y}</div>'
        for i, y in enumerate(years)
    )

    sections = []
    for i, year in enumerate(years):
        active = ' active' if i == 0 else ''
        body = build_year_section(year, txns_by_year[year])
        sections.append(f'<div class="section{active}" id="year-{year}">\n{body}\n</div>')

    date_start = min(d for d, _, _, _ in TRANSACTIONS)
    date_end   = max(d for d, _, _, _ in TRANSACTIONS)
    n_txn = len(TRANSACTIONS)

    css = """
  [data-theme="dark"]  { --bg:#0f1117;--bg2:#1a1f35;--border:#2d3748;--border2:#1e2a3a;--text:#e2e8f0;--text2:#cbd5e1;--muted:#94a3b8;--faint:#64748b;--thead:#0f1117;--detail-bg:#0f1117;--bar-bg:#0f1117;--accent:#3b82f6;--hover:rgba(59,130,246,0.06);--h1:#fff;--input-bg:#1a1f35; }
  [data-theme="light"] { --bg:#f1f5f9;--bg2:#ffffff;--border:#e2e8f0;--border2:#e2e8f0;--text:#1e293b;--text2:#334155;--muted:#64748b;--faint:#94a3b8;--thead:#f8fafc;--detail-bg:#f1f5f9;--bar-bg:#e2e8f0;--accent:#2563eb;--hover:rgba(37,99,235,0.05);--h1:#0f172a;--input-bg:#ffffff; }
  [data-theme="blue"]  { --bg:#0a1628;--bg2:#0f2040;--border:#1e3a5f;--border2:#162e4d;--text:#e2f0ff;--text2:#bcd6f5;--muted:#7aa8d8;--faint:#4e7aa8;--thead:#071120;--detail-bg:#071120;--bar-bg:#071120;--accent:#38bdf8;--hover:rgba(56,189,248,0.07);--h1:#fff;--input-bg:#0f2040; }
  [data-theme="green"] { --bg:#071612;--bg2:#0d2318;--border:#1a4030;--border2:#122e22;--text:#d1fae5;--text2:#a7f3d0;--muted:#6ee7b7;--faint:#34d399;--thead:#051009;--detail-bg:#051009;--bar-bg:#051009;--accent:#10b981;--hover:rgba(16,185,129,0.07);--h1:#ecfdf5;--input-bg:#0d2318; }
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--text);min-height:100vh;transition:background .25s,color .25s}
  .header{background:var(--bg2);border-bottom:1px solid var(--border);padding:1.5rem 2rem}
  .header-inner{max-width:1400px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem}
  .header h1{font-size:1.6rem;font-weight:700;color:var(--h1)}
  .header p{color:var(--muted);margin-top:.3rem;font-size:.875rem}
  .theme-switcher{display:flex;gap:.4rem;align-items:center}
  .theme-switcher span{font-size:.75rem;color:var(--faint);margin-right:.3rem}
  .theme-btn{width:28px;height:28px;border-radius:50%;border:2px solid transparent;cursor:pointer;transition:border-color .2s,transform .15s}
  .theme-btn:hover{transform:scale(1.15)}
  .theme-btn.active{border-color:var(--text)}
  .theme-btn[data-t="dark"] {background:linear-gradient(135deg,#0f1117 50%,#1a1f35 50%)}
  .theme-btn[data-t="light"]{background:linear-gradient(135deg,#f1f5f9 50%,#e2e8f0 50%);border-color:#cbd5e1}
  .theme-btn[data-t="blue"] {background:linear-gradient(135deg,#0a1628 50%,#38bdf8 50%)}
  .theme-btn[data-t="green"]{background:linear-gradient(135deg,#071612 50%,#10b981 50%)}
  .container{max-width:1400px;margin:0 auto;padding:1.5rem 2rem}
  .tabs{display:flex;gap:.5rem;margin-bottom:1.5rem;flex-wrap:wrap}
  .tab{padding:.5rem 1.2rem;border-radius:20px;cursor:pointer;font-size:.85rem;font-weight:600;border:1px solid var(--border);background:var(--bg2);color:var(--muted);transition:all .2s}
  .tab:hover{color:var(--text);border-color:var(--accent)}
  .tab.active{background:var(--accent);border-color:var(--accent);color:#fff}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;margin-bottom:1.5rem}
  .card{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:1.2rem}
  .card-label{font-size:.75rem;color:var(--faint);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.4rem}
  .card-value{font-size:1.4rem;font-weight:700}
  .card-value.green{color:#10b981}.card-value.red{color:#ef4444}.card-value.blue{color:var(--accent)}.card-value.neutral{color:var(--text)}
  .section{display:none}.section.active{display:block}
  .table-wrapper{background:var(--bg2);border:1px solid var(--border);border-radius:12px;overflow:hidden;margin-top:1rem}
  table{width:100%;border-collapse:collapse}
  thead{background:var(--thead)}
  th{padding:.45rem 1rem;text-align:left;font-size:.75rem;color:var(--faint);text-transform:uppercase;letter-spacing:.05em}
  th.right{text-align:right}
  tbody tr{border-top:1px solid var(--border2);transition:background .15s}
  tbody tr:hover{background:var(--hover)}
  td{padding:.35rem 1rem;font-size:.875rem}
  td.right{text-align:right;font-variant-numeric:tabular-nums}
  td.cp-name{font-weight:500;color:var(--text2);max-width:280px}
  td.count{color:var(--muted)}
  td.debit{color:#ef4444}td.credit{color:#10b981}
  td.net-pos{color:#10b981;font-weight:600}td.net-neg{color:#ef4444;font-weight:600}
  td.bar-cell{width:120px}
  .bar-wrap{background:var(--bar-bg);border-radius:4px;height:8px;overflow:hidden}
  .bar{height:8px;border-radius:4px}
  .bar.debit-bar{background:#ef4444}.bar.credit-bar{background:#10b981}
  details{cursor:pointer}
  details summary{list-style:none;display:inline}
  details summary::-webkit-details-marker{display:none}
  details[open] .expand-arrow{display:none}
  .expand-arrow{color:var(--faint);font-size:.75rem;margin-left:4px;user-select:none}
  .detail-inner{background:var(--detail-bg);padding:.75rem 1rem .75rem 2rem}
  .detail-inner table{font-size:.8rem}
  .detail-inner th{font-size:.7rem}
  .tag{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.7rem;font-weight:600;margin-left:4px}
  .tag.income{background:rgba(16,185,129,.15);color:#10b981}
  .tag.expense{background:rgba(239,68,68,.15);color:#ef4444}
  .tag.mixed{background:rgba(59,130,246,.15);color:#3b82f6}
  .charts-row{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.5rem}
  .chart-box{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:1.2rem}
  .chart-box h3{font-size:.8rem;color:var(--faint);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.8rem}
  @media(max-width:700px){.charts-row{grid-template-columns:1fr}.header-inner{flex-direction:column;align-items:flex-start}}
"""

    js = """
function setTheme(t){
  document.documentElement.setAttribute('data-theme',t);
  document.querySelectorAll('.theme-btn').forEach(b=>b.classList.toggle('active',b.dataset.t===t));
}
function showYear(y){
  document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('year-'+y).classList.add('active');
  document.getElementById('tab-'+y).classList.add('active');
}
"""

    ds = date_start[:10].replace('-', '.')
    de = date_end[:10].replace('-', '.')

    return f"""<!DOCTYPE html>
<html lang="de" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UBS Kreditkarten-Analyse</title>
<style>
{css}
</style>
</head>
<body>
<div class="header">
  <div class="header-inner" style="gap:0.8rem;">
    <div>
      <h1>UBS Kreditkarten-Analyse</h1>
      <p>Karte 64744 D 001 &mdash; Zeitraum {ds}&ndash;{de} &mdash; {n_txn} Transaktionen</p>
    </div>
    <div class="theme-switcher">
      <span>Thema:</span>
      <button class="theme-btn active" data-t="dark"  onclick="setTheme('dark')"  title="Dunkel"></button>
      <button class="theme-btn"        data-t="light" onclick="setTheme('light')" title="Hell"></button>
      <button class="theme-btn"        data-t="blue"  onclick="setTheme('blue')"  title="Blau"></button>
      <button class="theme-btn"        data-t="green" onclick="setTheme('green')" title="Grün"></button>
    </div>
  </div>
</div>
<div class="container">
  <div class="tabs" id="tabsContainer">
    {tabs}
  </div>

{"".join(sections)}

</div>
<script>
{js}
</script>
</body>
</html>"""


html = build_html()
with open('kreditkarten_analyse.html', 'w', encoding='utf-8') as f:
    f.write(html)

# Summary
txns_by_year = collections.defaultdict(list)
for txn in TRANSACTIONS:
    txns_by_year[int(txn[0][:4])].append(txn)

print("kreditkarten_analyse.html geschrieben.\n")
for year in sorted(txns_by_year.keys(), reverse=True):
    txns = txns_by_year[year]
    td = round(sum(d for _, _, d, _ in txns), 2)
    tc = round(sum(c for _, _, _, c in txns), 2)
    print(f"  {year}: {len(txns):3d} Txn | Ausgaben CHF {td:8,.2f} | Kartenzahlungen CHF {tc:8,.2f} | Saldo CHF {tc-td:+,.2f}")

td_all = round(sum(d for _, _, d, _ in TRANSACTIONS), 2)
tc_all = round(sum(c for _, _, _, c in TRANSACTIONS), 2)
print(f"\n  Total: Ausgaben CHF {td_all:,.2f} | Kartenzahlungen CHF {tc_all:,.2f} | Saldo CHF {tc_all-td_all:+,.2f}")
print("  (PDF-Gesamt: Belastung CHF 5'260.92, Gutschrift CHF 5'500.65)")
