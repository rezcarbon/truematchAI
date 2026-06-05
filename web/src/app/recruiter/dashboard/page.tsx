export const dynamic = 'force-dynamic';

import {
  Users, Briefcase, Calendar, FileText,
  Inbox, AlertTriangle, CheckCircle2,
  TrendingUp, Zap, Activity, Clock,
  ArrowRight, Plus
} from "lucide-react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScoreTrio } from "@/components/shared/ScoreTrio";
import { GovernanceBadge } from "@/components/shared/GovernanceBadge";
import { JDSimulationWidget } from "@/components/recruiter/JDSimulationWidget";
import { api } from "@/lib/api";
import { mockPipeline, mockPositions } from "@/lib/mock";

/* ── helpers ────────────────────────────────────────────────────────────── */

function TaskChip({
  icon: Icon, label, count, color, href,
}: { icon: React.ElementType; label: string; count: number; color: string; href: string }) {
  if (count === 0) return null;
  return (
    <Link href={href}>
      <div className={`flex cursor-pointer items-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-medium transition-colors hover:opacity-90 ${color} shrink-0`}>
        <Icon className="h-4 w-4" />
        <span className="tabular-nums font-bold">{count}</span>
        <span className="hidden sm:inline">{label}</span>
      </div>
    </Link>
  );
}

function HealthDot({ status }: { status: "on-track" | "at-risk" | "stalled" }) {
  const colors = { "on-track": "bg-emerald-400", "at-risk": "bg-amber-400", "stalled": "bg-red-400" };
  return <span className={`inline-block h-2.5 w-2.5 rounded-full shrink-0 ${colors[status]}`} />;
}

