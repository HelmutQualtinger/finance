#!/usr/bin/env python3
import csv
import re
from collections import defaultdict
from datetime import datetime

# Parse CSV (skip first 9 metadata lines, header on line 10)
transactions = []
with open('ubstrans.csv', encoding='utf-8') as f:
    lines = f.readlines()

# Skip metadata, parse from header line
header_line = 9  # 0-indexed
reader = csv.reader(lines[header_line:], delimiter=';')
headers = next(reader)

for row in reader:
    if len(row) < 11:
        continue
    date_str = row[0].strip()
    debit = row[5].strip()
    credit = row[6].strip()
    desc1 = row[10].strip().strip('"')
    desc2 = row[11].strip().strip('"') if len(row) > 11 else ''
    desc3 = row[12].strip().strip('"') if len(row) > 12 else ''

    if not date_str:
        continue
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except:
        continue

    year = date.year

    # Extract counterparty name (first part before semicolon)
    counterparty = desc1.split(';')[0].strip() if desc1 else 'Unbekannt'

    # Normalize name variants
    ALIASES = {
        'Europaische Patentorganisation':          'Europäische Patentorganisation',
        'EUROPAISCHE PATENTORGANISATION':          'Europäische Patentorganisation',
        'EUROPAEISCHE PATENTORGANISAT ON':         'Europäische Patentorganisation',
        'Strassenverkehrs- und':                   'Strassenverkehrsamt Kanton St. Gallen',
        'Strassenverkehrs- und Sc':                'Strassenverkehrsamt Kanton St. Gallen',
        'Strassenverkehrs- und Schifffahrtsamt Kanton St. Gallen': 'Strassenverkehrsamt Kanton St. Gallen',
        'Schweizerische Mobiliar Vers.':           'Schweizerische Mobiliar',
        'Schweizerische Mobiliar Versicherungsgesellschaft AG': 'Schweizerische Mobiliar',
        'Oviva Ag':                                'Oviva AG',
        'Saldo Dienstleistungspreisabschluss':     'UBS Kontogebühren',
    }
    counterparty = ALIASES.get(counterparty, counterparty)
    if 'Barbezug' in desc1 or desc1 == 'Barbezug':
        counterparty = '_SKIP_'
    if 'Einzahlung' in desc1 and not desc1.startswith('"'):
        counterparty = '_SKIP_'
    if counterparty in ('UBS Altstaetten', 'Herr Harald Beker u/o'):
        counterparty = '_SKIP_'

    amount = 0.0
    if debit:
        try:
            amount = abs(float(debit.replace("'", '')))
        except:
            pass
    if credit:
        try:
            amount = abs(float(credit.replace("'", '')))
        except:
            pass

    is_credit = bool(credit and credit.strip())

    if counterparty == '_SKIP_':
        continue

    transactions.append({
        'date': date,
        'year': year,
        'month': date.strftime('%Y-%m'),
        'counterparty': counterparty,
        'amount': amount,
        'is_credit': is_credit,
        'desc2': desc2,
        'desc3': desc3,
    })

# Group by year and counterparty
by_year_cp = defaultdict(lambda: defaultdict(list))
for t in transactions:
    by_year_cp[t['year']][t['counterparty']].append(t)

years = sorted(by_year_cp.keys(), reverse=True)

# Overall stats per year
year_stats = {}
for year in years:
    total_in = sum(t['amount'] for cp in by_year_cp[year].values() for t in cp if t['is_credit'])
    total_out = sum(t['amount'] for cp in by_year_cp[year].values() for t in cp if not t['is_credit'])
    count = sum(len(cp) for cp in by_year_cp[year].values())
    year_stats[year] = {'in': total_in, 'out': total_out, 'count': count, 'net': total_in - total_out}

