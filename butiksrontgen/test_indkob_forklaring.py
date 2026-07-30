"""Mock-test af Gemini-forklaringslaget for Indkøbsanalyse."""
import io, csv
from datetime import date, timedelta
from indkobsanalyse import analyze
from indkob_forklaring import forklar, SYSTEM_INSTRUKTION

start = date(2026, 1, 1)
rows = [["Ordrenr", "Varenavn", "Antal", "Ordredato", "Kunde"]]
for wk in range(4):
    d = (start + timedelta(days=wk*7)).strftime("%d-%m-%Y")
    rows.append([wk+1, "Mælk", 2, d, "A"])
buf = io.StringIO(); csv.writer(buf, delimiter=";").writerows(rows)
a = analyze(buf.getvalue())

cap = {}
def mock(system, prompt):
    cap["system"] = system; cap["prompt"] = prompt
    return "MOCK indkøbssvar"

res = forklar(a, caller=mock)
ok = True
if cap.get("system") != SYSTEM_INSTRUKTION:
    ok = False; print("FEJL: systeminstruktion")
if "Mælk" not in cap["prompt"]:
    ok = False; print("FEJL: produkt mangler i prompt")
if "SALGSHASTIGHED" not in cap["prompt"]:
    ok = False; print("FEJL: hastigheds-sektion mangler")
for k in ("forklaring_tekst", "prompt_brugt", "model", "note"):
    if k not in res: ok = False; print("FEJL: mangler", k)
if forklar({"error": "x"}, caller=mock).get("error") != "x":
    ok = False; print("FEJL: fejlhåndtering")
print("RESULTAT:", "✓ OK (mock)" if ok else "✗ FEJL")
print("Live Vertex-kald IKKE testet — kræver nøgle ved deployment.")
