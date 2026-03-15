#!/usr/bin/env python3
"""Build quarterly commodity prices CSV for Germany in EUR (1990-2026)."""

import subprocess
import json
import pandas as pd
import numpy as np
from datetime import datetime
import time
import io

###############################################################################
# 1. FX rates: USD/EUR (for converting world prices to EUR)
###############################################################################
print("=== Loading FX rates ===")

# From existing CSV (1999+)
main_df = pd.read_csv('chf_usd_monthly.csv')
main_df['date'] = pd.to_datetime(main_df['date'])
fx = main_df[['date', 'USD_EUR']].dropna().copy()
fx = fx.set_index('date')
fx_monthly = fx.resample('M').last()

# Pre-1999: use DEM/USD from FRED and fixed rate 1 EUR = 1.95583 DEM
# So USD_EUR = USD_DEM / 1.95583
# DEM rates from FRED (monthly averages)
dem_rates = {
    '1990-01': 1.6914, '1990-02': 1.6758, '1990-03': 1.7053, '1990-04': 1.6863,
    '1990-05': 1.6630, '1990-06': 1.6832, '1990-07': 1.6375, '1990-08': 1.5702,
    '1990-09': 1.5701, '1990-10': 1.5238, '1990-11': 1.4857, '1990-12': 1.4982,
    '1991-01': 1.5091, '1991-02': 1.4805, '1991-03': 1.6122, '1991-04': 1.7027,
    '1991-05': 1.7199, '1991-06': 1.7828, '1991-07': 1.7852, '1991-08': 1.7435,
    '1991-09': 1.6933, '1991-10': 1.6893, '1991-11': 1.6208, '1991-12': 1.5630,
    '1992-01': 1.5788, '1992-02': 1.6186, '1992-03': 1.6616, '1992-04': 1.6493,
    '1992-05': 1.6225, '1992-06': 1.5726, '1992-07': 1.4914, '1992-08': 1.4475,
    '1992-09': 1.4514, '1992-10': 1.4851, '1992-11': 1.5875, '1992-12': 1.5822,
    '1993-01': 1.6144, '1993-02': 1.6414, '1993-03': 1.6466, '1993-04': 1.5964,
    '1993-05': 1.6071, '1993-06': 1.6547, '1993-07': 1.7157, '1993-08': 1.6944,
    '1993-09': 1.6219, '1993-10': 1.6405, '1993-11': 1.7005, '1993-12': 1.7105,
    '1994-01': 1.7426, '1994-02': 1.7355, '1994-03': 1.6909, '1994-04': 1.6984,
    '1994-05': 1.6565, '1994-06': 1.6271, '1994-07': 1.5674, '1994-08': 1.5646,
    '1994-09': 1.5491, '1994-10': 1.5195, '1994-11': 1.5396, '1994-12': 1.5716,
    '1995-01': 1.5302, '1995-02': 1.5022, '1995-03': 1.4061, '1995-04': 1.3812,
    '1995-05': 1.4096, '1995-06': 1.4012, '1995-07': 1.3886, '1995-08': 1.4456,
    '1995-09': 1.4601, '1995-10': 1.4143, '1995-11': 1.4173, '1995-12': 1.4406,
    '1996-01': 1.4635, '1996-02': 1.4669, '1996-03': 1.4776, '1996-04': 1.5044,
    '1996-05': 1.5324, '1996-06': 1.5282, '1996-07': 1.5025, '1996-08': 1.4826,
    '1996-09': 1.5080, '1996-10': 1.5277, '1996-11': 1.5118, '1996-12': 1.5525,
    '1997-01': 1.6047, '1997-02': 1.6747, '1997-03': 1.6946, '1997-04': 1.7119,
    '1997-05': 1.7048, '1997-06': 1.7277, '1997-07': 1.7939, '1997-08': 1.8400,
    '1997-09': 1.7862, '1997-10': 1.7575, '1997-11': 1.7323, '1997-12': 1.7788,
    '1998-01': 1.8165, '1998-02': 1.8123, '1998-03': 1.8272, '1998-04': 1.8132,
    '1998-05': 1.7753, '1998-06': 1.7928, '1998-07': 1.7976, '1998-08': 1.7869,
    '1998-09': 1.6990, '1998-10': 1.6381, '1998-11': 1.6827, '1998-12': 1.6698,
}

