"""Tests for de fem NEXT-produkter. Kontrollerede data, kendte forventninger."""
import io, csv

ok = True

# ---------- 1. Produkttekst-optimering ----------
import produkttekst
rows = [["Produktnavn", "Beskrivelse"],
        ["God vare", "Dette er en fin beskrivelse med 2 sætninger. Den vejer 500 g og måler 10 cm. Passer perfekt?"],
        ["Dårlig vare", "billig"],
        ["MEGET RÅBENDE", "STORT PRODUKT KØB NU"]]
buf = io.StringIO(); csv.writer(buf).writerows(rows)
r = produkttekst.analyze(buf.getvalue())
weak_names = [w["product"] for w in r["weakest"]]
if "God vare" == r["weakest"][0]["product"]:
    ok = False; print("FEJL(produkttekst): god vare burde ikke være svagest")
if "Dårlig vare" not in weak_names:
    ok = False; print("FEJL(produkttekst): dårlig vare burde være blandt svageste")
# pris: 3 produkter -> max(60,250)=250
if r["pris"]["total_ekskl_moms"] != 250:
    ok = False; print("FEJL(produkttekst): pris burde være 250 (minimum)")
# batch-rabat over 100 produkter
if produkttekst.price_quote(200)["total_ekskl_moms"] != 3600:  # 200*20=4000, -10%=3600
    ok = False; print("FEJL(produkttekst): batch-rabat forkert")
print("Produkttekst OK — avg score:", r["meta"]["avg_aeo_score"], "| pris 3 prod:", r["pris"]["total_ekskl_moms"])

# ---------- 2. Review-analyse ----------
import review_analyse
rev = [["Rating", "Tekst"],
       ["5", "Super hurtig levering, god kvalitet"],
       ["1", "Forsinket levering og dårlig kvalitet"],
       ["2", "Dårlig kundeservice, fik ikke svar"],
       ["4", "Fin pasform"],
       ["1", "Pakken kom for sent, elendig levering"]]
buf = io.StringIO(); csv.writer(buf, delimiter=";").writerows(rev)
rr = review_analyse.analyze(buf.getvalue(), low_threshold=3.0)
print("Review OK — avg:", rr["meta"]["avg_rating"], "| lav-andel%:", rr["meta"]["low_rating_share_pct"],
      "| temaer i lave:", rr["themes_in_low_reviews"])
# avg af 5,1,2,4,1 = 2.6
if rr["meta"]["avg_rating"] != 2.6:
    ok = False; print("FEJL(review): avg rating forkert")
low_themes = dict(rr["themes_in_low_reviews"])
# 'levering' optræder i 2 lave reviews (rating 1 og 1)
if low_themes.get("levering", 0) < 2:
    ok = False; print("FEJL(review): levering burde være top-tema i lave reviews")

# ---------- 3. Landingsside-teardown ----------
import landingsside
god = "# Køb vores sko — fri fragt\n\nBedst i test. Over 5000 tilfredse kunder.\n\n- Levering på 1 dag\n- 30 dages garanti\n\nKontakt os på tlf 12345678. [Køb nu]"
daarlig = "velkommen til vores hjemmeside vi har eksisteret laenge og sælger forskellige ting til folk som gerne vil handle hos os uden nogen struktur eller opfordring overhovedet her"
lg = landingsside.analyze(god); ld = landingsside.analyze(daarlig)
print("Landingsside OK — god:", lg["score"], "| dårlig:", ld["score"])
if lg["score"] <= ld["score"]:
    ok = False; print("FEJL(landingsside): god side burde score højere")
if not lg["checks"]["har_cta"] or not lg["checks"]["har_trust_signaler"]:
    ok = False; print("FEJL(landingsside): god side burde have CTA + trust")

# ---------- 4. Annonce-spildsanalyse ----------
import annonce_spild
ads = [["Kampagne", "Forbrug", "Klik", "Konverteringer", "Omsætning"],
       ["Vinder", "1000", "500", "50", "5000"],
       ["Spild-ingen-konv", "800", "400", "0", "0"],
       ["Spild-tab", "600", "300", "5", "300"],
       ["Lille", "50", "20", "0", "0"]]
buf = io.StringIO(); csv.writer(buf, delimiter=";").writerows(ads)
ar = annonce_spild.analyze(buf.getvalue(), min_spend_flag=100.0)
waste_names = [w["campaign"] for w in ar["waste"]]
print("Annonce OK — spild-kampagner:", waste_names, "| spildt kr:", ar["estimated_wasted_spend"])
# Vinder ROAS=5 (ok), Spild-ingen-konv (0 konv), Spild-tab (ROAS 0.5<1), Lille (under 100 flag)
if "Vinder" in waste_names:
    ok = False; print("FEJL(annonce): vinder burde ikke være spild")
if "Spild-ingen-konv" not in waste_names or "Spild-tab" not in waste_names:
    ok = False; print("FEJL(annonce): spild-kampagner mangler")
if "Lille" in waste_names:
    ok = False; print("FEJL(annonce): under-tærskel burde ikke flagges")
# spildt = 800 + 600 = 1400
if ar["estimated_wasted_spend"] != 1400:
    ok = False; print("FEJL(annonce): spildt beløb forkert:", ar["estimated_wasted_spend"])

# ---------- 5. Søgeords-gap ----------
import soegeords_gap
sog = [["Søgeterm", "Antal", "Resultater"],
       ["blå sko", "120", "0"],
       ["rød taske", "80", "5"],
       ["grøn hat", "200", "0"],
       ["blå sko", "30", "0"]]
buf = io.StringIO(); csv.writer(buf, delimiter=";").writerows(sog)
sr = soegeords_gap.analyze(buf.getvalue())
gap_terms = [g["term"] for g in sr["gaps"]]
print("Søgeords OK — gaps:", [(g["term"], g["searches"]) for g in sr["gaps"]])
# gaps med 0 resultater: 'grøn hat'(200), 'blå sko'(120+30=150). 'rød taske' har resultater -> ikke gap
if gap_terms[0] != "grøn hat":
    ok = False; print("FEJL(søgeord): grøn hat burde være top-gap")
if "rød taske" in gap_terms:
    ok = False; print("FEJL(søgeord): term med resultater burde ikke være gap")
# blå sko aggregeret = 150
blaa = [g for g in sr["gaps"] if g["term"] == "blå sko"]
if not blaa or blaa[0]["searches"] != 150:
    ok = False; print("FEJL(søgeord): blå sko burde aggregeres til 150")

print("\n==== SAMLET:", "ALLE FEM OK ✓" if ok else "FEJL ✗", "====")
