#!/usr/bin/env python3
"""
Generiert wetter_wilhelminenberg_3h.html (72h, 3-stündig)
und wetter_wilhelminenberg_16tage.html (16-Tage-Vorhersage)
für Wien Wilhelminenberg (48.22°N, 16.28°E, 366m).
"""
import json, subprocess, math
from datetime import datetime

LAT, LON = 48.22, 16.28
ALT = 366
ORT = "Wien Wilhelminenberg"

# ---- API-Abruf ----
url = (
    f"https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    f"&hourly=temperature_2m,precipitation,windspeed_10m,winddirection_10m,weathercode"
    f"&daily=weathercode,temperature_2m_max,temperature_2m_min,"
    f"precipitation_sum,windspeed_10m_max,winddirection_10m_dominant"
    f"&timezone=Europe%2FVienna&forecast_days=16"
)
result = subprocess.run(["curl", "-s", url], capture_output=True, text=True)
data = json.loads(result.stdout)
hourly = data["hourly"]
daily  = data["daily"]
created = datetime.now().strftime("%-d. %B %Y, %H:%M")

# ---- Hilfsfunktionen ----
WC_MAP = {
    0:  ("☀️",  "Klar"),
    1:  ("🌤️", "Überwiegend klar"),
    2:  ("⛅",  "Teils bewölkt"),
    3:  ("☁️",  "Bewölkt"),
    45: ("🌫️", "Nebel"),
    48: ("🌫️", "Nebel (Raureif)"),
    51: ("🌦️", "Leichter Nieselregen"),
    53: ("🌦️", "Nieselregen"),
    55: ("🌧️", "Starker Nieselregen"),
    61: ("🌧️", "Leichter Regen"),
    63: ("🌧️", "Regen"),
    65: ("🌧️", "Starker Regen"),
    71: ("❄️",  "Leichter Schnee"),
    73: ("❄️",  "Schnee"),
    75: ("❄️",  "Starker Schnee"),
    77: ("🌨️", "Schneegriesel"),
    80: ("🌦️", "Regenschauer"),
    81: ("🌧️", "Regenschauer"),
    82: ("⛈️",  "Starke Schauer"),
    85: ("🌨️", "Schneeschauer"),
    86: ("❄️",  "Starke Schneeschauer"),
    95: ("⛈️",  "Gewitter"),
    96: ("⛈️",  "Gewitter mit Hagel"),
    99: ("⛈️",  "Starkes Gewitter"),
}

DAYS_DE = ["Mo","Di","Mi","Do","Fr","Sa","So"]
MONTHS_DE = ["","Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"]

def wc_info(code):
    code = int(code) if code else 0
    return WC_MAP.get(code, ("🌡️", f"Code {code}"))

def beaufort(kmh):
    bft = 0
    thresholds = [1,6,12,20,29,39,50,62,75,89,103,117]
    for t in thresholds:
        if kmh >= t:
            bft += 1
        else:
            break
    return bft

BFT_LABEL = {
    0:"Windstille",1:"Leiser Zug",2:"Leichte Brise",3:"Schwache Brise",
    4:"Mäßige Brise",5:"Frische Brise",6:"Starker Wind",7:"Steifer Wind",
    8:"Stürmischer Wind",9:"Sturm",10:"Schwerer Sturm",11:"Orkanartiger Sturm",12:"Orkan"
}

def wind_vane(deg, kmh):
    """SVG-Windfahne mit Richtungspfeil und Beaufort-Stärke."""
    deg = deg if deg is not None else 0
    bft = beaufort(kmh if kmh else 0)
    # Farbe nach Stärke
    if bft <= 2:   col = "#27ae60"
    elif bft <= 4: col = "#f39c12"
    elif bft <= 6: col = "#e67e22"
    else:          col = "#c0392b"
    # SVG-Kreis mit Pfeil, rotiert
    return (
        f'<span title="{deg}° | {kmh:.0f} km/h | Bft {bft} ({BFT_LABEL.get(bft,"")})" '
        f'style="display:inline-flex;align-items:center;gap:4px;">'
        f'<svg width="22" height="22" viewBox="0 0 22 22" style="flex-shrink:0">'
        f'<circle cx="11" cy="11" r="10" fill="#ecf0f1" stroke="#bdc3c7" stroke-width="1"/>'
        f'<g transform="rotate({deg} 11 11)">'
        f'<polygon points="11,2 8,14 11,12 14,14" fill="{col}"/>'
        f'</g>'
        f'</svg>'
        f'<small style="color:#555;font-size:11px">Bft {bft}</small>'
        f'</span>'
    )

