#!/usr/bin/env python3
"""
Erstellt Gmail-Entwurf mit dem Wetterbericht via IMAP.
Bild wird als inline CID-Attachment eingebettet (multipart/related),
damit Gmail es korrekt anzeigt.
"""
import imaplib, email.mime.multipart, email.mime.text, email.utils, re
from email.mime.image import MIMEImage
from datetime import datetime

# Credentials
USER = "qualcunodue@gmail.com"
PASS = "hvzxtoctcosodbrh"
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
