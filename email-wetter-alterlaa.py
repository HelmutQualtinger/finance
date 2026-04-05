#!/usr/bin/env python3
"""
Wettervorhersage Wien-Alterlaa — 72h (3h-Intervalle) + 14 Tage
Speichert als Gmail-Entwurf via IMAP. Kein automatischer Versand.

Verwendung: python3 email-wetter-alterlaa.py
"""

import imaplib
import subprocess
import base64
import json
import sys
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime, timezone

# ── .env laden ───────────────────────────────────────────────────────────────
def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        print(f"FEHLER: .env nicht gefunden: {env_path}", file=sys.stderr)
        sys.exit(1)
    env = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    for key in ("GMAIL_USER", "GMAIL_PWD"):
        if key not in env:
            print(f"FEHLER: {key} fehlt in .env", file=sys.stderr)
            sys.exit(1)
    return env

_env = _load_env()

# ── Konfiguration ────────────────────────────────────────────────────────────
GMAIL_USER   = _env["GMAIL_USER"]
GMAIL_PWD    = _env["GMAIL_PWD"]
TO           = "REDACTED"
SUBJECT      = "🌦️ Frohe Ostern & Wettervorhersage Wien-Alterlaa – 72h und 14 Tage"
LAT, LON     = 48.1500, 16.3167
TIMEZONE     = "Europe/Vienna"
BANNER_URL   = "https://mbr-alterlaa.at/wp-content/uploads/2020/08/wohnpark-alterlaa-panorama-dachbad-kirche-harry-glueck-park-rundturnhalle.jpg"
BANNER_LOCAL = os.path.join(os.path.dirname(__file__), "alterlaa_banner.jpg")

# ── Farben ───────────────────────────────────────────────────────────────────
C = {
    "bg":      "#0d1117", "card":    "#161b22", "card2":   "#1c2230",
    "accent":  "#1a5c8b", "accent2": "#e8a020", "hdr":     "#0a1628",
    "text":    "#c9d1d9", "muted":   "#8b949e", "border":  "#30363d",
    "hot":     "#e55c2f", "warm":    "#e8a020", "cool":    "#4da6ff",
    "cold":    "#8ac4ff",
    "easter1": "#c084fc", "easter2": "#f472b6", "easter3": "#34d399",
}

