"""Genererer realistiske eksempel-input pr. produkt OG kører dem gennem de
rigtige motorer for at verificere at de giver fornuftigt output.
Fungerer som end-to-end-acceptance-test + leverer kunde-skabeloner."""
import csv, io, json, os, random
from datetime import date, timedelta

random.seed(7)
OUT = "eksempler"
os.makedirs(OUT, exist_ok=True)
start = date(2026, 1, 1)

def w(name, rows, delim=";"):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter=delim).writerows(rows)
def wj(name, obj):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
def wt(name, text):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(text)

# ---------- 1) Ordre-CSV (bruges af salg/indkøb/lager/kunde/butik) ----------
PRODUKTER = [("Kaffe",79.50,40),("Filter",29.00,10),("Kop",49.00,18),
             ("Kande",199.00,90),("The",59.00,22),("Sukker",19.00,6),("Solcreme",89.00,45)]
kunder = [f"kunde{i}@mail.dk" for i in range(1,26)]
ordre = [["Ordrenr","Varenavn","Antal","Beloeb","Ordredato","Kunde"]]
oid = 1000
for wk in range(26):                       # et halvt år
    d = (start+timedelta(days=wk*7)).strftime("%d-%m-%Y")
    for _ in range(random.randint(6,12)):
        oid += 1
        cust = random.choice(kunder)
        # kaffe+filter købes ofte sammen
        prod, unit, cost = random.choice(PRODUKTER[:5])
        qty = random.randint(1,3)
        ordre.append([oid, prod, qty, f"{unit*qty:.2f}".replace(".",","), d, cust])
        if prod=="Kaffe" and random.random()<0.7:
            ordre.append([oid,"Filter",1,"29,00",d,cust])
    # solcreme kun forår/sommer (uge 8-20), aldrig efter → dødvare
    if 8 <= wk <= 20 and random.random()<0.5:
        oid += 1
        ordre.append([oid,"Solcreme",1,"89,00",d,random.choice(kunder)])
w("ordre-eksempel.csv", ordre)

# lager-CSV (kostpris) til lager/butik
lager = [["Produkt","Lagerantal","Kostpris"]]
for p,unit,cost in PRODUKTER:
    lager.append([p, random.randint(5,120), f"{cost:.2f}".replace(".",",")])
w("lager-eksempel.csv", lager)

# ---------- 2) Produkttekst: katalog ----------
kat = [["Produktnavn","Beskrivelse"],
       ["Håndbrygget kaffe 500g","Vores mørkristede kaffe vejer 500 g og har noter af chokolade. Hvordan brygger man den bedst? Brug 60 g pr. liter vand."],
       ["Kaffefilter str. 4","Filter."],
       ["KRUS I KERAMIK","STORT KRUS KØB NU"],
       ["Termokande 1L","Holder kaffen varm i 8 timer. Rummer 1 liter. Fri for BPA."]]
w("produktkatalog-eksempel.csv", kat)

# ---------- 3) Reviews ----------
rev = [["Rating","Tekst"],
       ["5","Super hurtig levering og god kvalitet"],
       ["1","Pakken kom alt for sent, elendig levering"],
       ["2","Dårlig kundeservice, fik aldrig svar"],
       ["4","Fin pasform og god pris"],
       ["1","Gik i stykker efter en uge, dårlig kvalitet"],
       ["3","Ok men leveringen var langsom"],
       ["5","Perfekt, kommer igen"]]
w("reviews-eksempel.csv", rev)

# ---------- 4) Annonce ----------
ads = [["Kampagne","Forbrug","Klik","Konverteringer","Omsætning"],
       ["Brand-search","1200","600","70","9800"],
       ["Shopping-alle","900","500","0","0"],
       ["Display-bred","700","800","4","350"],
       ["Retargeting","300","200","25","3600"],
       ["Test-ny","60","30","0","0"]]
w("annoncer-eksempel.csv", ads)

# ---------- 5) Søgelog ----------
sog = [["Søgeterm","Antal","Resultater"],
       ["espressomaskine","240","0"],
       ["kaffefilter","180","12"],
       ["stempelkande","160","0"],
       ["økologisk the","90","4"],
       ["espressomaskine","60","0"]]
w("soegelog-eksempel.csv", sog)

# ---------- 6) Landingsside ----------
wt("landingsside-eksempel.txt",
   "# Køb friskristet kaffe — fri fragt over 299 kr\n\n"
   "Bedst i test 2026. Over 8.000 tilfredse kunder.\n\n"
   "- Levering på 1-2 hverdage\n- 30 dages retur\n- Økologisk\n\n"
   "Kontakt os på tlf 12 34 56 78 eller hej@minshop.dk. [Køb nu]")

# ---------- 7) Strukturerede (JSON) input ----------
wj("konkurrentanalyse-eksempel.json", {
  "own":{"name":"minshop.dk","avg_price":250,"product_count":100,"traffic_estimate":5000,"ai_visibility":20,"shipping_free_over":299},
  "competitors":[
    {"name":"konkA.dk","avg_price":200,"product_count":300,"traffic_estimate":20000,"ai_visibility":60,"shipping_free_over":499},
    {"name":"konkB.dk","avg_price":220,"product_count":250,"traffic_estimate":15000,"ai_visibility":45,"shipping_free_over":399}]})
