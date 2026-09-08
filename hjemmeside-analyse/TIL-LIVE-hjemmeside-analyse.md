# Hjemmeside-analyse — vejen til live (to-do)

Motoren er kode-komplet og testet. Her er præcis hvad der mangler, hvem gør hvad, og rækkefølgen. Følger byggeprocessen: sandbox → godkend → prod.

## Status: hvad er færdigt (testet)
- `GOLDEN-STANDARD-hjemmeside-analyse.md` — produktdefinition.
- `analyze.py` — lag 1 (automatisk). **27 tests grønne** (`test_analyze.py`).
- `fetch_site.py` — crawler (kører på Cloud Run).
- `lang_layer.py` — lag 2 (sprog via Gemini), nøgle fra env, springes over uden nøgle.
- `GENERATOR-hjemmeside-analyse.py` — payload → client + demo HTML.
- `main.py` — Cloud Run-service (`/analyse`), wiring testet (demo/client/preview/fejl).
- `requirements.txt` + `Dockerfile`.
- Reference-output: Illona (client + demo).

## Hvad jeg skal bruge fra dig
1. **Gemini API-nøgle** (fra Bitwarden / Google AI Studio). Sættes som env-var ved deploy — **ikke i koden**. (Uden den virker alt undtagen sprog-fanen.)
2. **Repo-valg:** skal motoren ligge i `SLS-Tech-DK/afgang` (undermappe) eller et nyt repo `SLS-Tech-DK/hjemmeside-analyse`? Sig hvilket, så committer jeg koden.
3. **GCP-projekt/region:** samme som afgang (`afgang`, `europe-north1`)? Bekræft.
4. **Stripe:** skal jeg lave et produkt "Hjemmeside-analyse" + pris (fx samme model som butiksanalysen)? Sig pris.
5. **Dig til gcloud-deploy** — kun du deployer Cloud Run.

## Rækkefølge til live

### 1. Kode i GitHub (jeg)
Når du har valgt repo (punkt 2) committer jeg alle motor-filer dertil via push-til-github.

### 2. Deploy til Cloud Run SANDBOX (dig — gcloud)
Fra motor-mappen:
```
gcloud run deploy hjemmeside-analyse \
  --source . --project afgang --region europe-north1 \
  --allow-unauthenticated --no-traffic --tag sandbox \
  --set-env-vars GEMINI_API_KEY=<nøgle fra Bitwarden>
```
Den printer en sandbox-URL (`sandbox---hjemmeside-analyse-…run.app`).

### 3. Jeg verificerer server-side (sandbox)
- `…/health` → `{ok:true}`
- `…/analyse?url=illona-laursen.dk&preview=1` → score + top-3 (JSON)
- `…/analyse?url=illona-laursen.dk&mode=demo` → fuld demo-rapport
- Tjekker at fund + score matcher det vi ved om Illona. Ikke godt → tilbage til kode.

### 4. Godkend + udgiv (dig)
```
gcloud run services update-traffic hjemmeside-analyse \
  --project afgang --region europe-north1 --to-latest
```

### 5. One-click på afgang-frontend (jeg bygger, efter motoren er live)
En side på slstech.dk/afgang hvor kunden skriver sin URL:
- kalder `/analyse?url=…&preview=1` → viser **score + top-3 gratis**
- "Se hele analysen" → **Stripe-betaling** → låser fuld rapport (`mode=client`) op
- Samme køb-kæde som butiksanalysen (bevist 19/8).

### 6. Log på board (jeg)
Opdatér board_items: motor live, demo live, hvem har bolden.

## Faldgruber (verificeret undervejs)
- **Fetch må kun køre på Cloud Run** (din egress), ikke i cowork-containeren — derfor er `fetch_site.py` isoleret fra `analyze.py`.
- Nogle sider blokerer robots.txt/crawl (Illona gav 503 på simpel web-fetch) → Cloud Run med rigtig User-Agent klarer det; ellers falder motoren tilbage til forsidens links.
- Nøgler aldrig i kode/repo — kun env-var ved deploy.
- Sprog-laget er forslag, skal læses igennem. Aldrig "stak" — altid "stack".

## Bolden
Søren: svar på de 5 punkter under "Hvad jeg skal bruge fra dig" (mindst repo-valg + Gemini-nøgle-klar). Så committer jeg til GitHub og vi kører deploy-trinnet sammen.