# Convert DEM/USD to EUR/USD: EUR/USD = DEM/USD / 1.95583
pre99_eur = {}
for k, v in dem_rates.items():
    pre99_eur[k] = v / 1.95583

# Build complete monthly EUR/USD series
all_months = pd.date_range('1990-01-01', '2026-03-31', freq='M')
usd_eur = pd.Series(dtype=float, index=all_months)

for k, v in pre99_eur.items():
    dt = pd.Timestamp(k + '-01') + pd.offsets.MonthEnd(0)
    if dt in usd_eur.index:
        usd_eur[dt] = v

for dt, row in fx_monthly.iterrows():
    if dt in usd_eur.index and pd.notna(row['USD_EUR']):
        usd_eur[dt] = row['USD_EUR']

usd_eur = usd_eur.interpolate()
print(f"  EUR/USD: {usd_eur.notna().sum()} months")

###############################################################################
# 2. World Bank commodity prices (USD monthly)
###############################################################################
print("\n=== Loading World Bank data ===")
wb = pd.read_excel('wb_commodities.xlsx', sheet_name='Monthly Prices', header=None)
wb_names = wb.iloc[4].tolist()
wb_units = wb.iloc[5].tolist()

# Map columns
wb_cols = {}
for i, name in enumerate(wb_names):
    if pd.notna(name):
        wb_cols[str(name).strip()] = i

needed_wb = {
    'Crude oil, Brent': 'brent_usd_bbl',
    'Coal, Australian': 'coal_usd_mt',
    'Natural gas, Europe': 'natgas_usd_mmbtu',
    'Beef **': 'beef_usd_kg',
    'Chicken **': 'chicken_usd_kg',
    'Aluminum': 'aluminum_usd_mt',
    'Copper': 'copper_usd_mt',
    'Iron ore, cfr spot': 'ironore_usd_dmt',
    'Zinc': 'zinc_usd_mt',
}

wb_data = pd.DataFrame()
data_rows = wb.iloc[6:].copy()
wb_data['period'] = data_rows.iloc[:, 0].values

for name, col_name in needed_wb.items():
    if name in wb_cols:
        col_idx = wb_cols[name]
        wb_data[col_name] = pd.to_numeric(data_rows.iloc[:, col_idx], errors='coerce').values
        print(f"  {name}: col {col_idx}")

# Parse dates
wb_data = wb_data[wb_data['period'].astype(str).str.match(r'\d{4}M\d{2}')]
wb_data['date'] = pd.to_datetime(wb_data['period'].str.replace('M', '-'), format='%Y-%m')
wb_data['date'] = wb_data['date'] + pd.offsets.MonthEnd(0)
wb_data = wb_data.set_index('date')
print(f"  Rows: {len(wb_data)} ({wb_data.index.min()} to {wb_data.index.max()})")

###############################################################################
# 3. Convert USD prices to EUR
###############################################################################
print("\n=== Converting USD to EUR ===")
wb_eur = pd.DataFrame(index=wb_data.index)

for col in wb_data.columns:
    if col == 'period':
        continue
    if '_usd_' in col:
        eur_col = col.replace('_usd_', '_eur_')
        wb_eur[eur_col] = wb_data[col] / usd_eur.reindex(wb_data.index, method='nearest')