wj("ai-synlighed-eksempel.json", {
  "brand":"MinShop","competitors":["KonkA","KonkB"],
  "query_results":[
    {"query":"bedste webshop til kaffe?","response":"KonkA og KonkB anbefales."},
    {"query":"hvor køber man stempelkande?","response":"MinShop og KonkA."},
    {"query":"billigste kaffe online?","response":"KonkA er billigst."},
    {"query":"god kvalitetskaffe?","response":"MinShop har god kvalitet."}],
  "pages":[{"name":"forside","text":"## Hvad koster fragt?\n\nFragt koster 39 kr.\n\n- Gratis over 299\n<script type=\"application/ld+json\">{\"@type\":\"FAQPage\"}</script>"},
           {"name":"om","text":"Vi har solgt kaffe i mange aar."}]})
wj("prisovervagning-eksempel.json", {
  "current":[{"product":"Kaffe","own":79,"competitors":{"KonkA":75,"KonkB":85}},
             {"product":"The","own":59,"competitors":{"KonkA":65,"KonkB":62}}],
  "previous":[{"product":"Kaffe","own":79,"competitors":{"KonkA":90,"KonkB":85}},
              {"product":"The","own":59,"competitors":{"KonkA":65,"KonkB":60}}]})
wj("naevner-ai-alarm-eksempel.json", {
  "brand":"MinShop","competitors":["KonkA","KonkB"],
  "query_results":[{"query":"q1","response":"MinShop er bedst."},{"query":"q2","response":"MinShop og KonkA."},
                   {"query":"q3","response":"KonkB."},{"query":"q4","response":"MinShop."}],
  "previous_measurement":None})

print("Eksempler genereret i", OUT, "→", len(os.listdir(OUT)), "filer")

# ---------- VERIFIKATION: kør hver motor på sit eksempel ----------
import salgsanalyse, indkobsanalyse, lageranalyse, kundeanalyse, butiksanalyse
import konkurrentanalyse, ai_synlighed, prisovervagning, naevner_ai_alarm
import produkttekst, review_analyse, landingsside, annonce_spild, soegeords_gap

def rd(n): return open(os.path.join(OUT,n),encoding="utf-8").read()
def jr(n): return json.load(open(os.path.join(OUT,n),encoding="utf-8"))
ordre_csv = rd("ordre-eksempel.csv"); lager_csv = rd("lager-eksempel.csv")

checks = []
def chk(name, cond, extra=""):
    checks.append((name, cond)); print(("  ✓ " if cond else "  ✗ ")+name+("  "+extra if extra else ""))

print("\n=== End-to-end mod rigtige motorer ===")
r = salgsanalyse.analyze(ordre_csv);            chk("salgsanalyse", not r.get("error") and r["bestsellers"]["by_revenue"], "omsætning "+str(r.get("meta",{}).get("total_revenue")))
r = indkobsanalyse.analyze(ordre_csv);          chk("indkobsanalyse", not r.get("error") and r["velocity"])
r = lageranalyse.analyze(ordre_csv, lager_csv); chk("lageranalyse", not r.get("error") and "total_capital_tied" in r["capital_tied"], "kapital "+str(r["capital_tied"].get("total_capital_tied")))
r = kundeanalyse.analyze(ordre_csv);            chk("kundeanalyse", not r.get("error") and r["clv"])
r = butiksanalyse.analyze(ordre_csv, lager_csv);chk("butiksanalyse", not r.get("error") and r["handlingsplan"])
r = konkurrentanalyse.analyze(**{k:jr("konkurrentanalyse-eksempel.json")[k] for k in ("own","competitors")}); chk("konkurrentanalyse", not r.get("error") and r["where_to_win"])
d = jr("ai-synlighed-eksempel.json"); r = ai_synlighed.analyze(d["query_results"],d["brand"],d["competitors"],d["pages"]); chk("ai_synlighed", "geo" in r and "aeo" in r)
d = jr("prisovervagning-eksempel.json"); r = prisovervagning.analyze(d["current"],d["previous"]); chk("prisovervagning", r["alerts"])
d = jr("naevner-ai-alarm-eksempel.json"); r = naevner_ai_alarm.run_check(d["query_results"],d["brand"],d["competitors"],d["previous_measurement"]); chk("naevner_ai_alarm", "comparison" in r)
r = produkttekst.analyze(rd("produktkatalog-eksempel.csv")); chk("produkttekst", not r.get("error") and r["all_scores"], "gns "+str(r.get("meta",{}).get("avg_aeo_score")))
r = review_analyse.analyze(rd("reviews-eksempel.csv"));      chk("review_analyse", not r.get("error") and r["themes"])
r = landingsside.analyze(rd("landingsside-eksempel.txt"));   chk("landingsside", "score" in r, "score "+str(r.get("score")))
r = annonce_spild.analyze(rd("annoncer-eksempel.csv"));      chk("annonce_spild", not r.get("error") and r["waste"], "spild "+str(r.get("estimated_wasted_spend")))
r = soegeords_gap.analyze(rd("soegelog-eksempel.csv"));      chk("soegeords_gap", not r.get("error") and r["gaps"])

allok = all(c for _,c in checks)
print("\n==== ACCEPTANCE:", "ALLE 14 MOTORER GAV OUTPUT PÅ EKSEMPELDATA ✓" if allok else "FEJL ✗", "====")
