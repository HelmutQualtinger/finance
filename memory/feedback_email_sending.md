---
name: Gmail SMTP E-Mail-Versand
description: E-Mails über Gmail SMTP mit Python senden statt über MCP Gmail Draft
type: feedback
---

E-Mails direkt über Python smtplib und Gmail SMTP senden, nicht als Gmail-Entwurf.

**Methode:**
- Python3 `smtplib` mit `smtp.gmail.com:587` (STARTTLS)
- Absender: `qualcunodue@gmail.com`
- App-Passwort: `hvzxtoctcosodbrh`
- HTML-E-Mails mit `email.mime.multipart.MIMEMultipart("alternative")` und `MIMEText(html, "html")`

**Why:** MCP Gmail-Integration kann nur Entwürfe erstellen aber nicht senden. Python SMTP sendet direkt.

**How to apply:** Bei jeder E-Mail-Versandanfrage direkt ein Python-Script mit smtplib verwenden statt Gmail MCP Draft.
