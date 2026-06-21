'use client';

export const dynamic = 'force-dynamic';

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api, type SharedResultView } from "@/lib/api";
import { TrendingUp, Sparkles, Loader2 } from "lucide-react";

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
