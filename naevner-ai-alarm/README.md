# Afgang · "Nævner AI min virksomhed"-alarm (recurring)

Månedligt tjek: nævner AI-modellerne kundens virksomhed når folk spørger om branchen?
Alarmerer når synligheden flytter sig vs. sidste måned, og når en konkurrent rykker frem.

## Filer
- `naevner_ai_alarm.py` — deterministisk sammenlignings-/alarmkerne. Bygger på GEO-motoren i `ai_synlighed.py`.
- `ai_synlighed.py` — delt GEO-motor (fra AI-synlighedsproduktet).
- `test_alarm.py` — test af baseline, ændringsalarm, konkurrent-fremgang.

## Sådan kører den recurring
Hver måned: kør `run_check(query_results, brand, competitors, previous_measurement)`.
Gem `measurement` fra svaret → brug som `previous_measurement` næste måned.

## Ærlig arkitektur-grænse
AI-forespørgslerne wires til Gemini/Vertex via `ai_synlighed.run_queries` ved deployment.
- Deterministisk alarmkerne: testet og verificeret.
- Live model-forespørgsler: IKKE testet — kræver querier ved deploy.

## Kør
python3 test_alarm.py
