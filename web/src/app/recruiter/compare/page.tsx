'use client';

export const dynamic = 'force-dynamic';

import { useState } from "react";
import Link from "next/link";
import type { PipelineCandidate } from "@/lib/types";
import { PageHeader } from "@/components/shared/AppShell";
import { ScoreTrio } from "@/components/shared/ScoreTrio";
import { MatchTypeBadge } from "@/components/shared/MatchTypeBadge";
import { GovernanceBadge } from "@/components/shared/GovernanceBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { mockPipeline } from "@/lib/mock";
import {
  X, ArrowRight, Award, TrendingUp, Users
} from "lucide-react";

export default function ComparePage(): React.ReactElement {
  const pipeline = mockPipeline;

  return (
    <CompareContent candidates={pipeline} />
  );
}

function CompareContent({ candidates }: { candidates: PipelineCandidate[] }): React.ReactElement {
  const [selected, setSelected] = useState<PipelineCandidate[]>(candidates.slice(0, 2));

  const toggleCandidate = (candidate: PipelineCandidate): void => {
    if (selected.find((c) => c.id === candidate.id)) {
      setSelected(selected.filter((c) => c.id !== candidate.id));
    } else if (selected.length < 4) {
      setSelected([...selected, candidate]);
    }
  };

  const unselected = candidates.filter((c) => !selected.find((s) => s.id === c.id));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Compare Candidates"
        subtitle="Select 2–4 candidates to compare scores, fit, and governance across roles."
      />

      {/* Selection sidebar + comparison grid */}
      <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
        {/* Selection panel */}
        <Card className="h-fit">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Select to Compare</CardTitle>
            <p className="text-[11px] text-muted-foreground">{selected.length}/4 selected</p>
          </CardHeader>
          <CardContent className="space-y-2 pb-3">
            <div className="max-h-[500px] space-y-1.5 overflow-y-auto">
              {unselected.length === 0 ? (
                <p className="py-4 text-center text-xs text-muted-foreground">
                  {selected.length === 4 ? "Max candidates selected" : "No more candidates"}
                </p>
              ) : (
                unselected.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => toggleCandidate(c)}
                    className="w-full rounded-lg border-2 border-transparent bg-muted/50 p-2 text-left transition-all hover:border-primary/50 hover:bg-accent"
                  >
                    <p className="text-xs font-semibold truncate">{c.name}</p>
                    <p className="text-[10px] text-muted-foreground truncate">{c.appliedFor}</p>
                    <div className="mt-1.5 flex items-center gap-1">
                      <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-[9px] font-bold text-primary">
                        {Math.round(c.delta)}
                      </span>
                      <span className="text-[10px] font-medium">Δ{c.delta >= 0 ? "+" : ""}{c.delta}</span>
                    </div>
                  </button>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Comparison grid */}
        <div className="space-y-4">
          {selected.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Users className="mb-3 h-12 w-12 text-muted-foreground/50" />
                <p className="text-sm font-medium">No candidates selected</p>
                <p className="mt-1 text-xs text-muted-foreground">Choose candidates from the left to compare</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {selected.map((c) => (
                <Card key={c.id} className="relative">
                  {/* Remove button */}
                  <button
                    onClick={() => toggleCandidate(c)}
                    className="absolute right-2 top-2 rounded-lg bg-muted p-1 text-muted-foreground transition-all hover:bg-destructive/20 hover:text-destructive"
                  >
                    <X className="h-4 w-4" />
                  </button>

                  <CardHeader className="pb-3 pr-8">
                    <div>
                      <CardTitle className="text-base">{c.name}</CardTitle>
                      <p className="text-xs text-muted-foreground">{c.appliedFor}</p>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4 pb-3">
                    {/* 3-Signal score */}
                    <div className="space-y-2">
                      <p className="text-xs font-semibold text-muted-foreground">Three-Signal Score</p>
                      <ScoreTrio
                        traditional={c.traditionalScore}
                        capability={c.capabilityScore}
                        delta={c.delta}
                        compact
                      />
                    </div>

                    {/* Match type badge */}
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground mb-1.5">Match Type</p>
                      <MatchTypeBadge type={c.matchType} size="sm" />
                    </div>

                    {/* Governance status */}
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground mb-1.5">Governance</p>
                      <GovernanceBadge status={c.governanceStatus} size="sm" />
                    </div>

                    {/* Stage badge */}
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground mb-1.5">Stage</p>
                      <Badge variant="outline" className="capitalize">{c.stage}</Badge>
                    </div>

                    {/* Quick metrics */}
                    <div className="grid grid-cols-2 gap-2 rounded-lg bg-muted/40 p-2">
                      <div>
                        <p className="text-[9px] text-muted-foreground font-medium">ATS</p>
                        <p className="text-sm font-bold">{c.traditionalScore}</p>
                      </div>
                      <div>
                        <p className="text-[9px] text-muted-foreground font-medium">Cap</p>
                        <p className="text-sm font-bold text-primary">{c.capabilityScore}</p>
                      </div>
                    </div>

                    {/* View profile button */}
                    <Link href={`/recruiter/candidates/${c.id}`}>
                      <Button variant="outline" size="sm" className="w-full text-xs">
                        View Profile <ArrowRight className="ml-1 h-3 w-3" />
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Comparison insights */}
          {selected.length >= 2 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Award className="h-4 w-4 text-primary" /> Comparison Insights
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {(() => {
                  const byDelta = [...selected].sort((a, b) => b.delta - a.delta);
                  const bestFit = byDelta[0];
                  const avgCapability = Math.round(selected.reduce((sum, c) => sum + c.capabilityScore, 0) / selected.length);

                  return (
                    <>
                      <div className="rounded-lg border-l-4 border-emerald-500 bg-emerald-50/60 p-3">
                        <p className="text-xs font-semibold text-emerald-900">Strongest fit by capability</p>
                        <p className="mt-0.5 text-sm font-bold text-emerald-700">{bestFit.name}</p>
                        <p className="mt-1 text-[11px] text-emerald-800/80">Δ{bestFit.delta >= 0 ? "+" : ""}{bestFit.delta} over traditional match</p>
                      </div>

                      <div className="rounded-lg border-l-4 border-blue-500 bg-blue-50/60 p-3">
                        <p className="text-xs font-semibold text-blue-900">Pool capability average</p>
                        <p className="mt-0.5 text-sm font-bold text-blue-700">{avgCapability}/100</p>
                        <p className="mt-1 text-[11px] text-blue-800/80">across {selected.length} candidates</p>
                      </div>

                      {selected.some((c) => c.counterRecommendation?.triggered) && (
                        <div className="rounded-lg border-l-4 border-amber-500 bg-amber-50/60 p-3">
                          <p className="text-xs font-semibold text-amber-900">Hidden gems detected</p>
                          <p className="mt-1 text-[11px] text-amber-800/80">
                            {selected.filter((c) => c.counterRecommendation?.triggered).length} candidate(s) surfaced due to capability outliers
                          </p>
                        </div>
                      )}
                    </>
                  );
                })()}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
