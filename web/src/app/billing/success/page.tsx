'use client';

export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api, type BillingSummary } from "@/lib/api";
import { CheckCircle2, Loader2 } from "lucide-react";

export default function BillingSuccessPage(): React.ReactElement {
  const [billing, setBilling] = useState<BillingSummary | null>(null);

  // Fulfillment is driven by the Stripe webhook, which may land a moment after
  // the redirect — poll a few times so the balance/entitlement shows up.
  useEffect(() => {
    let tries = 0;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async (): Promise<void> => {
      const b = await api.getBilling().catch(() => null);
      setBilling(b);
      tries += 1;
      if (tries < 6 && b && !b.has_access) timer = setTimeout(poll, 1500);
    };
    poll();
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="mx-auto max-w-lg px-4 py-16">
      <Card>
        <CardHeader className="text-center">
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
            <CheckCircle2 className="h-7 w-7 text-green-600" />
          </div>
          <CardTitle>Payment received</CardTitle>
        </CardHeader>
        <CardContent className="text-center">
          {billing === null ? (
            <p className="flex items-center justify-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Confirming your purchase…
            </p>
          ) : billing.has_access ? (
            <p className="text-muted-foreground">
              {billing.unlimited
                ? `Your ${billing.entitlement?.plan ?? "plan"} access is active.`
                : `You now have ${billing.credit_balance} assessment credit${billing.credit_balance === 1 ? "" : "s"}.`}
            </p>
          ) : (
            <p className="text-muted-foreground">
              Your payment is confirmed. Access will appear here within a moment — you can
              refresh this page if it hasn&apos;t updated.
            </p>
          )}
          <div className="mt-6 flex justify-center gap-3">
            <Link href="/candidate/assess"><Button>Start an assessment</Button></Link>
            <Link href="/pricing"><Button variant="outline">Back to pricing</Button></Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
