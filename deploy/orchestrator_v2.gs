/* SLS Tech · Afgang — Orchestrator v2 (UDKAST)
 * Generaliserer den eksisterende pollAuditOrders til ALLE produkttyper.
 * Poll Supabase orders (betalt + i_gang) -> kald motor-routeren (Cloud Function)
 * -> gem leverance -> mail til kunde -> sæt leveret. Audit-gating: kun betalte.
 * Script Properties: SUPABASE_URL, SUPABASE_SERVICE, MOTOR_URL, SLS_EMAIL, DRIVE_FOLDER
 * Trigger (tids-drevet, hvert 5. min): pollProductOrders
 */
const P = PropertiesService.getScriptProperties();

function pollProductOrders() {
  const rows = sbGet("/rest/v1/orders?payment_status=eq.betalt&delivery_status=eq.i_gang&select=*");
  rows.forEach(function (o) {
    try {
      // Byg body til motor-routeren ud fra ordrens input.
      const body = Object.assign({ type: o.type }, o.input || {});
      const res = UrlFetchApp.fetch(P.getProperty("MOTOR_URL"), {
        method: "post", contentType: "application/json",
        headers: { "Authorization": "Bearer " + getIdToken() }, // Cloud Function kræver auth
        payload: JSON.stringify(body), muteHttpExceptions: true
      });
      if (res.getResponseCode() !== 200) {
        sbPatch("/rest/v1/orders?id=eq." + o.id, { delivery_status: "fejl" });
        return;
      }
      const data = JSON.parse(res.getContentText());
      // Gem leverancen som fil (JSON + evt. forklaring) i Drive.
      const folder = DriveApp.getFolderById(P.getProperty("DRIVE_FOLDER"));
      const name = "leverance-" + o.type + "-" + o.id + ".json";
      const file = folder.createFile(name, JSON.stringify(data, null, 2), MimeType.PLAIN_TEXT);
      if (o.customer_email) {
        MailApp.sendEmail({
          to: o.customer_email,
          subject: "Din " + o.type + " fra SLS Tech er klar",
          body: "Hej,\n\nTak for din bestilling. Din analyse er klar og vedhæftet.\n\nMvh SLS Tech",
          attachments: [file.getAs(MimeType.PLAIN_TEXT)]
        });
      }
      sbPatch("/rest/v1/orders?id=eq." + o.id,
        { delivery_status: "leveret", delivery_url: file.getUrl(), delivered_at: new Date().toISOString() });
    } catch (err) {
      sbPatch("/rest/v1/orders?id=eq." + o.id, { delivery_status: "fejl" });
    }
  });
}

/* getIdToken(): hent en OIDC-id-token til det private Cloud Function-kald.
 * I Apps Script kan ScriptApp.getIdentityToken() bruges hvis funktionen er
 * i samme GCP-projekt; ellers brug en service-konto. Wires ved deploy. */
function getIdToken() { return ScriptApp.getIdentityToken(); }

function sbGet(path) {
  const res = UrlFetchApp.fetch(P.getProperty("SUPABASE_URL") + path, { headers: sbHeaders(), muteHttpExceptions: true });
  return JSON.parse(res.getContentText() || "[]");
}
function sbPatch(path, obj) {
  UrlFetchApp.fetch(P.getProperty("SUPABASE_URL") + path, {
    method: "patch", contentType: "application/json", headers: sbHeaders(),
    payload: JSON.stringify(obj), muteHttpExceptions: true
  });
}
function sbHeaders() {
  const k = P.getProperty("SUPABASE_SERVICE");
  return { apikey: k, Authorization: "Bearer " + k, "content-type": "application/json" };
}
