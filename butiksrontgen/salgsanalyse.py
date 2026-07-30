"""
SLS Tech · Afgang — Salgsanalyse-motor (delelement af Butiksrøntgen)
--------------------------------------------------------------------
Deterministisk beregningskerne. Tager en vilkårlig ordre-/salgs-CSV,
genkender kolonnerne selv, og producerer:
  - bestsellere / bundfald (omsætning + antal)
  - købes-sammen-par (market basket)
  - bundle-forslag
  - kannibalisering (substitut-signal)

Gemini-laget (forklaring/anbefaling i klar tekst) ligger UDENPÅ denne fil.
Her regnes kun tal — de skal være korrekte og efterprøvelige.

Ingen tredjeparts-ML. Kun stdlib + valgfrit pandas hvis til stede (bruges ikke her).
"""

from __future__ import annotations
import csv, io, re, json, math
from collections import defaultdict, Counter
from datetime import datetime
from itertools import combinations


# ---------------------------------------------------------------------------
# 1. FLEKSIBELT KOLONNE-GENKENDELSESLAG
# ---------------------------------------------------------------------------
# Mapper vilkårlige kolonnenavne til semantiske roller. Dansk + engelsk +
# Shopify/WooCommerce-varianter. Heuristik på header-navn først; hvis en rolle
# ikke findes, forsøges værdi-baseret gæt (fx dato-parsing, numerisk).

# Rækkefølge betyder noget: mere specifikke roller tjekkes FØR "product"
# (som ellers grådigt ville opsluge fx "Lineitem quantity"/"Lineitem price").
ROLE_PATTERNS = {
    "order_id":  [r"order.*id", r"ordre.*(id|nr|nummer)", r"^order$", r"^ordre$", r"ordrenr",
                  r"transaction", r"kvittering", r"receipt", r"faktura", r"invoice", r"basket", r"kurv"],
    "quantity":  [r"quantity", r"antal", r"^qty$", r"stk", r"units?", r"mængde",
                  r"lineitem.*quantity"],
    "unit_price":[r"unit.*price", r"stykpris", r"pris(pr|per)(stk|enhed)", r"lineitem.*price",
                  r"enhedspris"],
    "line_total":[r"line.*total", r"linje.*total", r"total.*(amount|price)?", r"amount",
                  r"beløb", r"beloeb", r"sum", r"subtotal", r"omsætning", r"omsaetning", r"revenue"],
    "price":     [r"^price$", r"^pris$", r"salgspris"],   # generisk pris (fallback til unit_price)
    "date":      [r"date", r"dato", r"created", r"oprettet", r"tidspunkt", r"købsdato",
                  r"order.*date", r"ordredato"],
    "customer":  [r"customer", r"kunde", r"email", r"e-mail", r"buyer", r"køber", r"client", r"klient"],
    "product":   [r"product(name|title)?", r"produkt(navn|titel)?", r"varenavn", r"vare(navn)?",
                  r"item(name|title)", r"lineitemname", r"^title$", r"^navn$", r"^name$",
                  r"^sku$", r"varenr", r"artikel"],
}

DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%d.%m.%Y", "%Y/%m/%d",
]


def _norm(h: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (h or "").strip().lower())


def _match_role(header: str) -> str | None:
    h = _norm(header)
    for role, pats in ROLE_PATTERNS.items():
        for p in pats:
            if re.search(_norm_pat(p), h):
                return role
    return None


def _norm_pat(p: str) -> str:
    # patterns are written loosely; strip separators to match _norm'd headers
    return re.sub(r"[^a-z0-9().*+?^$|\\\[\]]", "", p.lower())


def _to_float(v):
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    # håndter dansk/EU-format: 1.234,56  og  1,234.56  og  "kr", valuta, mellemrum
    s = re.sub(r"[^\d,.\-]", "", s)
    if s.count(",") and s.count("."):
        # antag sidste separator er decimal
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif s.count(","):
        # komma som decimal hvis to cifre efter, ellers tusind-separator
        if re.search(r",\d{1,2}$", s):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def _to_date(v):
    if not v:
        return None
    s = str(v).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s[:len(fmt)+5], fmt).date()
        except (ValueError, TypeError):
            continue
    # sidste forsøg: find YYYY-MM-DD hvor som helst
    m = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", s)
    if m:
        try:
            return datetime(int(m[1]), int(m[2]), int(m[3])).date()
        except ValueError:
            return None
    return None


