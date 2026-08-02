# Afgang — kvalitets-review af alle 14 analyser

Ægte output kørt live gennem motorerne på prøvedata 2. aug 2026. Læs igennem og vurdér om analyserne er gode nok til at ligge bag betalingen. Seks produkter har Gemini-forklaringslag (markeret); resten leverer deterministisk motor-output uden forklaringstekst endnu.

## Salgsanalyse  
`salgsanalyse`

**Nøgletal:** rows_used=276, distinct_products=6, distinct_orders=231, total_revenue=39351.0, avg_order_value=170.35

**Gemini-analyse:**

Her er en analyse af jeres salgsdata:

**1. Kort resumé**
Webshoppen har genereret 39351.0 kr i omsætning fordelt på 231 ordrer og 6 produkter. Den gennemsnitlige ordreværdi er 170.35 kr. "Kande" og "Kaffe" er de primære omsætningsdrivere. "Solcreme" er det svagest sælgende produkt. "Filter" og "Kaffe" købes ofte sammen.

**2. Hvad der driver omsætningen**
Omsætningen drives primært af "Kande" med 15522.0 kr og "Kaffe" med 10812.0 kr. Disse to produkter udgør størstedelen af den samlede omsætning. "Filter" er det produkt, der er solgt flest enheder af (118 stk.), men bidrager med 3422.0 kr i omsætning.

**3. Bundle-muligheder**
Dataen viser, at "Filter" og "Kaffe" købes sammen i 45 ordrer med en lift på 1.0. Dette indikerer en stærk relation mellem produkterne og en oplagt mulighed for at oprette en bundle.

**4. Mulige kannibaliseringer at undersøge**
*   Undersøg om "Filter" og "Kop" kannibaliserer. De sælger hver for sig, men købes sjældent sammen (0 ordrer sammen, forventet 16.4).
*   Undersøg om "Filter" og "The" kannibaliserer. De sælger hver for sig, men købes sjældent sammen (0 ordrer sammen, forventet 15.3).
*   Undersøg om "Filter" og "Kande" kannibaliserer. De sælger hver for sig, men købes sjældent sammen (0 ordrer sammen, forventet 14.1).
*   Undersøg om "Kaffe" og "Kop" kannibaliserer. De sælger hver for sig, men købes sjældent sammen (0 ordrer sammen, forventet 12.0).
*   Undersøg om "Kaffe" og "The" kannibaliserer. De sælger hver for sig, men købes sjældent sammen (0 ordrer sammen, forventet 11.2).

**5. Prioriteret handlingsliste**

1.  **Opret bundle:** Tilbyd en bundle med "Filter" og "Kaffe" for at kapitalisere på det eksisterende købsmønster (45 ordrer sammen, lift 1.0).
2.  **Analyser "Solcreme":** Undersøg årsagen til det lave salg af "Solcreme" (4 enheder, 356.0 kr omsætning). Overvej at fjerne produktet eller justere markedsføring.
3.  **Undersøg kannibalisering "Filter" vs. "Kop":** Analyser kundeadfærd for at afgøre, om "Filter" og "Kop" substituerer hinanden, da de sjældent købes sammen (0 ordrer).
4.  **Fokus på top-produkter:** Fortsæt med at optimere markedsføring og synlighed for "Kande" (15522.0 kr) og "Kaffe" (10812.0 kr), da de driver størstedelen af omsætningen.
5.  **Undersøg kannibalisering "Filter" vs. "The":** Analyser kundeadfærd for at afgøre, om "Filter" og "The" substituerer hinanden, da de sjældent købes sammen (0 ordrer).

---

## Indkøbsanalyse  
`indkobsanalyse`

**Nøgletal:** rows_used=276, span_days=176

**Gemini-analyse:**

Her er en analyse af jeres salgshistorik for perioden 2026-01-01 til 2026-06-25 (176 dage).

**Kort resumé:**
I perioden blev der registreret 276 salgslinjer. De 5 bedst sælgende produkter udgør 99.2% af det samlede salg på 507 enheder.

**Hvad der skal bestilles hjem, og hvor tit:**
Genbestilling bør primært fokusere på de hurtigst sælgende varer for at opretholde lagerbeholdningen:

