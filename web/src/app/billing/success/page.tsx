import { useEffect, useState } from "react";
import Link from "next/link";
'use client';
function cn(...inputs: any[]) {
  return twMerge(clsx(inputs));
}

// import { api, type BillingSummary } from "@/lib/api"; (needs manual conversion)
import { CheckCircle2, Loader2 } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function Card({ className, ...props }: any) {
  return (
    <div className={cn("rounded-lg border border-gray-200 bg-white shadow-sm", className)} {...props} />
  );
}
function CardHeader({ className, ...props }: any) {
  return <div className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />;
}
function CardTitle({ className, ...props }: any) {
  return <h2 className={cn("text-2xl font-semibold leading-none tracking-tight", className)} {...props} />;
}
function CardDescription({ className, ...props }: any) {
  return <p className={cn("text-sm text-gray-500", className)} {...props} />;
}
function CardContent({ className, ...props }: any) {
  return <div className={cn("p-6 pt-0", className)} {...props} />;
}

function Button({ className, variant = "default", size = "default", ...props }: any) {
  const variants: any = { default: "bg-blue-600 text-white hover:bg-blue-700", outline: "border border-gray-300 bg-white hover:bg-gray-50", ghost: "hover:bg-gray-100" };
  const sizes: any = { default: "px-4 py-2", sm: "px-3 py-1 text-sm", lg: "px-6 py-3 text-lg" };
  return <button className={cn("inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none", variants[variant], sizes[size], className)} {...props} />;
}

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

export const dynamic = 'force-dynamic';


