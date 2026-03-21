#!/usr/bin/env python3
"""build_sskm_analyse.py — Stadtsparkasse München Kontoauszug-Analyse (SSKM-23-26.html)"""
import math, collections, re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

# ── Parse HTML ────────────────────────────────────────────────────────────────
HTML_FILE = 'SSKM-23-26.html'

print(f"Parsing {HTML_FILE} …")
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

transactions = []
divs = soup.find_all('div', id=re.compile(r'^u_\d+$'))
print(f"  Found {len(divs)} transaction divs")

for div in divs:
    # Payee
    h3 = div.find('h3', class_='nbf-box__title')
    payee = h3.get_text(strip=True) if h3 else ''

    # Reference + date | type
    subtitle = div.find('div', class_='nbf-box__subtitle')
    ref_raw = ''
    txn_type = ''
    if subtitle:
        full = subtitle.get_text(separator=' | ', strip=True)
        parts = [p.strip() for p in full.split('|')]
        # last part is often the type
        if len(parts) >= 2:
            ref_raw = ' | '.join(parts[:-1])
            txn_type = parts[-1].upper()
        else:
            ref_raw = full
            txn_type = ''

    # Booking date
    date_div = div.find('div', class_=lambda c: c and 'buchung' in c)
    booking_date = None
    if date_div:
        txt = date_div.get_text(strip=True)
        m = re.search(r'(\d{2}\.\d{2}\.\d{4})', txt)
        if m:
            try:
                booking_date = datetime.strptime(m.group(1), '%d.%m.%Y')
            except ValueError:
                pass

    if booking_date is None:
        # fallback: search reference for date
        m = re.search(r'(\d{2}\.\d{2}\.\d{4})', ref_raw)
        if m:
            try:
                booking_date = datetime.strptime(m.group(1), '%d.%m.%Y')
            except ValueError:
                booking_date = datetime(2023, 1, 1)
        else:
            booking_date = datetime(2023, 1, 1)

    # Amount sign: plus = income, minus = expense
    int_plus  = div.find('span', class_=lambda c: c and 'balance-predecimal' in c and 'plus' in c)
    dec_plus  = div.find('span', class_=lambda c: c and 'balance-decimal' in c and 'plus' in c)
    int_minus = div.find('span', class_=lambda c: c and 'balance-predecimal' in c and 'minus' in c)
    dec_minus = div.find('span', class_=lambda c: c and 'balance-decimal' in c and 'minus' in c)

    amount = 0.0
    if int_plus:
        int_str = re.sub(r'[^\d]', '', int_plus.get_text(strip=True))
        dec_str = '00'
        if dec_plus:
            dec_str = re.sub(r'[^\d]', '', dec_plus.get_text(strip=True))[:2]
        try:
            amount = float(f"{int_str}.{dec_str}")
        except ValueError:
            amount = 0.0
    elif int_minus:
        int_str = re.sub(r'[^\d]', '', int_minus.get_text(strip=True))
        dec_str = '00'
        if dec_minus:
            dec_str = re.sub(r'[^\d]', '', dec_minus.get_text(strip=True))[:2]
        try:
            amount = -float(f"{int_str}.{dec_str}")
        except ValueError:
            amount = 0.0

    transactions.append({
        'date': booking_date,
        'year': booking_date.year,
        'month': booking_date.strftime('%Y-%m'),
        'payee': payee,
        'type': txn_type,
        'reference': ref_raw,
        'amount': amount,
    })

print(f"  Parsed {len(transactions)} transactions")

# Remove own-account transfers (payee = Harald Beker himself)
before = len(transactions)
transactions = [
    t for t in transactions
    if not re.match(r'(?i)(Harald\s+Beker|Beker,\s*Harald)', t['payee'])
]
print(f"  Removed {before - len(transactions)} own-account transfers (Harald Beker)")

# Normalize Cigna payee variants → single canonical name
for txn in transactions:
    if txn['payee'].upper().startswith('CIGNA'):
        txn['payee'] = 'CIGNA INTERNATIONAL HEALTH'

