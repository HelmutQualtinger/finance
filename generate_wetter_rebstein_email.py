#!/usr/bin/env python3
"""
Generiert Wetterbericht für Rebstein (72h + 14 Tage) als HTML-E-Mail.
Holt Daten von Open-Meteo, Banner-Bild von Wikimedia Commons.
"""
import subprocess, json, base64, sys
from datetime import datetime, timezone

# --- Koordinaten Rebstein SG ---
LAT, LON = 47.4053, 9.5726
LOCATION = "Rebstein-Marbach SG, Schweiz"

def curl(url):
    r = subprocess.run(
        ["curl", "-s", "-L", "--max-time", "15",
         "-A", "Mozilla/5.0 WeatherBot/1.0"],
        input=url.encode(), capture_output=True,
        env={**__import__("os").environ}
    )
    # actually pass url as arg
    r = subprocess.run(
        ["curl", "-s", "-L", "--max-time", "15",
         "-A", "Mozilla/5.0 WeatherBot/1.0", url],
        capture_output=True
    )
    return r.stdout

# --- Banner-Bild laden und base64-kodieren ---
BANNER_LOCAL = "/tmp/rebstein_banner.jpg"
print("Lade Banner-Bild…")
import os
if os.path.exists(BANNER_LOCAL):
    with open(BANNER_LOCAL, "rb") as f:
        img_data = f.read()
    banner_b64 = base64.b64encode(img_data).decode()
    banner_src = f"data:image/jpeg;base64,{banner_b64}"
    print(f"  Bild geladen ({len(img_data)//1024} KB)")
else:
    banner_src = None
    print("  Bild nicht verfügbar, Fallback-Gradient wird verwendet")

# --- Wetterdaten Open-Meteo ---
print("Lade Wetterdaten…")
hourly_url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={LAT}&longitude={LON}"
    f"&hourly=temperature_2m,apparent_temperature,precipitation,"
    f"weathercode,windspeed_10m,winddirection_10m,relativehumidity_2m"
    f"&daily=weathercode,temperature_2m_max,temperature_2m_min,"
    f"precipitation_sum,windspeed_10m_max,winddirection_10m_dominant,sunrise,sunset"
    f"&timezone=Europe%2FZurich&forecast_days=16"
)
raw = curl(hourly_url)
data = json.loads(raw)

hourly = data["hourly"]
daily  = data["daily"]

# --- Hilfsfunktionen ---
WMO = {
    0: ("☀️", "Klar"),
    1: ("🌤️", "Überwiegend klar"),
    2: ("⛅", "Teils bewölkt"),
    3: ("☁️", "Bedeckt"),
    45: ("🌫️", "Nebel"),
    48: ("🌫️", "Raureif-Nebel"),
    51: ("🌦️", "Leichter Niesel"),
    53: ("🌦️", "Niesel"),
    55: ("🌧️", "Starker Niesel"),
    61: ("🌧️", "Leichter Regen"),
    63: ("🌧️", "Regen"),
    65: ("🌧️", "Starker Regen"),
    71: ("🌨️", "Leichter Schnee"),
    73: ("🌨️", "Schnee"),
    75: ("❄️", "Starker Schnee"),
    77: ("🌨️", "Schneekörner"),
    80: ("🌧️", "Regenschauer"),
    81: ("🌧️", "Regenschauer"),
    82: ("⛈️", "Starke Schauer"),
    85: ("🌨️", "Schneeschauer"),
    86: ("❄️", "Starke Schneeschauer"),
    95: ("⛈️", "Gewitter"),
    96: ("⛈️", "Gewitter mit Hagel"),
    99: ("⛈️", "Schweres Gewitter"),
}

def wmo(code):
    return WMO.get(code, ("🌡️", "Unbekannt"))

DIRS = ["N","NO","O","SO","S","SW","W","NW"]
def winddir(deg):
    if deg is None: return "–"
    return DIRS[int((deg + 22.5) / 45) % 8]

def beaufort(kmh):
    if kmh is None: return 0
    thresholds = [1,5,11,19,28,38,49,61,74,88,102,117]
    for i, t in enumerate(thresholds):
        if kmh < t:
            return i
    return 12