function WorkCard({ c }: { c: (typeof mockPipeline)[0] }) {
  const priority = c.delta > 40 ? "red" : c.delta > 15 ? "amber" : "slate";
  const borderColor = { red: "border-l-red-400", amber: "border-l-amber-400", slate: "border-l-slate-300" }[priority];
  return (
    <Link href={`/recruiter/candidates/${c.id}`}>
      <div className={`group flex cursor-pointer items-start gap-3 rounded-lg border border-l-4 bg-card p-4 transition-all hover:shadow-md ${borderColor}`}>
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
          {c.name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <p className="truncate text-sm font-semibold">{c.name}</p>
            <GovernanceBadge status={c.governanceStatus} label={c.governanceStatus === "review" ? "Review" : "✓"} />
          </div>
          <p className="truncate text-xs text-muted-foreground">{c.appliedFor}</p>
          {priority === "red" && <p className="mt-0.5 text-[11px] font-medium text-red-600">Scorecard needed</p>}
          <div className="mt-2">
            <ScoreTrio traditional={c.traditionalScore} capability={c.capabilityScore} delta={c.delta} compact />
          </div>
        </div>
        <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
      </div>
    </Link>
  );
}

function AgentCard({ name, running, processed, errors, icon: Icon }: {
  name: string; running: boolean; processed: number; errors: number; icon: React.ElementType;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border bg-card px-4 py-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className={`h-2 w-2 rounded-full ${running ? "bg-emerald-400 animate-pulse" : "bg-slate-300"}`} />
          <p className="truncate text-xs font-semibold">{name}</p>
        </div>
        <p className="text-[11px] text-muted-foreground">
          {processed} done today{errors > 0 ? ` · ` : ""}{errors > 0 && <span className="text-red-500">{errors} errors</span>}
        </p>
      </div>
    </div>
  );
}

function EventRow({ time, icon: Icon, text, color }: { time: string; icon: React.ElementType; text: string; color: string }) {
  return (
    <div className="flex items-start gap-3 py-2">
      <Icon className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${color}`} />
      <p className="flex-1 min-w-0 truncate text-xs text-foreground/90">{text}</p>
      <span className="shrink-0 text-[10px] tabular-nums text-muted-foreground">{time}</span>
    </div>
  );
}

/* ── page ────────────────────────────────────────────────────────────────── */

export default async function RecruiterDashboard() {
  const [pipeline, positions] = await Promise.all([
    api.getPipeline().catch(() => mockPipeline),
    api.getPositions().catch(() => mockPositions),
  ]);

  const openRoles    = positions.filter((p) => p.status === "open").length;
  const reviewNeeded = pipeline.filter((c) => c.governanceStatus === "review").length;
  const highDelta    = pipeline.filter((c) => c.delta > 40).length;
  const interviews   = pipeline.filter((c) => c.stage === "interview").length;
  const workQueue    = [...pipeline].sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta)).slice(0, 8);

  return (
    <div className="space-y-6">
      {/* header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Command Centre</h1>
          <p className="text-sm text-muted-foreground">Your hiring pipeline at a glance</p>
        </div>
        <Link href="/recruiter/positions/new">
          <Button size="sm"><Plus className="mr-1.5 h-4 w-4" /> New Position</Button>
        </Link>
      </div>

      {/* KPI tiles */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "Open roles",       value: openRoles,    icon: Briefcase,     color: "text-primary" },
          { label: "Interviews today", value: interviews,   icon: Calendar,      color: "text-blue-600" },
          { label: "Under review",     value: reviewNeeded, icon: AlertTriangle, color: "text-amber-600" },
          { label: "Hidden gems ⚡",   value: highDelta,    icon: Zap,           color: "text-amber-500" },
        ].map(({ label, value, icon: Icon, color }) => (
          <Card key={label}>
            <CardContent className="flex items-center gap-4 p-4">
              <div className={`flex h-10 w-10 items-center justify-center rounded-full bg-muted ${color}`}>
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold tabular-nums">{value}</p>
                <p className="text-xs text-muted-foreground">{label}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* task strip */}
      <div className="flex flex-wrap gap-2">
        <TaskChip icon={FileText}     label="scorecards due"   count={2}            color="bg-red-50 border-red-200 text-red-700"      href="/recruiter/pipeline" />
        <TaskChip icon={Calendar}     label="interviews today" count={interviews}   color="bg-blue-50 border-blue-200 text-blue-700"    href="/recruiter/pipeline" />
        <TaskChip icon={AlertTriangle}label="approvals pending"count={1}            color="bg-amber-50 border-amber-200 text-amber-700" href="/recruiter/agents/queue" />
        <TaskChip icon={Inbox}        label="CVs to review"    count={reviewNeeded} color="bg-purple-50 border-purple-200 text-purple-700" href="/recruiter/agents/queue" />
      </div>

      {/* three-column layout */}
      <div className="grid gap-6 lg:grid-cols-[220px_1fr_260px]">

        {/* LEFT — positions */}
        <Card className="self-start">
          <CardHeader className="pb-2 pt-4">
            <CardTitle className="text-sm">Active Positions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 pb-4">
            {positions.map((p, i) => {
              const health = i === 0 ? "at-risk" : i === 2 ? "stalled" : "on-track";
              return (
                <Link key={p.id} href={`/recruiter/positions/${p.id}`}>
                  <div className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-2 text-xs hover:bg-accent transition-colors">
                    <HealthDot status={health} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium">{p.title}</p>
                      <p className="text-muted-foreground">{p.candidateCount} candidates</p>
                    </div>
                  </div>
                </Link>
              );
            })}
            <Link href="/recruiter/positions">
              <Button variant="ghost" size="sm" className="mt-1 w-full text-xs">
                All positions <ArrowRight className="ml-1 h-3 w-3" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* CENTRE — work queue */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold">Candidate Work Queue</h2>
            <Link href="/recruiter/pipeline">
              <Button variant="ghost" size="sm" className="text-xs">
                View all <ArrowRight className="ml-1 h-3 w-3" />
              </Button>
            </Link>
          </div>
          {workQueue.length === 0 ? (
            <div className="flex h-32 items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
              All caught up — no candidates need action today.
            </div>
          ) : (
            <div className="space-y-2">
              {workQueue.map((c) => <WorkCard key={c.id} c={c} />)}
            </div>
          )}
        </div>

        {/* RIGHT — agents + feed */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-2 pt-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Agent Status</CardTitle>
                <Link href="/recruiter/agents">
                  <Button variant="ghost" size="sm" className="h-6 px-2 text-[11px]">Manage</Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent className="space-y-2 pb-4">
              <AgentCard name="CV Ingestion" running processed={47} errors={0} icon={Inbox} />
              <AgentCard name="JD Analysis"  running={false} processed={12} errors={0} icon={FileText} />
              <div className="flex gap-2 pt-1">
                <Link href="/recruiter/agents" className="flex-1">
                  <Button variant="outline" size="sm" className="w-full text-xs"><Inbox className="mr-1 h-3 w-3" /> Drop CV</Button>
                </Link>
                <Link href="/recruiter/agents" className="flex-1">
                  <Button variant="outline" size="sm" className="w-full text-xs"><FileText className="mr-1 h-3 w-3" /> JD Draft</Button>
                </Link>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2 pt-4">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Activity className="h-3.5 w-3.5 text-emerald-500" /> Live Events
              </CardTitle>
            </CardHeader>
            <CardContent className="divide-y pb-2">
              <EventRow time="14:32" icon={Zap}           color="text-amber-500"      text="Maya O. → AI Leader — δ+65 ⚡ counter-rec" />
              <EventRow time="14:28" icon={CheckCircle2}  color="text-emerald-500"    text="Assessment complete — M. Reezan" />
              <EventRow time="14:25" icon={FileText}      color="text-blue-500"       text="JD 'Eco Director' analysed — 75/100" />
              <EventRow time="14:20" icon={Inbox}         color="text-purple-500"     text="CV ingested — Sarah Chen" />
              <EventRow time="14:15" icon={TrendingUp}    color="text-primary"        text="You advanced Priya N. → Interview" />
              <EventRow time="14:10" icon={Clock}         color="text-muted-foreground" text="2 interviews tomorrow 10am" />
            </CardContent>
          </Card>

          <JDSimulationWidget
            recentSimulationCount={0}
            avgQualityScore={0}
            lastSimulationTitle={undefined}
            lastSimulationScore={undefined}
          />

          <Card>
            <CardHeader className="pb-2 pt-4">
              <CardTitle className="text-sm">Job Sources</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 pb-4">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Manual uploads</span>
                <span className="font-bold">47</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">USAJOBS API</span>
                <span className="font-bold">156</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">LinkedIn scraper</span>
                <span className="font-bold">23</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Indeed scraper</span>
                <span className="font-bold">89</span>
              </div>
              <Link href="/admin/uploads" className="block pt-2">
                <Button variant="outline" size="sm" className="w-full text-xs">
                  <FileText className="mr-1 h-3 w-3" /> Upload jobs
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
