#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
afgang Hjemmeside-analyse — analyse (lag 1, automatisk + objektiv).

Ren og netværksfri: tager en SiteData-dict (fra fetch_site.py) ind og returnerer
en payload-dict som GENERATOR-hjemmeside-analyse.py forstår. Kan testes lokalt uden
netværk (se test_analyze.py).

Lag 2 (stavefejl/sprog via sprogmodel) og lag 3 (Google-profil-bekræftelse) er IKKE her
— de flettes ind i payloaden bagefter. Se GOLDEN-STANDARD.
"""
from __future__ import annotations
import json
import re
from bs4 import BeautifulSoup

# faste scoringsvægte — samme hver gang, så to sider kan sammenlignes
WEIGHT = {"crit": 12, "hoej": 7, "med": 4, "let": 2}
SEV_TAG = {"crit": ("crit", "Kritisk"), "hoej": ("hoej", "Høj"), "med": ("med", "Mellem"), "let": ("let", "Let")}
SEV_STATUS = {"crit": ("fix", "Kritisk"), "hoej": ("fix", "Ret"), "med": ("del", "Løft"), "let": ("del", "Løft")}
PLACEHOLDER_PAT = re.compile(r"kommer snart|lorem ipsum|\[\s*\.{2,}\s*\]|\[branche\]|\[indsæt", re.I)
EN_FORM_PAT = re.compile(r"\b(Send Email|Your Name|Your Email)\b", re.I)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html or "", "html.parser")


def _schema_types(soup: BeautifulSoup) -> set[str]:
    """Collect all JSON-LD @type values, handling strings, lists and @graph."""
    types: set[str] = set()

    def collect(node):
        if isinstance(node, dict):
            t = node.get("@type")
            if isinstance(t, str):
                types.add(t)
            elif isinstance(t, list):
                types.update(x for x in t if isinstance(x, str))
            for v in node.values():
                collect(v)
        elif isinstance(node, list):
            for v in node:
                collect(v)

    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = tag.string or tag.get_text() or ""
        try:
            collect(json.loads(raw))
        except Exception:
            # tolerate malformed JSON-LD; just skip it
            continue
    return types


def _text_words(soup: BeautifulSoup) -> int:
    for t in soup(["script", "style", "noscript"]):
        t.extract()
    return len(soup.get_text(" ", strip=True).split())


def analyze(site: dict, meta_overrides: dict | None = None) -> dict:
    pages = site.get("pages", [])
    findings: list[dict] = []

    def add(dim, sev, title, body, **extra):
        st, stl = SEV_STATUS[sev]
        findings.append({"dim": dim, "sev": sev, "title": title, "body": body,
                         "status": st, "status_label": stl, **extra})

    # ---------- site-level ----------
    if not site.get("https"):
        add("seo", "crit", "Siden kører ikke på HTTPS",
            "Uden HTTPS markerer browsere siden som usikker, og Google rangerer den lavere.")
    robots = site.get("robots_txt")
    sitemap = site.get("sitemap_xml")
    llms = site.get("llms_txt")
    if not robots:
        add("seo", "med", "Ingen robots.txt", "robots.txt findes ikke (404). Styrer hvordan søgemaskiner crawler siden.")
    elif "sitemap" not in robots.lower():
        add("seo", "let", "robots.txt henviser ikke til sitemap",
            "Tilføj en Sitemap-linje i robots.txt, så crawlere finder sitemap hurtigere.")
    if not sitemap:
        add("seo", "med", "Intet sitemap", "sitemap.xml findes ikke. Uden det er det sværere for Google at finde alle sider.")
    if not llms:
        add("ai", "med", "Ingen llms.txt",
            "Filen AI-modeller læser for at forstå siden findes ikke (404) → modellerne har intet at gå ud fra.")

    # schema across all pages
    all_types: set[str] = set()
    for p in pages:
        all_types |= _schema_types(_soup(p["html"]))
    local_types = {"LocalBusiness", "HealthAndBeautyBusiness", "MedicalBusiness", "MedicalClinic", "Dentist", "Physician"}
    if not (all_types & local_types):
        if "Organization" in all_types:
            add("lokal", "hoej", "Kun generisk Organization-schema",
                "Siden fortæller ikke Google at det er en lokal virksomhed. Tilføj LocalBusiness-schema med adresse, telefon og åbningstider.")
        else:
            add("lokal", "hoej", "Ingen virksomheds-schema",
                "Der er ingen struktureret markup der fortæller Google hvad virksomheden er og hvor den ligger.")
    if "FAQPage" not in all_types:
        add("ai", "med", "Ingen FAQ-schema",
            "Uden FAQPage-schema bliver spørgsmål/svar ikke citeret af AI og Google. Største lette AEO-gevinst.")

    # ---------- per-page ----------
    titles: dict[str, list[str]] = {}
    no_meta, no_alt_pages, thin_pages, placeholder_pages, long_titles = [], [], 0, [], 0
    homepage_no_h1 = False
    en_form = False
    base = site.get("base_url", "")

    for i, p in enumerate(pages):
        soup = _soup(p["html"])
        path = (p["url"].replace(base, "") or "/") or "/"
        is_home = (i == 0) or p["url"].rstrip("/") == base.rstrip("/")

        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""
        if not title:
            add("seo", "hoej", f"Manglende title på {path}", "Siden har ingen <title> — det er den blå overskrift i Google.")
        else:
            titles.setdefault(title.lower(), []).append(path)
            if len(title) > 60:
                long_titles += 1

        if not soup.find("meta", attrs={"name": "description"}):
            no_meta.append(path)

        h1s = soup.find_all("h1")
        if len(h1s) == 0:
            if is_home:
                homepage_no_h1 = True
            # non-home missing h1 is minor; counted below via long list only if home
        # placeholder text
        body_txt = soup.get_text(" ", strip=True)
        if PLACEHOLDER_PAT.search(body_txt):
            placeholder_pages.append(path)
        # english form on danish page
        html_tag = soup.find("html")
        lang = (html_tag.get("lang", "") if html_tag else "").lower()
        if (lang.startswith("da") or not lang) and EN_FORM_PAT.search(p["html"]):
            en_form = True
        # images without alt
        imgs = soup.find_all("img")
        if any(not (im.get("alt") or "").strip() for im in imgs):
            no_alt_pages.append(path)
        # thin content
        if _text_words(soup) < 150:
            thin_pages += 1

    dupes = {t: paths for t, paths in titles.items() if len(paths) > 1}

    if homepage_no_h1:
        add("seo", "hoej", "Forsiden mangler en H1",
            "Forsidens overskrift er ikke en H1. Google bruger H1 til at forstå hvad siden handler om.")
    if long_titles:
        add("seo", "let", f"{long_titles} for lange titler", "Titler over ~60 tegn bliver klippet af i Google.")
    if dupes:
        add("seo", "med", "Ens titler på flere sider",
            "Flere sider deler samme title, så Google ikke kan skelne dem. Gør hver title unik.")
    if no_meta:
        add("seo", "med", "Manglende meta-beskrivelser",
            f"{len(no_meta)} sider mangler meta-beskrivelse, så Google klipper selv en tilfældig sætning ud.")
    if placeholder_pages:
        add("indhold", "hoej", 'Placeholder-tekst live ("kommer snart" o.l.)',
            f'Fundet på {len(placeholder_pages)} side(r). Tomme løfter på en live side koster tillid — skriv eller fjern.')
    if en_form:
        add("konvertering", "med", "Kontaktformular på engelsk",
            "Formularfelter på engelsk (Name/Email/Send Email) på en dansk side. Skift til dansk.")
    if no_alt_pages:
        add("seo", "let", "Billeder uden alt-tekst",
            f"Billeder uden alt-tekst på {len(no_alt_pages)} side(r). Alt-tekst hjælper Google-billedsøgning og skærmlæsere.")
    if thin_pages:
        add("indhold", "let", f"{thin_pages} tynde sider",
            "Sider med meget lidt tekst rangerer dårligt og giver lidt værdi. Overvej at uddybe eller slå sammen.")
    blog_pat = re.compile(r"/(blog|artikl|nyhed|viden|guide|indsigt)", re.I)
    has_blog = any(blog_pat.search(p["url"]) for p in pages)
    if not has_blog:
        add("indhold", "med", "Ingen blog / artikler fundet",
            "Der er intet indhold der kan rangere på informationssøgninger. Artikler trækker nye besøgende og gør siden citérbar.")

    # ---------- score ----------
    score = max(0, 100 - sum(WEIGHT[f["sev"]] for f in findings))

    # ---------- assemble payload ----------
    def cards(dim):
        return [{"title": f["title"], "status": f["status"], "status_label": f["status_label"],
                 "body": f["body"], **({"pre": f["pre"]} if f.get("pre") else {}),
                 **({"list": f["list"]} if f.get("list") else {}),
                 **({"ex": f["ex"]} if f.get("ex") else {})} for f in findings if f["dim"] == dim]

    order = {"crit": 0, "hoej": 1, "med": 2, "let": 3}
    ranked = sorted(findings, key=lambda f: order[f["sev"]])
    recommendations = []
    for i, f in enumerate(ranked[:8], 1):
        tag, tag_label = SEV_TAG[f["sev"]]
        recommendations.append({"rank": i, "title": f["title"], "body": f["body"], "tag": tag, "tag_label": tag_label})

    n_crit = sum(1 for f in findings if f["sev"] == "crit")
    n_all = len(findings)
    mo = meta_overrides or {}
    meta = {
        "name": mo.get("name") or site.get("name", ""),
        "name_demo": mo.get("name_demo") or "En hjemmeside",
        "url": site.get("base_url", "").replace("https://", "").replace("http://", ""),
        "type": mo.get("type") or site.get("type", ""),
        "tech": mo.get("tech") or site.get("tech", "—"),
        "pages": len(pages),
        "source": mo.get("source") or "automatisk analyse af sidens kildekode",
        "score": score,
        "score_max": 100,
        "score_label": "Samlet synligheds- & tillids-score (lag 1, automatisk). Sprog-laget lægges oveni.",
        "counts": [
            {"n": str(n_all), "l": "fund i alt", "c": "gul"},
            {"n": str(n_crit), "l": "kritiske", "c": "rod"},
            {"n": str(len(placeholder_pages)), "l": '"kommer snart"', "c": "gul"},
            {"n": str(len(pages)), "l": "sider gennemgået", "c": "gron"},
        ],
    }

    overblik = [
        {"title": "Fundamentet", "status": "ok" if site.get("https") and sitemap else "fix",
         "status_label": "OK" if site.get("https") and sitemap else "Ret",
         "body": "HTTPS, sitemap og mobil-opsætning tjekkes her. Er de på plads, fejler selve maskinen ikke noget."},
        {"title": "Indhold", "status": "fix" if any(f["dim"] == "indhold" for f in findings) else "ok",
         "status_label": "Ret" if any(f["dim"] == "indhold" for f in findings) else "OK",
         "body": "Placeholder-tekst, tynde sider og manglende artikler trækker ned her."},
        {"title": "Synlighed", "status": "fix" if any(f["dim"] in ("lokal", "ai") for f in findings) else "ok",
         "status_label": "Ret" if any(f["dim"] in ("lokal", "ai") for f in findings) else "OK",
         "body": "Lokal- og AI-synlighed: schema, Google-profil, llms.txt og FAQ."},
        {"title": "Konvertering", "status": "del" if any(f["dim"] == "konvertering" for f in findings) else "ok",
         "status_label": "Løft" if any(f["dim"] == "konvertering" for f in findings) else "OK",
         "body": "Booking-vej, formularsprog og pakker/klippekort."},
    ]

    # lokal: altid en manuel "bekræft Google-profil"-note (kan ikke afgøres fra kildekode alene)
    lokal = cards("lokal") + [{
        "title": "Google Business-profil — bekræft manuelt", "status": "del", "status_label": "Tjek",
        "body": "Kan ikke afgøres 100% fra kildekoden. Slå virksomheden op på Google Maps: findes en profil i det rigtige navn, er den udfyldt, og ligger den rette virksomhed på adressen?"}]

    ai = cards("ai") + [{
        "title": "Konsekvens", "status": "", "status_label": "",
        "body": "Med llms.txt + FAQ-schema + LocalBusiness bliver siden citérbar når folk spørger en AI om en leverandør i området."}]

    payload = {
        "meta": meta,
        "recommendations": recommendations,
        "overblik": overblik,
        "seo": cards("seo") or [{"title": "Ingen SEO-fejl fundet", "status": "ok", "status_label": "OK", "body": "De automatiske SEO-tjek gik rent."}],
        "sprog_intro": "Sprog-laget (stavefejl og klodset dansk) køres af sprogmodellen oven på den rå tekst og flettes ind her. Nedenfor står de rå fund når laget er kørt.",
        "sprog_rows": mo.get("sprog_rows", []),
        "lokal": lokal,
        "ai": ai,
        "indhold": cards("indhold") or [{"title": "Indhold ser fint ud", "status": "ok", "status_label": "OK", "body": "Ingen placeholder- eller tynde-side-fund."}],
        "konvertering": cards("konvertering") or [{"title": "Konvertering ser fin ud", "status": "ok", "status_label": "OK", "body": "Ingen oplagte konverterings-problemer fundet automatisk."}],
        "_findings": findings,  # rå fund, til debug/test — ignoreres af generatoren
    }
    return payload


if __name__ == "__main__":
    import sys
    site = json.load(open(sys.argv[1], encoding="utf-8"))
    out = analyze(site)
    print(json.dumps({k: v for k, v in out.items() if k != "_findings"}, ensure_ascii=False, indent=2))
