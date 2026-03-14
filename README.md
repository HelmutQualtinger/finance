# Finance — Asset & Commodity Price Data

Two datasets tracking financial assets and commodity/consumer prices, with interactive Plotly charts.

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

## Usage

```bash
# Generate the interactive asset chart
python3 plot_monthly.py
open chf_usd_monthly_plot.html

# Rebuild commodity prices from sources
python3 build_commodities.py
```

## Data Sources

- **FX rates**: ECB via `api.frankfurter.app` (1999+), FRED for pre-1999 CHF/DEM
- **Gold, S&P 500 TR, DAX, SMIC**: Yahoo Finance API
- **Commodity prices**: World Bank Pink Sheet (`wb_commodities.xlsx`)
- **Energy prices (DE)**: Eurostat (electricity `nrg_pc_204`, gas `nrg_pc_202`)
- **Food prices (DE)**: Eurostat HICP indices, anchored to 2020 retail prices

## Requirements

- Python 3 with `pandas`, `plotly`, `numpy`, `openpyxl`