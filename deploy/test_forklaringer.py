"""Tests for Gemini-forklaringslag (mock caller): review + butiks + at prompt er grounded."""
import sys, review_forklaring, butiks_forklaring
ok=True
def chk(c,m):
    global ok
    if not c: ok=False; print("FEJL:",m)

cap = lambda s,p: "PLAN:"+p[:20]

rv = review_forklaring.forklar({"meta":{"reviews":7,"avg_rating":3.0,"low_threshold":3.0,"low_rating_share_pct":57.1},
    "rating_distribution":{1:2,5:2},"themes":[["levering",3]],"themes_in_low_reviews":[["levering",2]]}, caller=cap)
chk("levering" in rv["prompt_brugt"], "review-prompt grounded på temaer")
chk(rv["forklaring_tekst"].startswith("PLAN:"), "review kalder caller")
# error passerer igennem
chk("error" in review_forklaring.forklar({"error":"x"}, caller=cap), "review error propagerer")

bk = butiks_forklaring.forklar({"meta":{"total_revenue":39351.0,"distinct_orders":231,"distinct_products":6,"avg_order_value":170.35},
    "salgsanalyse":{"bestsellers":{"by_revenue":[{"product":"Kande","revenue":15522.0}]},"co_purchase":[]},
    "kryds":{"kannibalisering":[],"margin_paa_tvaers":{}},"lageranalyse":{"deadstock":[]},
    "indkobsanalyse":{"reorder_list":[]},"kundeanalyse":{"segments":{}},"handlingsplan":["x"]}, caller=cap)
chk("39351" in bk["prompt_brugt"], "butiks-prompt grounded på nøgletal")
chk(bk["forklaring_tekst"].startswith("PLAN:"), "butiks kalder caller")

print("RESULTAT:", "OK" if ok else "FEJL")
sys.exit(0 if ok else 1)