# Build HTML
html = '''<!DOCTYPE html>
<html lang="de" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UBS Kontoauszug Analyse</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
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

  /* Month breakdown toggle */
  .expand-btn { cursor: pointer; background: none; border: none; color: var(--faint); font-size: 0.8rem; padding: 0; }
  .expand-btn:hover { color: var(--muted); }
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
  .tag.income { background: rgba(16,185,129,0.15); color: #10b981; }
  .tag.expense { background: rgba(239,68,68,0.15); color: #ef4444; }
  .tag.mixed { background: rgba(59,130,246,0.15); color: #3b82f6; }

  /* Pie charts */
  .charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; }
  .chart-box { background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; padding: 1.2rem; }
  .chart-box h3 { font-size: 0.8rem; color: var(--faint); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.8rem; }
  .chart-box canvas { max-height: 260px; }
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
</head>
<body>
<div class="header">
  <div class="header-inner">
    <div>
      <h1>UBS Kontoauszug Analyse</h1>
      <p>Konto 0225 00807761.05 &mdash; Zeitraum 2024&ndash;2026 &mdash; ''' + str(len(transactions)) + ''' Transaktionen</p>
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
'''

for year in years:
    active = 'active' if year == years[0] else ''
    html += f'    <div class="tab {active}" onclick="showYear({year})" id="tab-{year}">{year}</div>\n'

html += '  </div>\n'

# Generate sections per year
max_out_by_year = {}
for year in years:
    all_cps = by_year_cp[year]
    max_out = max((sum(t['amount'] for t in ts if not t['is_credit']) for ts in all_cps.values()), default=1)
    max_in = max((sum(t['amount'] for t in ts if t['is_credit']) for ts in all_cps.values()), default=1)
    max_out_by_year[year] = {'max_out': max_out or 1, 'max_in': max_in or 1}

