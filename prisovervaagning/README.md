# Afgang · Prisovervågning (recurring)

Overvåger konkurrenters priser over tid og alarmerer ved ændringer.
- Prisposition pr. produkt: billigst / midt / dyrest + billigste konkurrent + gap.
- Ændringsdetektion: sammenligner to snapshots → alarmer (retning + %) over en tærskel.
- Anbefalinger.

## Filer
- `prisovervagning.py` — deterministisk positions-/ændringskerne + `collect_snapshot()` scraping-interface.
- `test_pris.py` — test af position, alarmer, fetcher-mock.

## Ærlig arkitektur-grænse
Prisindsamlingen (skrabe konkurrentsider) wires ved deployment via `collect_snapshot(..., fetcher)`.
- Deterministisk kerne: testet og verificeret.
- Live scraping: IKKE testet — kræver fetcher ved deploy.
- Recurring: kør pr. tier (Start ~50 varer / Plus ~500 / Pro ~5000), gem snapshot hver kørsel, sammenlign med forrige.

## Kør
python3 test_pris.py
