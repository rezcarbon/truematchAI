'use client';

export const dynamic = 'force-dynamic';

import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api, type AdminOrder, type BillingAdminSummary } from "@/lib/api";
import { DollarSign, Package, Clock, RotateCcw, Loader2 } from "lucide-react";

const NEXT_STATE: Record<string, string | null> = {
  pending: "processing",
  queued: "processing",
  processing: "delivered",
  delivered: null,
};

function money(cents: number, currency = "usd"): string {
  return (cents / 100).toLocaleString("en-US", { style: "currency", currency: currency.toUpperCase() });
}

function fulfillmentBadge(s: string): React.ReactElement {
  const map: Record<string, string> = {
    delivered: "bg-green-100 text-green-800",
    processing: "bg-blue-100 text-blue-800",
    queued: "bg-amber-100 text-amber-800",
    pending: "bg-gray-100 text-gray-700",
  };
  return <Badge className={map[s] ?? ""}>{s}</Badge>;
}

export default function AdminBillingPage(): React.ReactElement {
  const [summary, setSummary] = useState<BillingAdminSummary | null>(null);
  const [orders, setOrders] = useState<AdminOrder[]>([]);
  const [filter, setFilter] = useState<"awaiting" | "all" | "paid">("awaiting");
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async (): Promise<void> => {
    setSummary(await api.getBillingSummary());
    // "awaiting" = paid but not yet delivered (the 48h manual queue).
    if (filter === "awaiting") {
      const r = await api.getAdminOrders("paid");
      setOrders(r.items.filter((o) => o.fulfillment_status !== "delivered"));
    } else if (filter === "paid") {
      setOrders((await api.getAdminOrders("paid")).items);
    } else {
      setOrders((await api.getAdminOrders()).items);
    }
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  const advance = async (o: AdminOrder): Promise<void> => {
    const next = NEXT_STATE[o.fulfillment_status];
    if (!next) return;
    setBusy(o.id);
    try {
      await api.setFulfillment(o.id, next, `Manual fulfillment → ${next}`);
      await load();
    } finally { setBusy(null); }
  };

  const refund = async (o: AdminOrder): Promise<void> => {
    if (!confirm(`Refund ${money(o.amount, o.currency)} to ${o.user_email}?`)) return;
    setBusy(o.id);
    try { await api.refundOrderById(o.id); await load(); }
    catch (e) { alert(e instanceof Error ? e.message : "Refund failed"); }
    finally { setBusy(null); }
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="mb-1 text-2xl font-bold tracking-tight">Billing &amp; fulfillment</h1>
      <p className="mb-6 text-sm text-muted-foreground">
        Work the 48-hour manual assessment queue and track Founding 100 inventory.
      </p>

      {summary && (
        <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <SummaryCard icon={<DollarSign className="h-4 w-4" />} label="Gross revenue" value={money(summary.gross_revenue)} />
          <SummaryCard icon={<Package className="h-4 w-4" />} label="Paid orders" value={String(summary.paid_orders)} />
          <SummaryCard icon={<Clock className="h-4 w-4" />} label="Awaiting fulfillment" value={String(summary.awaiting_fulfillment)} accent={summary.awaiting_fulfillment > 0} />
          <SummaryCard icon={<RotateCcw className="h-4 w-4" />} label="Refunded" value={String(summary.refunded_orders)} />
        </div>
      )}

      {summary && summary.founding.length > 0 && (
        <Card className="mb-6">
          <CardHeader><CardTitle className="text-base">Founding 100 inventory</CardTitle></CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-3">
            {summary.founding.map((t) => (
              <div key={t.sku}>
                <div className="mb-1 flex justify-between text-sm">
                  <span className="font-medium">{t.name}</span>
                  <span className="text-muted-foreground">{t.remaining}/{t.limit} left</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div className="h-full bg-blue-500" style={{ width: `${Math.min(100, (t.sold / t.limit) * 100)}%` }} />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <div className="mb-3 flex gap-2">
        {(["awaiting", "paid", "all"] as const).map((f) => (
          <Button key={f} size="sm" variant={filter === f ? "default" : "outline"} onClick={() => setFilter(f)}>
            {f === "awaiting" ? "Awaiting fulfillment" : f === "paid" ? "All paid" : "All orders"}
          </Button>
        ))}
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50 text-left text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-4 py-2">Customer</th>
                <th className="px-4 py-2">Product</th>
                <th className="px-4 py-2">Amount</th>
                <th className="px-4 py-2">Payment</th>
                <th className="px-4 py-2">Fulfillment</th>
                <th className="px-4 py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {orders.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">No orders.</td></tr>
              )}
              {orders.map((o) => (
                <tr key={o.id} className="border-b last:border-0">
                  <td className="px-4 py-2">{o.user_email}</td>
                  <td className="px-4 py-2">{o.sku}</td>
                  <td className="px-4 py-2">{money(o.amount, o.currency)}</td>
                  <td className="px-4 py-2"><Badge className={o.status === "paid" ? "bg-green-100 text-green-800" : o.status === "refunded" ? "bg-red-100 text-red-700" : ""}>{o.status}</Badge></td>
                  <td className="px-4 py-2">{fulfillmentBadge(o.fulfillment_status)}</td>
                  <td className="px-4 py-2 text-right">
                    <div className="flex justify-end gap-2">
                      {o.status === "paid" && NEXT_STATE[o.fulfillment_status] && (
                        <Button size="sm" disabled={busy === o.id} onClick={() => advance(o)}>
                          {busy === o.id ? <Loader2 className="h-4 w-4 animate-spin" /> : `→ ${NEXT_STATE[o.fulfillment_status]}`}
                        </Button>
                      )}
                      {o.status === "paid" && (
                        <Button size="sm" variant="outline" disabled={busy === o.id} onClick={() => refund(o)}>Refund</Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

function SummaryCard({ icon, label, value, accent }: {
  icon: React.ReactNode; label: string; value: string; accent?: boolean;
}): React.ReactElement {
  return (
    <Card className={accent ? "border-amber-300" : ""}>
      <CardContent className="py-4">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">{icon}{label}</div>
        <div className="mt-1 text-2xl font-bold">{value}</div>
      </CardContent>
    </Card>
  );
}
