# Afgang · Butiksrøntgen — analyse-motorer

Self-serve hyldeprodukter under Afgang. Kunden uploader sin egen ordre-/salgs-CSV
og får indsigt i salg, indkøb, lager og kunder. Moat: analyserne kører på kundens EGEN data.

## Struktur
Delelementer (købes enkeltvis) + premium samle-motor:
- `salgsanalyse.py` — bestsellere, købes-sammen, bundles, kannibalisering. Indeholder det fleksible CSV-genkendelseslag (delt).
- `indkobsanalyse.py` — salgshastighed, genkøbsinterval, genbestillingsliste.
- `lageranalyse.py` — dødvarer, langsomtsælgere, sæson, kapitalbinding (via valgfri lager-CSV).
- `kundeanalyse.py` — CLV, RFM, churn-signal, segmenter.
- `butiksanalyse.py` — PREMIUM: kører alle fire + krydsanalyser (margin på tværs, kannibalisering) + samlet handlingsplan.
- `*_forklaring.py` / `gemini_forklaring.py` — Gemini/Vertex-lag der oversætter tallene til kundevendt dansk tekst.

## Princip
Tal beregnes deterministisk (aldrig gættet af LLM). Gemini forklarer kun de tal den får.
Kannibalisering er et *signal* ("undersøg om"), ikke bevis.

## Status
- Alle deterministiske kerner: testet og verificeret (se `test_*.py`).
- Gemini-lag: testet med mock. Live Vertex-kald IKKE testet — kræver `GOOGLE_CLOUD_PROJECT` + ADC ved deployment.
- Ikke bygget endnu: deployment som Cloud Function (europe-north1), kobling til Supabase `orders`, Stripe-køb.

## Kør tests
```
for t in test_*.py; do python3 "$t"; done
```

## Deployment (næste skridt)
- Wrap analyze() + forklar() i Cloud Function (europe-north1), Gemini via Vertex.
- orders-mønster: type pr. produkt, audit-gating efter Stripe-betaling.
