'use client';

export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api, type CatalogItem, type BillingSummary, type FoundingTier } from "@/lib/api";
import { Check, Zap, Loader2 } from "lucide-react";

function price(amount: number, currency: string, mode: string): string {
  const v = (amount / 100).toLocaleString("en-US", { style: "currency", currency: currency.toUpperCase() });
  return mode === "subscription" ? `${v}/mo` : v;
}

export default function PricingPage(): React.ReactElement {
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [configured, setConfigured] = useState(true);
  const [billing, setBilling] = useState<BillingSummary | null>(null);
  const [founding, setFounding] = useState<Record<string, FoundingTier>>({});
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refCode, setRefCode] = useState<string | null>(null);
  const [refMsg, setRefMsg] = useState<string | null>(null);

  useEffect(() => {
    api.getCatalog().then((c) => { setItems(c.items); setConfigured(c.configured); });
    api.getBilling().then(setBilling).catch(() => {});
    api.getFounding().then((f) =>
      setFounding(Object.fromEntries(f.tiers.map((t) => [t.sku, t]))),
    ).catch(() => {});
    // Arrived from a referral link (?ref=CODE) — offer to redeem it.
    const ref = new URLSearchParams(window.location.search).get("ref");
    if (ref) setRefCode(ref.toUpperCase());
  }, []);

  const applyReferral = async (): Promise<void> => {
    if (!refCode) return;
    try {
      const r = await api.redeemReferral(refCode);
      setRefMsg(`Referral applied — +${r.granted_credits} free credit (balance ${r.balance}).`);
      setRefCode(null);
      api.getBilling().then(setBilling).catch(() => {});
    } catch (e) {
      setRefMsg(e instanceof Error ? e.message : "Could not apply referral code.");
    }
  };

  const buy = async (sku: string): Promise<void> => {
    setError(null);
    setPending(sku);
    try {
      const { checkout_url } = await api.startCheckout(sku);
      window.location.href = checkout_url; // hand off to Stripe-hosted Checkout
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start checkout");
      setPending(null);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight">Pricing</h1>
        <p className="mt-2 text-muted-foreground">
          See what the hiring system misses about you. Pay per assessment, bundle, or go Founding.
        </p>
      </div>

      {refCode && (
        <Card className="mb-6 border-green-200 bg-green-50/60">
          <CardContent className="flex items-center justify-between py-4">
            <div className="text-sm">
              <span className="font-medium">You were referred!</span> Redeem code{" "}
              <span className="font-mono font-semibold">{refCode}</span> for a free assessment.
            </div>
            <Button size="sm" onClick={applyReferral}>Apply</Button>
          </CardContent>
        </Card>
      )}
      {refMsg && (
        <div className="mb-6 rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">{refMsg}</div>
      )}

      {billing && (
        <Card className="mb-6 border-blue-200 bg-blue-50/50">
          <CardContent className="flex items-center justify-between py-4">
            <div className="text-sm">
              <span className="font-medium">Your access: </span>
              {billing.unlimited ? (
                <Badge className="ml-1">Unlimited{billing.entitlement?.plan ? ` · ${billing.entitlement.plan}` : ""}</Badge>
              ) : (
                <span>{billing.credit_balance} assessment credit{billing.credit_balance === 1 ? "" : "s"}</span>
              )}
            </div>
            {billing.has_access && <span className="text-sm text-green-700">Ready to assess ✓</span>}
          </CardContent>
        </Card>
      )}

      {!configured && (
        <div className="mb-6 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          Payments are not yet enabled in this environment. The catalogue is shown for preview.
        </div>
      )}
      {error && (
        <div className="mb-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((it) => {
          const isFounding = it.id.startsWith("founding_");
          const tier = founding[it.id];
          const soldOut = tier ? tier.remaining <= 0 : false;
          return (
            <Card key={it.id} className={isFounding ? "border-blue-300 ring-1 ring-blue-200" : ""}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{it.name}</CardTitle>
                  {isFounding && <Badge className="gap-1"><Zap className="h-3 w-3" />Founding</Badge>}
                </div>
                <CardDescription>{it.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="mb-4 text-2xl font-bold">{price(it.amount, it.currency, it.mode)}</div>
                {tier && (
                  <div className="mb-4">
                    <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
                      <span>{soldOut ? "Sold out" : `${tier.remaining} of ${tier.limit} spots left`}</span>
                      <span>{tier.sold}/{tier.limit}</span>
                    </div>
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                      <div
                        className={soldOut ? "h-full bg-red-400" : "h-full bg-blue-500"}
                        style={{ width: `${Math.min(100, (tier.sold / tier.limit) * 100)}%` }}
                      />
                    </div>
                  </div>
                )}
                <ul className="mb-5 space-y-1.5 text-sm text-muted-foreground">
                  {it.credits > 0 && (
                    <li className="flex items-center gap-2"><Check className="h-4 w-4 text-green-600" />{it.credits} assessment{it.credits === 1 ? "" : "s"}</li>
                  )}
                  {it.entitlement_kind && (
                    <li className="flex items-center gap-2"><Check className="h-4 w-4 text-green-600" />
                      {it.entitlement_kind === "subscription" ? "Recurring access" : "12-month access"}
                    </li>
                  )}
                  {it.mode === "subscription" && (
                    <li className="flex items-center gap-2"><Check className="h-4 w-4 text-green-600" />Cancel anytime</li>
                  )}
                </ul>
                <Button
                  className="w-full"
                  disabled={!configured || pending !== null || soldOut}
                  onClick={() => buy(it.id)}
                >
                  {soldOut ? "Sold out" : pending === it.id ? (
                    <span className="flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin" />Redirecting…</span>
                  ) : it.mode === "subscription" ? "Subscribe" : "Buy"}
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <p className="mt-8 text-center text-xs text-muted-foreground">
        Secure checkout by Stripe. Card details never touch TrueMatch servers. Singapore users can pay with PayNow.
      </p>
    </div>
  );
}