def bft_label(b):
    labels = ["Windstille","Zug","Leichte Brise","Schwache Brise",
              "Mäßige Brise","Frische Brise","Starker Wind","Steifer Wind",
              "Stürmischer Wind","Sturm","Schwerer Sturm","Orkan","Schwerer Orkan"]
    return labels[min(b, 12)]

def temp_color(t):
    """Hintergrundfarbe nach Temperatur."""
    if t is None: return "#2a2d3e"
    if t <= 0:    return "#1a3a5c"
    if t <= 5:    return "#1a4a6c"
    if t <= 10:   return "#1e5c50"
    if t <= 15:   return "#1e5c30"
    if t <= 20:   return "#3d5c1e"
    if t <= 25:   return "#5c4a1e"
    if t <= 30:   return "#6c2e1e"
    return "#7c1e1e"

# --- 72h Stunden-Daten (3h-Intervall) ---
now_iso = datetime.now(timezone.utc).astimezone().replace(tzinfo=None)
times_72 = []
for i, t_str in enumerate(hourly["time"]):
    dt = datetime.fromisoformat(t_str)
    if dt >= now_iso and i % 3 == 0 and len(times_72) < 24:
        times_72.append({
            "dt": dt,
            "temp": hourly["temperature_2m"][i],
            "feels": hourly["apparent_temperature"][i],
            "rain": hourly["precipitation"][i],
            "code": hourly["weathercode"][i],
            "wind": hourly["windspeed_10m"][i],
            "wdir": hourly["winddirection_10m"][i],
            "hum":  hourly["relativehumidity_2m"][i],
        })

# --- 14 Tage ---
days_14 = []
for i in range(min(14, len(daily["time"]))):
    dt = datetime.fromisoformat(daily["time"][i])
    days_14.append({
        "dt":    dt,
        "code":  daily["weathercode"][i],
        "tmax":  daily["temperature_2m_max"][i],
        "tmin":  daily["temperature_2m_min"][i],
        "rain":  daily["precipitation_sum"][i],
        "wind":  daily["windspeed_10m_max"][i],
        "wdir":  daily["winddirection_10m_dominant"][i],
        "rise":  daily["sunrise"][i][11:16] if daily["sunrise"][i] else "–",
        "set":   daily["sunset"][i][11:16]  if daily["sunset"][i]  else "–",
    })

WOCHENTAG = ["Mo","Di","Mi","Do","Fr","Sa","So"]
MONAT = ["","Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"]

def fmt_day(dt):
    return f"{WOCHENTAG[dt.weekday()]}, {dt.day}. {MONAT[dt.month]}"

# ─────────────────────────────────────────
# HTML generieren
# ─────────────────────────────────────────
now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

# Banner HTML
if banner_src:
    banner_html = f'''
  <tr>
    <td colspan="2" style="padding:0;line-height:0;">
      <img src="{banner_src}" alt="Bahnhof Rebstein-Marbach"
           style="width:100%;max-height:220px;object-fit:cover;display:block;">
    </td>
  </tr>'''
else:
    banner_html = '''
  <tr>
    <td colspan="2" style="padding:0;line-height:0;height:80px;
        background:linear-gradient(135deg,#1a3a6c,#2e6040,#5c4a1e);">
      <div style="padding:20px;color:#fff;font-size:20px;font-weight:bold;">
        🚂 Bahnhof Rebstein-Marbach
      </div>
    </td>
  </tr>'''

