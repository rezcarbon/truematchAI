"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { LanguageBadge, languageName } from "@/components/shared/LanguageBadge";
import { TransitionPathways } from "@/components/shared/TransitionPathways";
import { Button } from "@/components/ui/button";
import { api, type TransitionResult } from "@/lib/api";
import { Loader2, Compass, CalendarClock, Check } from "lucide-react";

export default function TransitionResultPage({ params }: { params: { id: string } }) {
  const [data, setData] = useState<TransitionResult | null>(null);
  const [tracking, setTracking] = useState(false);

  async function enableTracking() {
    try {
      const r = await api.setTransitionTracking(params.id, true);
      setTracking(r.tracking);
    } catch {
      /* non-blocking */
    }
  }

  useEffect(() => {
    let active = true;
    let tries = 0;
    const poll = async () => {
      try {
        const r = await api.getTransition(params.id);
        if (!active) return;
        setData(r);
        if (r.status === "completed" || r.status === "failed") return;
      } catch {
        /* keep polling */
      }
      if (active && tries++ < 60) setTimeout(poll, 4000);
    };
    poll();
    return () => {
      active = false;
    };
  }, [params.id]);

  if (!data || (data.status !== "completed" && data.status !== "failed")) {
    return (
      <div className="mx-auto flex max-w-2xl flex-col items-center gap-3 py-20 text-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">
          Mapping your transition pathways from your evidenced capability…
        </p>
      </div>
    );
  }

  if (data.status === "failed") {
    return (
      <div className="mx-auto max-w-2xl py-16">
        <Card className="border-destructive/40">
          <CardHeader>
            <CardTitle>Analysis failed</CardTitle>
            <CardDescription>{data.error || "Something went wrong. Please try again."}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 py-2">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
          <Compass className="h-6 w-6 text-primary" /> Your transition pathways
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {data.currentRole ? `Anchored on: ${data.currentRole}. ` : ""}
          {typeof data.capabilityScore === "number"
            ? `Capability verdict ${data.capabilityScore}/100. `
            : ""}
          Every pathway is grounded in your evidenced capability — feasibility and timelines are honest, not aspirational.
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {languageName(data.sourceLanguage) && (
            <LanguageBadge language={data.sourceLanguage} label="CV translated from" />
          )}
          <Button variant={tracking ? "outline" : "default"} size="sm" className="gap-1.5"
                  disabled={tracking} onClick={enableTracking}>
            {tracking ? <Check className="h-4 w-4" /> : <CalendarClock className="h-4 w-4" />}
            {tracking ? "Tracking quarterly" : "Track my progress quarterly"}
          </Button>
        </div>
      </div>

      <TransitionPathways result={data} />
    </div>
  );
}
