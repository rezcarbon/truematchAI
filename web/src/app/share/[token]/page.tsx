import { useEffect, useState } from "react";
import Link from "next/link";
'use client';
function cn(...inputs: any[]) {
  return twMerge(clsx(inputs));
}

// import { api, type SharedResultView } from "@/lib/api"; (needs manual conversion)
import { TrendingUp, Sparkles, Loader2 } from "lucide-react";
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

export default function SharedResultPage({ params }: { params: { token: string } }): React.ReactElement {
  const [data, setData] = useState<SharedResultView | null | undefined>(undefined);

  useEffect(() => {
    api.getSharedResult(params.token).then(setData).catch(() => setData(null));
  }, [params.token]);

  if (data === undefined) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-muted-foreground">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Loading result…
      </div>
    );
  }
  if (data === null) {
    return (
      <div className="mx-auto max-w-md px-4 py-20 text-center">
        <h1 className="text-xl font-semibold">Result not found</h1>
        <p className="mt-2 text-muted-foreground">This shared link is invalid or has expired.</p>
        <Link href="/pricing" className="mt-6 inline-block"><Button>See your own score</Button></Link>
      </div>
    );
  }

  const trad = data.traditional_score ?? 0;
  const cap = data.capability_score ?? 0;
  const delta = data.score_delta ?? cap - trad;
  const refHref = data.referral_code ? `/pricing?ref=${data.referral_code}` : "/pricing";

  return (
    <div className="mx-auto max-w-xl px-4 py-12">
      <div className="mb-6 text-center">
        <p className="text-sm font-medium text-muted-foreground">A TrueMatch capability result</p>
        <h1 className="mt-1 text-2xl font-bold">See what the hiring system misses</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <TrendingUp className="h-4 w-4 text-blue-600" /> The delta
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-center">
            <Score label="Traditional ATS" value={trad} tone="muted" />
            <Score label="Capability" value={cap} tone="accent" />
            <Score label="Delta" value={delta} tone="delta" prefix="+" />
          </div>
          {data.counter_rec && (
            <div className="mt-5 flex items-center justify-center gap-2 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
              <Sparkles className="h-4 w-4" /> Counter-recommendation fired — a hidden gem.
            </div>
          )}
          <p className="mt-5 text-center text-xs text-muted-foreground">
            Keyword screening saw {trad}%. TrueMatch measured {cap}% of demonstrated capability.
          </p>
        </CardContent>
      </Card>

      <Card className="mt-5 border-blue-200 bg-blue-50/40">
        <CardContent className="py-5 text-center">
          <p className="font-medium">Know someone who should see their real score?</p>
          <p className="mt-1 text-sm text-muted-foreground">
            They get their first assessment free — and so do you.
          </p>
          <Link href={refHref} className="mt-4 inline-block">
            <Button>Get your free assessment</Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}

function Score({ label, value, tone, prefix = "" }: {
  label: string; value: number; tone: "muted" | "accent" | "delta"; prefix?: string;
}): React.ReactElement {
  const color = tone === "accent" ? "text-blue-600" : tone === "delta" ? "text-green-600" : "text-muted-foreground";
  return (
    <div>
      <div className={`text-3xl font-bold ${color}`}>{prefix}{value}{tone === "delta" ? "" : "%"}</div>
      <div className="mt-1 text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

export const dynamic = 'force-dynamic';


