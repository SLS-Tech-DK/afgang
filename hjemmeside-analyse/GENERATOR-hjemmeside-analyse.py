#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
afgang Hjemmeside-analyse — generator.
Bygger en interaktiv single-file HTML-rapport (client eller demo) ud fra en payload (motor_data.json).
Samme mønster som GENERATOR-butiksanalyse.py: build('client') / build('demo').

Brug:
    python3 GENERATOR-hjemmeside-analyse.py illona_payload.json
-> skriver hjemmeside-analyse-client.html og hjemmeside-analyse-demo.html

Payloaden kommer fra analyze.py (lag 1 automatik + lag 2 sprog via LLM). Se GOLDEN-STANDARD.
Denne fil rører ingenting eksternt — ren rendering. Ingen netværk, ingen deploy.
"""
import json, html, sys

CSS = """
:root{color-scheme:dark;--ink:#0f1218;--ink-2:#151922;--panel:#191d27;--raised:#1f2431;--line:#262c38;--line-2:#323a49;--text:#edece7;--muted:#939aa8;--muted-2:#828b97;--gron:#57c98a;--gul:#e0aa4e;--rod:#e0745a;--blaa:#6ea8fe;--gron-dim:rgba(87,201,138,.12);--gul-dim:rgba(224,170,78,.12);--rod-dim:rgba(224,116,90,.12);--blaa-dim:rgba(110,168,254,.12);--shadow:0 24px 60px -24px rgba(0,0,0,.7)}
body[data-theme="lys"]{color-scheme:light;--ink:#f6f4ee;--ink-2:#fffdf8;--panel:#fff;--raised:#f3f0e8;--line:#e7e3d8;--line-2:#d9d4c6;--text:#1c1f26;--muted:#5e6874;--muted-2:#647080;--gron:#2f9e6b;--gul:#b9822a;--rod:#c8542c;--blaa:#2f6fd8;--gron-dim:rgba(47,158,107,.12);--gul-dim:rgba(185,130,42,.13);--rod-dim:rgba(200,84,44,.11);--blaa-dim:rgba(47,111,216,.10);--shadow:0 24px 50px -26px rgba(60,50,30,.28)}
*{box-sizing:border-box;margin:0;padding:0}html{-webkit-text-size-adjust:100%}
body{background:var(--ink);color:var(--text);font-family:'Inter',sans-serif;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1040px;margin:0 auto;padding:0 22px}a{color:var(--gron)}
.top{padding:44px 0 20px;background:radial-gradient(120% 90% at 84% -20%,var(--gron-dim),transparent 55%);border-bottom:1px solid var(--line)}
.brand{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:15px}.brand .dot{color:var(--gron)}
.eyebrow{font-family:'JetBrains Mono',monospace;font-size:11.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--gron);margin:18px 0 12px}
h1{font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:clamp(28px,4.6vw,44px);line-height:1.02;letter-spacing:-.03em}h1 em{color:var(--gron);font-style:normal}
.sub{color:var(--muted);font-size:15.5px;margin-top:14px;max-width:64ch}
.meta{font-family:'JetBrains Mono',monospace;font-size:11.5px;color:var(--muted-2);margin-top:14px;line-height:1.7}
.scoreband{display:flex;gap:26px;flex-wrap:wrap;align-items:center;margin-top:22px;background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:18px 22px}
.score{display:flex;align-items:baseline;gap:8px}.score .big{font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:40px;color:var(--gul);line-height:1}.score .max{font-family:'JetBrains Mono',monospace;font-size:14px;color:var(--muted-2)}.score .lbl{font-size:12.5px;color:var(--muted);max-width:22ch}
.scoreband .div{width:1px;align-self:stretch;background:var(--line)}
.mini{display:flex;gap:20px;flex-wrap:wrap}.mini .m .n{font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:20px}.mini .m .l{font-size:11px;color:var(--muted-2)}
.tabs{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--ink) 86%,transparent);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);margin-top:8px}
.tabs .in{max-width:1040px;margin:0 auto;padding:0 22px;display:flex;gap:4px;overflow-x:auto}
.tab{flex:0 0 auto;background:none;border:none;color:var(--muted);font-size:13.5px;font-weight:600;padding:15px 14px;border-bottom:2px solid transparent;white-space:nowrap;cursor:pointer;transition:color .15s,border-color .15s}
.tab:hover{color:var(--text)}.tab.on{color:var(--text);border-bottom-color:var(--gron)}
main{padding:30px 0 60px}.pane{display:none}.pane.on{display:block;animation:fade .25s ease}
@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.pane h2{font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:clamp(20px,3vw,27px);letter-spacing:-.02em;margin-bottom:6px}
.pane .lead{color:var(--muted);font-size:15px;max-width:64ch;margin-bottom:22px}
.rec{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin-bottom:12px;display:grid;grid-template-columns:34px 1fr auto;gap:14px;align-items:start}
.rec .rank{font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:20px;color:var(--muted-2)}
.rec h3{font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:17px;margin-bottom:4px}.rec p{color:var(--muted);font-size:14px;max-width:60ch}
.tag{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.06em;text-transform:uppercase;padding:4px 9px;border-radius:100px;white-space:nowrap;align-self:center;font-weight:600}
.tag.crit{color:var(--rod);background:var(--rod-dim);border:1px solid color-mix(in srgb,var(--rod) 34%,transparent)}
.tag.hoej{color:var(--gul);background:var(--gul-dim);border:1px solid color-mix(in srgb,var(--gul) 34%,transparent)}
.tag.med{color:var(--blaa);background:var(--blaa-dim);border:1px solid color-mix(in srgb,var(--blaa) 34%,transparent)}
.tag.let{color:var(--gron);background:var(--gron-dim);border:1px solid color-mix(in srgb,var(--gron) 34%,transparent)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin-bottom:12px}
.card h3{font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:16.5px;margin-bottom:6px}
.card h3 .st{font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;padding:3px 8px;border-radius:100px;margin-left:8px;vertical-align:middle}
.st.ok{color:var(--gron);background:var(--gron-dim)}.st.fix{color:var(--rod);background:var(--rod-dim)}.st.del{color:var(--gul);background:var(--gul-dim)}
.card p{color:var(--muted);font-size:14px}.card p b,.card li b{color:var(--text)}.card ul{margin:8px 0 0 18px;color:var(--muted);font-size:14px}.card li{margin:5px 0}
.ex{font-family:'JetBrains Mono',monospace;font-size:12.5px;background:var(--ink-2);border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin-top:10px;line-height:1.9;overflow-x:auto}
.ex .bad{color:var(--rod)}.ex .good{color:var(--gron)}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin-top:8px}
.pagetbl{width:100%;border-collapse:collapse;font-size:13.5px}.pagetbl th,.pagetbl td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}
.pagetbl th{font-family:'JetBrains Mono',monospace;font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted-2)}.pagetbl td code{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--gul)}
pre{background:var(--ink-2);border:1px solid var(--line);border-radius:12px;padding:14px 16px;overflow-x:auto;font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--muted);line-height:1.6;margin-top:10px;white-space:pre-wrap}
.band{background:var(--ink-2);border:1px solid var(--line);border-radius:20px;padding:32px;text-align:center;margin:26px 0 0}
.band h2{font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:clamp(20px,3vw,28px)}.band p{color:var(--muted);max-width:46ch;margin:10px auto 0}
.btn{font-family:'Inter';font-weight:600;font-size:15px;text-decoration:none;padding:14px 26px;border-radius:100px;display:inline-block;background:var(--gron);color:#08130c;margin-top:18px;transition:transform .12s}.btn:hover{transform:translateY(-2px)}
.demo-note{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--muted-2);border:1px dashed var(--line-2);border-radius:8px;padding:8px 12px;margin-top:16px;display:inline-block}
footer{border-top:1px solid var(--line);padding:26px 0;color:var(--muted-2);font-size:13px}.foot-in{display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px}
.theme-switch{position:fixed;right:16px;bottom:16px;z-index:60;display:flex;gap:4px;background:var(--panel);border:1px solid var(--line);border-radius:100px;padding:5px;box-shadow:var(--shadow)}
.theme-switch button{border:none;background:none;color:var(--muted);font-size:11px;font-family:'JetBrains Mono',monospace;padding:6px 11px;border-radius:100px;cursor:pointer}.theme-switch button.on{background:var(--gron-dim);color:var(--gron)}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""

