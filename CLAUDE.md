# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Financial data analysis and visualization project with two datasets:
1. Monthly end-of-month asset prices since 1990 (USD) with interactive Plotly charts
2. Quarterly commodity and consumer prices since 1990 (EUR, Germany-focused)

### Reports
- `Gold_vs_Aktien_Bericht.docx` — Vergleichsbericht Gold vs. Aktien
- `wetterbericht_schweiz.docx` — Wetterbericht Schweiz
- `wetter_rebstein.docx` — Wetterbericht Rebstein

## Data

### Asset Prices (`chf_usd_monthly.csv`)
- Columns: `date`, `USD_CHF`, `USD_EUR`, `USD_XAU`, `USD_SP500TR`, `USD_DAX`, `USD_SMIC`
- All values in USD (DAX converted from EUR, SMIC converted from CHF)
- 1990-1999: CHF from FRED (DEXSZUS), DEM from FRED (EXGEUS), EUR from frankfurter.app (1999 only), Gold from London PM fix monthly averages, SP500TR/DAX/SMI from Yahoo
- SMIC from 1995 (SMIC.SW), 2000-2015 from Yahoo, 2016+ reconstructed from `^SSMI` with interpolated dividend ratio
- EUR starts Jan 1999, SMIC starts Mar 1995

### Commodity & Consumer Prices (`commodities_quarterly.csv`)
- Built by `build_commodities.py` from World Bank, Eurostat, and HICP data
- Energy: Benzin, Kohle, Erdgas (wholesale + Haushalt), Strom — all EUR
- Food: Brot, Bier, Cola, Milch, Eier, Käse, Schwein, Rind, Hähnchen — EUR, derived from HICP indices anchored to 2020 retail prices
- Metals: Stahl, Aluminium, Kupfer, Messing — EUR/t
- Source files: `wb_commodities.xlsx`, `hicp_*.tsv`, Eurostat API

## Data Sources

- **FX rates (CHF, EUR)**: ECB data via `api.frankfurter.app` (1999+), FRED for pre-1999 CHF/DEM (fetched with `curl`, not `urllib` — APIs block requests without proper User-Agent)
- **Gold**: Yahoo Finance (2000+), London PM fix monthly averages for 1990s
- **S&P 500 TR, DAX, SMIC**: Yahoo Finance v8 chart API (`query1.finance.yahoo.com`), requires `User-Agent` header
- **Commodity prices**: World Bank Pink Sheet (`wb_commodities.xlsx`)
- **Energy prices (DE)**: Eurostat electricity (`nrg_pc_204`) and gas (`nrg_pc_202`), semi-annual
- **Food prices (DE)**: Eurostat HICP monthly indices (`prc_hicp_midx`), pre-downloaded as `hicp_*.tsv`
- Python `ssl` module has certificate issues on this machine — use `curl` subprocess for HTTP requests

## Commands

```bash
# Regenerate the interactive asset chart
python3 plot_monthly.py

# Open chart in browser
open chf_usd_monthly_plot.html

# Rebuild commodity prices from sources
python3 build_commodities.py
```

## Dependencies

- Python 3 with `pandas`, `plotly`, `numpy`, `openpyxl`
- `yfinance` installed but Yahoo API is accessed via `curl` due to SSL issues
- Use `python3` (not `python`), avoid port 5000 (macOS AirPlay)

## Versioning
- commite alle Änderungen mit `git commit -m "Beschreibung der Änderung"`
- pushen mit `git push origin main`

# Arbeitsweise

- Führe alle Änderungen direkt aus ohne vorher zu fragen
- Kein "Soll ich das wirklich tun?" — einfach machen
- Bei Datei-Operationen: direkt schreiben/löschen
- Tests nach jeder Änderung automatisch ausführen
- Nur fragen wenn echte Ambiguität besteht (z.B. zwei komplett verschiedene Lösungsansätze)