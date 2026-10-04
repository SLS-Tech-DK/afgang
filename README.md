# afgang

Self-serve AI-analyser for webshops. En webshop-ejer vælger en analyse, betaler, og får en rapport genereret af en analyse-motor på Google Cloud — uden at tale med et menneske.

## Analyser
Salg · indkøb · lager · kunde · konkurrent · fuld butiksanalyse · AI-synlighed (AEO/GEO). Hver type kører sin egen prompt-routing mod motoren og leverer en færdig rapport.

## Arkitektur
- **Gateway** (`gateway/main.py`) — ruter forespørgsler, håndterer adgang og betalings-gating (gratis demo vs. betalt kørsel via access-token)
- **Orchestrator** — styrer analyse-flowet pr. produkttype
- **Analyse-motor** — kører selve analysen (Gemini)
- **Betaling** — Stripe-webhook (`deploy/afgang-stripe-webhook`) → ordre i Supabase → auto-levering
- **Frontend** — self-serve købs- og rapport-flow

## Stack
Google Cloud (Cloud Run, europe-north1) · Python · Supabase · Stripe · Gemini

## Note
Showcase-udgave. Ingen nøgler i koden — alt læses fra server-side env-variabler. Kundedata og produktionskonfiguration er ikke med.