def detect_columns(headers: list[str], sample_rows: list[dict]) -> dict:
    """Returnér mapping {role: header}. Header-heuristik + værdi-gæt som backup."""
    mapping: dict[str, str] = {}
    used = set()
    for h in headers:
        role = _match_role(h)
        if role and role not in mapping:
            mapping[role] = h
            used.add(h)

    # Værdi-baseret backup for de vigtigste roller hvis header-gæt fejlede
    def col_values(h):
        return [r.get(h) for r in sample_rows if r.get(h) not in (None, "")]

    remaining = [h for h in headers if h not in used]

    if "date" not in mapping:
        for h in remaining:
            vals = col_values(h)
            if vals and sum(_to_date(v) is not None for v in vals) >= max(1, len(vals) * 0.6):
                mapping["date"] = h; used.add(h); break

    remaining = [h for h in headers if h not in used]
    if "line_total" not in mapping and "unit_price" not in mapping and "price" not in mapping:
        # vælg mest "penge-agtige" numeriske kolonne
        best, best_score = None, 0
        for h in remaining:
            vals = col_values(h)
            nums = [_to_float(v) for v in vals]
            nums = [n for n in nums if n is not None]
            if not nums:
                continue
            score = len(nums) * (1 + (sum(n != round(n) for n in nums) / len(nums)))  # decimaler = pris-agtigt
            if score > best_score:
                best, best_score = h, score
        if best:
            mapping["line_total"] = best; used.add(best)

    return mapping


# ---------------------------------------------------------------------------
# 2. INDLÆSNING → normaliserede linjer
# ---------------------------------------------------------------------------

def load_lines(csv_text: str) -> tuple[list[dict], dict]:
    """Returnér (linjer, kolonne-mapping). Hver linje: order_id, product,
    quantity, revenue, date, customer — udledt så robust som muligt."""
    # sniff delimiter
    sample = csv_text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delim = dialect.delimiter
    except csv.Error:
        delim = ","
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=delim)
    headers = reader.fieldnames or []
    rows = list(reader)
    mapping = detect_columns(headers, rows[:200])

    def g(row, role):
        h = mapping.get(role)
        return row.get(h) if h else None

    lines = []
    synth_order = 0
    for row in rows:
        product = g(row, "product")
        if not product or str(product).strip() == "":
            continue
        qty = _to_float(g(row, "quantity"))
        if qty is None:
            qty = 1.0
        unit = _to_float(g(row, "unit_price")) or _to_float(g(row, "price"))
        total = _to_float(g(row, "line_total"))
        if total is None and unit is not None:
            total = unit * qty
        if total is None:
            total = 0.0
        if unit is None and qty:
            unit = total / qty if qty else total
        oid = g(row, "order_id")
        if not oid or str(oid).strip() == "":
            synth_order += 1
            oid = f"_row{synth_order}"      # ingen ordre-id → hver linje = egen "ordre"
        lines.append({
            "order_id": str(oid).strip(),
            "product": str(product).strip(),
            "quantity": qty,
            "revenue": total,
            "unit_price": unit,
            "date": _to_date(g(row, "date")),
            "customer": (str(g(row, "customer")).strip() if g(row, "customer") else None),
        })
    return lines, mapping


# ---------------------------------------------------------------------------
# 3. ANALYSER (deterministiske)
# ---------------------------------------------------------------------------

def _round(x, n=2):
    return round(x + 0.0, n)


def bestsellers(lines, top=10):
    rev = defaultdict(float); qty = defaultdict(float)
    for l in lines:
        rev[l["product"]] += l["revenue"]
        qty[l["product"]] += l["quantity"]
    by_rev = sorted(rev.items(), key=lambda x: x[1], reverse=True)
    by_qty = sorted(qty.items(), key=lambda x: x[1], reverse=True)
    return {
        "by_revenue": [{"product": p, "revenue": _round(v), "quantity": _round(qty[p])} for p, v in by_rev[:top]],
        "by_quantity": [{"product": p, "quantity": _round(v), "revenue": _round(rev[p])} for p, v in by_qty[:top]],
        "worst_by_revenue": [{"product": p, "revenue": _round(v), "quantity": _round(qty[p])} for p, v in by_rev[-top:][::-1]],
    }