# Compute derived prices
# Gasoline from Brent: rough conversion 1 bbl = 159L, ~40% yield, + taxes/margins
# German retail gasoline ≈ Brent_EUR/bbl * 0.63/100 + 0.6547(energy tax) + 0.19*VAT + margins
# Simplified: Brent EUR/L ≈ Brent_EUR/bbl / 159, retail ≈ crude_cost * 2.5 + taxes
# Actually, let's use a simpler empirical relationship
if 'brent_eur_bbl' in wb_eur.columns:
    # German gasoline (Super E5) retail price EUR/L
    # Empirical: gasoline ≈ 0.004 * Brent_EUR + 0.85 (rough approximation)
    # Better: use ratio. In 2020, Brent avg ~42 USD ≈ 37 EUR/bbl, gasoline ~1.25 EUR/L
    # In 2008, Brent ~97 USD ≈ 66 EUR/bbl, gasoline ~1.45 EUR/L
    # Ratio shifts over time due to taxes. Let's use: gasoline ≈ Brent_EUR/bbl / 100 + 0.90
    wb_eur['benzin_eur_l'] = wb_eur['brent_eur_bbl'] / 100 + 0.90

# Brass ≈ 60% copper + 40% zinc (both in EUR/mt)
if 'copper_eur_mt' in wb_eur.columns and 'zinc_eur_mt' in wb_eur.columns:
    wb_eur['messing_eur_mt'] = 0.6 * wb_eur['copper_eur_mt'] + 0.4 * wb_eur['zinc_eur_mt']

# Steel: use iron ore price * ~5 as rough HRC steel price proxy
if 'ironore_eur_dmt' in wb_eur.columns:
    wb_eur['stahl_eur_mt'] = wb_eur['ironore_eur_dmt'] * 5

print("  Columns:", list(wb_eur.columns))

###############################################################################
# 4. Eurostat electricity & gas for Germany (semi-annual, 2007+)
###############################################################################
print("\n=== Fetching Eurostat energy prices ===")

def fetch_eurostat_tsv(dataset):
    r = subprocess.run(['curl', '-s', '-L', '-H', 'User-Agent: Mozilla/5.0',
        f'https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/{dataset}?format=TSV&startPeriod=1990&endPeriod=2026'],
        capture_output=True, text=True)
    return r.stdout

# Electricity
elec_tsv = fetch_eurostat_tsv('nrg_pc_204')
elec_data = {}
if elec_tsv and not elec_tsv.startswith('<?xml'):
    lines = elec_tsv.strip().split('\n')
    headers = lines[0].split('\t')
    for line in lines[1:]:
        # Medium household (2500-4999 kWh), excl tax, EUR, Germany
        if ',KWH2500-4999,' in line and ',X_TAX,' in line and ',EUR,' in line and ',DE\t' in line:
            parts = line.split('\t')
            for i, val in enumerate(parts[1:], 1):
                v = val.strip().replace(' ', '').replace('e', '').replace('p', '').replace('b', '')
                if v and v != ':':
                    period = headers[i].strip()
                    elec_data[period] = float(v)
print(f"  Electricity: {len(elec_data)} semi-annual values")

# Gas (nrg_pc_202)
gas_tsv = fetch_eurostat_tsv('nrg_pc_202')
gas_data = {}
if gas_tsv and not gas_tsv.startswith('<?xml'):
    lines = gas_tsv.strip().split('\n')
    headers = lines[0].split('\t')
    for line in lines[1:]:
        if ',GJ20-199,' in line and ',KWH,' in line and ',X_TAX,' in line and ',EUR,' in line and ',DE\t' in line:
            parts = line.split('\t')
            for i, val in enumerate(parts[1:], 1):
                v = val.strip().replace(' ', '').replace('e', '').replace('p', '').replace('b', '')
                if v and v != ':':
                    period = headers[i].strip()
                    gas_data[period] = float(v)
print(f"  Gas: {len(gas_data)} semi-annual values")

###############################################################################
# 5. German consumer prices from HICP indices (Eurostat) + anchor prices
###############################################################################
print("\n=== Loading HICP food price indices ===")

def parse_hicp(filename):
    with open(filename) as f:
        lines = f.read().strip().split('\n')
    headers = lines[0].split('\t')
    result = {}
    for line in lines[1:]:
        parts = line.split('\t')
        for i, val in enumerate(parts[1:], 1):
            v = val.strip().replace(' ', '').replace('e', '').replace('p', '').replace('d', '').replace('b', '')
            if v and v != ':':
                try:
                    result[headers[i].strip()] = float(v)
                except:
                    pass
    return result

