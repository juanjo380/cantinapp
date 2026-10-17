# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Single human role: **Administrador de negocio (ADMIN)**, one owner-operator per
business (tenant): the person running a small or medium business (pyme) who owns and
operates it directly. They register products, load sales (manual or CSV), consult
inventory and receive purchase recommendations. They work in Spanish (Colombia) and
think in COP. No other human roles in v0.1 — registration creates one ADMIN per
business (see `memoria.md` §6). They are not data analysts: they know their products
and their customers, not spreadsheets or forecasting.

Their job: keep the right amount of stock without holding capital hostage or losing
sales. Purchase decisions today rest on experience, perception and disorganized
spreadsheets, and are typically reactive.

**Second actor: Sistema.** "Sistema" is NOT a user role and has no login. It is the
automated actor that analyzes sales data, predicts demand and generates alerts and
recommendations. The owner never operates it directly; it appears in the UI as
generated content (forecasts, recommendations, alerts) that the owner reads and decides
on. The owner always keeps the decision: recommendations are advice, not orders.

## Product Purpose

CantinAPP is a SaaS that manages inventory and forecasts demand from historical sales
for small businesses. Success means the owner can see stock status, understand how
sales are trending, get a demand forecast, and receive a concrete purchase
recommendation — fast enough to act on before running out or overbuying.

## Positioning

The mechanism is a closed loop the owner cannot build in a spreadsheet: recorded
sales flow into a demand forecast, the forecast and inventory flow into a ranked
purchase recommendation with a plain-language justification, and low-stock alerts.
The value is the recommendation, not the chart.

## Operating Context

- Web SPA (React + Vite + MUI) on top of a deployed FastAPI API
  (`https://cantinapp.onrender.com`). The free tier cold-starts in 30–60 s after
  inactivity; the UI must show loading, never treat it as an error.
- Sales arrive two ways: manual single entries and bulk CSV history upload. Forecasts
  require ≥ 30 days of history (backend returns 422 otherwise), so a new business must
  load historical CSV before predictions work.
- Stock is never edited directly: it is a running total of inventory movements
  (sales, purchases, adjustments). Recommendations and alerts depend on an existing
  forecast; alerts require an explicit "generate" action.
- The Sistema does not act on its own in v0.1: forecasts, recommendations and alerts
  are produced only when requested through endpoints (`POST /api/forecasting`,
  `POST /api/recommendations`, `POST /api/alerts/generate`). The UI decides when to
  trigger them (for example on opening the dashboard, or through an explicit
  "Actualizar alertas" action) and must make clear when the data was generated.
- Everything is scoped to the authenticated user's business; the client never sends a
  business id.

## Capabilities and Constraints

Confirmed capability set (`MinimoReq.md` §3, backend coverage `memoria.md` §8):
register/login/logout, product CRUD with logical delete, manual + CSV sales,
inventory with NORMAL/BAJO/AGOTADO status, sales analytics by period, top/bottom
products, demand forecast with history-vs-forecast series, purchase recommendation
with urgency and justification, dashboard KPIs, and low-stock alerts (generate +
mark reviewed).

Durable constraints:
- **Locale:** Spanish (Colombia), COP currency, dates as ISO `YYYY-MM-DD` over the
  wire and DD/MM/YYYY in the UI.
- **Multitenancy** is enforced by the backend; never accept `business_id` from the UI.
- **Auth:** JWT Bearer; on 401 clear the session and redirect to `/login`.
- **API contract** is fixed by `memoria.md` §7 — do not guess endpoints, fields or
  status codes. All routes are under `/api`.
- **Stack is fixed:** React, Vite, React Router, Material UI. No other UI library.
- Out of v0.1 scope: mobile app, payments/subscriptions, e-invoicing (DIAN), ERP or
  multi-supplier integration, generative AI/chatbot, image/barcode recognition,
  additional human roles (employee, cashier) and role-based permissions.
- Open in source docs (do not invent answers): urgency threshold rationale, default
  forecast period, and confidence calculation are backend decisions already made
  (`memoria.md` §7); analysis charts' 30-day minimum is not stated as a constraint.

## Brand Commitments

Name: **CantinAPP** (binding; keep the capitalised "APP"). No logo or visual identity
exists yet — future work may create one, but must not fabricate existing brand assets.

## Evidence on Hand

- `memoria.md` — technical memory: architecture, schema decisions, full endpoint
  contract (§7), frontend notes (§10). Source of truth for the API.
- `MinimoReq.md` — product scope: value proposition, 9 user stories (HU01–HU09),
  MoSCoW priorities, functional/non-functional requirements, known open points.
- `db/schema.sql` — database schema source of truth.
- `AGENTS.md` — repo conventions, commands, design and React rules.
- Absent (must not fabricate): customers, testimonials, benchmarks, pricing,
  licensing, logos. The frontend is still the Vite scaffold — no incumbent UI exists.

## Product Principles

1. **The recommendation is the product.** Every screen ultimately serves the "what and
   how much to buy" decision; insight without a suggested action is unfinished.
2. **Show the state before the action.** Inventory status, alerts and low stock must be
   scannable at a glance — the operator decides quickly, not studies tables.
3. **Trust through transparency.** Everything the Sistema generates (forecasts,
   recommendations, alerts) shows its origin and basis: when it was generated, the
   history and coverage behind it, its confidence and urgency, and the justification.
   The owner must be able to believe the number, and always decides what to do.
4. **Honest data states.** Empty, insufficient-history and error states are first-class
   — a business with 3 days of sales is the common case, not an edge case.
5. **Built for one busy owner.** One human role, Spanish, COP, minimal steps to the
   decision.

## Accessibility & Inclusion

No product-specific accessibility standard was established. Baseline applies: semantic
HTML, keyboard operability, sufficient contrast, and respect for
`prefers-reduced-motion` (per `AGENTS.md`). Language is Spanish; consider `lang="es"`
and es-CO number/date formatting for screen readers.