# Afgang · AI-synlighed (GEO+AEO)

Input: brand + konkurrenter + branche (+ evt. sider). Output:
- GEO: bliver brandet nævnt når folk spørger AI-modeller? Mention-rate + share-of-voice vs. konkurrenter + quick wins.
- AEO: er sidernes tekst læsbar for AI-søgning? Audit (spørgsmålsoverskrifter, FAQ, schema, korte svar, lister) + anbefalinger.

## Filer
- `ai_synlighed.py` — deterministisk GEO-score + AEO-audit + `run_queries()`-interface til AI-forespørgsler.
- `ai_forklaring.py` — Gemini/Vertex-lag → kundevendt dansk tekst.
- `test_ai.py` — test af score, audit, query-mock, Gemini-mock.

## Ærlig arkitektur-grænse
AI-forespørgslerne (spørge modeller om branchen) wires til Gemini/Vertex ved deployment via `run_queries(prompts, querier)`.
- Deterministisk score-/audit-kerne: testet og verificeret.
- Live model-forespørgsler + live Vertex-kald: IKKE testet — kræver nøgle ved deploy.

## Kør
python3 test_ai.py