# Fetch HICP data from Eurostat (pre-downloaded TSV files)
hicp_codes = {
    'CP0111': ('brot', 'hicp_brot.tsv'),
    'CP0112': ('fleisch', 'hicp_fleisch.tsv'),
    'CP0114': ('milch_kaese_eier', 'hicp_milch_kaese_eier.tsv'),
    'CP0122': ('softdrinks', 'hicp_softdrinks.tsv'),
    'CP0213': ('bier', 'hicp_bier.tsv'),
    'CP01121': ('rind', 'hicp_rind.tsv'),
    'CP01122': ('schwein', 'hicp_schwein.tsv'),
    'CP01124': ('huehnchen', 'hicp_huehnchen.tsv'),
    'CP01141': ('milch_only', 'hicp_milch_only.tsv'),
    'CP01147': ('eier_only', 'hicp_eier_only.tsv'),
    'CP01142': ('kaese_only', 'hicp_kaese_only.tsv'),
}

hicp = {}
for code, (name, filename) in hicp_codes.items():
    try:
        hicp[name] = parse_hicp(filename)
        print(f"  {name}: {len(hicp[name])} values ({min(hicp[name].keys())} to {max(hicp[name].keys())})")
    except FileNotFoundError:
        # Fetch if not downloaded yet
        url = f'https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/prc_hicp_midx/M.I15.{code}.DE?format=TSV&startPeriod=1990&endPeriod=2026'
        r = subprocess.run(['curl', '-s', '-L', '-H', 'User-Agent: Mozilla/5.0', url], capture_output=True, text=True)
        if r.stdout and not r.stdout.startswith('<?xml'):
            with open(filename, 'w') as f:
                f.write(r.stdout)
            hicp[name] = parse_hicp(filename)
            print(f"  {name}: {len(hicp[name])} values (fetched)")
        else:
            print(f"  {name}: not available")

# 2020 anchor prices (German average retail, EUR)
anchor_2020 = {
    'brot': 2.80,       # Weißbrot, 1 kg
    'milch': 0.95,      # Vollmilch, 1 L
    'eier': 1.70,       # 10 Eier
    'kaese': 8.50,      # Hartkäse, 1 kg
    'schwein': 6.50,    # Schweinefleisch, 1 kg
    'rind': 12.00,      # Rindfleisch, 1 kg
    'huehnchen': 5.50,  # Hähnchenfleisch, 1 kg
    'cola': 1.00,       # Cola, 1 L
    'bier': 0.85,       # Bier, 0.5 L
}

# Build price series: use specific codes where available, extend with broader categories
price_configs = {
    'brot_eur': [('brot', 2.80)],
    'bier_eur': [('bier', 0.85)],
    'cola_eur': [('softdrinks', 1.00)],
    'milch_eur': [('milch_only', 0.95), ('milch_kaese_eier', 0.95)],
    'eier_eur': [('eier_only', 1.70), ('milch_kaese_eier', 1.70)],
    'kaese_eur': [('kaese_only', 8.50), ('milch_kaese_eier', 8.50)],
    'schwein_eur': [('schwein', 6.50), ('fleisch', 6.50)],
    'rind_eur': [('rind', 12.00), ('fleisch', 12.00)],
    'huehnchen_eur': [('huehnchen', 5.50), ('fleisch', 5.50)],
}

