import "jsr:@supabase/functions-js/edge-runtime.d.ts";
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const WEBHOOK_SECRET = Deno.env.get("STRIPE_WEBHOOK_SECRET") ?? "";
function timingSafeEqual(a: string, b: string): boolean { if (a.length !== b.length) return false; let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i); return d === 0; }
function toHex(buf: ArrayBuffer): string { return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, "0")).join(""); }
async function verifyStripeSignature(rawBody: string, sigHeader: string | null, secret: string): Promise<boolean> {
  if (!sigHeader) return false;
  const parts = Object.fromEntries(sigHeader.split(",").map((p) => { const i = p.indexOf("="); return [p.slice(0, i).trim(), p.slice(i + 1).trim()]; }));
  const t = parts["t"]; const v1 = parts["v1"]; if (!t || !v1) return false;
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const mac = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(`${t}.${rawBody}`));
  return timingSafeEqual(toHex(mac), v1);
}
Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return new Response("method not allowed", { status: 405 });
  const rawBody = await req.text();
  const sigHeader = req.headers.get("stripe-signature");
  if (WEBHOOK_SECRET) { const ok = await verifyStripeSignature(rawBody, sigHeader, WEBHOOK_SECRET); if (!ok) return new Response("bad signature", { status: 400 }); }
  else { console.warn("STRIPE_WEBHOOK_SECRET ikke sat - signatur IKKE verificeret"); }
  let event: any; try { event = JSON.parse(rawBody); } catch { return new Response("invalid json", { status: 400 }); }
  if (event?.type !== "checkout.session.completed") return new Response("ok", { status: 200 });
  const session = event?.data?.object ?? {};
  const meta = session.metadata ?? {};
  const product = meta.afgang_type ?? meta.type ?? "ukendt";
  const accessToken = crypto.randomUUID();
  const row = { stripe_session: session.id, product, access_token: accessToken, status: "paid", runs_allowed: 1, runs_used: 0, email: session.customer_details?.email ?? null, amount: Math.round((session.amount_total ?? 0) / 100), currency: (session.currency ?? "dkk").toLowerCase() };
  const resp = await fetch(`${SUPABASE_URL}/rest/v1/afgang_orders`, { method: "POST", headers: { "Content-Type": "application/json", apikey: SERVICE_ROLE, Authorization: `Bearer ${SERVICE_ROLE}`, Prefer: "return=minimal" }, body: JSON.stringify(row) });
  if (resp.ok) return new Response("ok", { status: 200 });
  if (resp.status === 409) return new Response("ok", { status: 200 });
  console.error(`Insert fejlede (${resp.status}): ${await resp.text()}`);
  return new Response("insert failed", { status: 500 });
});
