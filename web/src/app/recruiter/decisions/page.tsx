'use client';

export const dynamic = 'force-dynamic';

import { PageHeader } from "@/components/shared/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { mockDecisions } from "@/lib/mock";
import {
  AlertTriangle, CheckCircle2, TrendingUp, BarChart3,
  Filter, Download, Calendar
} from "lucide-react";

interface Decision {
  id: string;
  candidateName: string;
  positionTitle: string;
  recruiter: string;
  traditionalScore: number;
  capabilityScore: number;
  decision: string;
  overrodeRecommendation: boolean;
  timestamp: string;
  jdTitle?: string;
}

/* ── Decision status badge ──────────────────────────────────────────── */
function DecisionBadge({ decision }: { decision: string }) {
  const config = {
    advance: { label: "Advance", color: "bg-emerald-100 text-emerald-700 border-emerald-300" },
    hold: { label: "Hold", color: "bg-amber-100 text-amber-700 border-amber-300" },
    reject: { label: "Reject", color: "bg-red-100 text-red-700 border-red-300" },
  };
  const cfg = config[decision as keyof typeof config] || config.hold;
  return (
    <Badge variant="outline" className={`border ${cfg.color}`}>
      {cfg.label}
    </Badge>
  );
}

export default function DecisionsPage() {
  const decisions = mockDecisions;

  return (
    <DecisionsContent decisions={decisions} />
  );
}

function DecisionsContent({ decisions }: { decisions: Decision[] }) {
  const overrides = decisions.filter((d) => d.overrodeRecommendation);
  const advanceCount = decisions.filter((d) => d.decision === "advance").length;
  const rejectCount = decisions.filter((d) => d.decision === "reject").length;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <PageHeader
            title="Decisions & Overrides"
            subtitle="Audit log of hiring decisions with compliance flags for overrides and bias analysis."
          />
        </div>
        <button className="flex items-center gap-2 rounded-lg border bg-card px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-accent transition-colors shrink-0 mt-2">
          <Download className="h-4 w-4" /> Export
        </button>
      </div>

      {/* Summary metrics */}
      <div className="grid gap-3 sm:grid-cols-4">
        {[
          { label: "Total decisions", value: decisions.length, icon: BarChart3, color: "text-blue-600" },
          { label: "Advances", value: advanceCount, icon: CheckCircle2, color: "text-emerald-600" },
          { label: "Rejects", value: rejectCount, icon: AlertTriangle, color: "text-red-600" },
          { label: "Overrides", value: overrides.length, icon: TrendingUp, color: "text-amber-600" },
        ].map(({ label, value, icon: Icon, color }) => (
          <Card key={label}>
            <CardContent className="flex items-center gap-3 p-4">
              <Icon className={`h-5 w-5 shrink-0 ${color}`} />
              <div>
                <p className="text-xs text-muted-foreground font-medium">{label}</p>
                <p className="text-2xl font-bold">{value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <button className="flex h-10 items-center gap-2 rounded-lg border bg-card px-3 text-sm font-medium text-muted-foreground hover:bg-accent transition-colors">
          <Filter className="h-4 w-4" /> Decision
        </button>
        <button className="flex h-10 items-center gap-2 rounded-lg border bg-card px-3 text-sm font-medium text-muted-foreground hover:bg-accent transition-colors">
          <Calendar className="h-4 w-4" /> Date range
        </button>
        <select className="h-10 rounded-lg border bg-card px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30">
          <option>All recruiters</option>
          <option>Current user</option>
        </select>
      </div>

      {/* Overrides alert */}
      {overrides.length > 0 && (
        <Card className="border-l-4 border-amber-500 bg-gradient-to-r from-amber-50/60 to-transparent">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <AlertTriangle className="h-4 w-4 text-amber-600" /> {overrides.length} Decision Override(s)
            </CardTitle>
            <p className="text-xs text-muted-foreground">Decisions that contradict the assessment recommendation — flagged for bias review.</p>
          </CardHeader>
        </Card>
      )}

      {/* Decision table */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Decision Log</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/40 text-left text-muted-foreground">
                  <th className="p-4 font-medium">Candidate</th>
                  <th className="p-4 font-medium">Position</th>
                  <th className="p-4 font-medium text-center">Scores</th>
                  <th className="p-4 font-medium text-center">Decision</th>
                  <th className="p-4 font-medium">Recruiter</th>
                  <th className="p-4 font-medium">Flag</th>
                  <th className="p-4 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {decisions.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-muted-foreground">
                      No decisions recorded yet
                    </td>
                  </tr>
                ) : (
                  decisions.map((d) => {
                    const recommended =
                      d.capabilityScore >= d.traditionalScore ? "advance" : "reject";
                    const isOverride = d.decision !== recommended;

                    return (
                      <tr
                        key={d.id}
                        className={`border-b transition-colors hover:bg-muted/40 ${isOverride ? "bg-amber-50/40" : ""}`}
                      >
                        <td className="p-4 font-medium">{d.candidateName}</td>
                        <td className="p-4 text-muted-foreground">{d.positionTitle}</td>
                        <td className="p-4 text-center tabular-nums">
                          <div className="text-xs">
                            <span className="font-medium">{d.traditionalScore}</span>
                            <span className="text-muted-foreground"> / </span>
                            <span className="font-medium text-primary">{d.capabilityScore}</span>
                          </div>
                        </td>
                        <td className="p-4 text-center">
                          <DecisionBadge decision={d.decision} />
                        </td>
                        <td className="p-4 text-muted-foreground text-xs">{d.recruiter}</td>
                        <td className="p-4">
                          {isOverride ? (
                            <Badge variant="destructive" className="text-[10px]">
                              Override
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground text-xs">—</span>
                          )}
                        </td>
                        <td className="p-4 text-muted-foreground text-xs whitespace-nowrap">
                          {new Date(d.timestamp).toLocaleDateString()}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Bias analysis */}
      {overrides.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <TrendingUp className="h-4 w-4 text-amber-600" /> Override Analysis
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-xs font-semibold text-muted-foreground mb-2">Pattern summary</p>
              <ul className="space-y-1.5 text-sm">
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
                  <span>
                    <span className="font-medium">{overrides.filter((d) => d.decision === "advance").length}</span> overrides advanced despite lower capability scores
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
                  <span>
                    <span className="font-medium">{overrides.filter((d) => d.decision === "reject").length}</span> overrides rejected strong candidates
                  </span>
                </li>
              </ul>
            </div>

            <div className="rounded-lg border border-amber-200/50 bg-amber-50/40 p-3">
              <p className="text-xs font-semibold text-amber-900 mb-1">Recommendation</p>
              <p className="text-xs text-amber-800/90">
                Review overrides quarterly to identify patterns. TrueMatch's 3-signal scoring is designed to surface capability you might miss — overrides are rare flags that warrant bias audits.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