for year in years:
    active = 'active' if year == years[0] else ''
    stats = year_stats[year]
    net_class = 'green' if stats['net'] >= 0 else 'red'

    # Sort counterparties by total debit descending
    all_cps = by_year_cp[year]
    cp_list = []
    for cp, ts in all_cps.items():
        total_out = sum(t['amount'] for t in ts if not t['is_credit'])
        total_in = sum(t['amount'] for t in ts if t['is_credit'])
        net = total_in - total_out
        cp_list.append((cp, ts, total_out, total_in, net))
    cp_list.sort(key=lambda x: x[2], reverse=True)

    max_out = max_out_by_year[year]['max_out']
    max_in = max_out_by_year[year]['max_in']

    # Pie chart data: top 8 + Sonstige
    import json
    TOP_N = 8
    pie_colors = ['#3b82f6','#ef4444','#10b981','#f59e0b','#8b5cf6','#ec4899','#06b6d4','#f97316','#84cc16','#64748b']

    out_sorted = sorted([(cp, tot_out) for cp, ts, tot_out, tot_in, net in cp_list if tot_out > 0], key=lambda x: x[1], reverse=True)
    in_sorted  = sorted([(cp, tot_in)  for cp, ts, tot_out, tot_in, net in cp_list if tot_in  > 0], key=lambda x: x[1], reverse=True)

    def make_pie_data(items):
        top = items[:TOP_N]
        rest = items[TOP_N:]
        labels = [cp for cp, _ in top]
        vals   = [round(v, 2) for _, v in top]
        if rest:
            labels.append('Sonstige')
            vals.append(round(sum(v for _, v in rest), 2))
        clrs = pie_colors[:len(labels)]
        if rest: clrs[-1] = '#64748b'
        return json.dumps({'labels': labels, 'data': vals, 'colors': clrs})

    out_pie_json = make_pie_data(out_sorted)
    in_pie_json  = make_pie_data(in_sorted)

    html += f'''
<div class="section {active}" id="year-{year}">
  <div class="cards">
    <div class="card"><div class="card-label">Einnahmen</div><div class="card-value green">CHF {stats["in"]:,.2f}</div></div>
    <div class="card"><div class="card-label">Ausgaben</div><div class="card-value red">CHF {stats["out"]:,.2f}</div></div>
    <div class="card"><div class="card-label">Netto</div><div class="card-value {net_class}">CHF {stats["net"]:+,.2f}</div></div>
    <div class="card"><div class="card-label">Transaktionen</div><div class="card-value neutral">{stats["count"]}</div></div>
    <div class="card"><div class="card-label">Gegenparteien</div><div class="card-value blue">{len(cp_list)}</div></div>
  </div>
  <div class="charts-row">
    <div class="chart-box">
      <h3>Ausgaben nach Gegenpartei</h3>
      <canvas id="pie-out-{year}" data-pie=\'{out_pie_json}\'></canvas>
    </div>
    <div class="chart-box">
      <h3>Einnahmen nach Gegenpartei</h3>
      <canvas id="pie-in-{year}" data-pie=\'{in_pie_json}\'></canvas>
    </div>
  </div>
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
    <tbody>
'''

    for idx, (cp, ts, total_out, total_in, net) in enumerate(cp_list):
        net_class_td = 'net-pos' if net >= 0 else 'net-neg'
        bar_w = int(total_out / max_out * 100) if total_out else 0
        tag = ''
        if total_out > 0 and total_in > 0:
            tag = '<span class="tag mixed">beides</span>'
        elif total_in > 0:
            tag = '<span class="tag income">eingang</span>'
        else:
            tag = '<span class="tag expense">ausgang</span>'

        # Month breakdown
        by_month = defaultdict(lambda: {'out': 0, 'in': 0, 'items': []})
        for t in ts:
            m = t['month']
            if t['is_credit']:
                by_month[m]['in'] += t['amount']
            else:
                by_month[m]['out'] += t['amount']
            by_month[m]['items'].append(t)

        months_html = ''
        for m in sorted(by_month.keys()):
            md = by_month[m]
            out_str = ('-' + '{:,.2f}'.format(md['out'])) if md['out'] else ''
            in_str = '{:,.2f}'.format(md['in']) if md['in'] else ''
            months_html += '<tr><td>{}</td><td class="right debit">{}</td><td class="right credit">{}</td><td>{} Buchg.</td></tr>'.format(m, out_str, in_str, len(md['items']))

        months_table = f'''<div class="detail-inner"><table>
          <thead><tr><th>Monat</th><th class="right">Ausgaben</th><th class="right">Einnahmen</th><th>Anzahl</th></tr></thead>
          <tbody>{months_html}</tbody></table></div>'''

        html += f'''      <tr class="cp-row" data-cp="{cp.lower().replace('"','&quot;')}">
        <td class="cp-name">{cp}{tag}
          <button class="expand-btn" onclick="toggleDetail('d-{year}-{idx}')" title="Details">&#9660;</button>
        </td>
        <td class="right count">{len(ts)}</td>
        <td class="right debit">{f"-{total_out:,.2f}" if total_out else "—"}</td>
        <td class="right credit">{f"{total_in:,.2f}" if total_in else "—"}</td>
        <td class="right {net_class_td}">{net:+,.2f}</td>
        <td class="bar-cell"><div class="bar-wrap"><div class="bar debit-bar" style="width:{bar_w}%"></div></div></td>
      </tr>
      <tr class="detail-row" id="d-{year}-{idx}">
        <td colspan="6">{months_table}</td>
      </tr>
'''

    html += '    </tbody>\n  </table>\n  </div>\n</div>\n'

html += '''
<script>
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
  try { localStorage.setItem('ubs-theme', t); } catch(e) {}
}

// Restore saved theme
(function() {
  try {
    var saved = localStorage.getItem('ubs-theme');
    if (saved) setTheme(saved);
  } catch(e) {}
})();

// Init pie charts
(function() {
  var fmt = function(v) { return 'CHF ' + v.toLocaleString('de-CH', {minimumFractionDigits:2, maximumFractionDigits:2}); };
  document.querySelectorAll('canvas[data-pie]').forEach(function(canvas) {
    var d = JSON.parse(canvas.getAttribute('data-pie'));
    new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: d.labels,
        datasets: [{
          data: d.data,
          backgroundColor: d.colors,
          borderWidth: 0,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'right',
            labels: { color: '#94a3b8', font: { size: 11 }, padding: 10, boxWidth: 12 }
          },
          tooltip: {
            callbacks: {
              label: function(ctx) {
                var total = ctx.dataset.data.reduce(function(a,b){return a+b;},0);
                var pct = (ctx.parsed / total * 100).toFixed(1);
                return ' ' + fmt(ctx.parsed) + ' (' + pct + '%)';
              }
            }
          }
        },
        cutout: '60%'
      }
    });
  });
})();
</script>
</body>
</html>
'''

