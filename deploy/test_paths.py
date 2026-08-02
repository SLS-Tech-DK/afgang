"""Test af URL-sti → type mapping (paths.py). Kører uden motor-imports."""
from paths import path_to_type, resolve_type, CANONICAL

ok = True

def check(cond, msg):
    global ok
    if not cond:
        ok = False
        print("FEJL:", msg)

# 1. Hver kanonisk type kan rammes direkte som sti (med og uden underscore som '-')
for t in CANONICAL:
    check(path_to_type("/" + t) == t, f"kanonisk sti /{t}")
    hyphen = t.replace("_", "-")
    check(path_to_type("/" + hyphen) == t, f"bindestreg-sti /{hyphen}")

# 2. Aliaser og kælenavne
check(path_to_type("/butiksrontgen") == "butiksanalyse", "butiksrontgen-alias")
check(path_to_type("/ai-synlighed") == "ai_synlighed", "ai-synlighed-sti")
check(path_to_type("/prisovervaagning") == "prisovervagning", "prisovervaagning-alias")
check(path_to_type("/bliver-jeg-naevnt") == "naevner_ai_alarm", "bliver-jeg-naevnt-alias")
check(path_to_type("/soegeords-gap") == "soegeords_gap", "soegeords-gap-sti")

# 3. Store bogstaver og ekstra segmenter
check(path_to_type("/Salgsanalyse") == "salgsanalyse", "versal-sti")
check(path_to_type("/salgsanalyse/kør") == "salgsanalyse", "ekstra segment ignoreres")

# 4. Ikke-produkt-stier giver None
for p in ("/", "", "/health", "/findes-ikke"):
    check(path_to_type(p) is None, f"ikke-produkt-sti {p!r} burde give None")

# 5. resolve_type: body-type vinder over sti
check(resolve_type({"type": "lageranalyse"}, "/salgsanalyse") == "lageranalyse", "body-type vinder")
check(resolve_type({}, "/kundeanalyse") == "kundeanalyse", "sti bruges når body mangler type")
check(resolve_type({}, "/") is None, "ingen type + ingen sti = None")

print("RESULTAT:", "✓ OK" if ok else "✗ FEJL")
import sys; sys.exit(0 if ok else 1)
