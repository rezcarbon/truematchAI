'use client';

export const dynamic = 'force-dynamic';

import { PageHeader } from "@/components/shared/AppShell";
import { JDQualityCard } from "@/components/recruiter/JDQualityCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { mockPositions } from "@/lib/mock";
import {
  AlertTriangle, CheckCircle2, AlertCircle, TrendingDown,
  BarChart3, Zap, Filter
} from "lucide-react";

/* ── JD Quality status indicator ──────────────────────────────────────── */
function QualityIndicator({ score }: { score: number }) {
  const status =
    score >= 80 ? { label: "Excellent", color: "text-emerald-600", bg: "bg-emerald-50/60", icon: CheckCircle2 } :
    score >= 60 ? { label: "Good", color: "text-amber-600", bg: "bg-amber-50/60", icon: AlertCircle } :
    { label: "Needs work", color: "text-red-600", bg: "bg-red-50/60", icon: AlertTriangle };

  const Icon = status.icon;
  return (
    <div className={`flex items-center gap-2 rounded-lg px-3 py-2 ${status.bg}`}>
      <Icon className={`h-4 w-4 ${status.color}`} />
      <div>
        <p className="text-xs font-semibold">{score}/100</p>
        <p className={`text-[10px] ${status.color}`}>{status.label}</p>
      </div>
    </div>
  );
}

export default function JDQualityPage() {
  const positions = mockPositions;

  // Mock JD data per position
  const items = positions.map((p) => ({
    position: p,
    score: p.jdQualityScore ?? 75,
    issues: Math.ceil(Math.random() * 5),
    issueList: [
      { type: "proxy", text: "Requires 'MSc in Computer Science' — consider accepting equivalent experience", severity: "medium" },
      { type: "inflated", text: "Experience range '12–18 years' may be overspecified for this scope", severity: "medium" },
      { type: "vague", text: "'Strong communication skills' — define in behavioral terms", severity: "low" },
      { type: "exclusionary", text: "Phrase 'must be willing to relocate' narrows pool unnecessarily if role is hybrid", severity: "low" },
    ].slice(0, Math.ceil(Math.random() * 4)),
  }));

  const avgScore = Math.round(items.reduce((sum, i) => sum + i.score, 0) / items.length);
  const excellentCount = items.filter((i) => i.score >= 80).length;
  const needsWorkCount = items.filter((i) => i.score < 60).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="JD Quality Review"
        subtitle="Identify proxy requirements, impossible asks, and exclusionary language that may suppress strong candidates."
      />

      {/* Summary stats */}
      <div className="grid gap-3 sm:grid-cols-3">
        {[
          { label: "Avg quality", value: `${avgScore}/100`, icon: BarChart3, color: "text-blue-600" },
          { label: "Excellent JDs", value: excellentCount, icon: CheckCircle2, color: "text-emerald-600" },
          { label: "Needs attention", value: needsWorkCount, icon: AlertTriangle, color: "text-red-600" },
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

      {/* Filter + sort */}
      <div className="flex items-center gap-2">
        <button className="flex h-10 items-center gap-2 rounded-lg border bg-card px-3 text-sm font-medium text-muted-foreground hover:bg-accent transition-colors">
          <Filter className="h-4 w-4" /> Quality
        </button>
        <select className="h-10 rounded-lg border bg-card px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30">
          <option>Worst first</option>
          <option>Best first</option>
          <option>Most issues</option>
          <option>Recently updated</option>
        </select>
      </div>

      {/* JD quality cards per position */}
      <div className="space-y-4">
        {items.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Zap className="mb-3 h-12 w-12 text-muted-foreground/50" />
              <p className="text-sm font-medium">No positions yet</p>
              <p className="mt-1 text-xs text-muted-foreground">Create positions to analyze their JD quality</p>
            </CardContent>
          </Card>
        ) : (
          items
            .sort((a, b) => a.score - b.score)
            .map(({ position, score, issueList }) => (
              <Card key={position.id} className="overflow-hidden">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <CardTitle>{position.title}</CardTitle>
                      <p className="mt-1 text-sm text-muted-foreground">{position.department ?? "Engineering"} · {position.location ?? "Remote"}</p>
                    </div>
                    <QualityIndicator score={score} />
                  </div>
                </CardHeader>

                {issueList.length > 0 && (
                  <CardContent className="space-y-3 pb-3 border-t">
                    <p className="text-xs font-semibold text-muted-foreground">Issues identified</p>
                    <div className="space-y-2">
                      {issueList.map((issue, idx) => (
                        <div key={idx} className="rounded-lg border border-amber-200/50 bg-amber-50/40 p-3">
                          <div className="flex items-start gap-2">
                            <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-200">
                              <AlertCircle className="h-3 w-3 text-amber-700" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <p className="text-xs font-semibold text-amber-900 capitalize">{issue.type}</p>
                                <Badge
                                  variant="outline"
                                  className={
                                    issue.severity === "high" ? "border-red-200 bg-red-50/60 text-red-700" :
                                    issue.severity === "medium" ? "border-amber-200 bg-amber-50/60 text-amber-700" :
                                    "border-blue-200 bg-blue-50/60 text-blue-700"
                                  }
                                >
                                  {issue.severity}
                                </Badge>
                              </div>
                              <p className="mt-1 text-xs text-amber-800/90">{issue.text}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* AI recommendation */}
                    <div className="rounded-lg border border-emerald-200/50 bg-emerald-50/40 p-3">
                      <div className="flex items-start gap-2">
                        <Zap className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-semibold text-emerald-900">AI Suggestion</p>
                          <p className="mt-1 text-xs text-emerald-800/90">
                            Reframe "essential" proxy requirements as "preferred + equivalent experience considered."
                            This broadens your pool without compromising role fit.
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                )}

                {issueList.length === 0 && (
                  <CardContent className="flex items-center gap-2 py-4 text-sm text-emerald-700 bg-emerald-50/40">
                    <CheckCircle2 className="h-4 w-4 shrink-0" />
                    JD quality looks great — no issues flagged
                  </CardContent>
                )}
              </Card>
            ))
        )}
      </div>

      {/* Learning section */}
      <Card className="border-l-4 border-blue-500 bg-gradient-to-r from-blue-50/60 to-transparent">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <TrendingDown className="h-4 w-4 text-blue-600" /> Why JD Quality Matters
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>Poor-quality JDs are the #1 cause of invisible candidate pools. When you list proxy requirements (degrees, tools, exact experience) instead of actual capabilities, you exclude candidates who have the capability through different paths.</p>
          <p className="font-medium text-foreground">TrueMatch's JD analysis helps you: find and remove proxy language · clarify inflated seniority expectations · spot exclusionary phrasing · improve pool quality 30–60%.</p>
        </CardContent>
      </Card>
    </div>
  );
}
