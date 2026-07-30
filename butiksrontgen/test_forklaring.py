"""Test af Gemini-forklaringslaget med en MOCK-caller.
Verificerer: prompt samles korrekt med de rigtige tal, systeminstruktion
sendes med, output-kontrakten holder, og at intet tal opfindes af koden selv."""
import io, csv
from salgsanalyse import analyze
from gemini_forklaring import forklar, _byg_prompt, SYSTEM_INSTRUKTION

# lille kendt datasæt
rows = [
    ["Order ID", "Lineitem name", "Lineitem quantity", "Lineitem price"],
    ["1", "Kaffe", "2", "79.50"],
    ["1", "Filter", "1", "29.00"],
    ["2", "Kaffe", "1", "79.50"],
    ["2", "Filter", "1", "29.00"],
    ["3", "The", "1", "59.00"],
]
buf = io.StringIO(); csv.writer(buf).writerows(rows)
analysis = analyze(buf.getvalue())

captured = {}
def mock_caller(system, prompt):
    captured["system"] = system
    captured["prompt"] = prompt
    return "MOCK-SVAR: resumé + handlinger."

res = forklar(analysis, caller=mock_caller)

ok = True
# 1. systeminstruktion sendt med
if captured.get("system") != SYSTEM_INSTRUKTION:
    ok = False; print("FEJL: systeminstruktion ikke sendt korrekt")
# 2. prompten indeholder de rigtige tal (total omsætning)
tot = str(analysis["meta"]["total_revenue"])
if tot not in captured["prompt"]:
    ok = False; print(f"FEJL: total omsætning {tot} mangler i prompt")
# 3. bestseller-navn med i prompt
if "Kaffe" not in captured["prompt"]:
    ok = False; print("FEJL: bestseller mangler i prompt")
# 4. output-kontrakt
for k in ("forklaring_tekst", "prompt_brugt", "model", "note"):
    if k not in res:
        ok = False; print(f"FEJL: output mangler felt {k}")
if res.get("forklaring_tekst") != "MOCK-SVAR: resumé + handlinger.":
    ok = False; print("FEJL: model-tekst ikke ført igennem")
# 5. fejl-håndtering
err = forklar({"error": "tom"}, caller=mock_caller)
if err.get("error") != "tom":
    ok = False; print("FEJL: fejl-input håndteres ikke")

print("Prompt-uddrag:\n", captured["prompt"][:300], "...")
print("\nRESULTAT:", "✓ OK (mock)" if ok else "✗ FEJL")
print("BEMÆRK: live Vertex/Gemini-kald er IKKE testet — kræver nøgle ved deployment.")
