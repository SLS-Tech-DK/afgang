"""Tests for gemini_pro — JSON-udtræk + call_json (mock caller, ingen live)."""
import sys, gemini_pro as gp
ok=True
def chk(c,m):
    global ok
    if not c: ok=False; print("FEJL:",m)

chk(gp._extract_json('{"a":1}') == {"a":1}, "ren json")
chk(gp._extract_json('```json\n{"a":1,"b":[2,3]}\n```') == {"a":1,"b":[2,3]}, "json i fence")
chk(gp._extract_json('Her er svaret: {"x":true} tak') == {"x":True}, "json i tekst")
chk(gp._extract_json("intet json her") is None, "ingen json -> None")
chk(gp._extract_json("") is None, "tom -> None")

# call_json med mock caller
res = gp.call_json("sys","prompt", caller=lambda s,p: '{"resume":"ok","plan":["a","b"]}')
chk(res.get("resume")=="ok" and res.get("plan")==["a","b"], "call_json parser mock")
# uparsbart svar -> _parse_error, ingen crash
bad = gp.call_json("s","p", caller=lambda s,p: "ikke json")
chk(bad.get("_parse_error") is True, "uparsbart -> _parse_error uden crash")

print("RESULTAT:", "OK" if ok else "FEJL")
sys.exit(0 if ok else 1)