# ── PDF generieren ──────────────────────────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

PDF_FILE = 'ubstrans_analyse.pdf'
doc = SimpleDocTemplate(PDF_FILE, pagesize=A4,
    leftMargin=1.8*cm, rightMargin=1.8*cm, topMargin=1.8*cm, bottomMargin=1.8*cm)

styles = getSampleStyleSheet()
C_DARK   = colors.HexColor('#1e293b')
C_MUTED  = colors.HexColor('#64748b')
C_GREEN  = colors.HexColor('#059669')
C_RED    = colors.HexColor('#dc2626')
C_ACCENT = colors.HexColor('#2563eb')
C_HEAD   = colors.HexColor('#f1f5f9')
C_ROW    = colors.HexColor('#ffffff')
C_ROW2   = colors.HexColor('#f8fafc')
C_BORDER = colors.HexColor('#e2e8f0')

sTitle  = ParagraphStyle('T', fontSize=16, textColor=C_DARK, spaceAfter=2, fontName='Helvetica-Bold')
sSub    = ParagraphStyle('S', fontSize=9,  textColor=C_MUTED, spaceAfter=10)
sYear   = ParagraphStyle('Y', fontSize=12, textColor=C_ACCENT, spaceBefore=14, spaceAfter=4, fontName='Helvetica-Bold')
sFooter = ParagraphStyle('F', fontSize=7,  textColor=C_MUTED, alignment=TA_CENTER)
sCell   = ParagraphStyle('C', fontSize=8,  textColor=C_DARK,  fontName='Helvetica')
sCellB  = ParagraphStyle('CB', fontSize=8, textColor=C_DARK,  fontName='Helvetica-Bold')

def money(v, sign=False):
    if v == 0: return '—'
    s = '{:,.2f}'.format(abs(v)).replace(',', "'")
    if sign: return ('+' if v >= 0 else '−') + ' ' + s
    return s

def neg(v): return '−' + money(v) if v else '—'

story = []

# Title
story.append(Paragraph('UBS Kontoauszug – Gesamtübersicht', sTitle))
story.append(Paragraph(
    f'Konto 0225 00807761.05  ·  {min(years)}–{max(years)}  ·  {len(transactions)} Transaktionen',
    sSub))
story.append(HRFlowable(width='100%', thickness=0.5, color=C_BORDER, spaceAfter=8))

# ── Jahresübersicht Tabelle ──
sum_data = [['Jahr', 'Einnahmen CHF', 'Ausgaben CHF', 'Netto CHF', 'Buchungen']]
for y in sorted(years):
    s = year_stats[y]
    net_str = ('+' if s['net'] >= 0 else '−') + ' ' + '{:,.2f}'.format(abs(s['net'])).replace(',', "'")
    sum_data.append([
        str(y),
        money(s['in']),
        neg(s['out']),
        net_str,
        str(s['count']),
    ])
# Gesamtzeile
tot_in  = sum(year_stats[y]['in']  for y in years)
tot_out = sum(year_stats[y]['out'] for y in years)
tot_net = tot_in - tot_out
tot_cnt = sum(year_stats[y]['count'] for y in years)
net_str = ('+' if tot_net >= 0 else '−') + ' ' + '{:,.2f}'.format(abs(tot_net)).replace(',', "'")
sum_data.append(['Gesamt', money(tot_in), neg(tot_out), net_str, str(tot_cnt)])