def fmt_date_daily(iso):
    dt = datetime.strptime(iso, "%Y-%m-%d")
    wd = DAYS_DE[dt.weekday()]
    return f"{wd} {dt.day:02d}.{dt.month:02d}."

def fmt_time_hourly(iso):
    dt = datetime.strptime(iso, "%Y-%m-%dT%H:%M")
    wd = DAYS_DE[dt.weekday()]
    return f"{wd} {dt.day:02d}.{dt.month:02d}. {dt.hour:02d}:00"

# ---- Banner SVG (Wilhelminenberg Schloss Silhouette) ----
BANNER_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200" style="width:100%;display:block;border-radius:10px 10px 0 0">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1a3a5c"/>
      <stop offset="60%" stop-color="#2e6da4"/>
      <stop offset="100%" stop-color="#a8c8e8"/>
    </linearGradient>
    <linearGradient id="hill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#2d5a27"/>
      <stop offset="100%" stop-color="#1a3a18"/>
    </linearGradient>
  </defs>
  <!-- Himmel -->
  <rect width="800" height="200" fill="url(#sky)"/>
  <!-- Sterne/Punkte -->
  <circle cx="50" cy="20" r="1.2" fill="white" opacity="0.8"/>
  <circle cx="120" cy="35" r="1" fill="white" opacity="0.6"/>
  <circle cx="200" cy="15" r="1.4" fill="white" opacity="0.7"/>
  <circle cx="350" cy="25" r="1" fill="white" opacity="0.5"/>
  <circle cx="600" cy="18" r="1.2" fill="white" opacity="0.8"/>
  <circle cx="720" cy="30" r="0.9" fill="white" opacity="0.6"/>
  <circle cx="770" cy="12" r="1.1" fill="white" opacity="0.7"/>
  <!-- Mond -->
  <circle cx="680" cy="35" r="18" fill="#f5e642" opacity="0.9"/>
  <circle cx="693" cy="28" r="14" fill="#2e6da4"/>
  <!-- Wolken -->
  <ellipse cx="150" cy="55" rx="60" ry="18" fill="white" opacity="0.15"/>
  <ellipse cx="190" cy="50" rx="40" ry="14" fill="white" opacity="0.1"/>
  <ellipse cx="500" cy="65" rx="70" ry="16" fill="white" opacity="0.12"/>
  <!-- Hügel Hintergrund -->
  <path d="M0,160 Q100,100 200,120 Q300,90 400,110 Q500,95 600,115 Q700,100 800,130 L800,200 L0,200 Z" fill="#1a3a18" opacity="0.6"/>
  <!-- Haupthügel Wilhelminenberg -->
  <path d="M0,185 Q50,130 150,120 Q250,100 350,115 Q430,108 500,120 Q580,115 650,130 Q720,140 800,150 L800,200 L0,200 Z" fill="url(#hill)"/>
  <!-- Bäume links -->
  <g fill="#1a3a18">
    <polygon points="40,155 55,110 70,155"/>
    <polygon points="60,160 78,112 96,160"/>
    <polygon points="85,158 100,115 115,158"/>
    <polygon points="110,162 127,118 144,162"/>
  </g>
  <!-- Schloss Wilhelminenberg (Mitte) -->
  <g transform="translate(330,70)">
    <!-- Hauptgebäude -->
    <rect x="0" y="50" width="140" height="65" fill="#d4b896"/>
    <rect x="10" y="55" width="120" height="60" fill="#c9a87c"/>
    <!-- Mittelturm -->
    <rect x="55" y="20" width="30" height="50" fill="#b8956a"/>
    <!-- Turmspitze -->
    <polygon points="70,0 55,20 85,20" fill="#8b4513"/>
    <!-- Flagge -->
    <line x1="70" y1="0" x2="70" y2="-15" stroke="#555" stroke-width="1.5"/>
    <polygon points="70,-15 85,-8 70,-1" fill="#cc0000"/>
    <!-- Fenster -->
    <rect x="20" y="70" width="15" height="20" fill="#4a6fa5" rx="2"/>
    <rect x="45" y="70" width="15" height="20" fill="#4a6fa5" rx="2"/>
    <rect x="80" y="70" width="15" height="20" fill="#4a6fa5" rx="2"/>
    <rect x="105" y="70" width="15" height="20" fill="#4a6fa5" rx="2"/>
    <!-- Türmchen links -->
    <rect x="-15" y="35" width="20" height="45" fill="#b8956a"/>
    <polygon points="-5,20 -15,35 5,35" fill="#8b4513"/>
    <!-- Türmchen rechts -->
    <rect x="135" y="35" width="20" height="45" fill="#b8956a"/>
    <polygon points="145,20 135,35 155,35" fill="#8b4513"/>
    <!-- Eingang -->
    <rect x="60" y="90" width="20" height="25" fill="#3a2a1a" rx="2"/>
    <!-- Sockel -->
    <rect x="-5" y="115" width="150" height="8" fill="#a08060"/>
  </g>
  <!-- Bäume rechts -->
  <g fill="#1a3a18">
    <polygon points="610,148 627,105 644,148"/>
    <polygon points="635,152 652,108 669,152"/>
    <polygon points="660,150 678,106 696,150"/>
    <polygon points="690,155 708,112 726,155"/>
  </g>
  <!-- Wien Stadtsilhouette im Hintergrund -->
  <g fill="#1a3a5c" opacity="0.4">
    <rect x="20" y="140" width="8" height="30"/>
    <rect x="35" y="135" width="12" height="35"/>
    <rect x="750" y="138" width="10" height="32"/>
    <rect x="768" y="132" width="14" height="38"/>
    <rect x="785" y="140" width="8" height="30"/>
  </g>
  <!-- Titel -->
  <text x="400" y="185" font-family="Georgia,serif" font-size="22" fill="white"
        text-anchor="middle" opacity="0.95" font-weight="bold"
        style="text-shadow:1px 1px 3px rgba(0,0,0,0.8)">
    Wien · Wilhelminenberg · 366 m
  </text>
