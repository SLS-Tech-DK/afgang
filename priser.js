/* priser.js — Afgang, single source of truth for priser.
   Genereret 24-07-2026 fra pris-kontrolpanelet.
   Ret ALDRIG priser i de enkelte sider — ret i kontrolpanelet og upload denne fil igen. */
window.PRISER = {
  "sparring_1t": {
    "navn": "AI-sparring · 1 time",
    "type": "fast",
    "pris": 600
  },
  "workshop_halvdag": {
    "navn": "Halvdags workshop",
    "type": "fast",
    "pris": 2000
  },
  "workshop_heldag": {
    "navn": "Heldags workshop",
    "type": "fast",
    "pris": 3000
  },
  "workshop_hos_1dag": {
    "navn": "AI-workshop hos jer · 1 dag",
    "type": "fast",
    "pris": 5000
  },
  "workshop_hos_2dag": {
    "navn": "AI-workshop hos jer · 2 dage",
    "type": "fast",
    "pris": 8000
  },
  "klip_5": {
    "navn": "Klippekort · 5 klip",
    "type": "fast",
    "pris": 1000
  },
  "klip_10": {
    "navn": "Klippekort · 10 klip",
    "type": "fast",
    "pris": 1800
  },
  "hjemmeside": {
    "navn": "Hjemmeside + hosting",
    "type": "interval",
    "fra": 5000,
    "til": 15000
  },
  "data_fortolkning": {
    "navn": "Data-analyse & overblik",
    "type": "fra",
    "pris": 1000
  },
  "betalingsopsaetning": {
    "navn": "Betalingsopsætning",
    "type": "fra",
    "pris": 500
  },
  "kobling": {
    "navn": "Kobling til andre systemer",
    "type": "fra",
    "pris": 500
  },
  "konkurrent_bot": {
    "navn": "Konkurrent-bot",
    "type": "fast",
    "pris": 7000
  },
  "branchenyheds_bot": {
    "navn": "Branchenyheds-bot",
    "type": "fast",
    "pris": 5000
  },
  "mobil_app": {
    "navn": "Mobil-app",
    "type": "aftale",
    "tekst": "fra-pris, aftales"
  }
};

(function(){
  function tal(n){ return n.toLocaleString("da-DK"); }
  window.visPris = function(n){
    var p = window.PRISER[n]; if(!p) return "";
    if(p.type==="fast")     return tal(p.pris)+" kr";
    if(p.type==="fra")      return "fra "+tal(p.pris)+" kr";
    if(p.type==="interval") return tal(p.fra)+"–"+tal(p.til)+" kr";
    if(p.type==="aftale")   return p.tekst||"efter aftale";
    return "";
  };
  window.visTal = function(n){
    var p = window.PRISER[n]; if(!p) return "";
    if(p.type==="fast"||p.type==="fra") return tal(p.pris);
    if(p.type==="interval") return tal(p.fra)+"–"+tal(p.til);
    if(p.type==="aftale")   return p.tekst||"efter aftale";
    return "";
  };
  function fyld(){
    document.querySelectorAll("[data-pris]").forEach(function(el){
      var v=window.visPris(el.getAttribute("data-pris")); if(v) el.textContent=v; });
    document.querySelectorAll("[data-pris-tal]").forEach(function(el){
      var v=window.visTal(el.getAttribute("data-pris-tal")); if(v) el.textContent=v; });
  }
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",fyld);
  else fyld();
})();