*   **Kaffe:** Sælger 0.773 enheder/dag. Kunder genkøber i gennemsnit hver 53.2 dag. Bør genbestilles ca. hver 53. dag.
*   **Filter:** Sælger 0.67 enheder/dag. Kunder genkøber i gennemsnit hver 39.3 dag. Bør genbestilles ca. hver 39. dag.
*   **The:** Sælger 0.489 enheder/dag. Kunder genkøber i gennemsnit hver 40.2 dag. Bør genbestilles ca. hver 40. dag.
*   **Kop:** Sælger 0.483 enheder/dag. Kunder genkøber i gennemsnit hver 51.9 dag. Bør genbestilles ca. hver 52. dag.
*   **Kande:** Sælger 0.443 enheder/dag. Kunder genkøber i gennemsnit hver 69.5 dag. Bør genbestilles ca. hver 70. dag.
*   **Solcreme:** Sælger kun 0.023 enheder/dag. Der er ingen angivet genkøbsinterval. Denne vare bør bestilles sjældent og i små mængder grundet det meget lave salg.

**Varer med risiko for udsolgt:**
De varer med højest salgshastighed har størst risiko for at blive udsolgt hurtigt, hvis lageret ikke vedligeholdes:

1.  **Kaffe** (0.773 enheder/dag)
2.  **Filter** (0.67 enheder/dag)
3.  **The** (0.489 enheder/dag)
4.  **Kop** (0.483 enheder/dag)
5.  **Kande** (0.443 enheder/dag)

**Prioriteret genbestillingsliste:**
Baseret på salgshastighed og genkøbsinterval:

1.  **Kaffe:** Genbestilles ca. hver 53. dag.
2.  **Filter:** Genbestilles ca. hver 39. dag.
3.  **The:** Genbestilles ca. hver 40. dag.
4.  **Kop:** Genbestilles ca. hver 52. dag.
5.  **Kande:** Genbestilles ca. hver 70. dag.

---

## Lageranalyse  
`lageranalyse`

**Nøgletal:** rows_used=276, span_days=176

**Gemini-analyse:**

Her er en analyse af jeres lagerdata:

**Resumé:**
Jeres lager binder i alt 18.042 kr. i kapital. Ingen varer er klassificeret som dødvarer baseret på salgshistorikken. Dog er en betydelig del af kapitalen bundet i langsomtsælgende produkter, som også optager lagerplads.

**Hvor bindes kapital og plads:**
Den største kapitalbinding findes i følgende produkter:
*   **Kande:** 9.990 kr. (111 stk. på lager)
*   **Solcreme:** 3.870 kr. (86 stk. på lager)
*   **The:** 1.958 kr. (89 stk. på lager)
Disse tre produkter udgør ca. 87,7% af den samlede bundne kapital og optager tilsvarende en stor del af lagerpladsen.

**Dødvarer at rydde ud:**
Systemet identificerer ingen varer som "dødvarer" (intet salg længe). De langsomtsælgende varer, især dem med høj kapitalbinding, bør dog overvejes for oprydning for at frigøre kapital og plads.

**Prioriteret oprydningsliste (maks 5):**
1.  **Solcreme:** Ekstremt langsomt salg (0,023 enheder/dag) og høj kapitalbinding (3.870 kr.).
2.  **Kande:** Langsomt salg (0,443 enheder/dag) og den største kapitalbinding (9.990 kr.).
3.  **The:** Langsomt salg (0,489 enheder/dag) og betydelig kapitalbinding (1.958 kr.).
4.  **Kaffe:** Langsomt salg (0,773 enheder/dag) og kapitalbinding (1.600 kr.).
5.  **Kop:** Langsomt salg (0,483 enheder/dag), men lavere kapitalbinding (198 kr.).

---

## Kundeanalyse  
`kundeanalyse`

**Nøgletal:** rows_used=276, distinct_customers=25

**Gemini-analyse:**

Her er en analyse af kundedata for SLS Tech:

**Resumé**
Webshoppen har 25 kunder. En meget stor del af omsætningen (99.3%) kommer fra gentagne kunder, som udgør 96% af den samlede kundebase. Dette indikerer en sund kerne af loyale kunder.

