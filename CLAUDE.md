# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Financial data analysis and visualization project. Monthly end-of-month asset prices since 1990, with interactive Plotly charts.

## Data

- `chf_usd_monthly.csv`: Monthly end-of-month quotes with columns: `date`, `USD_CHF`, `USD_EUR`, `USD_XAU`, `USD_SP500TR`, `USD_DAX`, `USD_SMIC`
- All values are in USD (DAX converted from EUR, SMIC converted from CHF)
- 1990-1999 data: CHF from FRED (DEXSZUS), DEM from FRED (EXGEUS), EUR from frankfurter.app (1999 only), Gold from London PM fix monthly averages, SP500TR/DAX/SMI from Yahoo
- SMIC data from 1995 (SMIC.SW), 2000-2015 from Yahoo, 2016+ reconstructed from `^SSMI` with interpolated dividend ratio
- EUR data starts Jan 1999 (currency introduction), SMIC starts Mar 1995

## Data Sources

- **FX rates (CHF, EUR)**: ECB data via `api.frankfurter.app` (1999+), FRED for pre-1999 CHF/DEM (fetched with `curl`, not `urllib` — APIs block requests without proper User-Agent)
- **Gold**: Yahoo Finance (2000+), London PM fix monthly averages for 1990s
- **S&P 500 TR, DAX, SMIC**: Yahoo Finance v8 chart API (`query1.finance.yahoo.com`), requires `User-Agent` header
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

# Arbeitsweise

- Führe alle Änderungen direkt aus ohne vorher zu fragen
- Kein "Soll ich das wirklich tun?" — einfach machen
- Bei Datei-Operationen: direkt schreiben/löschen
- Tests nach jeder Änderung automatisch ausführen
- Nur fragen wenn echte Ambiguität besteht (z.B. zwei komplett verschiedene Lösungsansätze)