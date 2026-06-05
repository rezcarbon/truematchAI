export const dynamic = 'force-dynamic';

import Link from "next/link";
import { PageHeader } from "@/components/shared/AppShell";
import { ScoreTrio } from "@/components/shared/ScoreTrio";
import { GovernanceBadge } from "@/components/shared/GovernanceBadge";
import { api } from "@/lib/api";
import { mockPipeline } from "@/lib/mock";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search, Filter, SlidersHorizontal } from "lucide-react";

const STAGE_COLORS: Record<string, string> = {
  new:       "bg-slate-100 text-slate-600",
  screening: "bg-blue-100 text-blue-700",
  interview: "bg-violet-100 text-violet-700",
  offer:     "bg-emerald-100 text-emerald-700",
  rejected:  "bg-red-100 text-red-600",
};

export default async function CandidatesPage() {
  const candidates = await api.getPipeline().catch(() => mockPipeline);
  const sorted = [...candidates].sort((a, b) => b.delta - a.delta);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <PageHeader title="All Candidates" subtitle={`${candidates.length} candidates across all positions`} />
      </div>

      {/* Search + filter bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by name, position, or skills…"
            className="h-10 w-full rounded-lg border bg-card pl-9 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>
        <button className="flex h-10 items-center gap-2 rounded-lg border bg-card px-4 text-sm font-medium text-muted-foreground hover:bg-accent transition-colors">
          <Filter className="h-4 w-4" /> Stage
        </button>
        <button className="flex h-10 items-center gap-2 rounded-lg border bg-card px-4 text-sm font-medium text-muted-foreground hover:bg-accent transition-colors">
          <SlidersHorizontal className="h-4 w-4" /> Sort
        </button>
      </div>

      {/* Column headers */}
      <div className="grid grid-cols-[1fr_auto_auto_auto] gap-4 px-4 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
        <span>Candidate</span>
        <span className="w-48 text-center">3-Signal Score</span>
        <span className="w-24 text-center">Stage</span>
        <span className="w-20 text-center">Governance</span>
      </div>

      {/* Candidate rows */}
      <div className="space-y-2">
        {sorted.map((c) => (
          <Link key={c.id} href={`/recruiter/candidates/${c.id}`}>
            <Card className="group cursor-pointer transition-all hover:shadow-md hover:border-primary/30">
              <div className="grid grid-cols-[1fr_auto_auto_auto] items-center gap-4 p-4">
                {/* Identity */}
                <div className="flex items-center gap-3 min-w-0">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
                    {c.name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold truncate">{c.name}</p>
                    <p className="text-xs text-muted-foreground truncate">{c.appliedFor}</p>
                  </div>
                </div>

                {/* Scores */}
                <div className="w-48">
                  <ScoreTrio
                    traditional={c.traditionalScore}
                    capability={c.capabilityScore}
                    delta={c.delta}
                    compact
                  />
                </div>

                {/* Stage */}
                <div className="w-24 text-center">
                  <span className={`rounded-full px-2.5 py-1 text-[11px] font-medium capitalize ${STAGE_COLORS[c.stage] ?? "bg-muted text-muted-foreground"}`}>
                    {c.stage}
                  </span>
                </div>

                {/* Governance */}
                <div className="w-20 text-center">
                  <GovernanceBadge status={c.governanceStatus} label={c.governanceStatus === "review" ? "⚠ Review" : "✓"} />
                </div>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
