#!/usr/bin/env python3
"""Generate Schärding weather HTML files (dark theme, real photos, wind arrows)."""
import json, subprocess, datetime

# ── Helpers ──────────────────────────────────────────────────────────────────

WC_MAP = {
    0: ("☀️", "Klar"),
    1: ("🌤️", "Überwiegend klar"),
    2: ("⛅", "Teils bewölkt"),
    3: ("☁️", "Bewölkt"),
    45: ("🌫️", "Nebel"),
    48: ("🌫️", "Reifnebel"),
    51: ("🌦️", "Leichter Nieselregen"),
    53: ("🌦️", "Nieselregen"),
    55: ("🌧️", "Starker Nieselregen"),
    61: ("🌧️", "Leichter Regen"),
    63: ("🌧️", "Regen"),
    65: ("🌧️", "Starker Regen"),
    71: ("🌨️", "Leichter Schneefall"),
    73: ("🌨️", "Schneefall"),
    75: ("❄️", "Starker Schneefall"),
    77: ("🌨️", "Schneekörner"),
    80: ("🌦️", "Regenschauer"),
    81: ("🌦️", "Regenschauer"),
    82: ("⛈️", "Starke Schauer"),
    85: ("🌨️", "Schneeschauer"),
    86: ("❄️", "Starke Schneeschauer"),
    95: ("⛈️", "Gewitter"),
    96: ("⛈️", "Gewitter m. Hagel"),
    99: ("⛈️", "Schweres Gewitter"),
}

DIRS = ["N", "NO", "O", "SO", "S", "SW", "W", "NW"]
ARROWS_TO = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]  # direction wind blows TO

def wind_label(deg, speed):
    """Returns compass label, arrow, Beaufort."""
    d_idx = round(deg / 45) % 8
    label = DIRS[d_idx]
    # arrow points where wind blows TO (from_dir + 180°)
    a_idx = round(((deg + 180) % 360) / 45) % 8
    arrow = ARROWS_TO[a_idx]
    bft = (0 if speed < 1 else 1 if speed < 6 else 2 if speed < 12 else
           3 if speed < 20 else 4 if speed < 29 else 5 if speed < 39 else
           6 if speed < 50 else 7 if speed < 62 else 8 if speed < 75 else 9)
    return label, arrow, bft

def wcode(code):
    return WC_MAP.get(code, ("🌡️", f"Code {code}"))

def day_name_de(date_str):
    dt = datetime.date.fromisoformat(date_str)
    DAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    return f"{DAYS[dt.weekday()]} {dt.day:02d}.{dt.month:02d}."

def is_weekend(date_str):
    return datetime.date.fromisoformat(date_str).weekday() >= 5

def hour_label(dt_str):  # "2026-03-27T15:00" → "15:00"
    return dt_str[11:16]

def day_label_long(dt_str):
    DAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    MONTHS = ["", "Januar", "Februar", "März", "April", "Mai", "Juni",
              "Juli", "August", "September", "Oktober", "November", "Dezember"]
    dt = datetime.date.fromisoformat(dt_str[:10])
    return f"{DAYS[dt.weekday()]}, {dt.day}. {MONTHS[dt.month]} {dt.year}"

# ── Fetch data ────────────────────────────────────────────────────────────────

url = ("https://api.open-meteo.com/v1/forecast"
       "?latitude=48.45&longitude=13.43"
       "&daily=weathercode,temperature_2m_max,temperature_2m_min,"
       "precipitation_sum,windspeed_10m_max,winddirection_10m_dominant"
       "&hourly=temperature_2m,precipitation,windspeed_10m,winddirection_10m,weathercode"
       "&forecast_days=16&timezone=Europe%2FVienna")

raw = subprocess.check_output(["curl", "-s", url])
data = json.loads(raw)
dd = data["daily"]
hh = data["hourly"]

today_str = dd["time"][0]
today_dt  = datetime.date.fromisoformat(today_str)
MONTHS_DE = ["", "Januar", "Februar", "März", "April", "Mai", "Juni",
             "Juli", "August", "September", "Oktober", "November", "Dezember"]
today_long = f"{today_dt.day}. {MONTHS_DE[today_dt.month]} {today_dt.year}"

# ── Shared CSS (dark theme) ───────────────────────────────────────────────────

