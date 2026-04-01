#!/usr/bin/env python3
"""
Erstellt Gmail-Entwurf mit dem Wetterbericht via IMAP.
"""
import imaplib, email.mime.multipart, email.mime.text
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# Credentials
USER = "qualcunodue@gmail.com"
PASS = "hvzxtoctcosodbrh"
TO   = "REDACTED"
SUBJ = f"Wetterbericht Rebstein – {datetime.now().strftime('%d.%m.%Y')}"

# HTML lesen
with open("/Users/haraldbeker/finance/wetter_rebstein_email.html", "r", encoding="utf-8") as f:
    html_body = f.read()

# MIME-Nachricht aufbauen
msg = email.mime.multipart.MIMEMultipart("alternative")
msg["From"]    = USER
msg["To"]      = TO
msg["Subject"] = SUBJ
msg["Date"]    = email.utils.formatdate(localtime=True)

part = email.mime.text.MIMEText(html_body, "html", "utf-8")
msg.attach(part)

raw = msg.as_bytes()

# IMAP Verbindung
print(f"Verbinde mit Gmail IMAP…")
imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
imap.login(USER, PASS)
print("  Eingeloggt.")

# Draft-Ordner finden
typ, folders = imap.list()
draft_folder = None
for f in folders:
    decoded = f.decode()
    if "Draft" in decoded or "Entwurf" in decoded:
        # Ordnernamen extrahieren
        parts = decoded.split('"')
        name = parts[-2] if len(parts) > 1 else decoded.split()[-1]
        draft_folder = name
        break

if not draft_folder:
    draft_folder = "[Gmail]/Drafts"

print(f"  Draft-Ordner: {draft_folder}")

# Nachricht in Drafts anhängen
import time
date_time = imaplib.Time2Internaldate(time.time())
result = imap.append(draft_folder, "\\Draft", None, raw)
print(f"  Ergebnis: {result}")

imap.logout()
print(f"\n✅ Entwurf erstellt: '{SUBJ}'")
print(f"   An: {TO}")
print(f"   Größe: {len(raw)//1024} KB")
print(f"\n👉 Entwurf in Gmail öffnen:")
print(f"   https://mail.google.com/mail/#drafts")