# ── 1. Wetterdaten via curl ───────────────────────────────────────────────────
def curl_json(url):
    result = subprocess.run(
        ["curl", "-sL", "--max-time", "20", url],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"FEHLER curl: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)

def fetch_weather():
    base   = "https://api.open-meteo.com/v1/forecast"
    h_vars = "temperature_2m,precipitation,weathercode,windspeed_10m,winddirection_10m"
    d_vars = "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode,windspeed_10m_max,winddirection_10m_dominant"

    h_url = (f"{base}?latitude={LAT}&longitude={LON}"
             f"&hourly={h_vars}&forecast_days=3&timezone={TIMEZONE}")
    d_url = (f"{base}?latitude={LAT}&longitude={LON}"
             f"&daily={d_vars}&forecast_days=14&timezone={TIMEZONE}")

    print("🌐 Abruf Stundendaten (72h)...")
    hourly = curl_json(h_url)["hourly"]
    print("🌐 Abruf Tagesdaten (14 Tage)...")
    daily  = curl_json(d_url)["daily"]
    return hourly, daily

# ── 2. Banner laden (lokal gespeichert, Fallback: Download) ─────────────────
def load_banner():
    if os.path.exists(BANNER_LOCAL) and os.path.getsize(BANNER_LOCAL) > 10000:
        print(f"🖼️  Banner geladen: {BANNER_LOCAL}")
        with open(BANNER_LOCAL, "rb") as f:
            return f.read()
    print("🖼️  Banner nicht lokal gefunden, lade von URL...")
    result = subprocess.run(
        ["curl", "-sL", "--max-time", "30",
         "-A", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
         BANNER_URL, "-o", BANNER_LOCAL],
        capture_output=True
    )
    if result.returncode == 0 and os.path.getsize(BANNER_LOCAL) > 10000:
        print(f"✅ Banner heruntergeladen und gespeichert: {BANNER_LOCAL}")
        with open(BANNER_LOCAL, "rb") as f:
            return f.read()
    print("⚠️  Banner nicht verfügbar.")
    return None

# ── Helper: WMO-Code → Emoji + deutsche Beschreibung ────────────────────────
def wcode_info(code):
    mapping = {
        0:  ("☀️",  "Sonnig"),
        1:  ("🌤️", "Überw. sonnig"),
        2:  ("⛅",  "Teils bewölkt"),
        3:  ("☁️",  "Bedeckt"),
        45: ("🌫️", "Nebel"),
        48: ("🌫️", "Gefrierender Nebel"),
        51: ("🌦️", "Leichter Sprühregen"),
        53: ("🌦️", "Sprühregen"),
        55: ("🌧️", "Starker Sprühregen"),
        61: ("🌧️", "Leichter Regen"),
        63: ("🌧️", "Regen"),
        65: ("🌧️", "Starker Regen"),
        71: ("🌨️", "Leichter Schnee"),
        73: ("🌨️", "Schnee"),
        75: ("🌨️", "Starker Schnee"),
        77: ("🌨️", "Schneekörner"),
        80: ("🌦️", "Leichte Schauer"),
        81: ("🌦️", "Schauer"),
        82: ("🌧️", "Starke Schauer"),
        85: ("🌨️", "Schneeschauer"),
        86: ("🌨️", "Starke Schneeschauer"),
        95: ("⛈️",  "Gewitter"),
        96: ("⛈️",  "Gewitter + Hagel"),
        99: ("⛈️",  "Heftiges Gewitter"),
    }
    return mapping.get(code, ("❓", "Unbekannt"))

# ── Helper: Windrichtung → Pfeil + Himmelsrichtung ──────────────────────────
def wind_arrow(deg):
    labels = ["N","NO","O","SO","S","SW","W","NW"]
    arrows = ["↓","↙","←","↖","↑","↗","→","↘"]
    idx = round(deg / 45) % 8
    return f"{arrows[idx]} {labels[idx]}"

# ── Helper: Temperaturfarbe ──────────────────────────────────────────────────
def temp_color(t):
    if t >= 30: return C["hot"]
    if t >= 22: return C["warm"]
    if t >=  8: return C["cool"]
    if t >=  0: return C["cold"]
    return "#b0d4ff"

# ── Helper: Datum auf Deutsch ─────────────────────────────────────────────────
WOCHENTAGE_KURZ = ["Mo","Di","Mi","Do","Fr","Sa","So"]
WOCHENTAGE_LANG = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
MONATE = ["","Januar","Februar","März","April","Mai","Juni",
          "Juli","August","September","Oktober","November","Dezember"]

def fmt_tag_kurz(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    wd = d.weekday()
    return (f"{WOCHENTAGE_KURZ[wd]}.<br>"
            f"<span style='font-size:11px;font-weight:400;color:{C['muted']}'>"
            f"{d.day}. {MONATE[d.month][:3]}.</span>")

def fmt_tag_lang(date_str, idx):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    wd = d.weekday()
    extra = {0: " — heute", 1: " — morgen", 2: " — übermorgen"}.get(idx, "")
    return f"{WOCHENTAGE_LANG[wd]}, {d.day}. {MONATE[d.month]} {d.year}{extra}"

# ── Tabelle 72h: ein Tag (8 Spalten alle 3h) ─────────────────────────────────
def table_72h_tag(hourly, day_idx):
    base  = day_idx * 24
    slots = [base + h for h in range(0, 24, 3)]
    title = fmt_tag_lang(hourly["time"][base][:10], day_idx)

    th_s = (f'style="background:{C["accent"]};color:#fff;padding:7px 8px;'
            f'text-align:center;font-size:12px;font-weight:600;white-space:nowrap"')
    rl_s = (f'style="padding:6px 10px;color:{C["muted"]};font-size:12px;'
            f'font-weight:600;white-space:nowrap;background:{C["card2"]}"')

    c_uhr, c_wet, c_tmp, c_nds, c_wnd, c_wri = [], [], [], [], [], []
    for i in slots:
        uhr    = hourly["time"][i][11:16]
        emo, _ = wcode_info(hourly["weathercode"][i])
        tc     = temp_color(hourly["temperature_2m"][i])
        wa     = wind_arrow(hourly["winddirection_10m"][i])
        td = 'style="text-align:center;padding:6px 8px'
        c_uhr.append(f'<td {td};color:{C["muted"]};font-size:13px;white-space:nowrap">{uhr}</td>')
        c_wet.append(f'<td {td};font-size:20px">{emo}</td>')
        c_tmp.append(f'<td {td};font-weight:bold;color:{tc};font-size:14px">{hourly["temperature_2m"][i]:.1f}°</td>')
        c_nds.append(f'<td {td};color:{C["cool"]};font-size:13px">{hourly["precipitation"][i]:.1f} mm</td>')
        c_wnd.append(f'<td {td};color:{C["muted"]};font-size:13px">{hourly["windspeed_10m"][i]:.1f} km/h</td>')
        c_wri.append(f'<td {td};color:{C["accent2"]};font-size:13px;white-space:nowrap">{wa}</td>')

    def to_th(cells):
        return "".join(c.replace("<td ", "<th ").replace("</td>","</th>") for c in cells)

    def row(label, cells, bg):
        return f'<tr style="background:{bg}"><td {rl_s}>{label}</td>{"".join(cells)}</tr>'

    return f"""
<div style="margin-bottom:24px">
  <div style="font-size:15px;font-weight:700;color:{C['accent2']};margin-bottom:10px">🗓️ {title}</div>
  <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;background:{C['card']};border:1px solid {C['border']};border-radius:8px;overflow:hidden">
    <thead><tr style="background:{C['accent']}"><th {th_s}>Uhrzeit</th>{to_th(c_uhr)}</tr></thead>
    <tbody>
      {row("Wetter",     c_wet, C['card2'])}
      {row("Temp.",      c_tmp, C['card'])}
      {row("Niedersch.", c_nds, C['card2'])}
      {row("Wind",       c_wnd, C['card'])}
      {row("Richtung",   c_wri, C['card2'])}
    </tbody>
  </table>
</div>"""

# ── Tabelle 14 Tage: eine Woche (7 Spalten) ──────────────────────────────────
def table_14tage_woche(daily, week_idx):
    base  = week_idx * 7
    days  = range(base, base + 7)
    d0    = datetime.strptime(daily["time"][base],     "%Y-%m-%d")
    d6    = datetime.strptime(daily["time"][base + 6], "%Y-%m-%d")
    title = f"Woche {week_idx+1}: {d0.day}.–{d6.day}. {MONATE[d0.month]} {d0.year}"

    th_s = (f'style="background:{C["hdr"]};color:{C["muted"]};padding:8px 6px;'
            f'text-align:center;font-size:12px;font-weight:600;'
            f'border-bottom:1px solid {C["border"]};white-space:nowrap"')
    rl_s = (f'style="padding:8px 10px;color:{C["muted"]};font-size:12px;font-weight:600;'
            f'white-space:nowrap;background:{C["card2"]};border-right:1px solid {C["border"]}"')

    c_tag, c_wet, c_hoc, c_tie, c_nds, c_wnd, c_wri = [], [], [], [], [], [], []
    for i in days:
        emo, desc = wcode_info(daily["weathercode"][i])
        tc_h = temp_color(daily["temperature_2m_max"][i])
        tc_l = temp_color(daily["temperature_2m_min"][i])
        wa   = wind_arrow(daily["winddirection_10m_dominant"][i])
        td = 'style="text-align:center;padding:8px 6px'
        c_tag.append(f'<td {td};color:#fff;font-size:13px;font-weight:700;white-space:nowrap">{fmt_tag_kurz(daily["time"][i])}</td>')
        c_wet.append(f'<td {td};font-size:21px" title="{desc}">{emo}<br><span style="font-size:10px;color:{C["muted"]}">{desc[:14]}</span></td>')
        c_hoc.append(f'<td {td};font-weight:bold;color:{tc_h};font-size:14px">{daily["temperature_2m_max"][i]:.1f}°</td>')
        c_tie.append(f'<td {td};color:{tc_l};font-size:13px">{daily["temperature_2m_min"][i]:.1f}°</td>')
        c_nds.append(f'<td {td};color:{C["cool"]};font-size:12px">{daily["precipitation_sum"][i]:.1f} mm</td>')
        c_wnd.append(f'<td {td};color:{C["muted"]};font-size:12px">{daily["windspeed_10m_max"][i]:.1f} km/h</td>')
        c_wri.append(f'<td {td};color:{C["accent2"]};font-size:13px;white-space:nowrap">{wa}</td>')

    def to_th(cells):
        return "".join(c.replace("<td ", "<th ").replace("</td>","</th>") for c in cells)

    def row(label, cells, bg):
        return f'<tr style="background:{bg}"><td {rl_s}>{label}</td>{"".join(cells)}</tr>'

    return f"""
<div style="margin-bottom:24px">
  <div style="font-size:15px;font-weight:700;color:{C['accent2']};margin-bottom:10px">&#128197; {title}</div>
  <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;background:{C['card']};border:1px solid {C['border']};border-radius:8px;overflow:hidden">
    <thead><tr style="background:{C['hdr']}"><th {th_s}>Tag</th>{to_th(c_tag)}</tr></thead>
    <tbody>
      {row("Wetter",    c_wet, C['card2'])}
      {row("Höchst",    c_hoc, C['card'])}
      {row("Tief",      c_tie, C['card2'])}
      {row("Niedersch.",c_nds, C['card'])}
      {row("Wind max",  c_wnd, C['card2'])}
      {row("Richtung",  c_wri, C['card'])}
    </tbody>
  </table>
</div>"""

# ── HTML zusammenbauen ────────────────────────────────────────────────────────
def build_html(hourly, daily, banner_src):
    t72  = "".join(table_72h_tag(hourly, i) for i in range(3))
    t14  = "".join(table_14tage_woche(daily, i) for i in range(2))
    now  = datetime.now().strftime("%-d. %B %Y um %H:%M Uhr")
    d0   = datetime.strptime(daily["time"][0],  "%Y-%m-%d")
    d13  = datetime.strptime(daily["time"][13], "%Y-%m-%d")

    return f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><title>Wettervorhersage Wien-Alterlaa</title></head>
<body style="margin:0;padding:0;background:{C['bg']};font-family:Arial,Helvetica,sans-serif;color:{C['text']}">
<div style="max-width:860px;margin:0 auto;padding:20px 16px">

  <!-- BANNER -->
  <div style="border-radius:12px 12px 0 0;overflow:hidden;position:relative;line-height:0">
    <img src="{banner_src}" alt="Wohnpark Alterlaa – Panorama" width="100%"
         style="display:block;width:100%;height:220px;object-fit:cover;object-position:center 40%">
    <div style="position:absolute;bottom:0;left:0;right:0;background:linear-gradient(transparent,rgba(0,0,0,.80));padding:16px 20px">
      <div style="font-size:24px;font-weight:800;color:#fff">🏊 Wohnpark Alterlaa · Wien</div>
      <div style="font-size:13px;color:rgba(255,255,255,.75);margin-top:3px">
        Wettervorhersage {d0.day}. {MONATE[d0.month]}–{d13.day}. {MONATE[d13.month]} {d0.year}
      </div>
    </div>
  </div>

  <!-- OSTERGRÜSSE -->
  <div style="background:linear-gradient(135deg,#1a0533 0%,#0d1117 50%,#0a2010 100%);border:1px solid {C['border']};border-top:3px solid {C['easter1']};border-radius:0 0 12px 12px;padding:24px;margin-bottom:28px;text-align:center">
    <div style="font-size:32px;margin-bottom:10px">&#128163; &#127800; &#10013;&#65039; &#127800; &#129370;</div>
    <div style="font-size:26px;font-weight:800;color:{C['easter1']};margin-bottom:8px">
      Frohe Ostern, Roland!
    </div>
    <div style="font-size:15px;color:{C['text']};line-height:1.75;max-width:580px;margin:0 auto">
      Wir wünschen dir und deiner Familie ein frohes Osterfest —
      voller Freude, Ruhe und schöner gemeinsamer Momente. &#127775;<br>
      Möge dieses Osterfest neue Kraft und Zuversicht bringen,
      genau wie der Frühling neue Energie in die Natur bringt. &#127800;
    </div>
    <div style="font-size:13px;color:{C['muted']};margin-top:14px;font-style:italic">
      Herzliche Grüße · Ostern 2026
    </div>
  </div>

  <!-- STANDORT-INFO -->
  <div style="background:{C['hdr']};border:1px solid {C['border']};border-radius:10px;padding:14px 20px;margin-bottom:28px">
    <div style="font-size:13px;color:{C['muted']};line-height:1.8">
      <strong style="color:{C['text']}">Standort:</strong> Wien-Alterlaa, Österreich &nbsp;·&nbsp;
      48.150°N, 16.317°O &nbsp;·&nbsp; ~170 m ü.&#8239;M.<br>
      <strong style="color:{C['text']}">Zeitzone:</strong> Europe/Vienna (MESZ, UTC+2) &nbsp;·&nbsp;
      <strong style="color:{C['text']}">Quelle:</strong> open-meteo.com &nbsp;·&nbsp;
      <strong style="color:{C['text']}">Erstellt:</strong> {now}
    </div>
  </div>

  <!-- 72 STUNDEN -->
  <div style="margin-bottom:32px">
    <div style="margin-bottom:18px;padding-bottom:10px;border-bottom:2px solid {C['accent']}">
      <div style="font-size:20px;font-weight:800;color:#fff">&#128336; Vorhersage nächste 72 Stunden</div>
      <div style="font-size:13px;color:{C['muted']}">3-Stunden-Intervalle · 8 Zeitfenster pro Tag</div>
    </div>
    {t72}
  </div>

  <!-- 14 TAGE -->
  <div style="margin-bottom:32px">
    <div style="margin-bottom:18px;padding-bottom:10px;border-bottom:2px solid {C['accent2']}">
      <div style="font-size:20px;font-weight:800;color:#fff">&#128197; 14-Tage-Vorhersage</div>
      <div style="font-size:13px;color:{C['muted']}">7 Tage pro Woche · Höchst-/Tiefstwerte · Wind und Richtung</div>
    </div>
    {t14}
  </div>

  <!-- LEGENDE -->
  <div style="background:{C['card']};border:1px solid {C['border']};border-radius:10px;padding:16px 20px;margin-bottom:24px">
    <div style="font-size:13px;font-weight:700;color:{C['muted']};margin-bottom:8px">LEGENDE WINDRICHTUNG</div>
    <div style="font-size:12px;color:{C['muted']};line-height:2">
      &#8593; Wind aus Süden &nbsp;|&nbsp; &#8595; aus Norden &nbsp;|&nbsp;
      &#8592; aus Osten &nbsp;|&nbsp; &#8594; aus Westen &nbsp;|&nbsp;
      &#8599; aus SW &#8594; weht nach NO &nbsp;|&nbsp; &#8601; aus NW &#8594; weht nach SO (Föhn)
    </div>
  </div>

  <!-- FOOTER -->
  <div style="text-align:center;padding:16px;font-size:12px;color:{C['muted']};border-top:1px solid {C['border']}">
    Wien-Alterlaa · Österreich &#127462;&#127481; · Daten: open-meteo.com
  </div>

</div>
</body>
</html>"""

# ── Gmail-Entwurf via IMAP speichern → gibt direkten Draft-URL zurück ────────
def gmail_entwurf_speichern(msg_bytes):
    import re
    print("📥 Gmail-Entwurf via IMAP speichern...")
    draft_url = "https://mail.google.com/mail/u/0/#drafts"
    with imaplib.IMAP4_SSL("imap.gmail.com", 993) as imap:
        imap.login(GMAIL_USER, GMAIL_PWD)
        _, folders = imap.list()
        drafts_folder = None
        for f in folders:
            fname = f.decode() if isinstance(f, bytes) else f
            if "\\Drafts" in fname:
                parts = fname.split('"')
                drafts_folder = parts[-2] if len(parts) >= 2 else fname.split()[-1]
                break
        if not drafts_folder:
            drafts_folder = "[Google Mail]/Entwürfe"
        print(f"   Ordner: {drafts_folder}")
        status, data = imap.append(
            f'"{drafts_folder}"', "\\Draft",
            imaplib.Time2Internaldate(datetime.now(timezone.utc)),
            msg_bytes
        )
        # UID aus APPENDUID-Antwort lesen
        if status == "OK" and data and data[0]:
            resp = data[0].decode() if isinstance(data[0], bytes) else str(data[0])
            m = re.search(r"APPENDUID \d+ (\d+)", resp)
            if m:
                uid = m.group(1)
                imap.select(f'"{drafts_folder}"', readonly=True)
                _, fetch_data = imap.uid("fetch", uid, "(X-GM-MSGID)")
                if fetch_data and fetch_data[0]:
                    fd = fetch_data[0].decode() if isinstance(fetch_data[0], bytes) else str(fetch_data[0])
                    m2 = re.search(r"X-GM-MSGID (\d+)", fd)
                    if m2:
                        gm_id = hex(int(m2.group(1)))[2:]
                        draft_url = f"https://mail.google.com/mail/u/0/#drafts/{gm_id}"
    print("✅ Entwurf gespeichert!")
    return draft_url

# ════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # 1. Wetterdaten abrufen
    hourly, daily = fetch_weather()

    # 2. Banner laden
    banner_bytes = load_banner()

    # 3. HTML aufbauen
    banner_src = "cid:banner_alterlaa" if banner_bytes else ""
    html = build_html(hourly, daily, banner_src)

    # 4. Lokale Vorschau
    preview_path = "/tmp/wetter_alterlaa_preview.html"
    if banner_bytes:
        b64 = base64.b64encode(banner_bytes).decode("ascii")
        html_preview = html.replace("cid:banner_alterlaa", f"data:image/jpeg;base64,{b64}")
    else:
        html_preview = html
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(html_preview)

    # 5. MIME-Nachricht aufbauen
    msg_root = MIMEMultipart("related")
    msg_root["Subject"] = SUBJECT
    msg_root["From"]    = f"Wetter Alterlaa <{GMAIL_USER}>"
    msg_root["To"]      = TO

    msg_alt = MIMEMultipart("alternative")
    msg_alt.attach(MIMEText(html, "html", "utf-8"))
    msg_root.attach(msg_alt)

    if banner_bytes:
        img = MIMEImage(banner_bytes, _subtype="jpeg")
        img.add_header("Content-ID", "<banner_alterlaa>")
        img.add_header("Content-Disposition", "inline", filename="alterlaa.jpg")
        msg_root.attach(img)

    msg_bytes = msg_root.as_bytes()

    # 6. Gmail-Entwurf speichern + direkten Draft-URL holen
    draft_url = gmail_entwurf_speichern(msg_bytes)

    # 7. Direkt den Entwurf in Gmail öffnen
    subprocess.Popen(["open", draft_url])
    print(f"🌐 Gmail-Entwurf geöffnet: {draft_url}")
    print(f"📄 Vorschau: /tmp/wetter_alterlaa_preview.html")
