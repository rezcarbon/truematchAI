"use client";
import Link from "next/link";
import { Zap, AlertTriangle, CheckCircle2, Clock, ArrowRight, Settings } from "lucide-react";
import { ScoreTrio } from "@/components/shared/ScoreTrio";
import { GovernanceBadge } from "@/components/shared/GovernanceBadge";
import type { PipelineCandidate } from "@/lib/types";
import { cn } from "@/lib/utils";

const STAGES = [
  { key: "new",       label: "New",       color: "bg-slate-100 text-slate-700" },
  { key: "screening", label: "Screening", color: "bg-blue-100 text-blue-700" },
  { key: "interview", label: "Interview", color: "bg-violet-100 text-violet-700" },
  { key: "offer",     label: "Offer",     color: "bg-emerald-100 text-emerald-700" },
];

function priorityBorder(delta: number, govStatus: string) {
  if (govStatus === "review") return "border-l-amber-400";
  if (delta > 40)             return "border-l-red-400";
  if (delta > 15)             return "border-l-amber-300";
  return "border-l-slate-200";
}

function priorityIcon(delta: number, govStatus: string) {
  if (govStatus === "review") return <AlertTriangle className="h-3 w-3 text-amber-500" />;
  if (delta > 40)             return <Zap className="h-3 w-3 text-amber-500" />;
  if (delta < -20)            return <CheckCircle2 className="h-3 w-3 text-emerald-500" />;
  return null;
}

function CandidateKanbanCard({ c }: { c: PipelineCandidate }) {
  return (
    <Link href={`/recruiter/candidates/${c.id}`}>
      <div className={cn(
        "group mb-2 cursor-pointer rounded-lg border border-l-4 bg-card p-3 shadow-sm transition-all hover:shadow-md",
        priorityBorder(c.delta, c.governanceStatus)
      )}>
        {/* name row */}
        <div className="flex items-center justify-between gap-1 mb-1">
          <div className="flex items-center gap-1.5 min-w-0">
            {priorityIcon(c.delta, c.governanceStatus)}
            <span className="truncate text-xs font-semibold">{c.name}</span>
          </div>
          <GovernanceBadge status={c.governanceStatus} label={c.governanceStatus === "review" ? "⚠" : "✓"} />
        </div>
        {/* days in stage */}
        <div className="flex items-center gap-1 mb-2">
          <Clock className="h-2.5 w-2.5 text-muted-foreground" />
          <span className="text-[10px] text-muted-foreground">3d in stage</span>
        </div>
        {/* 3-signal score trio */}
        <ScoreTrio
          traditional={c.traditionalScore}
          capability={c.capabilityScore}
          delta={c.delta}
          compact
        />
      </div>
    </Link>
  );
}

export function PipelineKanban({ candidates }: { candidates: PipelineCandidate[] }) {
  return (
    <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${STAGES.length}, minmax(220px, 1fr))` }}>
      {STAGES.map((stage) => {
        const cols = candidates.filter((c) => c.stage === stage.key);
        return (
          <div key={stage.key} className="flex flex-col">
            {/* stage header */}
            <div className="mb-3 flex items-center gap-2">
              <span className={cn("rounded-full px-2.5 py-0.5 text-xs font-semibold", stage.color)}>
                {stage.label}
              </span>
              <span className="text-xs tabular-nums text-muted-foreground">{cols.length}</span>
              <button className="ml-auto text-muted-foreground hover:text-foreground">
                <Settings className="h-3 w-3" />
              </button>
            </div>
            {/* cards */}
            <div className="min-h-[120px] rounded-xl bg-muted/40 p-2">
              {cols.length === 0 ? (
                <p className="py-8 text-center text-[11px] text-muted-foreground">No candidates</p>
              ) : (
                cols.map((c) => <CandidateKanbanCard key={c.id} c={c} />)
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