col_w = [2.2*cm, 4*cm, 4*cm, 4*cm, 2.5*cm]
t = Table(sum_data, colWidths=col_w, repeatRows=1)
t.setStyle(TableStyle([
    ('BACKGROUND',  (0,0), (-1,0),  C_ACCENT),
    ('TEXTCOLOR',   (0,0), (-1,0),  colors.white),
    ('FONTNAME',    (0,0), (-1,0),  'Helvetica-Bold'),
    ('FONTSIZE',    (0,0), (-1,-1), 8),
    ('ALIGN',       (1,0), (-1,-1), 'RIGHT'),
    ('ALIGN',       (0,0), (0,-1),  'LEFT'),
    ('ROWBACKGROUNDS', (0,1), (-1,-2), [C_ROW, C_ROW2]),
    ('BACKGROUND',  (0,-1), (-1,-1), colors.HexColor('#dbeafe')),
    ('FONTNAME',    (0,-1), (-1,-1), 'Helvetica-Bold'),
    ('GRID',        (0,0), (-1,-1),  0.3, C_BORDER),
    ('TOPPADDING',  (0,0), (-1,-1), 4),
    ('BOTTOMPADDING',(0,0),(-1,-1), 4),
]))
story.append(t)
story.append(Spacer(1, 14))

# ── Pro Jahr: Gegenpartei-Tabelle ──
all_cp_agg = defaultdict(lambda: {'out': 0, 'in': 0, 'count': 0})
for year in years:
    for cp, ts in by_year_cp[year].items():
        all_cp_agg[cp]['out']   += sum(t['amount'] for t in ts if not t['is_credit'])
        all_cp_agg[cp]['in']    += sum(t['amount'] for t in ts if t['is_credit'])
        all_cp_agg[cp]['count'] += len(ts)

import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from reportlab.platypus import PageBreak, Image

PIE_COLORS = [
    '#3b82f6','#ef4444','#10b981','#f59e0b','#8b5cf6',
    '#06b6d4','#f97316','#ec4899','#84cc16','#6366f1',
    '#14b8a6','#e11d48','#0ea5e9','#a3e635','#d946ef',
]

def make_pie(labels, values, title, width_cm=17):
    """Torte mit Top-N Segmenten, Rest als 'Weitere'. Gibt ReportLab Image zurück."""
    MAX_SEG = 10
    pairs = sorted(zip(values, labels), reverse=True)
    if len(pairs) > MAX_SEG:
        top = pairs[:MAX_SEG]
        rest_val = sum(v for v, _ in pairs[MAX_SEG:])
        top_vals  = [v for v, _ in top]
        top_labels = [l for _, l in top]
        if rest_val > 0:
            top_vals.append(rest_val)
            top_labels.append('Weitere')
    else:
        top_vals  = [v for v, _ in pairs]
        top_labels = [l for _, l in pairs]

    total = sum(top_vals)
    pct_labels = ['{:.1f}%'.format(v / total * 100) for v in top_vals]
    clrs = PIE_COLORS[:len(top_vals)]
    if len(top_vals) > len(PIE_COLORS):
        clrs = (PIE_COLORS * 4)[:len(top_vals)]

    fig, ax = plt.subplots(figsize=(6.5, 3.8), facecolor='white')
    wedges, _ = ax.pie(
        top_vals, colors=clrs, startangle=90,
        wedgeprops=dict(linewidth=0.6, edgecolor='white'),
        pctdistance=0.78,
    )
    ax.set_title(title, fontsize=11, fontweight='bold', pad=8, color='#1e293b')

    legend_labels = ['{} — {} CHF ({})'.format(
        l[:32] + ('…' if len(l) > 32 else ''),
        '{:,.0f}'.format(v).replace(',', "'"),
        p
    ) for l, v, p in zip(top_labels, top_vals, pct_labels)]
    ax.legend(wedges, legend_labels, loc='center left', bbox_to_anchor=(1.01, 0.5),
              fontsize=6.5, frameon=False)

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=160, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    w = width_cm * cm
    img = Image(buf, width=w, height=w * 0.55)
    return img

from reportlab.platypus import PageBreak