# ── Categorize ────────────────────────────────────────────────────────────────
EXPENSE_CATEGORIES = [
    ('Lebensmittel', [
        'ALDI', 'LIDL', 'REWE', 'EDEKA', 'NETTO', 'PENNY', 'KAUFLAND',
        'BILLA', 'SUPERMARKT', 'MARKT', 'NORMA', 'TEGUT', 'REAL',
        'DENN', 'BIO', 'METZGER', 'BAECKER', 'BÄCKER', 'BECK', 'BIOMARKT',
        'SPAR ', 'INTERSPAR', 'LEBENSMITTEL',
    ]),
    ('Restaurant/Cafe', [
        'RESTAURANT', 'CAFE', 'CAFÉ', 'GASTHAUS', 'WIRTSHAUS', 'MCDONALD',
        'BURGER', 'PIZZA', 'SUBWAY', 'STARBUCKS', 'BAR ', 'IMBISS',
        'GASTSTÄTTE', 'BISTRO', 'BRASSERIE', 'CURRYWURST', 'DÖNER',
        'SUSHI', 'CHINA', 'THAI', 'TAPAS', 'TRATTORIA', 'OSTERIA',
        'EISCAFE', 'EISDIELE', 'KONDITOREI', 'BÄCKEREI',
    ]),
    ('Verkehr/Transport', [
        'TANK', 'SHELL', 'ARAL', 'OMV', 'ESSO', 'TOTAL ', 'AGIP', 'JET ',
        'DB BAHN', 'DEUTSCHE BAHN', 'DB ', 'MVGO', 'MVV', 'FLIXBUS',
        'RYANAIR', 'LUFTHANSA', 'EASYJET', 'EUROWINGS', 'WIZZ',
        'ÖPNV', 'OPNV', 'PARKHAUS', 'PARKEN', 'PARKING',
        'TAXI', 'UBER', 'SIXT', 'HERTZ', 'EUROPCAR',
        'BAHN', 'FLUGHAFEN', 'AIRPORT',
    ]),
    ('Wohnen', [
        'MIETE', 'NEBENKOSTEN', 'HAUSGELD', 'HAUSMEISTER',
        'STADTWERKE', 'ENERGI', 'STROM', 'GAS ', 'WASSER',
        'VERSICHERUNG', 'ALLIANZ', 'ERGO', 'HUK', 'ARAG', 'DEVK',
        'HAUSRAT', 'HAFTPFLICHT', 'KFZVERSICH',
        'VODAFONE', 'TELEKOM', 'O2', '1&1', 'UNITYMEDIA', 'INTERNET',
        'RUNDFUNK', 'GEZ', 'ARD ZDF', 'BEITRAGSSERVICE',
    ]),
    ('Gesundheit', [
        'APOTHEKE', 'ARZT', 'ZAHNARZT', 'KRANKENHAUS', 'KLINIK',
        'AOK', ' TK ', 'KRANKENKASSE', 'OPTIKER', 'AUGENARZT',
        'PHYSIOTHERAP', 'HEILPRAKT', 'LABOR ', 'SANITÄTS',
        'BARMER', 'DAK', 'BKK', 'IKK',
    ]),
    ('Shopping', [
        'AMAZON', 'ZALANDO', 'H&M', 'ZARA', 'OTTO ', 'EBAY',
        'SHOP ', 'KAUFHOF', 'GALERIA', 'C&A', 'PRIMARK', 'KODI',
        'TCHIBO', 'IKEA', 'SATURN', 'MEDIAMARKT', 'EXPERT ',
        'DOUGLAS', 'DM ', 'ROSSMANN', 'MÜLLER', 'DEPOT ',
    ]),
    ('Freizeit', [
        'KINO', 'THEATER', 'MUSEUM', 'SPORT', 'FITNESS', 'FITNESSSTUDIO',
        'CLUB', 'HOTEL', 'AIRBNB', 'BOOKING', 'HOLIDAY', 'URLAUB',
        'SCHWIMMBAD', 'FREIBAD', 'HALLENBAD', 'GYM',
        'SPOTIFY', 'NETFLIX', 'AMAZON PRIME', 'DISNEY',
        'BÜCHEREI', 'BIBLIOTHEK',
    ]),
    ('Sparen/Investments', [
        'SPARKASSE', 'TAGESGELD', 'FESTGELD', 'ETF', 'FONDS', 'DEPOT',
        'DKB', 'ING ', 'COMDIRECT', 'FLATEX', 'TRADE REPUBLIC',
        'CONSORSBANK', 'ÜBERWEISUNG SPAR', 'SPARBUCH',
    ]),
]

INCOME_CATEGORIES = [
    ('Gehalt/Rente', [
        'GEHALT', 'LOHN', 'PENSION', 'RENTE', 'BEZÜGE',
        'ARBEITGEBER', 'VERGÜTUNG', 'HONORAR',
    ]),
    ('Zinsen/Dividenden', [
        'ZINSEN', 'HABENZINS', 'DIVIDENDE', 'AUSSCHÜTTUNG',
        'ZINSGUTSCHRIFT', 'ZINSABSCHLUSS',
    ]),
    ('Krankenkasse', [
        'CIGNA', 'ERSTATTUNG VON KRANKHEITSKOSTEN',
    ]),
    ('Steuer/Soziales', [
        'STEUERERSTATTUNG', 'FINANZAMT', 'KINDERGELD', 'ELTERNGELD',
        'WOHNGELD', 'SOZIAL', 'JOBCENTER', 'ARBEITSAMT',
        'KRANKENGELD', 'RENTENVERSICHERUNG', 'ERSTATTUNG',
    ]),
]

TYPE_TO_CAT = {
    'LOHN/GEHALT': 'Gehalt/Rente',
    'GEHALT': 'Gehalt/Rente',
    'RENTE': 'Gehalt/Rente',
    'PENSION': 'Gehalt/Rente',
    'ZINSEN': 'Zinsen/Dividenden',
    'HABENZINSEN': 'Zinsen/Dividenden',
    'ZINSABSCHLUSS': 'Zinsen/Dividenden',
    'STEUERERSTATTUNG': 'Steuer/Soziales',
    'KINDERGELD': 'Steuer/Soziales',
}

def categorize(txn):
    amount = txn['amount']
    payee_up = txn['payee'].upper()
    type_up = txn['type'].upper()
    ref_up = txn['reference'].upper()
    search_str = payee_up + ' ' + type_up + ' ' + ref_up

    if amount > 0:
        # Income
        # Check type first
        for kw, cat in TYPE_TO_CAT.items():
            if kw in type_up:
                return cat
        # Check keyword lists
        for cat, keywords in INCOME_CATEGORIES:
            for kw in keywords:
                if kw in search_str:
                    return cat
        return 'Sonstige Einnahmen'
    else:
        # Expense
        for cat, keywords in EXPENSE_CATEGORIES:
            for kw in keywords:
                if kw in search_str:
                    return cat
        return 'Sonstiges'

for txn in transactions:
    txn['category'] = categorize(txn)

# ── Helpers ───────────────────────────────────────────────────────────────────
PIE_COLORS = [
    '#3b82f6','#ef4444','#10b981','#f59e0b','#8b5cf6',
    '#ec4899','#06b6d4','#f97316','#84cc16','#64748b',
    '#a855f7','#14b8a6','#fb923c','#facc15','#4ade80',
]

MONTH_DE = {
    1:'Januar',2:'Februar',3:'März',4:'April',5:'Mai',6:'Juni',
    7:'Juli',8:'August',9:'September',10:'Oktober',11:'November',12:'Dezember'
}

def fmt(v):
    s = f"{abs(v):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return s

