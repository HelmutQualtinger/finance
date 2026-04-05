#!/usr/bin/env python3
"""
Meteo Santiago del Cile — previsioni 72h (3h) + 14 giorni
Salva come bozza in Gmail via IMAP. Nessun invio automatico.

Uso: python3 email-python.py
"""

import imaplib
import base64
import subprocess
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
    for key in ("GMAIL_USER", "GMAIL_PWD", "MAIL_HARALD"):
        if key not in env:
            print(f"FEHLER: {key} fehlt in .env", file=sys.stderr)
            sys.exit(1)
    return env

_env = _load_env()

# ── Configurazione ───────────────────────────────────────────────────────────
GMAIL_USER  = _env["GMAIL_USER"]
GMAIL_PWD   = _env["GMAIL_PWD"]
TO          = _env["MAIL_HARALD"]
SUBJECT     = "🐣 Buona Pasqua! Previsioni Meteo Santiago del Cile – 72h e 14 giorni"
LAT, LON    = -33.45, -70.67
TIMEZONE    = "America/Santiago"
BANNER_URL  = ("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/"
               "Santiago_de_Chile%2C_Desde_Cerro_San_Crist%C3%B3bal_%28cropped_panorama%29.jpg/"
               "1200px-Santiago_de_Chile%2C_Desde_Cerro_San_Crist%C3%B3bal_%28cropped_panorama%29.jpg")
BANNER_TMP  = "/tmp/santiago_banner.jpg"

# ── Colori ───────────────────────────────────────────────────────────────────
C = {
    "bg":      "#0d1117", "card":    "#161b22", "card2":   "#1c2230",
    "accent":  "#1a6bbd", "accent2": "#e8a020", "hdr":     "#0a1628",
    "text":    "#c9d1d9", "muted":   "#8b949e", "border":  "#30363d",
    "hot":     "#e55c2f", "warm":    "#e8a020", "cool":    "#4da6ff",
    "easter1": "#c084fc", "easter3": "#34d399",
}

# ── 1. Dati meteo via curl (SSL-sicher) ──────────────────────────────────────
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
    base = "https://api.open-meteo.com/v1/forecast"
    hourly_vars = "temperature_2m,precipitation,weathercode,windspeed_10m,winddirection_10m"
    daily_vars  = "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode,windspeed_10m_max,winddirection_10m_dominant"

    h_url = (f"{base}?latitude={LAT}&longitude={LON}"
             f"&hourly={hourly_vars}&forecast_days=3&timezone={TIMEZONE}")
    d_url = (f"{base}?latitude={LAT}&longitude={LON}"
             f"&daily={daily_vars}&forecast_days=14&timezone={TIMEZONE}")

    print("🌐 Fetch dati orari (72h)...")
    hourly = curl_json(h_url)["hourly"]
    print("🌐 Fetch dati giornalieri (14gg)...")
    daily  = curl_json(d_url)["daily"]
    return hourly, daily

# ── 2. Banner via curl ───────────────────────────────────────────────────────
def fetch_banner():
    print("🖼️  Download banner Santiago...")
    result = subprocess.run(
        ["curl", "-sL", "--max-time", "30",
         "-A", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
         BANNER_URL, "-o", BANNER_TMP],
        capture_output=True
    )
    if result.returncode != 0 or not os.path.exists(BANNER_TMP) or os.path.getsize(BANNER_TMP) < 10000:
        print("⚠️  Banner non disponibile, continuo senza immagine.")
        return None
    with open(BANNER_TMP, "rb") as f:
        return f.read()