DARK_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Segoe UI', Arial, sans-serif;
  max-width: 840px; margin: 20px auto; padding: 0 15px;
  background: #0d1117; color: #c9d1d9;
}
.banner {
  width: 100%; border-radius: 12px; overflow: hidden;
  margin-bottom: 24px; box-shadow: 0 6px 24px rgba(0,0,0,0.6);
  position: relative; height: 200px;
}
.banner img {
  width: 100%; height: 100%; object-fit: cover; object-position: center 60%;
  display: block; filter: brightness(0.55) saturate(1.1);
}
.banner-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.55) 100%);
  display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 6px;
}
.banner-title {
  font-size: 2em; font-weight: 700; color: #fff;
  text-shadow: 0 2px 12px rgba(0,0,0,0.8); letter-spacing: 1px;
  font-family: Georgia, serif;
}
.banner-sub {
  font-size: 0.82em; color: #cce; letter-spacing: 2.5px;
  text-shadow: 0 1px 6px rgba(0,0,0,0.8); text-transform: uppercase;
}
.banner-coord {
  font-size: 0.75em; color: #99aacc;
  text-shadow: 0 1px 4px rgba(0,0,0,0.8);
}
.banner-photo-credit {
  position: absolute; bottom: 5px; right: 10px;
  font-size: 10px; color: rgba(200,210,230,0.6);
}
h1 {
  text-align: center; color: #e6edf3; font-size: 1.5em; margin-bottom: 4px;
}
.subtitle {
  text-align: center; color: #8b949e; margin-bottom: 22px; font-size: 0.93em;
}
h2 {
  color: #58a6ff; font-size: 1.1em; margin: 28px 0 10px;
  border-left: 3px solid #58a6ff; padding-left: 10px;
}
table {
  width: 100%; border-collapse: collapse;
  background: #161b22; border-radius: 10px; overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.4); margin-bottom: 6px;
}
th {
  background: #21262d; color: #8b949e; padding: 11px 8px;
  font-size: 12px; letter-spacing: 0.06em; text-transform: uppercase;
  border-bottom: 1px solid #30363d;
}
td {
  padding: 10px 8px; text-align: center;
  border-bottom: 1px solid #21262d; font-size: 13px;
}
tr:last-child td { border-bottom: none; }
tr:hover td { background: #1c2128; }
.day-name { text-align: left; font-weight: 600; padding-left: 14px; color: #e6edf3; }
.wknd td { background: #13181f; }
.wknd:hover td { background: #1c2128; }
.temp-max { color: #ff7b72; font-weight: bold; }
.temp-min { color: #79c0ff; font-weight: bold; }
.rain { color: #79c0ff; }
.wind-cell {
  display: flex; flex-direction: column; align-items: center;
  gap: 1px; font-size: 12px;
}
.wind-arrow { font-size: 1.3em; line-height: 1; color: #d2a8ff; }
.wind-kmh { color: #8b949e; font-size: 11px; }
.wind-bft { font-size: 10px; color: #58a6ff; font-weight: 600; }
.wind-dir { font-size: 11px; color: #c9d1d9; font-weight: 600; }

/* Day sections (3h) */
.day-header {
  background: #161b22; color: #58a6ff;
  text-align: center; padding: 9px 14px;
  font-weight: 600; font-size: 13px; letter-spacing: 0.05em;
  margin-top: 16px; border-radius: 8px 8px 0 0;
  border: 1px solid #30363d; border-bottom: none;
}
.night td { background: #0d1117; }
.night:hover td { background: #161b22; }
.source {
  text-align: center; color: #484f58; font-size: 11px;
  margin-top: 16px; padding-bottom: 12px; line-height: 1.7;
}
"""

PHOTO_URL = ("https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/"
             "Sch%C3%A4rding_-_Obere_Stadtplatz.JPG/"
             "1280px-Sch%C3%A4rding_-_Obere_Stadtplatz.JPG")

BANNER_HTML = f"""
<div class="banner">
  <img src="{PHOTO_URL}" alt="Schärding Stadtplatz" loading="eager">
  <div class="banner-overlay">
    <div class="banner-title">Schärding</div>
    <div class="banner-sub">Stadtplatz &middot; Oberösterreich</div>
    <div class="banner-coord">48.45&deg;N &nbsp;&middot;&nbsp; 13.43&deg;E &nbsp;&middot;&nbsp; 303 m ü.M.</div>
  </div>
  <div class="banner-photo-credit">© C.Stadler/Bwag, CC BY-SA 4.0 &nbsp;|&nbsp; Wikimedia Commons</div>
</div>
"""

def wind_cell(deg, speed):
    label, arrow, bft = wind_label(deg, speed)
    return (f'<td><div class="wind-cell">'
            f'<span class="wind-arrow">{arrow}</span>'
            f'<span class="wind-dir">{label}</span>'
            f'<span class="wind-kmh">{speed:.0f} km/h</span>'
            f'<span class="wind-bft">Bft {bft}</span>'
            f'</div></td>')

# ── 16-day HTML ───────────────────────────────────────────────────────────────

end_dt = datetime.date.fromisoformat(dd["time"][-1])
end_long = f"{end_dt.day}. {MONTHS_DE[end_dt.month]} {end_dt.year}"

rows_16 = []
for i in range(16):
    t      = dd["time"][i]
    tmax   = dd["temperature_2m_max"][i]
    tmin   = dd["temperature_2m_min"][i]
    prec   = dd["precipitation_sum"][i]
    wspd   = dd["windspeed_10m_max"][i]
    wdir   = dd["winddirection_10m_dominant"][i]
    wc     = dd["weathercode"][i]
    emoji, desc = wcode(wc)
    cls = ' class="wknd"' if is_weekend(t) else ""
    rows_16.append(
        f'<tr{cls}>'
        f'<td class="day-name">{day_name_de(t)}</td>'
        f'<td>{emoji} {desc}</td>'
        f'<td class="temp-max">{tmax}</td>'
        f'<td class="temp-min">{tmin}</td>'
        f'<td class="rain">{prec} mm</td>'
        + wind_cell(wdir, wspd) +
        f'</tr>'
    )

html_16 = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wetterbericht Schärding — 16 Tage</title>
<style>{DARK_CSS}</style>
</head>
<body>
{BANNER_HTML}
<h1>Wetterbericht Schärding, Oberösterreich</h1>
<p class="subtitle">16-Tage-Vorhersage &mdash; {today_long} bis {end_long}</p>

<table>
<thead>
<tr>
  <th>Tag</th><th>Wetter</th><th>Max °C</th><th>Min °C</th>
  <th>Niederschlag</th><th>Wind</th>
</tr>
</thead>
<tbody>
{"".join(rows_16)}
</tbody>
</table>

<p class="source">
  Datenquelle: Open-Meteo.com (48.45°N, 13.43°E, 303 m ü.M.) — erstellt am {today_long}<br>
  Foto: © C.Stadler/Bwag, CC BY-SA 4.0, Wikimedia Commons
</p>
</body>
</html>"""

with open("wetter_schaerding_16tage.html", "w", encoding="utf-8") as f:
    f.write(html_16)
print("✓ wetter_schaerding_16tage.html")

# ── 48h / 3h HTML ─────────────────────────────────────────────────────────────

# Group hourly into days (first 48 hours = 16 slots at 3h)
slots = list(range(0, 48, 3))
days = {}
for i in slots:
    dt_str = hh["time"][i]
    day = dt_str[:10]
    days.setdefault(day, []).append(i)

end_48h_dt = datetime.date.fromisoformat(hh["time"][45][:10])
end_48h_long = f"{end_48h_dt.day}. {MONTHS_DE[end_48h_dt.month]} {end_48h_dt.year}"

day_sections = []
for day_str, idxs in days.items():
    rows = []
    for i in idxs:
        t     = hh["time"][i]
        temp  = hh["temperature_2m"][i]
        prec  = hh["precipitation"][i]
        wspd  = hh["windspeed_10m"][i]
        wdir  = hh["winddirection_10m"][i]
        wc    = hh["weathercode"][i]
        emoji, desc = wcode(wc)
        h_int = int(t[11:13])
        is_night = (h_int < 6 or h_int >= 21)
        cls = ' class="night"' if is_night else ""
        tc = "temp-max" if temp >= 15 else "temp-min" if temp < 5 else ""
        rows.append(
            f'<tr{cls}>'
            f'<td style="font-weight:600;color:#e6edf3">{hour_label(t)}</td>'
            f'<td>{emoji} {desc}</td>'
            f'<td class="{tc}" style="font-weight:bold">{temp:.1f}</td>'
            f'<td class="rain">{prec:.1f} mm</td>'
            + wind_cell(wdir, wspd) +
            f'</tr>'
        )
    day_sections.append(
        f'<div class="day-header">{day_label_long(day_str)}</div>\n'
        f'<table>\n'
        f'<thead><tr><th>Uhrzeit</th><th>Wetter</th><th>Temp °C</th>'
        f'<th>Niederschlag</th><th>Wind</th></tr></thead>\n'
        f'<tbody>{"".join(rows)}</tbody>\n'
        f'</table>'
    )

html_3h = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wetterbericht Schärding — 48h (3h-Intervall)</title>
<style>{DARK_CSS}</style>
</head>
<body>
{BANNER_HTML}
<h1>Wetterbericht Schärding, Oberösterreich</h1>
<p class="subtitle">48-Stunden-Vorhersage im 3h-Intervall &mdash; {today_long} bis {end_48h_long}</p>

{"".join(day_sections)}

<p class="source">
  Datenquelle: Open-Meteo.com (48.45°N, 13.43°E, 303 m ü.M.) — erstellt am {today_long}<br>
  Foto: © C.Stadler/Bwag, CC BY-SA 4.0, Wikimedia Commons
</p>
</body>
</html>"""

with open("wetter_schaerding_3h.html", "w", encoding="utf-8") as f:
    f.write(html_3h)
print("✓ wetter_schaerding_3h.html")
print(f"  Days covered: {list(days.keys())}")
