"""Tests for konkurrentanalyse.analyze_web (mock fetcher+caller, ingen live)."""
import sys, konkurrentanalyse as k
ok=True
def chk(c,m):
    global ok
    if not c: ok=False; print("FEJL:",m)

def fetch_ok(url,*a,**kw): return {"url":("https://"+url), "ok":True, "text":f"Side {url}: kaffe 99 kr, 50 produkter"}
def caller_json(system,prompt):
    chk("EGEN AKTØR" in prompt, "prompt har egen aktør")
    chk("kaffe 99 kr" in prompt, "prompt er grounded på hentet tekst")
    return '{"aktorer":[{"navn":"minshop.dk","pris_niveau":"middel","sortiment_bredde":"smal","styrker":["fri fragt"],"svagheder":["smalt"]}],"gaps":[{"omraade":"sortiment","din_position":"smal","bedste_konkurrent":"bred","status":"bagud"}],"hvor_du_kan_vinde":[{"omraade":"sortiment","handling":"udvid"}],"resume":"kort","handlingsplan":["udvid sortiment"]}'

r = k.analyze_web("minshop.dk", ["a.dk","b.dk"], fetcher=fetch_ok, caller=caller_json)
chk(r["meta"]["own"]=="minshop.dk", "meta own")
chk(len(r["meta"]["pages_fetched"])==3, "3 sider hentet (egen+2)")
chk(r["analyse"]["resume"]=="kort", "analyse parset")
chk(r["analyse"]["handlingsplan"]==["udvid sortiment"], "plan med")

# manglende domæne
chk("error" in k.analyze_web("", [], fetcher=fetch_ok, caller=caller_json), "tomt domæne -> fejl")

# alle fetches fejler -> pæn fejl, intet model-kald
def fetch_fail(url,*a,**kw): return {"url":url,"ok":False,"error":"nede"}
r3 = k.analyze_web("x.dk", ["y.dk"], fetcher=fetch_fail, caller=lambda s,p:(_ for _ in ()).throw(Exception("må ikke kaldes")))
chk("error" in r3, "alle fetch fejler -> pæn fejl uden model-kald")

# numerisk fallback stadig intakt
rn = k.analyze({"name":"minshop.dk","avg_price":250,"product_count":100},[{"name":"a.dk","avg_price":200,"product_count":300}])
chk("side_by_side" in rn and "where_to_win" in rn, "numerisk analyze intakt")

print("RESULTAT:", "OK" if ok else "FEJL")
sys.exit(0 if ok else 1)