hicp_prices = {}
for col_name, configs in price_configs.items():
    primary_name, anchor = configs[0]
    series_data = dict(hicp.get(primary_name, {}))

    # Extend with fallback if available
    if len(configs) > 1 and series_data:
        fallback_name, fallback_anchor = configs[1]
        fallback_data = hicp.get(fallback_name, {})
        if fallback_data:
            overlap = set(series_data.keys()) & set(fallback_data.keys())
            if overlap:
                ratios = [series_data[k] / fallback_data[k] for k in sorted(overlap)[:12]]
                ratio = np.mean(ratios)
                for k, v in fallback_data.items():
                    if k not in series_data:
                        series_data[k] = v * ratio
    elif not series_data and len(configs) > 1:
        fallback_name, anchor = configs[1]
        series_data = dict(hicp.get(fallback_name, {}))

    if not series_data:
        continue

    idx_2020 = [v for k, v in series_data.items() if k.startswith('2020')]
    if not idx_2020:
        continue
    avg_2020 = np.mean(idx_2020)

    prices = {}
    for period, idx in series_data.items():
        try:
            dt = pd.Timestamp(period) + pd.offsets.MonthEnd(0)
            prices[dt] = anchor * (idx / avg_2020)
        except:
            pass

    ps = pd.Series(prices).sort_index()
    hicp_prices[col_name] = ps.resample('Q').mean()
    n = hicp_prices[col_name].notna().sum()
    print(f"  → {col_name}: {n} quarters")

###############################################################################
# 6. Fill 2025+ gaps (World Bank ends Dec 2024)
###############################################################################
print("\n=== Adding 2025 commodity data ===")

# Q1 2025 and Q2 2025 prices from IndexMundi/FRED/IMF (USD)
supplement_usd = {
    '2025-01': {'brent': 78.19, 'coal': 118.60, 'natgas': 14.76, 'aluminum': 2573.40, 'copper': 8991.41, 'zinc': 2818.96, 'ironore': 99.58},
    '2025-02': {'brent': 75.19, 'coal': 106.93, 'natgas': 15.38, 'aluminum': 2657.60, 'copper': 9330.60, 'zinc': 2800.14, 'ironore': 105.08},
    '2025-03': {'brent': 71.74, 'coal': 103.97, 'natgas': 13.16, 'aluminum': 2658.29, 'copper': 9739.68, 'zinc': 2889.29, 'ironore': 100.10},
    '2025-04': {'brent': 66.93, 'coal': 98.61, 'natgas': 11.57, 'aluminum': 2371.60, 'copper': 9176.80, 'zinc': 2621.55, 'ironore': 97.24},
    '2025-05': {'brent': 64.09, 'coal': 104.41, 'natgas': 11.62, 'aluminum': 2448.79, 'copper': 9532.98, 'zinc': 2644.37, 'ironore': 96.97},
    '2025-06': {'brent': 69.85, 'coal': 109.03, 'natgas': 12.30, 'aluminum': 2525.96, 'copper': 9835.07, 'zinc': 2654.65, 'ironore': 92.33},
    # Q3 2025 (World Bank Pink Sheet Mar 2026)
    '2025-07': {'brent': 69.00, 'coal': 116.30, 'natgas': 11.47, 'aluminum': 2606, 'copper': 9771, 'zinc': 2763, 'ironore': 101.2},
    '2025-08': {'brent': 67.87, 'coal': 119.20, 'natgas': 10.98, 'aluminum': 2599, 'copper': 9672, 'zinc': 2790, 'ironore': 103.3},
    '2025-09': {'brent': 67.99, 'coal': 112.50, 'natgas': 11.00, 'aluminum': 2654, 'copper': 9995, 'zinc': 2937, 'ironore': 106.4},
    # Q4 2025
    '2025-10': {'brent': 64.54, 'coal': 111.50, 'natgas': 10.90, 'aluminum': 2793, 'copper': 10740, 'zinc': 3152, 'ironore': 106.9},
    '2025-11': {'brent': 63.80, 'coal': 115.40, 'natgas': 10.36, 'aluminum': 2819, 'copper': 10812, 'zinc': 3177, 'ironore': 106.2},
    '2025-12': {'brent': 62.54, 'coal': 115.70, 'natgas': 9.48, 'aluminum': 2876, 'copper': 11791, 'zinc': 3162, 'ironore': 104.6},
    # Q1 2026 (FRED/WB through Feb, Mar MTD)
    '2026-01': {'brent': 66.60, 'coal': 109.80, 'natgas': 11.76, 'aluminum': 3134, 'copper': 12987, 'zinc': 3207, 'ironore': 105.5},
    '2026-02': {'brent': 70.89, 'coal': 118.40, 'natgas': 11.24, 'aluminum': 3065, 'copper': 12951, 'zinc': 3324, 'ironore': 98.8},
    '2026-03': {'brent': 86.79, 'coal': 134.80, 'natgas': 13.00, 'aluminum': 3387, 'copper': 12884, 'zinc': 3288, 'ironore': 105.0},
}
supplement_eurusd = {
    '2025-01': 1.0348, '2025-02': 1.0412, '2025-03': 1.0789,
    '2025-04': 1.1221, '2025-05': 1.1276, '2025-06': 1.1518,
    '2025-07': 1.1671, '2025-08': 1.1647, '2025-09': 1.1739,
    '2025-10': 1.1641, '2025-11': 1.1558, '2025-12': 1.1710,
    '2026-01': 1.1744, '2026-02': 1.1824, '2026-03': 1.1625,
}