**Hvem tjener butikken penge?**
De kunder, der driver mest omsætning, er:
*   **kunde5@mail.dk:** 3011.0 kr. fordelt på 13 ordrer.
*   **kunde16@mail.dk:** 2245.5 kr. fordelt på 12 ordrer.
*   **kunde4@mail.dk:** 2199.5 kr. fordelt på 9 ordrer.
*   **kunde19@mail.dk:** 2079.0 kr. fordelt på 10 ordrer.
*   **kunde7@mail.dk:** 1951.5 kr. fordelt på 11 ordrer.

Disse kunder er butikkens mest værdifulde og hyppige købere.

**Hvem er ved at forsvinde, og hvad skal man gøre?**
*   **kunde2@mail.dk** er allerede forsvundet, da det er 175 dage siden sidste køb.
*   **Potentielle churnere** (kunder med høj recency):
    *   **kunde20@mail.dk:** 70 dage siden sidste køb.
    *   **kunde14@mail.dk:** 49 dage siden sidste køb.
    *   **kunde8@mail.dk:** 42 dage siden sidste køb.
    *   **kunde21@mail.dk:** 35 dage siden sidste køb.

Disse kunder har ikke handlet i længere tid og er i risiko for at forsvinde helt.

**Prioriteret handlingsliste:**

1.  **Plej topkunder:** Identificer og beløn kunder som kunde5@mail.dk, kunde16@mail.dk, kunde4@mail.dk og kunde19@mail.dk for at fastholde deres loyalitet.
2.  **Re-engager potentielle churnere:** Kontakt proaktivt kunder som kunde20@mail.dk (70 dage), kunde14@mail.dk (49 dage), kunde8@mail.dk (42 dage) og kunde21@mail.dk (35 dage) med et målrettet tilbud.
3.  **Win-back forsøg:** Send et genaktiveringstilbud til kunde2@mail.dk, som ikke har handlet i 175 dage.
4.  **Fasthold gentagne kunder:** Fortsæt med at optimere oplevelsen for de 96% af kunderne, der er gentagne købere og står for 99.3% af omsætningen.
5.  **Løbende RFM-overvågning:** Etabler en proces for regelmæssigt at identificere kunder med stigende recency for at forebygge churn.

---

## Fuld Butiksanalyse  
`butiksanalyse`

**Nøgletal:** rows_used=276, distinct_products=6, distinct_orders=231, total_revenue=39351.0, avg_order_value=170.35

**Motor-output (uddrag):**
```json
{
  "meta": {
    "column_mapping": {
      "order_id": "Ordrenr",
      "product": "Varenavn",
      "quantity": "Antal",
      "line_total": "Beloeb",
      "date": "Ordredato",
      "customer": "Kunde"
    },
    "rows_used": 276,
    "distinct_products": 6,
    "distinct_orders": 231,
    "total_revenue": 39351.0,
    "avg_order_value": 170.35
  },
  "salgsanalyse": {
    "meta": {
      "column_mapping": {
        "order_id": "Ordrenr",
        "product": "Varenavn",
        "quantity": "Antal",
        "line_total": "Beloeb",
        "date": "Ordredato",
        "customer": "Kunde"
      },
      "rows_used": 276,
      "distinct_products": 6,
      "distinct_orders": 231,
      "total_revenue": 39351.0,
      "avg_order_value": 170.35
    },
    "bestsellers": {
      "by_revenue": [
        {
          "product": "Kande",
          "revenue": 15522.0,
          "quantity": 78.0
        },
        {
          "product": "Kaffe",
          "revenue": 10812.0,
          "quantity": 136.0
        },
        {
          "product": "The",
          "revenue": 5074.0,
          "quantity": 86.0
        },
        {
          "product": "Kop",
          "revenue": 4165.0,
          "quantity": 85.0
        },
        {
          "product": "Filter",
          "revenue": 3422.0,
          "quantity": 118.0
        },
        {
          "product": "Solcreme",
          "revenue": 356.0,
          "quantity": 4.0
        }
      ],
      "by_quantity": [
        {
          "p
```

---

## Konkurrentanalyse  
`konkurrentanalyse`

**Nøgletal:** n_competitors=2

**Gemini-analyse:**

Her er en nøgtern analyse af minshop.dk's position i markedet:

**Resumé af hvor minshop.dk står:**
minshop.dk er markant bagud på trafik, produktsortiment, gennemsnitspris og AI-synlighed sammenlignet med konkurrenterne. Den eneste klare styrke er en lavere grænse for fri fragt.