JS = """
(function(){
  var bar=document.getElementById('tabbar');var tabs=[].slice.call(bar.querySelectorAll('.tab'));
  var panes={};[].slice.call(document.querySelectorAll('.pane')).forEach(function(p){panes[p.id]=p;});
  bar.addEventListener('click',function(e){var b=e.target.closest('.tab');if(!b)return;
    tabs.forEach(function(t){t.classList.toggle('on',t===b);});
    Object.keys(panes).forEach(function(k){panes[k].classList.toggle('on',k===b.dataset.p);});
    window.scrollTo({top:0,behavior:'smooth'});});
  var sw=document.getElementById('themeSwitch');
  sw.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;
    if(b.dataset.t==='lys')document.body.setAttribute('data-theme','lys');else document.body.removeAttribute('data-theme');
    [].slice.call(sw.querySelectorAll('button')).forEach(function(x){x.classList.toggle('on',x===b);});});
})();
"""

def esc(s): return html.escape(str(s), quote=True)

def card(item):
    st = ""
    if item.get("status"):
        st = f' <span class="st {esc(item["status"])}">{esc(item["status_label"])}</span>'
    h = f'<div class="card"><h3>{esc(item["title"])}{st}</h3><p>{esc(item["body"])}</p>'
    if item.get("list"):
        h += '<ul>' + ''.join(f'<li>{esc(x)}</li>' for x in item["list"]) + '</ul>'
    if item.get("ex"):
        rows = '<br>'.join(f'<span class="bad">{esc(b)}</span> &rarr; <span class="good">{esc(g)}</span>' for b, g in item["ex"])
        h += f'<div class="ex">{rows}</div>'
    if item.get("pre"):
        h += f'<pre>{esc(item["pre"])}</pre>'
    return h + '</div>'

