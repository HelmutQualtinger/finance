import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

df = pd.read_csv('chf_usd_monthly.csv', parse_dates=['date'])

# Normalize all series to 100 at first common data point
cols = ['USD_CHF', 'USD_EUR', 'USD_XAU', 'USD_SP500TR', 'USD_DAX', 'USD_SMIC']
df_clean = df.dropna(subset=cols)
base = df_clean.iloc[0]
base_date = base['date'].strftime('%Y-%m-%d')

fig = make_subplots(specs=[[{"secondary_y": True}]])

labels = {
    'USD_CHF': 'CHF/USD',
    'USD_EUR': 'EUR/USD',
    'USD_XAU': 'Gold (XAU)',
    'USD_SP500TR': 'S&P 500 TR',
    'USD_DAX': 'DAX',
    'USD_SMIC': 'SMIC (SMI TR)',
}

colors = {
    'USD_CHF': '#e74c3c',
    'USD_EUR': '#3498db',
    'USD_XAU': '#f1c40f',
    'USD_SP500TR': '#2ecc71',
    'USD_DAX': '#9b59b6',
    'USD_SMIC': '#e67e22',
}

for col in cols:
    normalized = (df[col] / base[col]) * 100
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=normalized,
        name=labels[col],
        line=dict(color=colors[col], width=2),
        hovertemplate=f'{labels[col]}<br>%{{x|%b %Y}}<br>Index: %{{y:.1f}}<br>Value: %{{customdata:.2f}}<extra></extra>',
        customdata=df[col],
    ))

fig.add_hline(y=100, line_dash="dot", line_color="gray", opacity=0.5)

fig.update_layout(
    title=f'Monthly Asset Performance (Indexed to 100 at {base_date})',
    xaxis_title='',
    yaxis_title='Index (100 = Aug 2000)',
    template='plotly_dark',
    hovermode='x unified',
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.02,
        xanchor='center',
        x=0.5,
    ),
    height=700,
    margin=dict(t=100),
)

fig.update_yaxes(type='log', dtick=0.30103)

fig.write_html('chf_usd_monthly_plot.html', include_plotlyjs=True)
print(f'Plot saved to chf_usd_monthly_plot.html (base: {base_date})')