**Hvor minshop.dk står stærkt:**
*   **Fri fragt:** minshop.dk tilbyder fri fragt ved 299 DKK, hvilket er lavere end konkB.dk (399 DKK) og konkA.dk (499 DKK).

**Hvor minshop.dk er bagud:**
*   **Gennemsnitspris:** Med 250 DKK er gennemsnitsprisen 50 DKK højere end konkA.dk (200 DKK).
*   **Produktsortiment:** minshop.dk har kun 100 produkter, hvilket er 200 færre end konkA.dk (300 produkter).
*   **Trafik:** Trafikestimatet på 5000 besøgende er 15000 lavere end konkA.dk (20000 besøgende).
*   **AI-synlighed:** Med en score på 20 er minshop.dk 40 point mindre synlig i AI-svar end konkA.dk (60 point).

**Prioriteret handlingsliste:**
1.  **Styrk SEO/AI-synlighed og markedsføring:** Adresser den store trafikforskel på 15000 besøgende.
2.  **Udvid produktsortimentet:** Luk hullet på 200 produkter i forhold til den bedste konkurrent.
3.  **Overvej prisjustering eller tydeliggørelse af værdi:** Håndter den højere gennemsnitspris på 50 DKK.
4.  **Kør AEO-optimering:** Forbedr AI-synligheden, som er 40 point lavere end den bedste konkurrent.

---

## AI-synlighed (GEO+AEO)  
`ai_synlighed`

**Nøgletal:** queries=4

**Gemini-analyse:**

Her er en analyse af MinShops AI-synlighed:

**Resumé**
MinShop nævnes i 50,0% af de kørte AI-forespørgsler.

**GEO – Synlighed vs. konkurrenter**
MinShop nævnes i 50,0% af forespørgslerne, hvilket giver en Share of Voice på 33,3%. MinShop nævnes 2 gange. Konkurrenten KonkA nævnes 3 gange, og KonkB nævnes 1 gang. KonkA nævnes altså oftere end MinShop.

**AEO – Hvad skal sider rettes**
Den gennemsnitlige AI-læsbarhedsscore for MinShops sider er 60,0%.
*   **Forsiden** har en score på 100,0% og er velfungerende med spørgsmålsoverskrifter, FAQ-struktur, schema markup, korte svar og lister.
*   **"Om"-siden** har en score på 20,0% og mangler spørgsmålsoverskrifter, FAQ-struktur, schema markup og lister.

**Prioriteret handlingsliste**
1.  **Analysér KonkA's indhold:** Undersøg KonkA's indhold for at forstå, hvorfor de nævnes oftere, og luk hullet.
2.  **Optimer "om"-siden med spørgsmålsoverskrifter:** Tilføj overskrifter formuleret som spørgsmål på "om"-siden.
3.  **Implementer FAQ-struktur på "om"-siden:** Tilføj en FAQ-sektion med konkrete spørgsmål og svar på "om"-siden.
4.  **Tilføj schema markup på "om"-siden:** Implementer FAQPage/Product schema (JSON-LD) på "om"-siden.
5.  **Brug punktlister på "om"-siden:** Indfør punktlister på "om"-siden for at forbedre AI-læsbarheden.

---

## Prisovervågning  
`prisovervagning`

**Nøgletal:** products=2, has_previous=True, threshold_pct=1.0

**Motor-output (uddrag):**
```json
{
  "meta": {
    "products": 2,
    "has_previous": true,
    "threshold_pct": 1.0
  },
  "positions": [
    {
      "product": "Kaffe",
      "own": 79,
      "cheapest_competitor": {
        "name": "KonkA",
        "price": 75.0
      },
      "dearest_competitor": {
        "name": "KonkB",
        "price": 85.0
      },
      "position": "midt",
      "gap_to_cheapest": 4.0
    },
    {
      "product": "The",
      "own": 59,
      "cheapest_competitor": {
        "name": "KonkB",
        "price": 62.0
      },
      "dearest_competitor": {
        "name": "KonkA",
        "price": 65.0
      },
      "position": "billigst",
      "gap_to_cheapest": -3.0
    }
  ],
  "alerts": [
    {
      "product": "Kaffe",
      "competitor": "KonkA",
      "old_price": 90.0,
      "new_price": 75.0,
      "change_pct": -16.7,
      "direction": "ned"
    },
    {
      "product": "The",
      "competitor": "KonkB",
      "old_price": 60.0,
      "new_price": 62.0,
      "change_pct": 3.3,
      "direction": "op"
    }
  ],
  "recommendations": [
    "'KonkA' sænkede prisen på Kaffe med 16.7% — reager hvis du vil matche.",
    "'KonkB' hævede prisen på The — du kan evt. tjene mere uden at miste position."
  ]
}
```