for month, prices in supplement_usd.items():
    dt = pd.Timestamp(month + '-01') + pd.offsets.MonthEnd(0)
    eur_rate = supplement_eurusd[month]
    if dt not in wb_eur.index:
        wb_eur.loc[dt] = np.nan
    wb_eur.loc[dt, 'brent_eur_bbl'] = prices['brent'] / eur_rate
    wb_eur.loc[dt, 'coal_eur_mt'] = prices['coal'] / eur_rate
    wb_eur.loc[dt, 'natgas_eur_mmbtu'] = prices['natgas'] / eur_rate
    wb_eur.loc[dt, 'aluminum_eur_mt'] = prices['aluminum'] / eur_rate
    wb_eur.loc[dt, 'copper_eur_mt'] = prices['copper'] / eur_rate
    wb_eur.loc[dt, 'zinc_eur_mt'] = prices['zinc'] / eur_rate
    wb_eur.loc[dt, 'ironore_eur_dmt'] = prices['ironore'] / eur_rate
    # Derived
    wb_eur.loc[dt, 'benzin_eur_l'] = prices['brent'] / eur_rate / 100 + 0.90
    wb_eur.loc[dt, 'messing_eur_mt'] = 0.6 * prices['copper'] / eur_rate + 0.4 * prices['zinc'] / eur_rate
    wb_eur.loc[dt, 'stahl_eur_mt'] = prices['ironore'] / eur_rate * 5

wb_eur = wb_eur.sort_index()
print(f"  Extended to {wb_eur.index.max()}")

###############################################################################
# 7. Build quarterly output
###############################################################################
print("\n=== Building quarterly CSV ===")

quarters = pd.date_range('1990-03-31', '2026-03-31', freq='Q')
result = pd.DataFrame(index=quarters)
result.index.name = 'date'

# Resample World Bank EUR data to quarterly
for col in wb_eur.columns:
    quarterly = wb_eur[col].resample('Q').mean()
    result[col] = quarterly.reindex(result.index)

# Rename columns to final names
rename_map = {
    'benzin_eur_l': 'benzin_eur_pro_l',
    'coal_eur_mt': 'kohle_eur_pro_t',
    'natgas_eur_mmbtu': 'erdgas_eur_pro_mmbtu',
    'aluminum_eur_mt': 'aluminium_eur_pro_t',
    'copper_eur_mt': 'kupfer_eur_pro_t',
    'zinc_eur_mt': 'zink_eur_pro_t',
    'messing_eur_mt': 'messing_eur_pro_t',
    'stahl_eur_mt': 'stahl_eur_pro_t',
    'ironore_eur_dmt': 'eisenerz_eur_pro_t',
    'beef_eur_kg': 'rindfleisch_eur_pro_kg',
    'chicken_eur_kg': 'huehnchen_eur_pro_kg',
    'brent_eur_bbl': 'brent_eur_pro_bbl',
}
result = result.rename(columns=rename_map)

