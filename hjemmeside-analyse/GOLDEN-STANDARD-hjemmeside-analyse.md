# afgang Hjemmeside-analyse — Golden Standard (produktdefinition)

> Modstykket til Butiksanalysen: butiksanalyse = webshops (CSV ind), hjemmeside-analyse = hjemmesider (URL ind).
> Reference-bygget på illona-laursen.dk. Denne fil definerer produktet, så næste kundes URL kører gennem samme motor og giver samme kvalitet.

## Hvad kunden får
Én interaktiv HTML-analyse (single-file, virker offline, mørkt+lyst tema, afgang-design) med 8 faner:
1. **Anbefalinger** — rangeret efter effekt (crit/høj/mellem/let). Beslutningsværktøj, ikke fejlliste. Det vigtigste.
2. Overblik — samlet score + fundament (OK) vs. det der trækker ned.
3. SEO — titler, meta-beskrivelser, H1, canonical, sitemap, robots.
4. Sprog & tekst — konkrete fejl side for side (tabel).
5. Lokal synlighed — Google Business-profil, LocalBusiness-schema (færdig kode), anmeldelser.
6. AI-synlighed (AEO) — llms.txt, robots, FAQ-schema, citérbarhed.
7. Indhold & blog — "kommer snart", manglende artikler/emner, tynde sider, uens priser.
8. Booking & konvertering — book-vej, formularsprog, pakker/klippekort, forsikring.

## Input (kræves)
Én **URL** til forsiden. Motoren finder selv undersider via sitemap.xml (fallback: links på forsiden).
Valgfrit: brancheord (klinik/webshop/…) + adresse/telefon hvis de skal bruges i schema-forslag.

## To output fra samme motor (som butiksanalysen)
- **Klient** (`client`): fuld, navngivet, fortrolig. → leveres til kunden.
- **Demo** (`demo`): navn kan anonymiseres (fx "en klinik i København"), afgang-branding + CTA "Book din egen analyse". → frontend på slstech.dk/afgang.
`GENERATOR-hjemmeside-analyse.py` bygger begge fra samme payload: `build('client')` / `build('demo')`.

## Metode — hvad der tjekkes, og hvordan (ærligt: hvad er automatik, hvad er vurdering)

### Lag 1 — Automatiske, objektive tjek (kan køres maskinelt, ingen gæt)
Pr. side: `<title>` (findes, længde, dubletter), meta-description (findes/længde), antal `<h1>`, `lang`-attribut, ordantal (tynd side?), billeder uden `alt`, placeholder-tekst ("kommer snart", "lorem", "[…]"), engelske formularfelter (Name/Email/Message/Send) på dansk side.
Site-niveau: robots.txt (findes? peger på sitemap?), sitemap.xml (findes?), llms.txt (findes?), schema-typer i JSON-LD (Organization / LocalBusiness / FAQPage / …), HTTPS, viewport/mobil, canonical, døde links (HEAD-status).

### Lag 2 — Sprog/kvalitet (AI-vurdering, ikke ren automatik)
Stavefejl og klodset dansk fanges bedst med en sprogmodel oven på den rå tekst. **Regel (SLS): kundevendt/B2C = Gemini** (billigt, self-serve). Interne kørsler kan bruge Anthropic. Aldrig "stak" — altid "stack".
Output: liste af (side, fundet → foreslået rettelse). Markér at det er forslag der skal læses igennem fagligt.

### Lag 3 — Synligheds-vurdering (regler + kontekst)
Google Business-profil: kan ikke afgøres 100% fra kildekoden alene → tjek Maps-opslag (menneske eller browser-tjek), notér "bekræft". LocalBusiness-kode genereres ud fra adresse/telefon. Score sammensættes af lag 1+2+3 med faste vægte (se scoring).

## Scoring (så tallet er ærligt og reproducerbart)
Start 100. Træk fra pr. fundtype med fast vægt (kritisk −12, høj −7, mellem −4, let −2), gulv 0. Samme vægte hver gang → to sider kan sammenlignes. Vis altid hvad der trak ned.

## Pipeline (teknisk)
1. **Fetch** (`fetch_site.py`) — henter forside + undersider (sitemap → ellers links). **Kører på Cloud Run (kundens/afgangs egress), IKKE i cowork-containeren** (web-fetch-restriktion). Gemmer rå HTML pr. side.
2. **Analyse** (`analyze.py`) — lag 1 automatisk + kalder LLM (Gemini) for lag 2 → `motor_data.json` (payload).
3. **Generér** (`GENERATOR-hjemmeside-analyse.py`) — payload → 2 HTML (client/demo).
4. **Test** (playwright headless) — alle 8 faner skifter, tema skifter, 0 JS-fejl.
5. Klient leveres; demo → afgang-frontend (sandbox → godkend → prod, per byggeproces).

## One-click fra frontend (målet)
Bruger skriver sin URL på slstech.dk/afgang → afgang-gateway kalder fetch+analyse på Cloud Run → gratis forhåndsvisning (score + top-3 anbefalinger) → betaling (Stripe) låser fuld rapport op. Samme flow som butiksanalysens køb-kæde.
**Kræver (Søren):** Cloud Run-service til fetch+analyse, Gemini-nøgle til lag 2, Stripe-produkt/pris, gateway-rute. Nøgler leveres når vi når deploy-trinnet.

## Faldgruber
- **Web-fetch må ikke køre i cowork-containeren** — kun via WebFetch/browser her, ellers på Cloud Run. Aldrig curl/python-fetch i denne container.
- Robots-blokerede sider (fx illona-laursen.dk gav 503 på WebFetch) → brug browser-render i stedet, eller kør fetch på Cloud Run.
- Stavefejl-laget er forslag, ikke facit — skal læses igennem.
- Google-profil kan ikke afgøres fra kildekode alene → markér "bekræft".
- Aldrig oversælg: score og fund skal kunne genfindes i sidens kildekode.

## Status 08-09-2026
- Golden standard: denne fil.
- Generator (`GENERATOR-hjemmeside-analyse.py`): bygget + testet, laver client+demo fra payload.
- Illona-payload (`illona_payload.json`) + genereret demo: bygget som reference-output.
- Mangler til one-click: fetch+analyse på Cloud Run, Gemini-nøgle, Stripe, gateway (Sørens infra).