for year in sorted(years):
    story.append(PageBreak())
    story.append(Paragraph(str(year), sYear))
    story.append(HRFlowable(width='100%', thickness=0.3, color=C_BORDER, spaceAfter=6))

    cp_list_pdf = []
    for cp, ts in by_year_cp[year].items():
        out = sum(t['amount'] for t in ts if not t['is_credit'])
        inc = sum(t['amount'] for t in ts if t['is_credit'])
        cp_list_pdf.append((cp, len(ts), out, inc, inc - out))
    cp_list_pdf.sort(key=lambda x: x[2], reverse=True)

    # ── Tortengrafiken nebeneinander ──
    out_items = [(cp, out) for cp, _, out, _, _ in cp_list_pdf if out > 0]
    inc_items = [(cp, inc) for cp, _, _, inc, _ in cp_list_pdf if inc > 0]

    charts = []
    if out_items:
        charts.append(make_pie([l for l,_ in out_items], [v for _,v in out_items],
                               f'Ausgaben {year}', width_cm=8.2))
    if inc_items:
        charts.append(make_pie([l for l,_ in inc_items], [v for _,v in inc_items],
                               f'Einnahmen {year}', width_cm=8.2))

    if len(charts) == 2:
        story.append(Table([[charts[0], charts[1]]],
                           colWidths=[9*cm, 9*cm]))
    elif charts:
        story.append(charts[0])

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width='100%', thickness=0.3, color=C_BORDER, spaceAfter=4))

    rows = [['Gegenpartei', 'N', 'Ausgaben CHF', 'Einnahmen CHF', 'Netto CHF']]
    for cp, cnt, out, inc, net in cp_list_pdf:
        net_str = ('+' if net >= 0 else '−') + '{:,.2f}'.format(abs(net)).replace(',', "'")
        rows.append([
            Paragraph(cp, sCell),
            str(cnt),
            neg(out),
            money(inc) if inc else '—',
            net_str,
        ])

    cw = [7.5*cm, 1*cm, 3.3*cm, 3.3*cm, 3.3*cm]
    tbl = Table(rows, colWidths=cw, repeatRows=1)
    net_col_styles = []
    for i, (_, _, _, _, net) in enumerate(cp_list_pdf, start=1):
        c = C_GREEN if net >= 0 else C_RED
        net_col_styles.append(('TEXTCOLOR', (4, i), (4, i), c))

    tbl.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,0),  colors.HexColor('#334155')),
        ('TEXTCOLOR',   (0,0), (-1,0),  colors.white),
        ('FONTNAME',    (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,-1), 7.5),
        ('ALIGN',       (1,0), (-1,-1), 'RIGHT'),
        ('ALIGN',       (0,0), (0,-1),  'LEFT'),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [C_ROW, C_ROW2]),
        ('GRID',        (0,0), (-1,-1),  0.3, C_BORDER),
        ('TOPPADDING',  (0,0), (-1,-1), 3),
        ('BOTTOMPADDING',(0,0),(-1,-1), 3),
        ('TEXTCOLOR',   (2,1), (2,-1),  C_RED),
        ('TEXTCOLOR',   (3,1), (3,-1),  C_GREEN),
        *net_col_styles,
    ]))
    story.append(tbl)

story.append(Spacer(1, 20))
story.append(HRFlowable(width='100%', thickness=0.3, color=C_BORDER, spaceAfter=4))
story.append(Paragraph('Generiert aus UBS Kontoauszug · Eigenübertäge ausgeblendet', sFooter))

doc.build(story)

# ── PDF-Link ins HTML einfügen ──
html = html.replace(
    '<div class="header-inner">',
    '<div class="header-inner" style="gap:0.8rem;">'
)
html = html.replace(
    '</div>\n</div>\n<div class="container">',
    '''  <a href="ubstrans_analyse.pdf" class="pdf-link" title="PDF öffnen / drucken" download>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:5px;vertical-align:-2px"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
      Drucken / PDF
    </a>
</div>
</div>
<div class="container">'''
)
html = html.replace(
    '.theme-switcher span {',
    '''.pdf-link { display:inline-flex; align-items:center; padding:0.45rem 1rem;
    background:var(--accent); color:#fff; border-radius:8px; text-decoration:none;
    font-size:0.8rem; font-weight:600; transition:opacity 0.2s; white-space:nowrap; }
  .pdf-link:hover { opacity:0.85; }
  .theme-switcher span {'''
)

with open('ubstrans_analyse.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Fertig! {len(transactions)} Transaktionen, {len(years)} Jahre: {years}")
for y in years:
    s = year_stats[y]
    print(f"  {y}: +{s['in']:,.2f} / -{s['out']:,.2f} / Netto {s['net']:+,.2f} CHF ({s['count']} Buchungen)")