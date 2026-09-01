# Billing go-live checklist (Stripe)

The billing system is **already built and integrated** into the FastAPI backend
+ Next.js web app (Checkout, webhooks, credits, entitlements, Founding-100
inventory, referrals, admin fulfillment queue, refunds). Going live is
**configuration, not code** — there is no Supabase, no Payment Links, no second
payment path. Card data never touches our servers (Stripe-hosted Checkout, PCI
SAQ A).

This doc is the operator runbook. Steps marked **[you]** require your Stripe
account / credentials (I can't enter secrets); steps marked **[done]** are
already in the codebase.

---

## 1. Environment variables to set

Add these to `backend/.env` (test values first). Field→env mapping is
case-insensitive; these are the exact names the app reads.

```dotenv
# --- Stripe (test mode first: keys start with sk_test_ / pk_test_) ---
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx        # from the webhook you register in step 4

# --- Redirects (point at your deployed web domain) ---
BILLING_CURRENCY=usd                   # or sgd
BILLING_SUCCESS_URL=https://app.truematch.digital/billing/success?session_id={CHECKOUT_SESSION_ID}
BILLING_CANCEL_URL=https://app.truematch.digital/pricing?canceled=1

# --- Enforcement (leave false until you WANT assessments metered) ---
BILLING_ENFORCE=false

# --- Referrals (optional tuning) ---
REFERRAL_ENABLED=true
REFERRAL_REWARD_CREDITS=1
SHARE_BASE_URL=https://app.truematch.digital/share
```

With **no** `STRIPE_SECRET_KEY`, the system is a safe no-op: `/billing/checkout`
returns 503 and assessments run unmetered (current behaviour). Nothing breaks.

---

## 2. Create the Stripe account **[you]**

1. Create / use the Stripe account for the operating entity (MustafarAI /
   Digital Court). Toggle **Test mode** on (top-right) while integrating.
2. **Developers → API keys** → copy the **Secret key** (`sk_test_…`) and
   **Publishable key** (`pk_test_…`) into the env above.
3. (Singapore) **Settings → Payment methods** → enable **PayNow** and **Cards**.
   PayNow then appears automatically on Checkout for SGD — no extra integration.

> Products/prices do **not** need to be created in the dashboard — the catalog
> lives in code (`app/services/billing/catalog.py`) and is sent as inline
> `price_data`. Single $3 · 5-pack $9 · CV $5 · JD $50/$200 · Team $500 ·
> Founding $49/$499/$2,500 · Premium $9.90/mo.

---

## 3. Test webhooks locally with the Stripe CLI **[you + me]**

Webhooks are the source of truth for fulfillment, so test them before going live.

```bash
# install once: https://stripe.com/docs/stripe-cli
stripe login
# forward live test events to the running local backend:
stripe listen --forward-to localhost:8000/api/v1/billing/webhook
```

`stripe listen` prints a `whsec_…` — put it in `STRIPE_WEBHOOK_SECRET`, restart
uvicorn. Then a full test-mode purchase flows: checkout → Stripe test card
`4242 4242 4242 4242` → webhook → credit/entitlement granted.

**Once your test keys are in `.env`, tell me and I'll run a real end-to-end:**
create a Checkout Session via `/billing/checkout`, drive the test webhook, and
assert the credit ledger / Founding counter / referral all update.

---

## 4. Register the production webhook **[you]**

In **Developers → Webhooks → Add endpoint**:

- URL: `https://api.truematch.digital/api/v1/billing/webhook`
- Events: `checkout.session.completed`, `invoice.paid`,
  `customer.subscription.deleted`
- Copy the endpoint's **Signing secret** (`whsec_…`) → `STRIPE_WEBHOOK_SECRET`.

---

## 5. Go live **[you]**

1. Flip Stripe to **Live mode**, swap in `sk_live_…` / `pk_live_…` and the
   **live** webhook secret.
2. Point `BILLING_SUCCESS_URL` / `BILLING_CANCEL_URL` / `SHARE_BASE_URL` at the
   production web domain.
3. Restart the API. Checkout, fulfillment, Founding counter, referrals all
   light up automatically.
4. Set `BILLING_ENFORCE=true` when you want assessments to consume credits /
   require a plan. (Leave false to keep them free during early testing.)

---

## 6. What's already wired **[done]**

| Endpoint | Purpose |
|---|---|
| `GET /billing/catalog` | public pricing |
| `GET /billing/founding` | live Founding-100 remaining-spots counter |
| `POST /billing/checkout` | create Stripe Checkout Session (auth) |
| `POST /billing/webhook` | signature-verified, idempotent fulfillment |
| `GET /billing/me` | caller's credits + entitlement + orders |
| `POST /billing/referral/redeem`, `GET /billing/referral` | two-sided referrals |
| `POST /assessments/{id}/share` · `GET /billing/share/{token}` | shareable anonymised result |
| `GET /billing/admin/orders` · `PATCH …/fulfillment` · `GET /billing/admin/summary` · `POST /billing/refund` | admin fulfillment queue + refunds |

Web: `/pricing` (+ Founding counter + `?ref=` redeem), `/billing/success`,
`/refer`, `/share/[token]`, `/admin/billing`.

---

## 7. Not engineering — confirm with professionals

- **Legal entity + bank account** Stripe pays out to.
- **Settlement currency** (USD vs SGD; PayNow settles SGD).
- **GST**: mandatory above S$1M turnover; below it optional — confirm with an
  accountant.
- Using Stripe as processor means **you are not operating a payment service**
  yourself (no MAS PSA licence needed) — a key reason to stay on hosted Checkout.
