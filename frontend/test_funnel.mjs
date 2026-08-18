/* Afgang self-serve — funnel-kontrakttest (ingen netværk, ingen hemmeligheder).
   Kører den RIGTIGE afgang-selfserve.html mod en mocket gateway og verificerer at
   frontend-funnel'en matcher motor-kontrakten:
     - suite-produkter sender raa CSV som 'ordre_csv' (+ 'vare_csv'), IKKE 'csv'
     - "Kør analyse" uden token = gratis demo (demo:true)
     - efter Stripe-retur: ?session_id -> token gemmes i PAID, produkt aabnes
     - betalt kald sender access_token (ingen demo), renderer html + Excel-download
     - 402 -> koeb-besked
   Fejler => exit 1 (CI rødt). Dette er testen der ville have fanget felt-mismatchen.
*/
import { createRequire } from 'module';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
const require = createRequire(import.meta.url);
const { JSDOM } = require('jsdom');
const __dir = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(__dir, 'afgang-selfserve.html'), 'utf8');
const csv = "Ordrenr;Varenavn;Antal;Beloeb;Ordredato;Kunde\n1001;Kande;3;597,00;01-01-2026;a@b.dk\n1002;Kaffe;2;120,00;02-01-2026;c@d.dk";

let failures = 0;
function ok(cond, msg){ console.log((cond?'PASS  ':'FAIL  ')+msg); if(!cond) failures++; }
const wait = ms => new Promise(r=>setTimeout(r,ms));

function dom(search){
  const captured=[];
  const d = new JSDOM(html,{runScripts:'dangerously', url:'https://slstech.dk/afgang-selfserve.html'+(search||''),
    beforeParse(w){
      w.fetch=(u,o)=>{ const b=JSON.parse(o.body); captured.push(b);
        const mk=(s,x)=>Promise.resolve({status:s,json:()=>Promise.resolve(x)});
        if(b.session_id) return mk(200,{ok:true,access_token:'TKN',product:'salgsanalyse'});
        if(b.demo)       return mk(200,{ok:true,type:b.type,result:{meta:{total_revenue:717},html:'<h4>TEASER</h4>'}});
        if(b.access_token) return mk(200,{ok:true,type:b.type,result:{meta:{total_revenue:717},html:'<h4>FULD</h4>',xlsx_base64:'QUJD'}});
        return mk(402,{ok:false,betaling_kraevet:true,error:'Betaling'}); };
      class FR{ readAsText(){ this.result=csv; this.onload&&this.onload(); } } w.FileReader=FR;
    }});
  return {captured, d:d.window.document};
}
const openSalg = d => [...d.querySelectorAll('.card')].find(x=>/Salgsanalyse/.test(x.textContent)&&!/NEXT/.test(x.textContent)).onclick();
const setFile  = d => Object.defineProperty(d.getElementById('f_csv'),'files',{value:[{name:'o.csv'}],configurable:true});

// 1) DEMO: gratis forhaandsvisning sender ordre_csv + demo:true
{ const {captured,d}=dom(); openSalg(d); setFile(d); d.getElementById('run').onclick(); await wait(50);
  const b=captured[0]||{};
  ok(b.type==='salgsanalyse','demo: type=salgsanalyse');
  ok(b.demo===true,'demo: demo:true sat');
  ok(typeof b.ordre_csv==='string' && b.ordre_csv.startsWith('Ordrenr'),'demo: sender ordre_csv (ikke csv)');
  ok(b.csv===undefined,'demo: sender IKKE feltet csv');
  ok(!b.access_token,'demo: ingen access_token');
  ok(/FORHÅNDSVISNING/.test(d.getElementById('out').innerHTML),'demo: gratis-banner vises');
  ok(/TEASER/.test(d.getElementById('out').innerHTML),'demo: teaser-html renderes');
}
// 2) BETALT: session_id -> token -> fuld levering + Excel
{ const {captured,d}=dom('?session_id=cs_x'); await wait(60);
  ok(captured.some(x=>x.session_id==='cs_x'),'betalt: session_id vekslet til token');
  ok(/Betaling gennemført/.test(d.getElementById('out').innerHTML),'betalt: kvitterings-banner');
  setFile(d); d.getElementById('run').onclick(); await wait(60);
  const f=captured[captured.length-1]||{};
  ok(f.access_token==='TKN','betalt: fuldt kald sender access_token');
  ok(!f.demo,'betalt: fuldt kald har ikke demo-flag');
  ok(typeof f.ordre_csv==='string','betalt: fuldt kald sender ordre_csv');
  const out=d.getElementById('out').innerHTML;
  ok(/FULD/.test(out),'betalt: fuld html renderes');
  ok(/Download Excel-rapport/.test(out) && /data:application\/vnd\.openxmlformats/.test(out),'betalt: Excel-download (data-uri)');
}
// 3) 402 -> koeb-besked
{ const {d}=dom(); d.defaultView.eval("renderResult({ok:false,betaling_kraevet:true},402,{type:'salgsanalyse'},true)");
  ok(/kræver køb/.test(d.getElementById('out').innerHTML),'402: koeb-besked vises'); }

console.log(failures? ('\n'+failures+' TEST(S) FEJLEDE') : '\nALLE FUNNEL-TESTS BESTAAET');
process.exit(failures?1:0);
