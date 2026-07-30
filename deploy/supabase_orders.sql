-- SLS Tech · Afgang — Supabase orders-skema (UDKAST, migration)
-- Generisk ordre-tabel til alle self-serve produkter. Orchestratoren poller
-- rækker med delivery_status='i_gang', kører rette motor, leverer, sætter 'leveret'.
-- Service-role bruges KUN server-side (orchestrator). RLS lukker alt for anon.

create table if not exists public.orders (
  id             uuid primary key default gen_random_uuid(),
  created_at     timestamptz not null default now(),
  type           text not null,                      -- fx 'salgsanalyse', 'konkurrentanalyse'
  tier           text,                               -- fx 'lite' | 'pro' | 'start' | 'plus'
  customer_email text,
  amount_dkk     numeric,                            -- betalt beløb (ekskl. moms)
  stripe_session text,                               -- Stripe checkout session id (idempotens)
  payment_status text not null default 'afventer',   -- afventer | betalt | refunderet
  delivery_status text not null default 'ny',        -- ny | i_gang | leveret | fejl
  input          jsonb,                              -- upload/parametre (csv-ref, domæne, brand ...)
  metadata       jsonb,                              -- fx {audit_url, engine, ...}
  delivery_url   text,                               -- link til leveret rapport i Drive/Storage
  delivered_at   timestamptz
);

create index if not exists orders_delivery_idx on public.orders (delivery_status);
create index if not exists orders_type_idx      on public.orders (type);
create unique index if not exists orders_stripe_uniq on public.orders (stripe_session)
  where stripe_session is not null;                  -- idempotens: én ordre pr. checkout

alter table public.orders enable row level security;
-- Ingen anon-policy = anon kan intet. Kun service-role (orchestrator) rører tabellen.

-- Betalings-webhook (Stripe) sætter payment_status='betalt' + delivery_status='i_gang'
-- audit-gating: levering starter FØRST når payment_status='betalt'.
