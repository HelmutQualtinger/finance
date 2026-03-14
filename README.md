# Finance — Monthly Asset Performance

Interactive chart comparing major asset classes since 2000, normalized to a common base date.

## Assets Tracked

| Ticker | Description |
|--------|-------------|
| CHF/USD | Swiss Franc exchange rate |
| EUR/USD | Euro exchange rate |
| XAU | Gold price |
| S&P 500 TR | S&P 500 Total Return |
| DAX | German stock index (converted to USD) |
| SMIC | Swiss Market Index Total Return (converted to USD) |

All values are in USD. Monthly end-of-month data starting from August 2000.

## Usage

```bash
# Generate the interactive Plotly chart
python3 plot_monthly.py

# Open in browser
open chf_usd_monthly_plot.html
```

## Data Sources

- **FX rates (CHF, EUR)**: ECB via `api.frankfurter.app`
- **Gold, S&P 500 TR, DAX, SMIC**: Yahoo Finance API

## Requirements

- Python 3
- `pandas`, `plotly`