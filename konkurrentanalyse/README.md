# Afgang · Konkurrentanalyse-motor

Input: kundens domæne + op til 3 konkurrenter. Output: side-om-side (pris, sortiment, trafik, AI-synlighed, fragt), gaps (foran/bagud), og prioriteret "hvor du kan vinde".

## Filer
- `konkurrentanalyse.py` — data-kontrakt + deterministisk sammenlignings-/scoringskerne + `collect()`-interface til dataindsamling.
- `konk_forklaring.py` — Gemini/Vertex-lag → kundevendt dansk tekst.
- `test_konk.py` — test af kerne + mock-fetcher + Gemini-mock.

## Ærlig arkitektur-grænse
Dataindsamlingen (skrabe konkurrentsider, trafik-estimat, SEO/AI-synlighed) sker UDEFRA og wires til rigtige kilder ved deployment via `collect(domain, competitors, fetcher)`. 
- Deterministisk sammenligningskerne: testet og verificeret.
- Live fetch + live Vertex-kald: IKKE testet — kræver at kilder (scraping/SEO-API/AI-synlighedsmotor) og Gemini-nøgle wires ved deploy.

## Kør
python3 test_konk.py
