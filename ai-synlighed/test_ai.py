"""Test af AI-synlighed: GEO-score, AEO-audit, query-interface + Gemini-mock."""
from ai_synlighed import analyze, geo_visibility, aeo_audit, run_queries
from ai_forklaring import forklar, SYSTEM_INSTRUKTION

brand = "MinShop"
comps = ["KonkA", "KonkB"]
# 5 forespørgsler: brand nævnt i 2, KonkA i 4, KonkB i 3
qr = [
    {"query": "bedste webshop til X?", "response": "Vi anbefaler KonkA og KonkB."},
    {"query": "hvor køber man Y?", "response": "MinShop og KonkA er gode."},
    {"query": "billigste Z?", "response": "KonkA er billigst, KonkB nummer to."},
    {"query": "kvalitet?", "response": "MinShop har god kvalitet, ligesom KonkA."},
    {"query": "levering?", "response": "KonkB leverer hurtigt."},
]
vis = geo_visibility(qr, brand, comps)
print("Brand mention-rate:", vis["brand_mention_rate_pct"], "%")
print("Share-of-voice:", vis["share_of_voice_pct"], "%")
print("Konkurrent-omtaler:", vis["competitor_mentions"])

ok = True
# brand nævnt i 2 af 5 = 40%
if vis["brand_mention_rate_pct"] != 40.0:
    ok = False; print("FEJL: mention-rate burde være 40")
# omtaler: brand 2, KonkA 4, KonkB 3 → sov = 2/9 = 22.2%
if vis["competitor_mentions"]["KonkA"] != 4 or vis["competitor_mentions"]["KonkB"] != 3:
    ok = False; print("FEJL: konkurrent-optælling forkert")
if abs(vis["share_of_voice_pct"] - 22.2) > 0.2:
    ok = False; print("FEJL: share-of-voice forkert:", vis["share_of_voice_pct"])

# AEO-audit: en god side vs. en dårlig
god = "## Hvad koster fragt?\n\nFragt koster 39 kr.\n\n- Gratis over 299 kr\n\n<script type=\"application/ld+json\">{\"@type\":\"FAQPage\"}</script>"
daarlig = "Velkommen til vores side. Vi sælger mange ting og har gjort det i mange aar med en lang uddybende tekst uden struktur eller spoergsmaal."
ag = aeo_audit(god); ad = aeo_audit(daarlig)
print("AEO god score:", ag["score"], "| dårlig score:", ad["score"])
if ag["score"] <= ad["score"]:
    ok = False; print("FEJL: god side burde score højere end dårlig")
if not ag["checks"]["har_schema_markup"] or not ag["checks"]["har_faq_struktur"]:
    ok = False; print("FEJL: god side burde bestå schema+faq")

# fuld analyze med sider
full = analyze(qr, brand, comps, pages=[{"name":"forside","text":god},{"name":"om","text":daarlig}])
if "aeo" not in full or "pages" not in full["aeo"]:
    ok = False; print("FEJL: aeo mangler i fuld analyse")

# query-interface med mock
res = run_queries(["q1","q2"], querier=lambda p: f"svar til {p}")
if len(res) != 2 or res[0]["response"] != "svar til q1":
    ok = False; print("FEJL: run_queries mock")

# Gemini-lag mock
cap = {}
fr = forklar(full, caller=lambda s,p:(cap.update({"s":s,"p":p}),"MOCK")[1])
if cap["s"] != SYSTEM_INSTRUKTION or "GEO" not in cap["p"] or "forklaring_tekst" not in fr:
    ok = False; print("FEJL: ai_forklaring")

print("\nRESULTAT:", "✓ OK" if ok else "✗ FEJL")
print("Live model-forespørgsler + live Vertex IKKE testet — wires ved deployment.")