---

## Nævner-AI-alarm  
`naevner_ai_alarm`

**Motor-output (uddrag):**
```json
{
  "brand": "MinShop",
  "measurement": {
    "queries_run": 4,
    "brand_mention_rate_pct": 75.0,
    "share_of_voice_pct": 60.0,
    "brand_mentions": 3,
    "competitor_mentions": {
      "KonkA": 1,
      "KonkB": 1
    },
    "per_query": [
      {
        "query": "q1",
        "brand_mentioned": true,
        "competitors_mentioned": []
      },
      {
        "query": "q2",
        "brand_mentioned": true,
        "competitors_mentioned": [
          "KonkA"
        ]
      },
      {
        "query": "q3",
        "brand_mentioned": false,
        "competitors_mentioned": [
          "KonkB"
        ]
      },
      {
        "query": "q4",
        "brand_mentioned": true,
        "competitors_mentioned": []
      }
    ],
    "score": 75.0
  },
  "comparison": {
    "current": {
      "brand_mention_rate_pct": 75.0,
      "share_of_voice_pct": 60.0
    },
    "deltas": {},
    "alerts": [
      {
        "type": "baseline",
        "besked": "Første måling registreret — næste måned kan vi vise ændringer."
      }
    ],
    "alarm": false
  }
}
```

---

## Produkttekst-optimering  
`produkttekst`

**Nøgletal:** products=4, avg_aeo_score=45.0

**Motor-output (uddrag):**
```json
{
  "meta": {
    "columns": {
      "name": "Produktnavn",
      "desc": "Beskrivelse",
      "price": null
    },
    "products": 4,
    "avg_aeo_score": 45.0
  },
  "weakest": [
    {
      "product": "KRUS I KERAMIK",
      "words": 4,
      "checks": {
        "laengde_ok": false,
        "har_specifikationer": false,
        "har_spoergsmaal_svar": false,
        "ikke_kun_store_bogstaver": false,
        "har_flere_saetninger": false
      },
      "aeo_score": 0.0
    },
    {
      "product": "Kaffefilter str. 4",
      "words": 1,
      "checks": {
        "laengde_ok": false,
        "har_specifikationer": false,
        "har_spoergsmaal_svar": false,
        "ikke_kun_store_bogstaver": true,
        "har_flere_saetninger": false
      },
      "aeo_score": 20.0
    }
  ],
  "all_scores": [
    {
      "product": "Håndbrygget kaffe 500g",
      "words": 22,
      "checks": {
        "laengde_ok": true,
        "har_specifikationer": true,
        "har_spoergsmaal_svar": true,
        "ikke_kun_store_bogstaver": true,
        "har_flere_saetninger": true
      },
      "aeo_score": 100.0
    },
    {
      "product": "Kaffefilter str. 4",
      "words": 1,
      "checks": {
        "laengde_ok": false,
        "har_specifikationer": false,
        "har_spoergsmaal_svar": false,
        "ikke_kun_store_bogstaver": true,
        "har_flere_saetninger": false
      },
      "aeo_score": 20.0
    },
    {
      "product": "KRUS I KERAMIK",
      "words": 4,
      "check
```

---

## Review-analyse  
`review_analyse`

**Nøgletal:** reviews=7, avg_rating=3.0, low_rating_share_pct=57.1, low_threshold=3.0

