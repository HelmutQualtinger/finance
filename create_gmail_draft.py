#!/usr/bin/env python3
"""
Erstellt Gmail-Entwurf mit dem Wetterbericht via IMAP.
Bild wird als inline CID-Attachment eingebettet (multipart/related),
damit Gmail es korrekt anzeigt.
"""
import imaplib, email.mime.multipart, email.mime.text, email.utils, re, os, sys
from email.mime.image import MIMEImage
from datetime import datetime

# ── .env laden ───────────────────────────────────────────────────────────────
def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        print(f"FEHLER: .env nicht gefunden: {env_path}", file=sys.stderr); sys.exit(1)
    env = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1); env[k.strip()] = v.strip()
    for key in ("GMAIL_USER", "GMAIL_PWD"):
        if key not in env:
            print(f"FEHLER: {key} fehlt in .env", file=sys.stderr); sys.exit(1)
    return env

_env = _load_env()
USER = _env["GMAIL_USER"]
PASS = _env["GMAIL_PWD"]
TO   = "REDACTED"
SUBJ = f"Wetterbericht Rebstein – {datetime.now().strftime('%d.%m.%Y')}"
CID  = "rebstein_banner"

# HTML lesen
with open("/Users/haraldbeker/finance/wetter_rebstein_email.html", "r", encoding="utf-8") as f:
    html_body = f.read()

# Base64-Bild im HTML durch CID ersetzen
html_email = re.sub(
    r'src="data:image/jpeg;base64,[^"]+"',
    f'src="cid:{CID}"',
    html_body
)

# MIME-Struktur: multipart/related → HTML + Bild
related = email.mime.multipart.MIMEMultipart("related")

html_part = email.mime.text.MIMEText(html_email, "html", "utf-8")
related.attach(html_part)

# Bild als inline Attachment laden
with open("/tmp/rebstein_banner.jpg", "rb") as f:
    img_data = f.read()

img_part = MIMEImage(img_data, "jpeg")
img_part["Content-ID"]          = f"<{CID}>"
img_part["Content-Disposition"] = "inline"
related.attach(img_part)

# Äußere Nachricht
msg = email.mime.multipart.MIMEMultipart("mixed")
msg["From"]    = USER
msg["To"]      = TO
msg["Subject"] = SUBJ
msg["Date"]    = email.utils.formatdate(localtime=True)
msg.attach(related)

raw = msg.as_bytes()

# IMAP → Gmail Entwürfe
print("Verbinde mit Gmail IMAP…")
imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
imap.login(USER, PASS)
print("  Eingeloggt.")

draft_folder = '"[Google Mail]/Entw&APw-rfe"'
result = imap.append(draft_folder, r"\Draft", None, raw)
print(f"  Ergebnis: {result}")
imap.logout()

print(f"\n✅ Entwurf erstellt: '{SUBJ}'")
print(f"   An: {TO}")
print(f"   Größe: {len(raw)//1024} KB")
print(f"\n👉 https://mail.google.com/mail/#drafts")