# ── Helper: WMO weathercode → emoji + descrizione ───────────────────────────
def wcode_info(code):
    mapping = {
        0:  ("☀️",  "Soleggiato"),
        1:  ("🌤️", "Prev. soleggiato"),
        2:  ("⛅",  "Parz. nuvoloso"),
        3:  ("☁️",  "Nuvoloso"),
        45: ("🌫️", "Nebbia"),
        48: ("🌫️", "Nebbia gelata"),
        51: ("🌦️", "Pioggerella leggera"),
        53: ("🌦️", "Pioggerella"),
        55: ("🌧️", "Pioggerella intensa"),
        61: ("🌧️", "Pioggia leggera"),
        63: ("🌧️", "Pioggia"),
        65: ("🌧️", "Pioggia intensa"),
        71: ("🌨️", "Neve leggera"),
        73: ("🌨️", "Neve"),
        75: ("🌨️", "Neve intensa"),
        80: ("🌦️", "Rovesci leggeri"),
        81: ("🌦️", "Rovesci"),
        82: ("🌧️", "Rovesci intensi"),
        95: ("⛈️",  "Temporale"),
        96: ("⛈️",  "Temp. con grandine"),
        99: ("⛈️",  "Temp. con grandine"),
    }
    return mapping.get(code, ("❓", "Sconosciuto"))

# ── Helper: direzione vento ──────────────────────────────────────────────────
def wind_arrow(deg):
    labels  = ["N","NE","E","SE","S","SO","O","NO"]
    arrows  = ["↓","↙","←","↖","↑","↗","→","↘"]
    idx = round(deg / 45) % 8
    return f"{arrows[idx]} {labels[idx]}"

# ── Helper: colore temperatura ───────────────────────────────────────────────
def temp_color(t):
    if t >= 28: return C["hot"]
    if t >= 22: return C["warm"]
    if t >= 10: return C["cool"]
    return "#8ac4ff"

# ── Helper: data in italiano ─────────────────────────────────────────────────
GIORNI = ["lun","mar","mer","gio","ven","sab","dom"]

