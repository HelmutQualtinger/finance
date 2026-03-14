---
name: Commit and push every change
description: User wants every code/data change committed and pushed immediately
type: feedback
---

Committe und pushe jede Änderung sofort nach Durchführung — nicht erst am Ende oder gebündelt.

**Why:** User erwartet einen sauberen Git-Verlauf mit granularen Commits und will Änderungen sofort auf dem Remote sehen.

**How to apply:** Nach jeder Datei-Änderung (Code, Daten, Config) direkt `git add` + `git commit` + `git push origin main` ausführen, ohne nachzufragen.
