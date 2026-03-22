---
name: SSKM Kontoauszug-Analyse Script
description: Location and purpose of the SSKM bank statement analysis script
type: project
---

`build_sskm_analyse.py` — parst `SSKM-23-26.html` (Stadtsparkasse München, Konto DE10 7015 0000 0045 1277 84, HARALD BEKER UND ROSEMARIE BEKER, 1044 Buchungen 21.03.2023–21.03.2026) und erzeugt `sskm_analyse.html` + `sskm_analyse.pdf`.

**Why:** Für zukünftige Wiederverwendung und Erweiterung des Analyse-Scripts.

**How to apply:** Bei neuen SSKM-Auswertungen dieses Script als Basis verwenden und ggf. mit neuem HTML-Export aktualisieren.

## Kategorisierung (Stand 2026-03-21)

### Ausschlüsse (eigene Überweisungen)
- Payees matching `Harald Beker` / `Beker, Harald` → komplett ausgeschlossen
- Carl Beker Zahlungen **> 9.000 €** → ausgeschlossen

### Payee-Normalisierungen
- Alle CIGNA-Varianten → `CIGNA INTERNATIONAL HEALTH`
- Alle AMAZON-Varianten + `LANDESBANK BERLIN` → `Amazon`
- Alle PAYPAL-Varianten → `PayPal`
- Dr. Meindl/Meinl-Varianten → `Dr. Meindl u. Partner`
- Andree Runge-Varianten → `Andree Runge`
- Dr. Kaufmann-Varianten → `Dr. Daniel Kaufmann`
- Sowa/Sowaa-Varianten → `Dr. Volker Sowa`
- Dres./BAG HNO-Varianten → `Dres. Roth/Stelzer/Köhler/Woldt`
- Allergieambulatorium-Varianten → `Allergieambulatorium`

### Kategorien (Ausgaben)
- **Kinder**: Carl Beker, Maria Beker (separate Empfänger)
- **Ärzte**: DR., DRES., RUNGE, MEINDL, SOWA, ALLERGI, BAG HNO
- **PayPal**: PayPal
- **Shopping**: Amazon (inkl. Landesbank Berlin), Zalando, H&M, etc.
- **Lebensmittel**: Aldi, Lidl, Rewe, Edeka, etc.
- **Restaurant/Cafe**, **Verkehr/Transport**, **Wohnen**, **Gesundheit**, **Freizeit**, **Sparen/Investments**, **Sonstiges**

### Kategorien (Einnahmen)
- **Krankenkasse**: CIGNA INTERNATIONAL HEALTH (127 Erstattungen)
- **Gehalt/Rente**, **Zinsen/Dividenden**, **Steuer/Soziales**, **Sonstige Einnahmen**
