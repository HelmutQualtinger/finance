# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Financial data analysis and visualization project with three main areas:
1. Monthly end-of-month asset prices since 1990 (USD) with interactive Plotly charts
2. Quarterly commodity and consumer prices since 1990 (EUR, Germany-focused)
3. UBS Kontoauszug analysis — interactive HTML + PDF reports from CSV and PDF sources
4. UBS Kreditkarten analysis — interactive HTML + PDF reports from credit card PDF

### Reports
- `Gold_vs_Aktien_Bericht.docx` — Vergleichsbericht Gold vs. Aktien
- `wetterbericht_schweiz.docx` — Wetterbericht Schweiz
- `wetter_rebstein.docx` — Wetterbericht Rebstein

### Wetterberichte (16-Tage-Vorhersagen)
Statische HTML-Dateien mit 16-Tage-Wettervorhersagen, generiert von Claude auf Anfrage.
Datenquelle: Open-Meteo.com (kostenloses Wetter-API, kein Key nötig).
Format: Tabelle mit Tag, Wetterlage (Emoji), Max/Min-Temperatur, Niederschlag, Windstärke.

Standorte:
- `wetter_rebstein_16tage.html` — Rebstein SG, Schweiz (47.4°N, 9.57°E)
- `wetter_rebstein.html` — Rebstein SG (älterer Bericht)
- `wetterbericht_schweiz.html` — Schweiz (allgemein)
- `wetter_ffb.html` — Fürstenfeldbruck, Bayern
- `wettervorhersage_ottakring.html` — Ottakring, Wien
- `wetter_schaerding_16tage.html` — Schärding, Oberösterreich
- `wetter_neudauberg_16tage.html` — Neudauberg
- `wetter_wilhelminenberg_16tage.html` — Wien Wilhelminenberg

Docx-Berichte: `wetterbericht_schweiz.docx`, `wetter_rebstein.docx`

### UBS Kontoauszug Analyse
- `analyze_ubs.py` — Parst `ubstrans.csv`, generiert `ubstrans_analyse.html` + `ubstrans_analyse.pdf`
- `build_pdf_analyse.py` — Extrahiert Transaktionen aus PDF-Kontoauszug, generiert `pdf_analyse.html` + `pdf_analyse.pdf`
- Beide HTML-Berichte: 4 Themes, Jahr-Tabs, SVG-Tortendiagramme, aufklappbare Monatsdetails
- E-Mail-Versand: Python `smtplib` via `qualcunodue@gmail.com` (App-Passwort in memory)

### Pension Calculator
- `pension.py` — CLI-Tool: Berechnet Endkapital einer monatlichen Renteneinzahlung mit Zinseszins
- Aufruf: `python3 pension.py <monatlicher_betrag> <jahreszins_%> <jahre>`
- Ausgabe: Einzahlungssumme, Zinserträge, Endkapital, Multiplikationsfaktor

### UBS Kreditkarten Analyse
- `build_kreditkarten_analyse.py` — Hardcoded transactions aus `transactions-KreditKarten.pdf` (10 Seiten, 105 Transaktionen, 01.01.2024–21.03.2026)
- Generiert `kreditkarten_analyse.html` + `kreditkarten_analyse.pdf`
- HTML: 4 Themes, Jahr-Tabs, SVG-Tortendiagramme, aufklappbare Monatsdetails, PDF-Link im Header
- PDF: ReportLab A4, matplotlib Tortendiagramme, Gegenpartei-Tabellen pro Jahr
- Karte 64744 D 001 — Total: Belastung CHF 5'260.92, Gutschrift CHF 5'500.65

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

# Regenerate UBS CSV-based HTML + PDF analysis
python3 analyze_ubs.py

# Regenerate UBS PDF-based HTML + PDF analysis
python3 build_pdf_analyse.py

# Open analyses in browser
open ubstrans_analyse.html
open pdf_analyse.html

# Regenerate Kreditkarten HTML + PDF analysis
python3 build_kreditkarten_analyse.py
open kreditkarten_analyse.html
```

## Dependencies

- Python 3 with `pandas`, `plotly`, `numpy`, `openpyxl`, `reportlab`, `matplotlib`
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