</svg>
""".strip()

# ================================================================
# 1) 72h / 3-stündige Vorhersage
# ================================================================
rows_3h = []
for i in range(0, 72, 3):
    t   = hourly["time"][i]
    tmp = hourly["temperature_2m"][i]
    pre = hourly["precipitation"][i]
    ws  = hourly["windspeed_10m"][i]
    wd  = hourly["winddirection_10m"][i]
    wc  = hourly["weathercode"][i]
    emoji, desc = wc_info(wc)
    vane = wind_vane(wd, ws)
    pre_str = f'<span style="color:#2980b9">{pre:.1f} mm</span>' if pre and pre > 0 else '<span style="color:#aaa">—</span>'
    rows_3h.append(
        f'<tr>'
        f'<td class="day-name">{fmt_time_hourly(t)}</td>'
        f'<td>{emoji} {desc}</td>'
        f'<td class="temp-max">{tmp:.1f}</td>'
        f'<td>{pre_str}</td>'
        f'<td>{vane}</td>'
        f'</tr>'
    )

html_3h = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wetterbericht {ORT} – 72h</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 820px; margin: 20px auto;
         padding: 0 12px; background: #f0f4f8; color: #2c3e50; }}
  .card {{ background: #fff; border-radius: 10px; overflow: hidden;
           box-shadow: 0 4px 16px rgba(0,0,0,0.12); margin-bottom: 20px; }}
  .subtitle {{ text-align: center; color: #7f8c8d; padding: 12px 0 6px; font-size: 15px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ background: #2c3e50; color: #fff; padding: 10px 8px; font-size: 13px; }}
  td {{ padding: 9px 8px; border-bottom: 1px solid #ecf0f1; font-size: 13px; text-align: center; vertical-align: middle; }}
  tr:hover {{ background: #f7f9fc; }}
  tr:nth-child(odd) {{ background: #fafbfc; }}
  tr:nth-child(odd):hover {{ background: #f0f4f8; }}
  .day-name {{ text-align: left; font-weight: 600; white-space: nowrap; }}
  .temp-max {{ color: #e74c3c; font-weight: bold; }}
  .source {{ text-align: center; color: #95a5a6; font-size: 11px; padding: 10px; }}
  /* Tag-Trennlinien alle 8 Zeilen (= 1 Tag) */
  tr:nth-child(8n) td {{ border-bottom: 3px solid #bdc3c7; }}
</style>
</head>
<body>
<div class="card">
{BANNER_SVG}
<p class="subtitle">72-Stunden-Vorhersage · 3-stündiges Intervall · erstellt am {created}</p>
<table>
<thead>
<tr>
  <th style="text-align:left">Zeitpunkt</th>
  <th>Wetter</th>
  <th>Temp °C</th>
  <th>Niederschlag</th>
  <th>Wind &amp; Richtung</th>
</tr>
</thead>
<tbody>
{''.join(rows_3h)}
</tbody>
</table>
<p class="source">Datenquelle: Open-Meteo.com ({LAT}°N, {LON}°E, {ALT}m) · Windfahne zeigt Herkunftsrichtung · Beaufort-Skala</p>
</div>
</body>
</html>"""