def fmt_giorno(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    wd = d.weekday()  # 0=lun, 6=dom
    gi = GIORNI[wd] if wd < 6 else "dom"
    return f"{gi}.<br><span style='font-size:11px;font-weight:400;color:{C['muted']}'>{d.day} apr.</span>"

def day_label_long(date_str, idx):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    wd = d.weekday()
    nomi = ["lunedì","martedì","mercoledì","giovedì","venerdì","sabato","domenica"]
    nome = nomi[wd]
    extra = [" — oggi", " — domani", " — dopodomani"][idx] if idx < 3 else ""
    return f"{nome.capitalize()}, {d.day} aprile 2026{extra}"

# ── Tabella 72h: un giorno (8 colonne ogni 3h) ───────────────────────────────
def table_72h_day(hourly, day_idx):
    base  = day_idx * 24
    slots = [base + h for h in range(0, 24, 3)]   # 8 colonne: 00,03,06,...,21
    title = day_label_long(hourly["time"][base][:10], day_idx)

    th   = f'style="background:{C["accent"]};color:#fff;padding:7px 8px;text-align:center;font-size:12px;font-weight:600;white-space:nowrap"'
    rl   = f'style="padding:6px 10px;color:{C["muted"]};font-size:12px;font-weight:600;white-space:nowrap;background:{C["card2"]}"'

    def row(label, cells, bg):
        return f'<tr style="background:{bg}"><td {rl}>{label}</td>{"".join(cells)}</tr>'

    c_ora = c_met = c_tmp = c_pre = c_wnd = c_wdr = []
    c_ora, c_met, c_tmp, c_pre, c_wnd, c_wdr = [], [], [], [], [], []
    for i in slots:
        ora  = hourly["time"][i][11:16]
        emo, _ = wcode_info(hourly["weathercode"][i])
        tc   = temp_color(hourly["temperature_2m"][i])
        wa   = wind_arrow(hourly["winddirection_10m"][i])
        td   = 'style="text-align:center;padding:6px 8px'
        c_ora.append(f'<td {td};color:{C["muted"]};font-size:13px;white-space:nowrap">{ora}</td>')
        c_met.append(f'<td {td};font-size:20px">{emo}</td>')
        c_tmp.append(f'<td {td};font-weight:bold;color:{tc};font-size:14px">{hourly["temperature_2m"][i]:.1f}°</td>')
        c_pre.append(f'<td {td};color:{C["cool"]};font-size:13px">{hourly["precipitation"][i]:.1f} mm</td>')
        c_wnd.append(f'<td {td};color:{C["muted"]};font-size:13px">{hourly["windspeed_10m"][i]:.1f} km/h</td>')
        c_wdr.append(f'<td {td};color:{C["accent2"]};font-size:13px;white-space:nowrap">{wa}</td>')

    th_ora = "".join(c.replace("<td ", "<th ").replace("</td>","</th>") for c in c_ora)

    return f"""
<div style="margin-bottom:24px">
  <div style="font-size:15px;font-weight:700;color:{C['accent2']};margin-bottom:10px">🗓️ {title}</div>
  <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;background:{C['card']};border:1px solid {C['border']};border-radius:8px;overflow:hidden">
    <thead><tr style="background:{C['accent']}"><th {th}>Orario</th>{th_ora}</tr></thead>
    <tbody>
      {row("Meteo",     c_met, C['card2'])}
      {row("Temp.",     c_tmp, C['card'])}
      {row("Precip.",   c_pre, C['card2'])}
      {row("Vento",     c_wnd, C['card'])}
      {row("Direzione", c_wdr, C['card2'])}
    </tbody>
  </table>
</div>"""

# ── Tabella 14 giorni: una settimana (7 colonne) ─────────────────────────────
def table_14day_week(daily, week_idx):
    base = week_idx * 7
    days = range(base, base + 7)
    d0   = datetime.strptime(daily["time"][base],     "%Y-%m-%d")
    d6   = datetime.strptime(daily["time"][base + 6], "%Y-%m-%d")
    title = f"Settimana {week_idx+1}: {d0.day}–{d6.day} aprile 2026"

    th   = f'style="background:{C["hdr"]};color:{C["muted"]};padding:8px 6px;text-align:center;font-size:12px;font-weight:600;border-bottom:1px solid {C["border"]};white-space:nowrap"'
    rl   = f'style="padding:8px 10px;color:{C["muted"]};font-size:12px;font-weight:600;white-space:nowrap;background:{C["card2"]};border-right:1px solid {C["border"]}"'

    def row(label, cells, bg):
        return f'<tr style="background:{bg}"><td {rl}>{label}</td>{"".join(cells)}</tr>'

    c_day = c_met = c_max = c_min = c_pre = c_wnd = c_wdr = []
    c_day, c_met, c_max, c_min, c_pre, c_wnd, c_wdr = [], [], [], [], [], [], []
    for i in days:
        emo, desc = wcode_info(daily["weathercode"][i])
        tc_max = temp_color(daily["temperature_2m_max"][i])
        tc_min = temp_color(daily["temperature_2m_min"][i])
        wa  = wind_arrow(daily["winddirection_10m_dominant"][i])
        td  = 'style="text-align:center;padding:8px 6px'
        c_day.append(f'<td {td};color:#fff;font-size:13px;font-weight:700;white-space:nowrap">{fmt_giorno(daily["time"][i])}</td>')
        c_met.append(f'<td {td};font-size:21px" title="{desc}">{emo}<br><span style="font-size:10px;color:{C["muted"]}">{desc[:14]}</span></td>')
        c_max.append(f'<td {td};font-weight:bold;color:{tc_max};font-size:14px">{daily["temperature_2m_max"][i]:.1f}°</td>')
        c_min.append(f'<td {td};color:{tc_min};font-size:13px">{daily["temperature_2m_min"][i]:.1f}°</td>')
        c_pre.append(f'<td {td};color:{C["cool"]};font-size:12px">{daily["precipitation_sum"][i]:.1f} mm</td>')
        c_wnd.append(f'<td {td};color:{C["muted"]};font-size:12px">{daily["windspeed_10m_max"][i]:.1f} km/h</td>')
        c_wdr.append(f'<td {td};color:{C["accent2"]};font-size:13px;white-space:nowrap">{wa}</td>')

    th_day = "".join(c.replace("<td ", "<th ").replace("</td>","</th>") for c in c_day)

    return f"""
<div style="margin-bottom:24px">
  <div style="font-size:15px;font-weight:700;color:{C['accent2']};margin-bottom:10px">&#128197; {title}</div>
  <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;background:{C['card']};border:1px solid {C['border']};border-radius:8px;overflow:hidden">
    <thead><tr style="background:{C['hdr']}"><th {th}>Giorno</th>{th_day}</tr></thead>
    <tbody>
      {row("Meteo",     c_met, C['card2'])}
      {row("Massima",   c_max, C['card'])}
      {row("Minima",    c_min, C['card2'])}
      {row("Precipit.", c_pre, C['card'])}
      {row("Vento max", c_wnd, C['card2'])}
      {row("Direzione", c_wdr, C['card'])}
    </tbody>
  </table>
</div>"""

# ── Costruisci HTML completo ─────────────────────────────────────────────────
def build_html(hourly, daily, banner_src):
    t72  = "".join(table_72h_day(hourly, i) for i in range(3))
    t14  = "".join(table_14day_week(daily, i) for i in range(2))
    now  = datetime.now().strftime("%-d aprile %Y alle %H:%M")

    return f"""<!DOCTYPE html>
<html lang="it">
<head><meta charset="UTF-8"><title>Meteo Santiago del Cile</title></head>
<body style="margin:0;padding:0;background:{C['bg']};font-family:Arial,Helvetica,sans-serif;color:{C['text']}">
<div style="max-width:860px;margin:0 auto;padding:20px 16px">

  <!-- BANNER -->
  <div style="border-radius:12px 12px 0 0;overflow:hidden;position:relative;line-height:0">
    <img src="{banner_src}" alt="Santiago del Cile" width="100%"
         style="display:block;width:100%;height:220px;object-fit:cover;object-position:center 60%">
    <div style="position:absolute;bottom:0;left:0;right:0;background:linear-gradient(transparent,rgba(0,0,0,.80));padding:18px 20px">
      <div style="font-size:26px;font-weight:800;color:#fff">&#127464;&#127473; Santiago del Cile</div>
      <div style="font-size:13px;color:rgba(255,255,255,.75);margin-top:3px">Previsioni meteorologiche · Aprile 2026</div>
    </div>
  </div>

  <!-- AUGURI PASQUALI -->
  <div style="background:linear-gradient(135deg,#1a0533,#0d1117 50%,#0a2010);border:1px solid {C['border']};border-top:3px solid {C['easter1']};border-radius:0 0 12px 12px;padding:28px 24px;margin-bottom:28px;text-align:center">
    <div style="font-size:34px;margin-bottom:10px">&#128163; &#127800; &#10013;&#65039; &#127800; &#129370;</div>
    <div style="font-size:27px;font-weight:800;color:{C['easter1']};margin-bottom:10px;letter-spacing:1px">Buona Pasqua, Harald!</div>
    <div style="font-size:16px;color:{C['text']};line-height:1.75;max-width:620px;margin:0 auto">
      In questo giorno di Pasqua ti auguriamo, insieme a tutta la tua famiglia,<br>
      una festa piena di gioia, serenità e luce. &#127775;<br>
      Che questa Pasqua porti rinnovamento e speranza in ogni angolo della vostra vita —<br>
      proprio come la primavera porta nuova vita alla terra. &#127799;
    </div>
    <div style="font-size:13px;color:{C['muted']};margin-top:16px;font-style:italic">Con affetto · Pasqua 2026</div>
  </div>

  <!-- 72 ORE -->
  <div style="margin-bottom:32px">
    <div style="margin-bottom:18px;padding-bottom:10px;border-bottom:2px solid {C['accent']}">
      <div style="font-size:20px;font-weight:800;color:#fff">&#128336; Previsioni prossime 72 ore</div>
      <div style="font-size:13px;color:{C['muted']}">Intervalli di 3 ore · 8 fasce orarie al giorno · Santiago del Cile (CLT, UTC&#8722;3)</div>
    </div>
    {t72}
  </div>

  <!-- 14 GIORNI -->
  <div style="margin-bottom:32px">
    <div style="margin-bottom:18px;padding-bottom:10px;border-bottom:2px solid {C['easter3']}">
      <div style="font-size:20px;font-weight:800;color:#fff">&#128197; Previsioni a 14 giorni</div>
      <div style="font-size:13px;color:{C['muted']}">7 giorni per settimana · Temperature max/min · Vento e direzione</div>
    </div>
    {t14}
  </div>

  <!-- LEGENDA -->
  <div style="background:{C['card']};border:1px solid {C['border']};border-radius:10px;padding:16px 20px;margin-bottom:24px">
    <div style="font-size:13px;font-weight:700;color:{C['muted']};margin-bottom:8px">LEGENDA DIREZIONE VENTO</div>
    <div style="font-size:12px;color:{C['muted']};line-height:2">
      &#8593; da Sud &nbsp;|&nbsp; &#8595; da Nord &nbsp;|&nbsp; &#8592; da Est &nbsp;|&nbsp; &#8594; da Ovest &nbsp;|&nbsp;
      &#8599; da SO &#8594; soffia verso NE (tipico di Santiago)
    </div>
    <div style="margin-top:8px;font-size:11px;color:{C['muted']}">Fonte: open-meteo.com · 33.5°S, 70.625°O · 540 m s.l.m.</div>
  </div>

  <!-- FOOTER -->
  <div style="text-align:center;padding:16px;font-size:12px;color:{C['muted']};border-top:1px solid {C['border']}">
    Generato il {now} · Santiago del Cile, Cile
  </div>

</div>
</body>
</html>"""

# ── Salva Gmail-Entwurf via IMAP ─────────────────────────────────────────────
def save_gmail_draft(msg_bytes):
    print("📥 Salvataggio bozza in Gmail via IMAP...")
    with imaplib.IMAP4_SSL("imap.gmail.com", 993) as imap:
        imap.login(GMAIL_USER, GMAIL_PWD)
        # Trova la cartella con il flag \Drafts (indipendente dalla lingua)
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
        print(f"   Cartella: {drafts_folder}")
        quoted = f'"{drafts_folder}"'
        imap.append(quoted, "\\Draft",
                    imaplib.Time2Internaldate(datetime.now(timezone.utc)),
                    msg_bytes)
    print("✅ Bozza salvata!")

# ════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # 1. Dati meteo
    hourly, daily = fetch_weather()

    # 2. Banner
    banner_bytes = fetch_banner()
    use_cid = banner_bytes is not None

    # 3. HTML
    banner_src = "cid:banner_santiago" if use_cid else ""
    html = build_html(hourly, daily, banner_src)

    # 4. Preview locale
    preview_path = "/tmp/meteo_santiago_preview.html"
    if use_cid:
        b64 = base64.b64encode(banner_bytes).decode("ascii")
        html_preview = html.replace("cid:banner_santiago", f"data:image/jpeg;base64,{b64}")
    else:
        html_preview = html
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(html_preview)

    # 5. MIME message
    msg_root = MIMEMultipart("related")
    msg_root["Subject"] = SUBJECT
    msg_root["From"]    = f"Meteo Santiago <{GMAIL_USER}>"
    msg_root["To"]      = TO

    msg_alt = MIMEMultipart("alternative")
    msg_alt.attach(MIMEText(html, "html", "utf-8"))
    msg_root.attach(msg_alt)

    if use_cid:
        img = MIMEImage(banner_bytes, _subtype="jpeg")
        img.add_header("Content-ID", "<banner_santiago>")
        img.add_header("Content-Disposition", "inline", filename="santiago.jpg")
        msg_root.attach(img)

    msg_bytes = msg_root.as_bytes()

    # 6. Gmail-Entwurf
    save_gmail_draft(msg_bytes)

    # 7. Gmail Entwürfe im Browser öffnen
    import subprocess as sp
    sp.Popen(["open", "https://mail.google.com/mail/u/0/#drafts"])
    print("🌐 Gmail Entwürfe geöffnet")
    print(f"📄 Preview: {preview_path}")