def recs(items):
    out = ''
    for r in items:
        out += (f'<div class="rec"><span class="rank">{esc(r["rank"])}</span>'
                f'<div><h3>{esc(r["title"])}</h3><p>{esc(r["body"])}</p></div>'
                f'<span class="tag {esc(r["tag"])}">{esc(r["tag_label"])}</span></div>')
    return out

def sprogtable(intro, rows):
    body = ''.join(f'<tr><td><code>{esc(s)}</code></td><td>{esc(f)}</td></tr>' for s, f in rows)
    return (f'<p class="lead">{esc(intro)}</p><div class="scroll"><table class="pagetbl">'
            f'<thead><tr><th>Side</th><th>Fund</th></tr></thead><tbody>{body}</tbody></table></div>')

def build(payload, mode):
    m = payload["meta"]
    name = m["name"] if mode == "client" else m["name_demo"]
    counts = ''.join(f'<div class="m"><div class="n" style="color:var(--{c["c"]})">{esc(c["n"])}</div><div class="l">{esc(c["l"])}</div></div>' for c in m["counts"])
    tabdefs = [("anbefalinger","Anbefalinger"),("overblik","Overblik"),("seo","SEO"),
               ("sprog","Sprog &amp; tekst"),("lokal","Lokal synlighed"),("ai","AI-synlighed"),
               ("indhold","Indhold &amp; blog"),("konvertering","Booking &amp; konvertering")]
    tabbtns = ''.join(f'<button class="tab{" on" if i==0 else ""}" data-p="{k}">{lbl}</button>' for i,(k,lbl) in enumerate(tabdefs))

    panes = ''
    panes += f'<section class="pane on" id="anbefalinger"><h2>Anbefalinger — rangeret efter effekt</h2><p class="lead">Det jeg ville tage først. Øverst = mest at hente for mindst indsats.</p>{recs(payload["recommendations"])}</section>'
    panes += f'<section class="pane" id="overblik"><h2>Overblik</h2><p class="lead">Det gode først: fundamentet er i orden. Det der trækker ned er indhold og synlighed — billige rettelser.</p>{"".join(card(x) for x in payload["overblik"])}</section>'
    panes += f'<section class="pane" id="seo"><h2>Teknisk SEO</h2><p class="lead">Bliver siden forstået og vist rigtigt af Google?</p>{"".join(card(x) for x in payload["seo"])}</section>'
    panes += f'<section class="pane" id="sprog"><h2>Sprog &amp; tekst — side for side</h2>{sprogtable(payload["sprog_intro"], payload["sprog_rows"])}</section>'
    panes += f'<section class="pane" id="lokal"><h2>Lokal synlighed</h2><p class="lead">Det vigtigste for at blive fundet lokalt — og det svageste punkt lige nu.</p>{"".join(card(x) for x in payload["lokal"])}</section>'
    panes += f'<section class="pane" id="ai"><h2>AI-synlighed (AEO)</h2><p class="lead">Flere finder behandlere gennem ChatGPT, Perplexity og Google AI. De læser andre signaler end Google.</p>{"".join(card(x) for x in payload["ai"])}</section>'
    panes += f'<section class="pane" id="indhold"><h2>Indhold &amp; blog</h2><p class="lead">Indhold trækker nye søgninger ind over tid — og gør siden troværdig. Her er mest ubrugt potentiale.</p>{"".join(card(x) for x in payload["indhold"])}</section>'
    panes += f'<section class="pane" id="konvertering"><h2>Booking &amp; konvertering</h2><p class="lead">Bookingen virker — men vejen derhen er gemt, og der sælges ikke forløb.</p>{"".join(card(x) for x in payload["konvertering"])}</section>'

    if mode == "demo":
        band = ('<div class="band"><h2>Vil du have din egen analyse?</h2>'
                '<p>Jeg kører den samme fulde gennemgang på din side — og leverer en prioriteret plan du kan handle på.</p>'
                '<a class="btn" href="mailto:sls@slstech.dk?subject=Hjemmeside-analyse">Book din egen analyse &rarr;</a>'
                '<div class="demo-note">Demo · rigtig analyse, delt med tilladelse. Din egen leveres fortroligt.</div></div>')
    else:
        band = ''

    return f"""<!DOCTYPE html>
<html lang="da"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>afgang — Hjemmeside-analyse{" (demo)" if mode=="demo" else ""}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,700;12..96,800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<header class="top"><div class="wrap">
<div class="brand">afgang<span class="dot">.</span> · hjemmeside-analyse</div>
<div class="eyebrow">Fuld analyse · rigtig side</div>
<h1>Hvad står i vejen — og <em>hvad det er værd at rette</em></h1>
<p class="sub">En gennemgang af hele siden, side for side: teknisk SEO, sprog, lokal og AI-synlighed, indhold og booking-rejsen. Hvert fund er hentet direkte fra sidens kildekode — rangeret efter effekt.</p>
<p class="meta">Analyseret: {esc(name)} · {esc(m["type"])} · {esc(m["tech"])} · {esc(m["pages"])} sider · {esc(m["source"])}</p>
<div class="scoreband"><div class="score"><span class="big">{esc(m["score"])}</span><span class="max">/ {esc(m["score_max"])}</span><span class="lbl">{esc(m["score_label"])}</span></div>
<div class="div"></div><div class="mini">{counts}</div></div>
</div></header>
<div class="tabs"><div class="in" id="tabbar">{tabbtns}</div></div>
<main><div class="wrap">{panes}{band}</div></main>
<footer><div class="wrap foot-in"><span class="brand">afgang<span class="dot">.</span></span><span>Hjemmeside-analyse · fra afgang / SLS Tech</span><span>sls@slstech.dk</span></div></footer>
<div class="theme-switch" id="themeSwitch" role="group" aria-label="Tema"><button data-t="moerk" class="on">Mørk</button><button data-t="lys">Lys</button></div>
<script>{JS}</script></body></html>"""

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "illona_payload.json"
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    for mode in ("client", "demo"):
        out = build(payload, mode)
        fn = f"hjemmeside-analyse-{mode}.html"
        with open(fn, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"skrev {fn} ({len(out)} bytes)")
