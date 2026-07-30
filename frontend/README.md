# Afgang · Self-serve frontend

`afgang-selfserve.html` — én selvstændig fil (ingen frameworks, ingen build). Kunde-UI for alle 14 produkter: vælg produkt → upload/indtast data → kør analyse / køb / se eksempel.

## Konfiguration
- `window.AFGANG_MOTOR_URL` — sæt til den deployede Cloud Function-router for live kald. Tom = demo-tilstand (eksempeldata, ingen backend).
- `window.AFGANG_STRIPE_LINKS` — {type: checkout-url} når Stripe er oppe.

## Status
- UI testet headless (Playwright, `test_ui.mjs`): 14 produkter, formular-varianter pr. inputtype, demo-output, ingen JS-fejl.
- Live motor-kald + Stripe-køb: IKKE testet — kræver deployet router + Stripe. Falder pænt tilbage til demo indtil da.

## Kør test
node test_ui.mjs
