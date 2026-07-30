# Afgang · Deploy-infrastruktur

Samler alle motorer bag én HTTP-router og gør dem klar til Cloud Run/Functions.

## Filer
- `main.py` — Cloud Function-router (functions-framework). Ruter POST {type,...} til rette motor. Entry-point: `handler`. Ren `route()`-funktion er testet.
- `test_router.py` — tester routing for alle 14 produkttyper + fejl-håndtering.
- `requirements.txt` — functions-framework + google-cloud-aiplatform (Vertex/Gemini).
- `cloudbuild.yaml` — deployer som Cloud Function gen2 til europe-north1 (`gcloud builds submit`).
- `Dockerfile` — alternativ: kør som container på Cloud Run.
- `supabase_orders.sql` — UDKAST til generisk `orders`-tabel + RLS + idempotens.
- `orchestrator_v2.gs` — UDKAST: Apps Script der poller betalte ordrer → kalder routeren → leverer → mailer.

## Sådan hænger det sammen (deploy-flow)
1. Kunde betaler via Stripe → webhook sætter `orders.payment_status='betalt'`, `delivery_status='i_gang'`.
2. `orchestrator_v2.pollProductOrders` (trigger hvert 5. min) henter betalte+i_gang ordrer.
3. Kalder motor-routeren (`main.handler`) med `{type, ...input}`.
4. Motoren kører deterministisk analyse (+ Gemini-forklaring hvis `GEMINI_ENABLED=1`).
5. Orchestrator gemmer leverancen i Drive, mailer kunden, sætter `delivery_status='leveret'`.

## Hvad DU skal sætte ved deploy (kræver dine nøgler/adgange)
- GCP: `gcloud builds submit --config cloudbuild.yaml` (projekt = Kniven GCP eller nyt Afgang-projekt).
- Vertex/Gemini: service-kontoen skal have Vertex AI-adgang; sæt `GOOGLE_CLOUD_PROJECT` + `VERTEX_LOCATION=europe-north1` (cloudbuild sætter allerede sidstnævnte).
- Data-kilder for konkurrent/AI-synlighed/pris: wire de rigtige fetcher/querier-funktioner (scraping + AI-forespørgsler) — motorerne har interfaces klar.
- Supabase: kør `supabase_orders.sql` (tjek/justér mod eksisterende `orders`-tabel før!).
- Stripe: opret produkter/priser + webhook der sætter orders-rækker.
- Apps Script: læg `orchestrator_v2.gs` ind, sæt Script Properties (SUPABASE_URL, SUPABASE_SERVICE, MOTOR_URL, SLS_EMAIL, DRIVE_FOLDER), opret 5-min trigger.

## Status
- `route()` + alle 14 motorer: testet lokalt. CI kører alle test_*.py ved hvert push (se .github/workflows/ci.yml).
- IKKE testet: live deploy, Vertex-kald, dataindsamling, Stripe/Supabase-kobling — kræver dine adgange.
