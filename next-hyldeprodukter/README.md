# Afgang · NEXT-hyldeprodukter

Fem self-serve produkter, samme metodik som dag 1: deterministisk kerne (testet) + data-upload; nuanceret tekst = Gemini-lag (wires ved deploy).

## Produkter
- `produkttekst.py` — Produkttekst-optimering: upload katalog → AEO-parathedsscore pr. produkt + pris/produkt (20 kr, min. 250, batch-rabat >100). Omskrivning til bedre tekst = Gemini.
- `review_analyse.py` — Review-/omdømme-analyse: upload reviews → rating-fordeling, tema-frekvens, hvad der koster salg i lave anmeldelser.
- `landingsside.py` — Landingsside-teardown: sidetekst → konverterings-kritik (overskrift, CTA, trust, kontakt, struktur) + score + anbefalinger.
- `annonce_spild.py` — Annonce-spildsanalyse: upload annonce-data → ROAS/CPA/CTR pr. kampagne + prioriteret spildliste (højt forbrug, lavt afkast).
- `soegeords_gap.py` — Søgeords-gap: upload intern søgelog → termer med mange søgninger men ingen resultater = manglende produkter. 100% egen data.

`salgsanalyse.py` genbruges for CSV-parsing-hjælpere.

## Status
- Alle deterministiske kerner: testet og verificeret (`test_next.py`).
- Gemini-forklarings-/omskrivningslag: samme validerede mønster som dag 1, wires ved deploy (ikke testet mod live API).

## Kør
python3 test_next.py
