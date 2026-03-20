# Finance — Asset & Commodity Price Data

Financial data analysis: asset prices, commodity prices, UBS bank account and credit card analysis.

## 1. Monthly Asset Prices (`chf_usd_monthly.csv`)

Monthly end-of-month prices since 1990, all in USD.

| Ticker | Description |
|--------|-------------|
| CHF/USD | Swiss Franc exchange rate |
| EUR/USD | Euro exchange rate (from Jan 1999) |
| XAU | Gold price |
| S&P 500 TR | S&P 500 Total Return |
| DAX | German stock index (converted to USD) |
| SMIC | Swiss Market Index Total Return (converted to USD, from Mar 1995) |

## 2. Quarterly Commodity & Consumer Prices (`commodities_quarterly.csv`)

Quarterly prices since 1990, primarily in EUR, focused on Germany.

| Category | Columns |
|----------|---------|
| Energy | Benzin (EUR/L), Kohle (EUR/t), Erdgas (EUR/MMBtu + Haushalt EUR/kWh), Strom (EUR/kWh) |
| Food | Brot, Bier, Cola, Milch, Eier, Käse, Schwein, Rind, Hähnchen |
| Metals | Stahl, Aluminium, Kupfer, Messing (alle EUR/t) |

## 3. UBS Kontoauszug Analyse

Interactive HTML + PDF reports from UBS account statements (2024–2026).

| File | Description |
|------|-------------|
| `analyze_ubs.py` | Parst `ubstrans.csv` → `ubstrans_analyse.html` + `ubstrans_analyse.pdf` |
| `build_pdf_analyse.py` | Parst PDF-Kontoauszug → `pdf_analyse.html` + `pdf_analyse.pdf` |
| `ubstrans_analyse.html` | Interaktive HTML-Analyse (CSV-Quelle, 200 Transaktionen) |
| `pdf_analyse.html` | Interaktive HTML-Analyse (PDF-Quelle, 210 Transaktionen) |

**Features:** 4 Farbthemes · Jahr-Tabs · SVG-Tortendiagramme · aufklappbare Monatsdetails · Suche

| Jahr | Einnahmen | Ausgaben | Netto |
|------|-----------|----------|-------|
| 2026 (Jan–Mär) | CHF 24'148 | CHF 2'707 | +21'441 |
| 2025 | CHF 165'000 | CHF 32'973 | +132'027 |
| 2024 | CHF 158'320 | CHF 26'868 | +131'452 |

## 4. UBS Kreditkarten Analyse

Interactive HTML + PDF report from UBS credit card statement (2024–2026).

| File | Description |
|------|-------------|
| `build_kreditkarten_analyse.py` | Parst `transactions-KreditKarten.pdf` → `kreditkarten_analyse.html` + `kreditkarten_analyse.pdf` |
| `kreditkarten_analyse.html` | Interaktive HTML-Analyse (105 Transaktionen, PDF-Link im Header) |
| `kreditkarten_analyse.pdf` | PDF-Bericht mit Tortendiagrammen und Gegenpartei-Tabellen |

**Features:** 4 Farbthemes · Jahr-Tabs · SVG-Tortendiagramme · aufklappbare Monatsdetails · PDF-Link

| Jahr | Ausgaben | Kartenzahlungen | Saldo |
|------|---------|----------------|-------|
| 2026 (Jan–Mär) | CHF 108.72 | CHF 107.65 | −1.07 |
| 2025 | CHF 3'005.51 | CHF 2'987.80 | −17.71 |
| 2024 | CHF 2'146.69 | CHF 2'405.20 | +258.51 |
| **Total** | **CHF 5'260.92** | **CHF 5'500.65** | **+239.73** |

## 5. Gehaltsnachweise

| File | Description |
|------|-------------|
| `Payslip_2026_01_740_022704_00_1.pdf` | Gehaltsnachweis Januar 2026 |
| `Payslip_2026_02_740_022704_00_1.pdf` | Gehaltsnachweis Februar 2026 |

## 6. Pension Calculator

| File | Description |
|------|-------------|
| `pension.py` | Zinseszins-Rechner für monatliche Sparraten |

## 7. Reports

| File | Description |
|------|-------------|
| `Gold_vs_Aktien_Bericht.docx` | Vergleichsbericht Gold vs. Aktien |
| `wetterbericht_schweiz.docx` | Wetterbericht Schweiz |
| `wetter_rebstein.docx` | Wetterbericht Rebstein |

## Usage

```bash
# Regenerate Kreditkarten HTML + PDF analysis
python3 build_kreditkarten_analyse.py
open kreditkarten_analyse.html
```

## Full Usage

```bash
# Generate the interactive asset chart
python3 plot_monthly.py
open chf_usd_monthly_plot.html

# Rebuild commodity prices from sources
python3 build_commodities.py

# Regenerate UBS CSV-based analysis
python3 analyze_ubs.py
open ubstrans_analyse.html

# Regenerate UBS PDF-based analysis
python3 build_pdf_analyse.py
open pdf_analyse.html
```

## Data Sources

- **FX rates**: ECB via `api.frankfurter.app` (1999+), FRED for pre-1999 CHF/DEM
- **Gold, S&P 500 TR, DAX, SMIC**: Yahoo Finance API
- **Commodity prices**: World Bank Pink Sheet (`wb_commodities.xlsx`)
- **Energy prices (DE)**: Eurostat (electricity `nrg_pc_204`, gas `nrg_pc_202`)
- **Food prices (DE)**: Eurostat HICP indices, anchored to 2020 retail prices
- **UBS Kontoauszug**: `ubstrans.csv` (E-Banking Export) + `transactions (1).pdf` (32-seitiger PDF-Auszug)
- **UBS Kreditkarte**: `transactions-KreditKarten.pdf` (10-seitiger PDF-Auszug, Karte 64744 D 001)

## Requirements

- Python 3 with `pandas`, `plotly`, `numpy`, `openpyxl`, `reportlab`, `matplotlib`