def fmt_eur(v):
    return f"{'−' if v < 0 else ''}{fmt(abs(v))} €"

def make_pie_svg(items, currency='EUR'):
    TOP_N = 10
    items = [(lbl, v) for lbl, v in items if v > 0]
    if not items:
        return '<svg viewBox="0 0 340 60"><text x="170" y="35" text-anchor="middle" font-size="12" fill="#94a3b8">Keine Daten</text></svg>'
    items = sorted(items, key=lambda x: x[1], reverse=True)
    top  = items[:TOP_N]
    rest = items[TOP_N:]
    labels = [lbl for lbl, _ in top]
    vals   = [v   for _, v   in top]
    if rest:
        labels.append('Sonstige')
        vals.append(round(sum(v for _, v in rest), 2))
    total = sum(vals)
    if total <= 0:
        return '<svg viewBox="0 0 340 60"><text x="170" y="35" text-anchor="middle" font-size="12" fill="#94a3b8">Keine Daten</text></svg>'
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
            path = (
                f'<path d="M {cx} {cy-r:.2f} A {r} {r} 0 1 1 {cx} {cy+r:.2f} '
                f'A {r} {r} 0 1 1 {cx} {cy-r:.2f} '
                f'L {cx} {cy-ri:.2f} A {ri} {ri} 0 1 0 {cx} {cy+ri:.2f} '
                f'A {ri} {ri} 0 1 0 {cx} {cy-ri:.2f} Z" '
                f'fill="{colors[i]}" stroke="var(--bg2)" stroke-width="1.5">'
                f'<title>{lbl}: {fmt(v)} € (100.0%)</title></path>'
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
                f'<title>{lbl}: {fmt(v)} € ({pct*100:.1f}%)</title></path>'
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


# ── Group transactions ────────────────────────────────────────────────────────
def filter_txns(txns, year=None):
    if year is None:
        return txns
    return [t for t in txns if t['year'] == year]

def build_year_section(year, txns):
    income_txns  = [t for t in txns if t['amount'] > 0]
    expense_txns = [t for t in txns if t['amount'] < 0]

    total_income  = round(sum(t['amount'] for t in income_txns), 2)
    total_expense = round(sum(t['amount'] for t in expense_txns), 2)  # negative
    saldo = round(total_income + total_expense, 2)

    n_txn = len(txns)

    # Category aggregation
    cat_expense = collections.defaultdict(float)
    cat_income  = collections.defaultdict(float)
    for t in expense_txns:
        cat_expense[t['category']] += abs(t['amount'])
    for t in income_txns:
        cat_income[t['category']] += t['amount']

    # Summary cards
    saldo_cls  = 'green' if saldo >= 0 else 'red'
    saldo_sign = '+' if saldo >= 0 else ''
    cards = f"""
  <div class="cards">
    <div class="card"><div class="card-label">Einnahmen</div><div class="card-value green">{fmt(total_income)} €</div></div>
    <div class="card"><div class="card-label">Ausgaben</div><div class="card-value red">{fmt(abs(total_expense))} €</div></div>
    <div class="card"><div class="card-label">Saldo</div><div class="card-value {saldo_cls}">{saldo_sign}{fmt(saldo)} €</div></div>
    <div class="card"><div class="card-label">Transaktionen</div><div class="card-value neutral">{n_txn}</div></div>
  </div>"""

    # Pie charts
    expense_items = sorted(cat_expense.items(), key=lambda x: x[1], reverse=True)
    income_items  = sorted(cat_income.items(),  key=lambda x: x[1], reverse=True)
    pie_expense = make_pie_svg(expense_items)
    pie_income  = make_pie_svg(income_items)

    pie_section = f"""
  <div class="charts-row">
    <div class="chart-box"><h3>Ausgaben nach Kategorie</h3>{pie_expense}</div>
    <div class="chart-box"><h3>Einnahmen nach Kategorie</h3>{pie_income}</div>
  </div>"""

    # ── Category accordion (expenses) ──────────────────────────────────────────
    def make_txn_rows_html(t_list):
        rows = ''
        for t in sorted(t_list, key=lambda x: x['date']):
            cls = 'credit' if t['amount'] >= 0 else 'debit'
            sign = '+' if t['amount'] >= 0 else ''
            ref_d = t['reference'][:60] + ('…' if len(t['reference']) > 60 else '')
            rows += (f'<tr>'
                     f'<td style="padding-left:2rem">{t["date"].strftime("%d.%m.%Y")}</td>'
                     f'<td class="txn-type">{t["type"]}</td>'
                     f'<td class="txn-ref" title="{t["reference"]}">{ref_d}</td>'
                     f'<td class="right {cls}">{sign}{fmt(t["amount"])} €</td>'
                     f'</tr>\n')
        return rows

    def make_cat_accordion(cat_txns_list, is_income):
        html = '<div class="cat-accordion">'
        for cat, total in sorted(cat_txns_list, key=lambda x: x[1], reverse=True):
            sign = '+' if is_income else '−'
            cls = 'credit' if is_income else 'debit'
            t_list = [t for t in (income_txns if is_income else expense_txns) if t['category'] == cat]
            cnt = len(t_list)
            # Group by payee within category
            payee_map = collections.defaultdict(list)
            for t in t_list:
                payee_map[t['payee']].append(t)

            payee_html = ''
            for payee, p_txns in sorted(payee_map.items(), key=lambda x: abs(sum(t['amount'] for t in x[1])), reverse=True):
                p_total = sum(t['amount'] for t in p_txns)
                p_sign = '+' if p_total >= 0 else '−'
                p_cls = 'credit' if p_total >= 0 else 'debit'
                p_cnt = len(p_txns)
                txn_rows = make_txn_rows_html(p_txns)
                payee_html += f"""<details class="payee-details">
  <summary class="payee-summary">
    <span class="pd-name">{payee[:55]}</span>
    <span class="pd-count">{p_cnt} Buchungen</span>
    <span class="pd-amt {p_cls}">{p_sign}{fmt(abs(p_total))} €</span>
  </summary>
  <div class="payee-txn-wrap"><table>
    <thead><tr><th>Datum</th><th>Typ</th><th>Referenz</th><th class="right">Betrag</th></tr></thead>
    <tbody>{txn_rows}</tbody>
  </table></div>
</details>"""

            html += f"""<details class="cat-details">
  <summary class="cat-summary">
    <span class="cd-name">{cat}</span>
    <span class="cd-count">{cnt}</span>
    <span class="cd-amt {cls}">{sign}{fmt(abs(total))} €</span>
  </summary>
  <div class="cat-payee-list">{payee_html}</div>
</details>"""
        html += '</div>'
        return html

    exp_accordion = make_cat_accordion(cat_expense.items(), is_income=False)
    inc_accordion = make_cat_accordion(cat_income.items(), is_income=True)

    cat_tables = f"""
  <div class="charts-row" style="grid-template-columns:1fr 1fr">
    <div class="table-wrapper" style="margin-top:0">
      <div style="padding:.8rem 1rem;font-size:.8rem;font-weight:600;color:var(--faint);text-transform:uppercase;letter-spacing:.05em">Ausgaben nach Kategorie</div>
      <div style="padding:.5rem .5rem .5rem .5rem">{exp_accordion}</div>
    </div>
    <div class="table-wrapper" style="margin-top:0">
      <div style="padding:.8rem 1rem;font-size:.8rem;font-weight:600;color:var(--faint);text-transform:uppercase;letter-spacing:.05em">Einnahmen nach Kategorie</div>
      <div style="padding:.5rem .5rem .5rem .5rem">{inc_accordion}</div>
    </div>
  </div>"""

    # Top 20 payees
    payee_totals = collections.defaultdict(float)
    payee_counts = collections.defaultdict(int)
    for t in txns:
        payee_totals[t['payee']] += t['amount']
        payee_counts[t['payee']] += 1

    top20 = sorted(payee_totals.items(), key=lambda x: abs(x[1]), reverse=True)[:20]
    top20_rows = ''
    for payee, net in top20:
        cnt = payee_counts[payee]
        cls = 'credit' if net >= 0 else 'debit'
        sign = '+' if net >= 0 else ''
        p_txns = sorted([t for t in txns if t['payee'] == payee], key=lambda t: t['date'])
        txn_rows = ''
        for t in p_txns:
            tc = 'credit' if t['amount'] >= 0 else 'debit'
            ts = '+' if t['amount'] >= 0 else ''
            ref_d = t['reference'][:60] + ('…' if len(t['reference']) > 60 else '')
            txn_rows += (f'<tr>'
                         f'<td style="padding-left:1.5rem">{t["date"].strftime("%d.%m.%Y")}</td>'
                         f'<td class="txn-type">{t["type"]}</td>'
                         f'<td class="txn-ref" title="{t["reference"]}">{ref_d}</td>'
                         f'<td>{t["category"]}</td>'
                         f'<td class="right {tc}">{ts}{fmt(t["amount"])} €</td>'
                         f'</tr>\n')
        top20_rows += f"""<details class="payee-details top20-details">
  <summary class="payee-summary">
    <span class="pd-name" style="min-width:260px">{payee[:55]}</span>
    <span class="pd-count">{cnt} Buchungen</span>
    <span class="pd-amt {cls}">{sign}{fmt(abs(net))} €</span>
  </summary>
  <div class="payee-txn-wrap"><table>
    <thead><tr><th>Datum</th><th>Typ</th><th>Referenz</th><th>Kategorie</th><th class="right">Betrag</th></tr></thead>
    <tbody>{txn_rows}</tbody>
  </table></div>
</details>"""

    top20_table = f"""
  <div class="table-wrapper">
    <div style="padding:.8rem 1rem;font-size:.8rem;font-weight:600;color:var(--faint);text-transform:uppercase;letter-spacing:.05em">Top 20 Empfänger/Auftraggeber (nach Betrag)</div>
    <div style="padding:.5rem">{top20_rows}</div>
  </div>"""

    # Monthly collapsible sections
    months = sorted(set(t['month'] for t in txns))
    month_sections = []
    for month in months:
        m_txns = [t for t in txns if t['month'] == month]
        m_txns_sorted = sorted(m_txns, key=lambda t: t['date'])
        m_income  = round(sum(t['amount'] for t in m_txns if t['amount'] > 0), 2)
        m_expense = round(sum(t['amount'] for t in m_txns if t['amount'] < 0), 2)
        m_saldo   = round(m_income + m_expense, 2)
        yr, mo = month.split('-')
        month_label = f"{MONTH_DE[int(mo)]} {yr}"

        rows_html = ''
        for t in m_txns_sorted:
            cls = 'credit' if t['amount'] >= 0 else 'debit'
            sign = '+' if t['amount'] >= 0 else ''
            payee_display = t['payee'][:50] + ('…' if len(t['payee']) > 50 else '')
            ref_display = t['reference'][:60] + ('…' if len(t['reference']) > 60 else '')
            rows_html += (
                f'<tr>'
                f'<td>{t["date"].strftime("%d.%m.%Y")}</td>'
                f'<td class="payee-name">{payee_display}</td>'
                f'<td class="txn-type">{t["type"]}</td>'
                f'<td class="txn-ref">{ref_display}</td>'
                f'<td>{t["category"]}</td>'
                f'<td class="right {cls}">{sign}{fmt(t["amount"])} €</td>'
                f'</tr>\n'
            )

        saldo_cls2 = 'green' if m_saldo >= 0 else 'red'
        month_sections.append(f"""
  <details class="month-details">
    <summary>
      <span class="month-label">{month_label}</span>
      <span class="month-stats">
        <span class="credit">+{fmt(m_income)} €</span>
        <span class="debit">−{fmt(abs(m_expense))} €</span>
        <span class="{saldo_cls2}">Saldo: {"+" if m_saldo >= 0 else ""}{fmt(m_saldo)} €</span>
        <span class="muted-count">{len(m_txns)} Buchungen</span>
      </span>
      <span class="expand-arrow">&#9660;</span>
    </summary>
    <div class="month-table-wrap">
      <table>
        <thead><tr>
          <th>Datum</th><th>Empfänger/Auftraggeber</th><th>Typ</th><th>Referenz</th><th>Kategorie</th><th class="right">Betrag</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
  </details>""")

    monthly_section = f"""
  <div class="section-header">Monatliche Buchungen</div>
  {"".join(month_sections)}"""

    return cards + pie_section + '\n' + cat_tables + '\n' + top20_table + '\n' + monthly_section


def build_html(transactions):
    years_in_data = sorted(set(t['year'] for t in transactions))
    all_years = years_in_data + ['Gesamt']

    tabs = ''.join(
        f'<div class="tab{" active" if i==0 else ""}" onclick="showYear(\'{y}\')" id="tab-{y}">{y}</div>'
        for i, y in enumerate(all_years)
    )

    sections = []
    for i, year in enumerate(all_years):
        active = ' active' if i == 0 else ''
        if year == 'Gesamt':
            body = build_year_section('Gesamt', transactions)
        else:
            body = build_year_section(year, [t for t in transactions if t['year'] == year])
        sections.append(f'<div class="section{active}" id="year-{year}">\n{body}\n</div>')

    date_start = min(t['date'] for t in transactions).strftime('%d.%m.%Y')
    date_end   = max(t['date'] for t in transactions).strftime('%d.%m.%Y')
    n_txn = len(transactions)

    css = """
  [data-theme="dark"]    { --bg:#0f1117;--bg2:#1a1f35;--border:#2d3748;--border2:#1e2a3a;--text:#e2e8f0;--text2:#cbd5e1;--muted:#94a3b8;--faint:#64748b;--thead:#0f1117;--detail-bg:#0f1117;--bar-bg:#0f1117;--accent:#3b82f6;--hover:rgba(59,130,246,0.06);--h1:#fff;--input-bg:#1a1f35; }
  [data-theme="light"]   { --bg:#f1f5f9;--bg2:#ffffff;--border:#e2e8f0;--border2:#e2e8f0;--text:#1e293b;--text2:#334155;--muted:#64748b;--faint:#94a3b8;--thead:#f8fafc;--detail-bg:#f1f5f9;--bar-bg:#e2e8f0;--accent:#2563eb;--hover:rgba(37,99,235,0.05);--h1:#0f172a;--input-bg:#ffffff; }
  [data-theme="sepia"]   { --bg:#f5f0e8;--bg2:#fffdf5;--border:#d4c5a9;--border2:#e8ddc8;--text:#3d2b1f;--text2:#5c3d2a;--muted:#8b6b4a;--faint:#b08c6a;--thead:#ede5d8;--detail-bg:#f0ead8;--bar-bg:#e8ddc8;--accent:#8b5e3c;--hover:rgba(139,94,60,0.05);--h1:#2c1810;--input-bg:#fffdf5; }
  [data-theme="contrast"]{ --bg:#000000;--bg2:#0a0a0a;--border:#ffff00;--border2:#888800;--text:#ffffff;--text2:#ffff00;--muted:#ffff88;--faint:#aaaaaa;--thead:#000000;--detail-bg:#000000;--bar-bg:#000000;--accent:#00ffff;--hover:rgba(0,255,255,0.08);--h1:#ffffff;--input-bg:#111111; }
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
  .theme-btn[data-t="dark"]    {background:linear-gradient(135deg,#0f1117 50%,#1a1f35 50%)}
  .theme-btn[data-t="light"]   {background:linear-gradient(135deg,#f1f5f9 50%,#e2e8f0 50%);border-color:#cbd5e1}
  .theme-btn[data-t="sepia"]   {background:linear-gradient(135deg,#f5f0e8 50%,#8b5e3c 50%)}
  .theme-btn[data-t="contrast"]{background:linear-gradient(135deg,#000000 50%,#ffff00 50%)}
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
  .section-header{font-size:.85rem;font-weight:700;color:var(--faint);text-transform:uppercase;letter-spacing:.08em;margin:1.5rem 0 .75rem}
  .table-wrapper{background:var(--bg2);border:1px solid var(--border);border-radius:12px;overflow:hidden;margin-top:1rem}
  table{width:100%;border-collapse:collapse}
  thead{background:var(--thead)}
  th{padding:.45rem 1rem;text-align:left;font-size:.75rem;color:var(--faint);text-transform:uppercase;letter-spacing:.05em}
  th.right{text-align:right}
  tbody tr{border-top:1px solid var(--border2);transition:background .15s}
  tbody tr:hover{background:var(--hover)}
  td{padding:.35rem 1rem;font-size:.875rem}
  td.right{text-align:right;font-variant-numeric:tabular-nums}
  td.payee-name{font-weight:500;color:var(--text2);max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  td.txn-type{font-size:.75rem;color:var(--muted);white-space:nowrap}
  td.txn-ref{font-size:.75rem;color:var(--faint);max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  td.debit{color:#ef4444}td.credit{color:#10b981}
  .charts-row{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.5rem}
  .chart-box{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:1.2rem}
  .chart-box h3{font-size:.8rem;color:var(--faint);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.8rem}
  .month-details{background:var(--bg2);border:1px solid var(--border);border-radius:10px;margin-bottom:.5rem;overflow:hidden}
  .month-details summary{display:flex;align-items:center;gap:1rem;padding:.75rem 1rem;cursor:pointer;list-style:none;flex-wrap:wrap}
  .month-details summary::-webkit-details-marker{display:none}
  .month-label{font-weight:600;font-size:.9rem;min-width:140px}
  .month-stats{display:flex;gap:1rem;font-size:.82rem;flex-wrap:wrap}
  .month-stats .credit{color:#10b981;font-weight:600}
  .month-stats .debit{color:#ef4444;font-weight:600}
  .month-stats .green{color:#10b981;font-weight:700}
  .month-stats .red{color:#ef4444;font-weight:700}
  .month-stats .muted-count{color:var(--muted)}
  .expand-arrow{color:var(--faint);font-size:.75rem;margin-left:auto;user-select:none}
  details[open] .expand-arrow{display:none}
  .month-table-wrap{border-top:1px solid var(--border);overflow-x:auto}
  .pdf-link{display:inline-flex;align-items:center;padding:.45rem 1rem;background:var(--accent);color:#fff;border-radius:8px;text-decoration:none;font-size:.8rem;font-weight:600;transition:opacity .2s;white-space:nowrap}
  .pdf-link:hover{opacity:.85}
  /* Category & Payee accordions */
  .cat-accordion{display:flex;flex-direction:column;gap:.3rem}
  .cat-details,.payee-details{border-radius:8px;overflow:hidden;border:1px solid var(--border2)}
  .cat-summary{display:flex;align-items:center;gap:.6rem;padding:.55rem .8rem;cursor:pointer;list-style:none;background:var(--bg);transition:background .15s}
  .cat-summary::-webkit-details-marker{display:none}
  .cat-summary:hover{background:var(--hover)}
  .cd-name{flex:1;font-weight:600;font-size:.85rem}
  .cd-count{font-size:.75rem;color:var(--muted);min-width:3rem;text-align:right}
  .cd-amt{font-weight:700;font-size:.9rem;min-width:90px;text-align:right}
  .cat-payee-list{padding:.4rem .4rem .4rem 1rem;display:flex;flex-direction:column;gap:.25rem;background:var(--detail-bg)}
  .payee-details{border-color:var(--border2)}
  .payee-summary{display:flex;align-items:center;gap:.6rem;padding:.4rem .7rem;cursor:pointer;list-style:none;background:var(--bg2);transition:background .15s}
  .payee-summary::-webkit-details-marker{display:none}
  .payee-summary:hover{background:var(--hover)}
  .pd-name{flex:1;font-size:.82rem;font-weight:500;color:var(--text2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .pd-count{font-size:.72rem;color:var(--muted);min-width:5rem;text-align:right}
  .pd-amt{font-size:.82rem;font-weight:600;min-width:90px;text-align:right}
  .payee-txn-wrap{border-top:1px solid var(--border2);overflow-x:auto}
  .top20-details{margin-bottom:.2rem}
  @media(max-width:700px){.charts-row{grid-template-columns:1fr}.header-inner{flex-direction:column;align-items:flex-start}}
"""

    js = """
function setTheme(t){
  document.documentElement.setAttribute('data-theme',t);
  document.querySelectorAll('.theme-btn').forEach(b=>b.classList.toggle('active',b.dataset.t===t));
  localStorage.setItem('sskm-theme',t);
}
function showYear(y){
  document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('year-'+y).classList.add('active');
  document.getElementById('tab-'+y).classList.add('active');
}
(function(){
  var t=localStorage.getItem('sskm-theme')||'dark';
  setTheme(t);
})();
"""

    return f"""<!DOCTYPE html>
<html lang="de" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SSKM Kontoauszug-Analyse</title>
<style>
{css}
</style>
</head>
<body>
<div class="header">
  <div class="header-inner" style="gap:0.8rem;">
    <div>
      <h1>Stadtsparkasse München — Kontoauszug-Analyse</h1>
      <p>Konto DE10 7015 0000 0045 1277 84 &mdash; HARALD BEKER UND ROSEMARIE BEKER &mdash; {date_start}&ndash;{date_end} &mdash; {n_txn} Transaktionen &mdash; Kontostand 17.03.2026: 63.050,36 €</p>
    </div>
    <div class="theme-switcher">
      <span>Thema:</span>
      <button class="theme-btn active" data-t="dark"     onclick="setTheme('dark')"     title="Dunkel"></button>
      <button class="theme-btn"        data-t="light"    onclick="setTheme('light')"    title="Hell"></button>
      <button class="theme-btn"        data-t="sepia"    onclick="setTheme('sepia')"    title="Sepia"></button>
      <button class="theme-btn"        data-t="contrast" onclick="setTheme('contrast')" title="Hoher Kontrast"></button>
    </div>
    <a href="sskm_analyse.pdf" class="pdf-link" title="PDF öffnen / drucken" download>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:5px;vertical-align:-2px"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>Drucken / PDF
    </a>
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


# ── Write HTML ────────────────────────────────────────────────────────────────
print("Generating sskm_analyse.html …")
html = build_html(transactions)
with open('sskm_analyse.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"  Written: sskm_analyse.html ({len(html):,} bytes)")

# ── Print summary ─────────────────────────────────────────────────────────────
years_in_data = sorted(set(t['year'] for t in transactions))
print("\nJahresübersicht:")
for yr in years_in_data:
    yr_txns = [t for t in transactions if t['year'] == yr]
    inc = round(sum(t['amount'] for t in yr_txns if t['amount'] > 0), 2)
    exp = round(sum(t['amount'] for t in yr_txns if t['amount'] < 0), 2)
    print(f"  {yr}: {len(yr_txns):4d} Buchungen | Einnahmen {inc:10,.2f} € | Ausgaben {abs(exp):10,.2f} € | Saldo {inc+exp:+10,.2f} €")

total_inc = round(sum(t['amount'] for t in transactions if t['amount'] > 0), 2)
total_exp = round(sum(t['amount'] for t in transactions if t['amount'] < 0), 2)
print(f"\n  Gesamt: {len(transactions):4d} Buchungen | Einnahmen {total_inc:10,.2f} € | Ausgaben {abs(total_exp):10,.2f} € | Saldo {total_inc+total_exp:+10,.2f} €")

# ── PDF ───────────────────────────────────────────────────────────────────────
print("\nGenerating sskm_analyse.pdf …")
import io, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as rl_colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                Paragraph, Spacer, HRFlowable, PageBreak, Image)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

PDF_OUT = 'sskm_analyse.pdf'
doc = SimpleDocTemplate(PDF_OUT, pagesize=A4,
    leftMargin=1.8*cm, rightMargin=1.8*cm, topMargin=1.8*cm, bottomMargin=1.8*cm)

C_DARK   = rl_colors.HexColor('#1e293b')
C_MUTED  = rl_colors.HexColor('#64748b')
C_GREEN  = rl_colors.HexColor('#059669')
C_RED    = rl_colors.HexColor('#dc2626')
C_ACCENT = rl_colors.HexColor('#2563eb')
C_ROW    = rl_colors.HexColor('#ffffff')
C_ROW2   = rl_colors.HexColor('#f8fafc')
C_BORDER = rl_colors.HexColor('#e2e8f0')
C_HEAD   = rl_colors.HexColor('#f1f5f9')

sTitle  = ParagraphStyle('T', fontSize=16, textColor=C_DARK,   spaceAfter=2,  fontName='Helvetica-Bold')
sSub    = ParagraphStyle('S', fontSize=9,  textColor=C_MUTED,  spaceAfter=10)
sYear   = ParagraphStyle('Y', fontSize=12, textColor=C_ACCENT, spaceBefore=14, spaceAfter=4, fontName='Helvetica-Bold')
sFooter = ParagraphStyle('F', fontSize=7,  textColor=C_MUTED,  alignment=TA_CENTER)
sCell   = ParagraphStyle('C', fontSize=8,  textColor=C_DARK,   fontName='Helvetica')
sSect   = ParagraphStyle('SE', fontSize=10, textColor=C_DARK,  spaceBefore=10, spaceAfter=4, fontName='Helvetica-Bold')

PDF_COLORS = ['#3b82f6','#ef4444','#10b981','#f59e0b','#8b5cf6',
              '#ec4899','#06b6d4','#f97316','#84cc16','#6366f1','#64748b']

def money_pdf(v):
    if v == 0: return '—'
    return "{:,.2f} EUR".format(abs(v)).replace(',', '.')

def make_pie_img(labels, values, title, width_cm=16.0):
    MAX_SEG = 10
    pairs = sorted(zip(values, labels), reverse=True)
    if not pairs or sum(v for v, _ in pairs) == 0:
        return None
    if len(pairs) > MAX_SEG:
        top = pairs[:MAX_SEG]
        rest_val = sum(v for v, _ in pairs[MAX_SEG:])
        top_vals   = [v for v, _ in top] + ([rest_val] if rest_val else [])
        top_labels = [l for _, l in top] + (['Weitere'] if rest_val else [])
    else:
        top_vals   = [v for v, _ in pairs]
        top_labels = [l for _, l in pairs]
    clrs = PDF_COLORS[:len(top_vals)]
    total = sum(top_vals)
    legend = ['{} — {:,.2f} € ({:.1f}%)'.format(
                (l[:30]+'…') if len(l) > 31 else l, v, v / total * 100)
              for l, v in zip(top_labels, top_vals)]
    fig, ax = plt.subplots(figsize=(9.0, 4.5), facecolor='white')
    wedges, _ = ax.pie(top_vals, colors=clrs, startangle=90,
                       wedgeprops=dict(linewidth=0.6, edgecolor='white'))
    ax.set_title(title, fontsize=11, fontweight='bold', pad=8, color='#1e293b')
    ax.legend(wedges, legend, loc='center left', bbox_to_anchor=(1.01, 0.5),
              fontsize=7, frameon=False)
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=160, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    w = width_cm * cm
    return Image(buf, width=w, height=w * 0.47)

def tbl_style(data, col_widths=None):
    n = len(data)
    style = TableStyle([
        ('BACKGROUND',  (0,0), (-1,0), C_HEAD),
        ('TEXTCOLOR',   (0,0), (-1,0), C_MUTED),
        ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,0), 8),
        ('BOTTOMPADDING',(0,0),(-1,0), 4),
        ('TOPPADDING',  (0,0), (-1,0), 4),
        ('FONTNAME',    (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',    (0,1), (-1,-1), 8),
        ('BOTTOMPADDING',(0,1),(-1,-1), 3),
        ('TOPPADDING',  (0,1), (-1,-1), 3),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_ROW, C_ROW2]),
        ('GRID',        (0,0), (-1,-1), 0.3, C_BORDER),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
    ])
    return style

# Build PDF story
story = []

story.append(Paragraph('Stadtsparkasse München — Kontoauszug-Analyse', sTitle))
story.append(Paragraph(
    'Konto DE10 7015 0000 0045 1277 84  ·  HARALD BEKER UND ROSEMARIE BEKER  ·  '
    f'{min(t["date"] for t in transactions).strftime("%d.%m.%Y")}–'
    f'{max(t["date"] for t in transactions).strftime("%d.%m.%Y")}  ·  '
    f'{len(transactions)} Transaktionen  ·  Kontostand 17.03.2026: 63.050,36 €',
    sSub))
story.append(HRFlowable(width='100%', thickness=0.5, color=C_BORDER, spaceAfter=8))

# Summary table
sum_data = [['Jahr', 'Einnahmen (€)', 'Ausgaben (€)', 'Saldo (€)', 'Buchungen']]
for yr in years_in_data:
    yr_txns = [t for t in transactions if t['year'] == yr]
    inc = round(sum(t['amount'] for t in yr_txns if t['amount'] > 0), 2)
    exp = round(sum(t['amount'] for t in yr_txns if t['amount'] < 0), 2)
    sal = round(inc + exp, 2)
    sum_data.append([
        str(yr),
        f"{inc:,.2f}".replace(',','.'),
        f"{abs(exp):,.2f}".replace(',','.'),
        f"{sal:+,.2f}".replace(',','.'),
        str(len(yr_txns)),
    ])
# Gesamt row
sum_data.append([
    'Gesamt',
    f"{total_inc:,.2f}".replace(',','.'),
    f"{abs(total_exp):,.2f}".replace(',','.'),
    f"{total_inc+total_exp:+,.2f}".replace(',','.'),
    str(len(transactions)),
])

sum_tbl = Table(sum_data, colWidths=[2.5*cm, 4*cm, 4*cm, 4*cm, 2.5*cm])
sum_tbl.setStyle(tbl_style(sum_data))
# Color saldo column
for row_i in range(1, len(sum_data)):
    val = sum_data[row_i][3]
    c = C_GREEN if val.startswith('+') else C_RED
    sum_tbl.setStyle(TableStyle([('TEXTCOLOR', (3, row_i), (3, row_i), c),
                                  ('FONTNAME',  (3, row_i), (3, row_i), 'Helvetica-Bold')]))
story.append(sum_tbl)
story.append(Spacer(1, 0.5*cm))

# Per-year detail
for yr in years_in_data:
    story.append(PageBreak())
    yr_txns = [t for t in transactions if t['year'] == yr]
    inc = round(sum(t['amount'] for t in yr_txns if t['amount'] > 0), 2)
    exp = round(sum(t['amount'] for t in yr_txns if t['amount'] < 0), 2)
    sal = round(inc + exp, 2)

    story.append(Paragraph(f'Jahr {yr}  —  {len(yr_txns)} Buchungen', sYear))
    story.append(Paragraph(
        f'Einnahmen: {inc:,.2f} €  |  Ausgaben: {abs(exp):,.2f} €  |  Saldo: {sal:+,.2f} €'.replace(',','.'),
        sSub))
    story.append(HRFlowable(width='100%', thickness=0.3, color=C_BORDER, spaceAfter=6))

    # Category expense pie
    cat_expense = collections.defaultdict(float)
    cat_income  = collections.defaultdict(float)
    expense_txns = [t for t in yr_txns if t['amount'] < 0]
    income_txns  = [t for t in yr_txns if t['amount'] > 0]
    for t in expense_txns:
        cat_expense[t['category']] += abs(t['amount'])
    for t in income_txns:
        cat_income[t['category']] += t['amount']

    exp_pie = make_pie_img(list(cat_expense.keys()), list(cat_expense.values()),
                           f'{yr} — Ausgaben nach Kategorie')
    if exp_pie:
        story.append(exp_pie)
        story.append(Spacer(1, 0.3*cm))

    inc_pie = make_pie_img(list(cat_income.keys()), list(cat_income.values()),
                           f'{yr} — Einnahmen nach Kategorie')
    if inc_pie:
        story.append(inc_pie)
        story.append(Spacer(1, 0.3*cm))

    # Expense category table
    story.append(Paragraph('Ausgaben nach Kategorie', sSect))
    cat_data = [['Kategorie', 'Buchungen', 'Betrag (€)']]
    for cat, total in sorted(cat_expense.items(), key=lambda x: x[1], reverse=True):
        cnt = sum(1 for t in expense_txns if t['category'] == cat)
        cat_data.append([cat, str(cnt), f"{total:,.2f}".replace(',','.')])
    if len(cat_data) > 1:
        cat_tbl = Table(cat_data, colWidths=[8*cm, 3*cm, 4*cm])
        cat_tbl.setStyle(tbl_style(cat_data))
        story.append(cat_tbl)
        story.append(Spacer(1, 0.3*cm))

    # Income category table
    story.append(Paragraph('Einnahmen nach Kategorie', sSect))
    inc_data = [['Kategorie', 'Buchungen', 'Betrag (€)']]
    for cat, total in sorted(cat_income.items(), key=lambda x: x[1], reverse=True):
        cnt = sum(1 for t in income_txns if t['category'] == cat)
        inc_data.append([cat, str(cnt), f"{total:,.2f}".replace(',','.')])
    if len(inc_data) > 1:
        inc_tbl = Table(inc_data, colWidths=[8*cm, 3*cm, 4*cm])
        inc_tbl.setStyle(tbl_style(inc_data))
        story.append(inc_tbl)
        story.append(Spacer(1, 0.3*cm))

    # Top 20 payees
    story.append(Paragraph('Top 20 Empfänger/Auftraggeber', sSect))
    payee_totals = collections.defaultdict(float)
    payee_counts = collections.defaultdict(int)
    for t in yr_txns:
        payee_totals[t['payee']] += t['amount']
        payee_counts[t['payee']] += 1
    top20 = sorted(payee_totals.items(), key=lambda x: abs(x[1]), reverse=True)[:20]
    top20_data = [['Empfänger/Auftraggeber', 'Buchungen', 'Netto (€)']]
    for payee, net in top20:
        sign = '+' if net >= 0 else ''
        top20_data.append([
            payee[:45] + ('…' if len(payee) > 45 else ''),
            str(payee_counts[payee]),
            f"{sign}{net:,.2f}".replace(',','.')
        ])
    top20_tbl = Table(top20_data, colWidths=[10*cm, 2.5*cm, 3.5*cm])
    top20_tbl.setStyle(tbl_style(top20_data))
    for row_i in range(1, len(top20_data)):
        val = top20_data[row_i][2]
        c = C_GREEN if val.startswith('+') else C_RED
        top20_tbl.setStyle(TableStyle([('TEXTCOLOR', (2, row_i), (2, row_i), c)]))
    story.append(top20_tbl)

doc.build(story)
print(f"  Written: {PDF_OUT}")
print("\nDone.")