# Drop intermediate columns
for col in ['brent_eur_pro_bbl', 'eisenerz_eur_pro_t', 'zink_eur_pro_t']:
    if col in result.columns:
        result = result.drop(columns=[col])

# Add Eurostat electricity (semi-annual → spread to quarters)
elec_series = pd.Series(dtype=float, index=result.index)
for period, val in elec_data.items():
    # period like "2007-S1" → Q1+Q2, "2007-S2" → Q3+Q4
    year = int(period[:4])
    semester = period[-2:]
    if semester == 'S1':
        for q in [f'{year}-03-31', f'{year}-06-30']:
            dt = pd.Timestamp(q)
            if dt in elec_series.index:
                elec_series[dt] = val
    else:
        for q in [f'{year}-09-30', f'{year}-12-31']:
            dt = pd.Timestamp(q)
            if dt in elec_series.index:
                elec_series[dt] = val
result['strom_eur_pro_kwh'] = elec_series

# Add Eurostat gas
gas_series = pd.Series(dtype=float, index=result.index)
for period, val in gas_data.items():
    year = int(period[:4])
    semester = period[-2:]
    if semester == 'S1':
        for q in [f'{year}-03-31', f'{year}-06-30']:
            dt = pd.Timestamp(q)
            if dt in gas_series.index:
                gas_series[dt] = val
    else:
        for q in [f'{year}-09-30', f'{year}-12-31']:
            dt = pd.Timestamp(q)
            if dt in gas_series.index:
                gas_series[dt] = val
result['erdgas_haushalt_eur_pro_kwh'] = gas_series

# Add food prices from HICP (already quarterly in hicp_prices dict)
# Map HICP column names to final column names
hicp_to_final = {
    'rind_eur': 'rindfleisch_eur_pro_kg',
    'huehnchen_eur': 'huehnchen_eur_pro_kg',
}
for col_name, quarterly_series in hicp_prices.items():
    final_name = hicp_to_final.get(col_name, col_name)
    # For meat: HICP German retail prices override World Bank international prices
    hicp_vals = quarterly_series.reindex(result.index)
    if final_name in result.columns:
        result[final_name] = hicp_vals.combine_first(result[final_name])
    else:
        result[final_name] = hicp_vals
    n = result[final_name].notna().sum()
    print(f"  {final_name}: {n} quarters")

###############################################################################
# 8. Final column ordering and formatting
###############################################################################

# Desired column order
final_cols = [
    'benzin_eur_pro_l',
    'kohle_eur_pro_t',
    'erdgas_eur_pro_mmbtu',
    'erdgas_haushalt_eur_pro_kwh',
    'strom_eur_pro_kwh',
    'brot_eur',
    'bier_eur',
    'cola_eur',
    'milch_eur',
    'schwein_eur',
    'rindfleisch_eur_pro_kg',
    'huehnchen_eur_pro_kg',
    'stahl_eur_pro_t',
    'aluminium_eur_pro_t',
    'kupfer_eur_pro_t',
    'messing_eur_pro_t',
    'eier_eur',
    'kaese_eur',
]

# Add missing columns
for col in final_cols:
    if col not in result.columns:
        result[col] = np.nan

result = result[final_cols]

# Format
result.index = result.index.strftime('%Y-%m-%d')
result.index.name = 'date'

# Round
for col in result.columns:
    if 'pro_t' in col or 'pro_mt' in col:
        result[col] = result[col].round(0)
    elif 'pro_kwh' in col:
        result[col] = result[col].round(4)
    else:
        result[col] = result[col].round(2)

result.to_csv('commodities_quarterly.csv')

print(f"\n=== DONE ===")
print(f"Saved {len(result)} quarters to commodities_quarterly.csv")
print(f"Date range: {result.index[0]} to {result.index[-1]}")
print(f"\nData availability:")
for col in result.columns:
    n = result[col].notna().sum()
    total = len(result)
    pct = n / total * 100
    print(f"  {col}: {n}/{total} ({pct:.0f}%)")