def _baskets(lines):
    """Gruppér produkter pr. ordre (kun ordrer med >=2 forskellige varer tæller til par)."""
    b = defaultdict(set)
    for l in lines:
        b[l["order_id"]].add(l["product"])
    return [prods for prods in b.values() if len(prods) >= 1]


def co_purchase(lines, top=10, min_support=2):
    baskets = [b for b in _baskets(lines) if len(b) >= 2]
    pair = Counter()
    prod_orders = Counter()
    for b in baskets:
        for p in b:
            prod_orders[p] += 1
        for a, c in combinations(sorted(b), 2):
            pair[(a, c)] += 1
    n_multi = len(baskets)
    results = []
    for (a, c), cnt in pair.items():
        if cnt < min_support:
            continue
        # lift = P(a,c) / (P(a)*P(c)) over multi-item baskets
        pa = prod_orders[a] / n_multi
        pc = prod_orders[c] / n_multi
        pac = cnt / n_multi
        lift = pac / (pa * pc) if pa and pc else 0
        results.append({"pair": [a, c], "orders_together": cnt,
                        "lift": _round(lift, 2)})
    results.sort(key=lambda x: (x["orders_together"], x["lift"]), reverse=True)
    return results[:top]


def bundle_suggestions(co_pairs, top=5):
    """Bundle = par der købes sammen oftere end tilfældigt (lift>1) og har volumen."""
    cand = [c for c in co_pairs if c["lift"] >= 1.15 and c["orders_together"] >= 2]
    cand.sort(key=lambda x: (x["lift"], x["orders_together"]), reverse=True)
    out = []
    for c in cand[:top]:
        out.append({
            "products": c["pair"],
            "orders_together": c["orders_together"],
            "lift": c["lift"],
            "rationale": f"Købes sammen {c['orders_together']} gange — {c['lift']}x oftere end tilfældigt."
        })
    return out


def cannibalization(lines, co_pairs, top=5):
    """Substitut-signal: to varer der hver især sælger godt, men NÆSTEN aldrig
    købes i samme ordre (lav lift). Indikerer at de konkurrerer om samme kunde.
    Dette er et SIGNAL, ikke bevis — flag som 'undersøg'."""
    rev = defaultdict(float); orders = defaultdict(set)
    for l in lines:
        rev[l["product"]] += l["revenue"]
        orders[l["product"]].add(l["order_id"])
    # kun produkter med rimelig volumen
    strong = {p for p, v in rev.items() if len(orders[p]) >= 3}
    pair_lift = {tuple(sorted(c["pair"])): c["lift"] for c in co_pairs}
    total_orders = len({l["order_id"] for l in lines})
    out = []
    for a, c in combinations(sorted(strong), 2):
        together = len(orders[a] & orders[c])
        # forventet antal fælles ordrer hvis uafhængige
        exp = len(orders[a]) * len(orders[c]) / total_orders if total_orders else 0
        if exp >= 1 and together <= exp * 0.4:   # markant færre end forventet
            out.append({
                "products": [a, c],
                "orders_together": together,
                "expected_if_independent": _round(exp, 1),
                "revenue_each": [_round(rev[a]), _round(rev[c])],
                "signal": "Sælger hver for sig, men købes sjældent sammen — mulig substitution. Undersøg om de kannibaliserer."
            })
    out.sort(key=lambda x: x["expected_if_independent"] - x["orders_together"], reverse=True)
    return out[:top]


def analyze(csv_text: str) -> dict:
    lines, mapping = load_lines(csv_text)
    if not lines:
        return {"error": "Ingen brugbare salgslinjer fundet i CSV'en.", "column_mapping": mapping}
    co = co_purchase(lines)
    total_rev = sum(l["revenue"] for l in lines)
    n_orders = len({l["order_id"] for l in lines})
    return {
        "meta": {
            "column_mapping": mapping,
            "rows_used": len(lines),
            "distinct_products": len({l["product"] for l in lines}),
            "distinct_orders": n_orders,
            "total_revenue": _round(total_rev),
            "avg_order_value": _round(total_rev / n_orders) if n_orders else 0,
        },
        "bestsellers": bestsellers(lines),
        "co_purchase": co,
        "bundles": bundle_suggestions(co),
        "cannibalization": cannibalization(lines, co),
    }


if __name__ == "__main__":
    import sys
    txt = open(sys.argv[1], encoding="utf-8").read()
    print(json.dumps(analyze(txt), ensure_ascii=False, indent=2, default=str))
