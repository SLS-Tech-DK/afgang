import { chromium } from '@playwright/test';
const url = 'file://' + process.cwd() + '/afgang-selfserve.html';
let ok = true;
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' }).catch(async()=>await chromium.launch());
const pg = await b.newPage();
const errs = [];
pg.on('pageerror', e => errs.push(String(e)));
await pg.goto(url);

// 1. katalog viser 14 produkter
const cards = await pg.$$('#grid .card');
if (cards.length !== 14) { ok=false; console.log('FEJL: forventede 14 kort, fik', cards.length); }
else console.log('Katalog: 14 produkter ✓');

// 2. demo-tilstand markeret
const mode = await pg.textContent('#modeflag');
if (!/demo/.test(mode)) { ok=false; console.log('FEJL: demo-tilstand ikke markeret'); }

// 3. åbn Salgsanalyse (kort nr 2) og vis eksempel
await cards[1].click();
await pg.waitForSelector('#product:not(.hidden)');
const pname = await pg.textContent('#p_name');
if (!/Salgsanalyse/.test(pname)) { ok=false; console.log('FEJL: forkert produkt åbnet:', pname); }
await pg.click('#demo');
const out1 = await pg.textContent('#out');
if (!/EKSEMPEL/.test(out1) || !/bestsellere/i.test(out1)) { ok=false; console.log('FEJL: demo-output mangler'); }
else console.log('Produkt + demo-output ✓');

// 4. csv-upload-felt findes for salgsanalyse
if (!(await pg.$('#f_csv'))) { ok=false; console.log('FEJL: CSV-upload-felt mangler'); }

// 5. "Kør analyse" i demo falder pænt tilbage til eksempel
await pg.click('#run');
const out2 = await pg.textContent('#out');
if (!/ikke koblet på|EKSEMPEL|eksempel/i.test(out2)) { ok=false; console.log('FEJL: run-fallback virker ikke'); }
else console.log('Kør-analyse demo-fallback ✓');

// 6. tilbage, åbn konkurrentanalyse → domæne+konkurrent-felter
await pg.click('#back');
const cards2 = await pg.$$('#grid .card');
// find konkurrentanalyse-kortet
let idx=-1; const titles = await pg.$$eval('#grid .card h3', els=>els.map(e=>e.textContent));
titles.forEach((t,i)=>{ if(/Konkurrentanalyse/.test(t)) idx=i; });
await cards2[idx].click();
if (!(await pg.$('#f_own')) || !(await pg.$('#f_c1'))) { ok=false; console.log('FEJL: konkurrent-formular mangler felter'); }
else console.log('Konkurrent-formular (domæne+konkurrenter) ✓');

// 7. landingsside → textarea
await pg.click('#back');
const titles2 = await pg.$$eval('#grid .card h3', els=>els.map(e=>e.textContent));
let li=-1; titles2.forEach((t,i)=>{ if(/Landingsside/.test(t)) li=i; });
(await pg.$$('#grid .card'))[li].click ? await (await pg.$$('#grid .card'))[li].click() : null;
await pg.waitForTimeout(100);
if (!(await pg.$('#f_page'))) { ok=false; console.log('FEJL: landingsside-textarea mangler'); }
else console.log('Landingsside-formular (textarea) ✓');

if (errs.length){ ok=false; console.log('JS-FEJL på siden:', errs); }
else console.log('Ingen JS-fejl ✓');

console.log('\nRESULTAT:', ok ? '✓ OK' : '✗ FEJL');
await b.close();
process.exit(ok?0:1);