# ── 72h vertikal ────────────────────────────────────────────────
rows_72 = ""
prev_date = None
for h in times_72:
    emoji, beschr = wmo(h["code"])
    b = beaufort(h["wind"])
    bg = temp_color(h["temp"])
    date_str = h["dt"].strftime("%A, %d. %B")
    # Datumstrennlinie
    cur_date = h["dt"].date()
    if cur_date != prev_date:
        WOCHENTAG_LANG = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
        MONAT_LANG = ["","Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"]
        day_label = f"{WOCHENTAG_LANG[h['dt'].weekday()]}, {h['dt'].day}. {MONAT_LANG[h['dt'].month]} {h['dt'].year}"
        rows_72 += f'''
  <tr>
    <td colspan="2" style="background:#1e2130;padding:6px 16px;
        font-size:12px;font-weight:700;color:#8899bb;letter-spacing:1px;
        text-transform:uppercase;border-top:1px solid #2a2d4e;">
      {day_label}
    </td>
  </tr>'''
        prev_date = cur_date

    time_str = h["dt"].strftime("%H:%M")
    rain_str = f"💧 {h['rain']:.1f} mm" if h["rain"] and h["rain"] > 0.05 else ""
    rows_72 += f'''
  <tr>
    <td style="background:{bg};padding:10px 16px;width:90px;text-align:center;
        vertical-align:middle;border-bottom:1px solid #1a1d2e;">
      <div style="font-size:26px;">{emoji}</div>
      <div style="font-size:18px;font-weight:700;color:#fff;">{h["temp"]:.0f}°</div>
      <div style="font-size:11px;color:#aabbcc;">gefühlt {h["feels"]:.0f}°</div>
    </td>
    <td style="background:{bg};padding:10px 16px;vertical-align:middle;
        border-bottom:1px solid #1a1d2e;">
      <div style="font-size:15px;font-weight:700;color:#fff;">{time_str} Uhr</div>
      <div style="font-size:13px;color:#ccddef;">{beschr}</div>
      <div style="font-size:12px;color:#99aacc;margin-top:4px;">
        💨 {winddir(h["wdir"])} {h["wind"]:.0f} km/h (Bft {b} · {bft_label(b)})
        &nbsp;·&nbsp; 💦 {h["hum"]:.0f}%
        {"&nbsp;·&nbsp; " + rain_str if rain_str else ""}
      </div>
    </td>
  </tr>'''

# ── 72h horizontal (pro Tag eine Zeile) ──────────────────────────
from itertools import groupby
WOCHENTAG_LANG = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
MONAT_LANG = ["","Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"]

def h_cell(h):
    emoji, beschr = wmo(h["code"])
    b = beaufort(h["wind"])
    bg = temp_color(h["temp"])
    rain_str = f"<br>💧{h['rain']:.1f}" if h["rain"] and h["rain"] > 0.05 else ""
    return f'''<td style="background:{bg};border:1px solid #1a1d2e;padding:8px 4px;
        text-align:center;vertical-align:top;width:12.5%;">
      <div style="font-size:11px;font-weight:700;color:#aabbdd;">{h["dt"].strftime("%H:%M")}</div>
      <div style="font-size:22px;margin:3px 0;">{emoji}</div>
      <div style="font-size:13px;font-weight:700;color:#fff;">{h["temp"]:.0f}°</div>
      <div style="font-size:10px;color:#8899bb;">gef. {h["feels"]:.0f}°</div>
      <div style="font-size:10px;color:#99aacc;margin-top:2px;">
        💨{winddir(h["wdir"])}<br>{h["wind"]:.0f}km/h<br>Bft{b}{rain_str}
      </div>
    </td>'''

horiz_72 = ""
for day_date, slots in groupby(times_72, key=lambda h: h["dt"].date()):
    slots = list(slots)
    day_dt = slots[0]["dt"]
    day_label = f"{WOCHENTAG_LANG[day_dt.weekday()]}, {day_dt.day}. {MONAT_LANG[day_dt.month]} {day_dt.year}"
    cells = "".join(h_cell(h) for h in slots)
    # Leere Zellen auffüllen falls < 8 Slots
    empty = 8 - len(slots)
    for _ in range(empty):
        cells += '<td style="background:#0f1117;border:1px solid #1a1d2e;"></td>'
    horiz_72 += f'''
  <tr>
    <td colspan="2" style="background:#1e2130;padding:6px 16px;
        font-size:12px;font-weight:700;color:#8899bb;letter-spacing:1px;
        text-transform:uppercase;border-top:1px solid #2a2d4e;">
      {day_label}
    </td>
  </tr>
  <tr>
    <td colspan="2" style="background:#0f1117;padding:4px 8px;">
      <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
        <tr>{cells}</tr>
      </table>
    </td>
  </tr>'''

