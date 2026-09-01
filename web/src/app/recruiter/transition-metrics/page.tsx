"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/shared/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { api, type TransitionMetrics } from "@/lib/api";
import { Loader2, TrendingUp, Users, Target, GraduationCap } from "lucide-react";

function Stat({ label, value, icon: Icon }: { label: string; value: string | number; icon: React.ElementType }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-4">
        <div className="rounded-md bg-primary/10 p-2 text-primary"><Icon className="h-5 w-5" /></div>
        <div>
          <div className="text-2xl font-bold">{value}</div>
          <div className="text-xs text-muted-foreground">{label}</div>
        </div>
      </CardContent>
    </Card>
  );
}

function Bar({ label, value, total, color }: { label: string; value: number; total: number; color: string }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs">
        <span className="capitalize">{label}</span>
        <span className="text-muted-foreground">{value}</span>
      </div>
      <div className="h-2 w-full rounded-full bg-muted">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function TransitionMetricsPage() {
  const [m, setM] = useState<TransitionMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getTransitionMetrics().then((d) => { setM(d); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center gap-3 py-20 text-center">
        <Loader2 className="h-7 w-7 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">Loading cohort metrics…</p>
      </div>
    );
  }

  const readiness = m?.readiness ?? {};
  const outcomes = m?.outcomes ?? {};
  const readyTotal = (readiness.ready ?? 0) + (readiness.stretch ?? 0) + (readiness.aspirational ?? 0);
  const outcomeTotal = Object.values(outcomes).reduce((a, b) => a + (b ?? 0), 0);
  const rate = typeof m?.achievementRate === "number" ? `${Math.round(m.achievementRate * 100)}%` : "—";

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        title="Mandate Impact"
        subtitle="Cohort-level transition outcomes: how many people the platform identified as ready to move up, and how many actually transitioned. The 'no jobless growth' measurement layer — every number traces to grounded, evidence-anchored analyses."
      />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Candidates analyzed" value={m?.candidates ?? 0} icon={Users} />
        <Stat label="Analyses (completed)" value={m?.analysesCompleted ?? 0} icon={GraduationCap} />
        <Stat label="Under quarterly tracking" value={m?.tracked ?? 0} icon={TrendingUp} />
        <Stat label="Transition achievement rate" value={rate} icon={Target} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Readiness distribution</CardTitle>
            <CardDescription>Predicted pathways across all analyses, by feasibility.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Bar label="Ready now" value={readiness.ready ?? 0} total={readyTotal} color="bg-emerald-500" />
            <Bar label="Stretch" value={readiness.stretch ?? 0} total={readyTotal} color="bg-amber-500" />
            <Bar label="Aspirational" value={readiness.aspirational ?? 0} total={readyTotal} color="bg-slate-400" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recorded outcomes</CardTitle>
            <CardDescription>Did predicted transitions actually happen?</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Bar label="Achieved" value={outcomes.achieved ?? 0} total={outcomeTotal} color="bg-emerald-500" />
            <Bar label="Pursuing" value={outcomes.pursuing ?? 0} total={outcomeTotal} color="bg-blue-500" />
            <Bar label="Predicted (no action yet)" value={outcomes.predicted ?? 0} total={outcomeTotal} color="bg-slate-400" />
            <Bar label="Not pursued" value={outcomes.not_pursued ?? 0} total={outcomeTotal} color="bg-rose-400" />
            <p className="pt-1 text-xs text-muted-foreground">
              Achievement rate = achieved ÷ (achieved + not pursued), the resolved-outcome conversion.
            </p>
          </CardContent>
        </Card>
      </div>

      {outcomeTotal === 0 && (
        <p className="text-center text-sm text-muted-foreground">
          No outcomes recorded yet. As transitions are confirmed (via the analysis outcome control),
          this dashboard fills in — turning predictions into measured mandate impact.
        </p>
      )}
    </div>
  );
}
