#!/usr/bin/env python3
"""
Erstellt Gmail-Entwurf mit dem Wetterbericht via IMAP.
"""
import imaplib, email.mime.multipart, email.mime.text, email.utils
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
# Gmail Entwürfe-Ordner (IMAP-UTF7: ü = &APw-)
draft_folder = '"[Google Mail]/Entw&APw-rfe"'
print(f"  Draft-Ordner: {draft_folder}")

# Nachricht in Drafts anhängen
result = imap.append(draft_folder, r"\Draft", None, raw)
print(f"  Ergebnis: {result}")

imap.logout()
print(f"\n✅ Entwurf erstellt: '{SUBJ}'")
print(f"   An: {TO}")
print(f"   Größe: {len(raw)//1024} KB")
print(f"\n👉 Entwurf in Gmail öffnen:")
print(f"   https://mail.google.com/mail/#drafts")