**Motor-output (uddrag):**
```json
{
  "meta": {
    "columns": {
      "rating": "Rating",
      "text": "Tekst",
      "product": null
    },
    "reviews": 7,
    "avg_rating": 3.0,
    "low_rating_share_pct": 57.1,
    "low_threshold": 3.0
  },
  "rating_distribution": {
    "1": 2,
    "2": 1,
    "3": 1,
    "4": 1,
    "5": 2
  },
  "themes": [
    [
      "levering",
      3
    ],
    [
      "kvalitet",
      3
    ],
    [
      "kundeservice",
      1
    ],
    [
      "pris",
      1
    ],
    [
      "størrelse/pasform",
      1
    ]
  ],
  "themes_in_low_reviews": [
    [
      "levering",
      2
    ],
    [
      "kvalitet",
      2
    ],
    [
      "kundeservice",
      1
    ]
  ]
}
```

---

## Landingsside-teardown  
`landingsside`

**Nøgletal:** words=41

**Motor-output (uddrag):**
```json
{
  "meta": {
    "page": "landingsside",
    "words": 41
  },
  "checks": {
    "har_overskrift": true,
    "har_cta": true,
    "har_vaerditilbud": true,
    "har_trust_signaler": true,
    "har_kontakt": true,
    "har_konkrete_tal": true,
    "ikke_for_lang_uden_struktur": true
  },
  "score": 100.0,
  "anbefalinger": []
}
```

---

## Annonce-spild  
`annonce_spild`

**Nøgletal:** campaigns=5, total_spend=3160.0, total_revenue=13750.0, overall_roas=4.35, min_spend_flag=100.0

**Motor-output (uddrag):**
```json
{
  "meta": {
    "columns": {
      "campaign": "Kampagne",
      "spend": "Forbrug",
      "clicks": "Klik",
      "conversions": "Konverteringer",
      "revenue": "Omsætning"
    },
    "campaigns": 5,
    "total_spend": 3160.0,
    "total_revenue": 13750.0,
    "overall_roas": 4.35,
    "min_spend_flag": 100.0
  },
  "per_campaign": [
    {
      "campaign": "Brand-search",
      "spend": 1200.0,
      "clicks": 600.0,
      "conversions": 70.0,
      "revenue": 9800.0,
      "roas": 8.17,
      "cpa": 17.14,
      "conversion_rate_pct": 11.67
    },
    {
      "campaign": "Shopping-alle",
      "spend": 900.0,
      "clicks": 500.0,
      "conversions": 0.0,
      "revenue": 0.0,
      "roas": 0.0,
      "cpa": null,
      "conversion_rate_pct": 0.0
    },
    {
      "campaign": "Display-bred",
      "spend": 700.0,
      "clicks": 800.0,
      "conversions": 4.0,
      "revenue": 350.0,
      "roas": 0.5,
      "cpa": 175.0,
      "conversion_rate_pct": 0.5
    },
    {
      "campaign": "Retargeting",
      "spend": 300.0,
      "clicks": 200.0,
      "conversions": 25.0,
      "revenue": 3600.0,
      "roas": 12.0,
      "cpa": 12.0,
      "conversion_rate_pct": 12.5
    },
    {
      "campaign": "Test-ny",
      "spend": 60.0,
      "clicks": 30.0,
      "conversions": 0.0,
      "revenue": 0.0,
      "roas": 0.0,
      "cpa": null,
      "conversion_rate_pct": 0.0
    }
  ],
  "waste": [
    {
      "campaign": "Shopping-alle",
      "spend": 900.0,
      "click
```

---

## Søgeords-gap  
`soegeords_gap`

**Nøgletal:** distinct_terms=4, has_results_column=True

**Motor-output (uddrag):**
```json
{
  "meta": {
    "columns": {
      "term": "Søgeterm",
      "count": "Antal",
      "results": "Resultater"
    },
    "distinct_terms": 4,
    "has_results_column": true
  },
  "note": "Termer med mange søgninger og ingen resultater = manglende produkter/kategorier.",
  "gaps": [
    {
      "term": "espressomaskine",
      "searches": 300.0,
      "avg_results": 0.0
    },
    {
      "term": "stempelkande",
      "searches": 160.0,
      "avg_results": 0.0
    }
  ],
  "top_searches": [
    {
      "term": "espressomaskine",
      "searches": 300.0,
      "avg_results": 0.0
    },
    {
      "term": "kaffefilter",
      "searches": 180.0,
      "avg_results": 12.0
    },
    {
      "term": "stempelkande",
      "searches": 160.0,
      "avg_results": 0.0
    },
    {
      "term": "økologisk the",
      "searches": 90.0,
      "avg_results": 4.0
    }
  ]
}
```

---