# ── 14-Tage 2×7 ──────────────────────────────────────────────────
def day_cell(d):
    emoji, beschr = wmo(d["code"])
    b = beaufort(d["wind"])
    bg = temp_color((d["tmax"] + d["tmin"]) / 2)
    rain_str = f"💧 {d['rain']:.1f}" if d["rain"] and d["rain"] > 0.1 else "–"
    return f'''
        <td style="background:{bg};border:1px solid #1a1d2e;padding:10px 8px;
            text-align:center;vertical-align:top;width:14%;">
          <div style="font-size:11px;font-weight:700;color:#8899bb;">{fmt_day(d["dt"])}</div>
          <div style="font-size:28px;margin:4px 0;">{emoji}</div>
          <div style="font-size:14px;color:#fff;font-weight:700;">
            {d["tmax"]:.0f}° / <span style="color:#8899bb;">{d["tmin"]:.0f}°</span>
          </div>
          <div style="font-size:10px;color:#aabbcc;margin-top:3px;">{beschr}</div>
          <div style="font-size:10px;color:#99aacc;margin-top:3px;">
            💨 {winddir(d["wdir"])} {d["wind"]:.0f} km/h<br>
            Bft {b} · {rain_str} mm<br>
            🌅 {d["rise"]} 🌇 {d["set"]}
          </div>
        </td>'''

row1 = "".join(day_cell(d) for d in days_14[:7])
row2 = "".join(day_cell(d) for d in days_14[7:14])
table_14 = f'''
    <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
      <tr>{row1}</tr>
      <tr>{row2}</tr>
    </table>'''

# ── Gesamt-HTML ───────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wetterbericht Rebstein – {now_str}</title>
</head>
<body style="margin:0;padding:20px;background:#0f1117;font-family:Arial,sans-serif;">
<table width="640" cellpadding="0" cellspacing="0"
       style="max-width:640px;margin:0 auto;border-radius:12px;overflow:hidden;
              box-shadow:0 4px 24px rgba(0,0,0,0.7);">

  <!-- Banner -->
  {banner_html}

  <!-- Header -->
  <tr>
    <td colspan="2" style="background:#1a1d2e;padding:16px 20px;">
      <div style="font-size:22px;font-weight:700;color:#e0e8ff;">
        🌦 Wetterbericht {LOCATION}
      </div>
      <div style="font-size:12px;color:#6677aa;margin-top:4px;">
        Stand: {now_str} · Open-Meteo.com
      </div>
    </td>
  </tr>

  <!-- 72h horizontal Titel -->
  <tr>
    <td colspan="2" style="background:#12152a;padding:12px 20px;
        font-size:15px;font-weight:700;color:#7090e0;letter-spacing:0.5px;">
      ⏱ 72-Stunden-Vorhersage · Tagesübersicht (3h-Intervalle)
    </td>
  </tr>

  <!-- 72h horizontal (pro Tag) -->
  {horiz_72}

  <!-- 72h vertikal Titel -->
  <tr>
    <td colspan="2" style="background:#12152a;padding:12px 20px;
        font-size:15px;font-weight:700;color:#7090e0;letter-spacing:0.5px;">
      ⏱ 72-Stunden-Vorhersage · Detailansicht
    </td>
  </tr>

  <!-- 72h Zeilen vertikal -->
  {rows_72}

  <!-- 14-Tage Titel -->
  <tr>
    <td colspan="2" style="background:#12152a;padding:12px 20px;
        font-size:15px;font-weight:700;color:#70c080;letter-spacing:0.5px;">
      📅 14-Tage-Übersicht
    </td>
  </tr>
  <tr>
    <td colspan="2" style="background:#0f1117;padding:12px;">
      {table_14}
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td colspan="2" style="background:#0a0c18;padding:10px 20px;
        font-size:10px;color:#445566;text-align:center;">
      Daten: Open-Meteo.com · Foto: SBB Historic / Wikimedia Commons (CC BY-SA 4.0)
      · Erstellt {now_str}
    </td>
  </tr>

</table>
</body>
</html>"""

# HTML-Datei speichern
out_path = "/Users/haraldbeker/finance/wetter_rebstein_email.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"HTML gespeichert: {out_path}")
print(f"  72h-Blöcke: {len(times_72)}, 14-Tage-Einträge: {len(days_14)}")

# HTML-Inhalt für E-Mail zurückgeben
print("=== HTML_CONTENT_START ===")
print(html)
print("=== HTML_CONTENT_END ===")
