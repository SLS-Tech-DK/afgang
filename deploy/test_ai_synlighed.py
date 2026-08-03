"""Tests for ai_synlighed: geo_visibility-tal, aeo_audit, analyze_live (mock querier)."""
import sys, ai_synlighed as a
ok=True
def chk(c,m):
    global ok
    if not c: ok=False; print("FEJL:",m)

# geo_visibility korrekthed
qr=[{"query":"q1","response":"MinShop er bedst"},
    {"query":"q2","response":"MinShop og KonkA"},
    {"query":"q3","response":"KonkB"},
    {"query":"q4","response":"ingen nævnt"}]
v=a.geo_visibility(qr,"MinShop",["KonkA","KonkB"])
chk(v["brand_mentions"]==2, "brand nævnt 2 gange")
chk(v["brand_mention_rate_pct"]==50.0, "mention-rate 50%")
chk(v["competitor_mentions"]=={"KonkA":1,"KonkB":1}, "konkurrent-optælling")
# SoV = 2/(2+1+1)=50
chk(v["share_of_voice_pct"]==50.0, "share of voice 50%")

# aeo_audit: stærk side scorer højt, svag lavt
strong=a.aeo_audit("## Hvad koster fragt?\nFragt 39 kr.\n- Gratis over 299\n<script type=\"application/ld+json\">{\"@type\":\"FAQPage\"}</script>")
weak=a.aeo_audit("Vi sælger ting. Ring til os.")
chk(strong["score"]>weak["score"], "stærk side scorer højere end svag")
chk(len(weak["anbefalinger"])>0, "svag side får anbefalinger")

# analyze_live med mock querier (ingen live)
def q(prompt): return "MinShop anbefales" if "bedste" in prompt.lower() else "KonkA"
r=a.analyze_live("MinShop","kaffe",["KonkA"],pages=[{"name":"forside","text":"## Spørgsmål?\nKort svar.\n- punkt"}],querier=q)
chk(r["meta"]["live"] is True and r["meta"]["field"]=="kaffe", "live meta sat")
chk(r["meta"]["queries"]==5, "5 branche-prompts kørt")
chk("aeo" in r and "geo" in r, "geo+aeo i output")

print("RESULTAT:", "OK" if ok else "FEJL")
sys.exit(0 if ok else 1)