with open("wetter_wilhelminenberg_3h.html", "w", encoding="utf-8") as f:
    f.write(html_3h)
print("✓ wetter_wilhelminenberg_3h.html erstellt")

# ================================================================
# 2) 16-Tage-Vorhersage
# ================================================================
rows_16 = []
for i in range(len(daily["time"])):
    d   = daily["time"][i]
    wc  = daily["weathercode"][i]
    tmax = daily["temperature_2m_max"][i]
    tmin = daily["temperature_2m_min"][i]
    pre  = daily["precipitation_sum"][i]
    ws   = daily["windspeed_10m_max"][i]
    wd   = daily["winddirection_10m_dominant"][i]
    emoji, desc = wc_info(wc)
    vane = wind_vane(wd, ws)
    pre_str = f'<span style="color:#2980b9">{pre:.1f} mm</span>' if pre and pre > 0 else '<span style="color:#aaa">—</span>'
    rows_16.append(
        f'<tr>'
        f'<td class="day-name">{fmt_date_daily(d)}</td>'
        f'<td>{emoji} {desc}</td>'
        f'<td class="temp-max">{tmax:.1f}</td>'
        f'<td class="temp-min">{tmin:.1f}</td>'
        f'<td>{pre_str}</td>'
        f'<td>{vane}</td>'
        f'</tr>'
    )

# Datumsbereich
d0 = datetime.strptime(daily["time"][0],  "%Y-%m-%d")
d1 = datetime.strptime(daily["time"][-1], "%Y-%m-%d")
daterange = (f"{d0.day}. {MONTHS_DE[d0.month]} – {d1.day}. {MONTHS_DE[d1.month]} {d1.year}")

html_16 = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wetterbericht {ORT} – 16 Tage</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 820px; margin: 20px auto;
         padding: 0 12px; background: #f0f4f8; color: #2c3e50; }}
  .card {{ background: #fff; border-radius: 10px; overflow: hidden;
           box-shadow: 0 4px 16px rgba(0,0,0,0.12); margin-bottom: 20px; }}
  .subtitle {{ text-align: center; color: #7f8c8d; padding: 12px 0 6px; font-size: 15px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ background: #2c3e50; color: #fff; padding: 10px 8px; font-size: 13px; }}
  td {{ padding: 9px 8px; border-bottom: 1px solid #ecf0f1; font-size: 13px; text-align: center; vertical-align: middle; }}
  tr:hover {{ background: #f7f9fc; }}
  tr:nth-child(odd) {{ background: #fafbfc; }}
  tr:nth-child(odd):hover {{ background: #f0f4f8; }}
  .day-name {{ text-align: left; font-weight: 600; white-space: nowrap; }}
  .temp-max {{ color: #e74c3c; font-weight: bold; }}
  .temp-min {{ color: #2980b9; font-weight: bold; }}
  .source {{ text-align: center; color: #95a5a6; font-size: 11px; padding: 10px; }}
</style>
</head>
<body>
<div class="card">
{BANNER_SVG}
<p class="subtitle">16-Tage-Vorhersage · {daterange} · erstellt am {created}</p>
<table>
<thead>
<tr>
  <th style="text-align:left">Tag</th>
  <th>Wetter</th>
  <th>Max °C</th>
  <th>Min °C</th>
  <th>Niederschlag</th>
  <th>Wind &amp; Richtung</th>
</tr>
</thead>
<tbody>
{''.join(rows_16)}
</tbody>
</table>
<p class="source">Datenquelle: Open-Meteo.com ({LAT}°N, {LON}°E, {ALT}m) · Windfahne zeigt Herkunftsrichtung · Beaufort-Skala</p>
</div>
</body>
</html>"""

with open("wetter_wilhelminenberg_16tage.html", "w", encoding="utf-8") as f:
    f.write(html_16)
print("✓ wetter_wilhelminenberg_16tage.html erstellt")