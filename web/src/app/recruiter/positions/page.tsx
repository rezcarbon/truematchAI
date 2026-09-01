export const dynamic = 'force-dynamic';

import Link from "next/link";
import { PageHeader } from "@/components/shared/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { mockPositions } from "@/lib/mock";
import {
  BarChart3, Clock, Users, Zap, TrendingUp,
  AlertTriangle, Plus, Search
} from "lucide-react";

/* ── Mini funnel ──────────────────────────────────────────────────────── */
function MiniFunnel({ stages }: { stages: { label: string; count: number }[] }) {
  const maxCount = Math.max(...stages.map((s) => s.count), 1);
  return (
    <div className="space-y-1.5">
      {stages.map((s) => {
        const widthPercent = (s.count / maxCount) * 100;
        return (
          <div key={s.label} className="text-[10px]">
            <div className="flex items-center justify-between mb-0.5">
              <span className="text-muted-foreground font-medium">{s.label}</span>
              <span className="tabular-nums font-bold">{s.count}</span>
            </div>
            <div className="h-2 rounded-full bg-muted overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-400 to-blue-600 transition-all"
                style={{ width: `${Math.max(widthPercent, 10)}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ── Position health card ────────────────────────────────────────────── */
interface PositionCardProps {
  id: string;
  title: string;
  department: string;
  location: string;
  status: string;
  candidateCount: number;
  jdQualityScore: number;
  totalApplied?: number;
  inProgress?: number;
  daysOpen?: number;
}

function PositionCard(p: PositionCardProps) {
  const stages = [
    { label: "New", count: Math.ceil(p.candidateCount * 0.3) },
    { label: "Screening", count: Math.ceil(p.candidateCount * 0.4) },
    { label: "Interview", count: Math.ceil(p.candidateCount * 0.2) },
    { label: "Offer", count: Math.ceil(p.candidateCount * 0.1) },
  ];

  const jdStatus =
    p.jdQualityScore >= 80 ? "pass" :
    p.jdQualityScore >= 60 ? "review" : "fail";

  return (
    <Link href={`/recruiter/positions/${p.id}`}>
      <Card className="transition-all hover:shadow-md hover:border-primary/30 cursor-pointer group">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <CardTitle className="text-lg group-hover:text-primary transition-colors">{p.title}</CardTitle>
              <p className="text-sm text-muted-foreground">{p.department} · {p.location}</p>
            </div>
            <StatusBadge status={p.status} />
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Key metrics */}
          <div className="grid grid-cols-3 gap-2">
            <div className="rounded-lg bg-muted/60 p-2">
              <p className="text-[10px] text-muted-foreground font-medium">Total applied</p>
              <p className="text-xl font-bold">{p.totalApplied ?? p.candidateCount}</p>
            </div>
            <div className="rounded-lg bg-muted/60 p-2">
              <p className="text-[10px] text-muted-foreground font-medium">In progress</p>
              <p className="text-xl font-bold">{p.inProgress ?? Math.ceil(p.candidateCount * 0.6)}</p>
            </div>
            <div className="rounded-lg bg-muted/60 p-2">
              <p className="text-[10px] text-muted-foreground font-medium">Days open</p>
              <p className="text-xl font-bold">{p.daysOpen ?? 14}</p>
            </div>
          </div>

          {/* JD quality indicator */}
          <div className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-primary/5 to-transparent p-2.5">
            <BarChart3 className="h-4 w-4 text-primary shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium">JD Quality</p>
              <p className="text-[11px] text-muted-foreground">
                {p.jdQualityScore}/100
                {p.jdQualityScore < 70 && " — needs attention"}
              </p>
            </div>
            <StatusBadge status={jdStatus} />
          </div>

          {/* Mini funnel */}
          <div>
            <p className="mb-2 text-[11px] font-semibold text-muted-foreground">Pipeline</p>
            <MiniFunnel stages={stages} />
          </div>

          {/* SLA indicator */}
          <div className="flex items-center justify-between rounded-lg border border-amber-200/50 bg-amber-50/40 p-2">
            <div className="flex items-center gap-2">
              <Clock className="h-3.5 w-3.5 text-amber-600" />
              <p className="text-[10px] font-medium text-amber-800">
                {p.daysOpen ?? 14} days open — {p.daysOpen && p.daysOpen > 30 ? "SLA warning" : "on track"}
              </p>
            </div>
            {p.daysOpen && p.daysOpen > 30 && (
              <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

export default function PositionsPage() {
  const positions = mockPositions;

  return (
    <div className="space-y-6">
      {/* Header + quick actions */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <PageHeader
            title="Positions"
            subtitle={`${positions.length} open roles`}
          />
        </div>
        <button className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 shrink-0 mt-2">
          <Plus className="h-4 w-4" /> New position
        </button>
      </div>

      {/* Search + filter bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search positions by title or department…"
            className="h-10 w-full rounded-lg border bg-card pl-9 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>
        <select className="h-10 rounded-lg border bg-card px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30">
          <option>All statuses</option>
          <option>Open</option>
          <option>In progress</option>
          <option>Closed</option>
        </select>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "Open positions", value: positions.filter((p) => p.status === "open").length, icon: Zap, color: "text-blue-600" },
          { label: "Total candidates", value: positions.reduce((sum, p) => sum + (p.candidateCount ?? 0), 0), icon: Users, color: "text-purple-600" },
          { label: "Avg days open", value: Math.round(positions.reduce((sum, p) => sum + (p.daysOpen ?? 14), 0) / positions.length), icon: Clock, color: "text-amber-600" },
          { label: "Avg JD quality", value: `${Math.round(positions.reduce((sum, p) => sum + (p.jdQualityScore ?? 75), 0) / positions.length)}/100`, icon: TrendingUp, color: "text-emerald-600" },
        ].map(({ label, value, icon: Icon, color }) => (
          <Card key={label}>
            <CardContent className="flex items-center gap-3 p-3">
              <Icon className={`h-5 w-5 shrink-0 ${color}`} />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground font-medium">{label}</p>
                <p className="text-lg font-bold tabular-nums">{value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Positions grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {positions.map((p) => (
          <PositionCard
            key={p.id}
            id={p.id}
            title={p.title}
            department={p.department ?? "Engineering"}
            location={p.location ?? "Remote"}
            status={p.status}
            candidateCount={p.candidateCount ?? 5}
            jdQualityScore={p.jdQualityScore ?? 75}
          />
        ))}
      </div>

      {positions.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <Zap className="mb-3 h-12 w-12 text-muted-foreground/50" />
            <p className="text-sm font-medium">No positions yet</p>
            <p className="mt-1 text-xs text-muted-foreground">Create your first position to start recruiting</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
