# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Financial data analysis and visualization project. Monthly end-of-month asset prices since 2000, with interactive Plotly charts.

## Data

- `chf_usd_monthly.csv`: Monthly end-of-month quotes with columns: `date`, `USD_CHF`, `USD_EUR`, `USD_XAU`, `USD_SP500TR`, `USD_DAX`, `USD_SMIC`
- All values are in USD (DAX converted from EUR, SMIC converted from CHF)
- SMIC data 2000-2015 from Yahoo `SMIC.SW`, 2016+ reconstructed from `^SSMI` with interpolated dividend ratio
- Gold data starts Aug 2000 (first complete row for all instruments)

## Data Sources

- **FX rates (CHF, EUR)**: ECB data via `api.frankfurter.app` (fetched with `curl`, not `urllib` — the API blocks requests without proper User-Agent)
- **Gold, S&P 500 TR, DAX, SMIC**: Yahoo Finance v8 chart API (`query1.finance.yahoo.com`), requires `User-Agent` header
- Python `ssl` module has certificate issues on this machine — use `curl` subprocess for HTTP requests

## Commands

```bash
# Regenerate the interactive plot
python3 plot_monthly.py

# Open plot in browser
open chf_usd_monthly_plot.html
```

## Dependencies

- Python 3 with `pandas`, `plotly`
- `yfinance` installed but Yahoo API is accessed via `curl` due to SSL issues
- Use `python3` (not `python`), avoid port 5000 (macOS AirPlay)

## Versioning
- commite alle Änderungen mit `git commit -m "Beschreibung der Änderung"`
- pushen mit `git push origin main`