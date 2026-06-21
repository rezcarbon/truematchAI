"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ArrowRight } from "lucide-react";

// Reusable "capability gap" display — the signature TrueMatch visual.
// Leads with the gap between what an ATS sees (keyword) and real fit, shows the
// before→after legibility lift from Capability Translation, and (when supplied)
// the rigorous capability verdict as a constant anchor. Used on the candidate
// translation results page; the same component renders the recruiter view when
// a capability score is provided.
interface CapabilityGapProps {
  beforeKeyword: number;
  afterKeyword: number;
  beforeSemantic: number;
  afterSemantic: number;
  capability?: number | null; // the assessment verdict; omitted on translation-only views
  targetRole?: string | null;
}

function Bar({ before, after, anchor }: { before?: number; after: number; anchor?: boolean }) {
  const pct = (n: number) => `${Math.max(0, Math.min(100, n))}%`;
  return (
    <div className="relative mt-2 h-2 w-full rounded-full bg-muted">
      <div
        className="absolute inset-y-0 left-0 rounded-full bg-blue-500/90"
        style={{ width: pct(after) }}
      />
      {!anchor && before !== undefined && (
        <div
          className="absolute inset-y-[-3px] w-0.5 bg-foreground/40"
          style={{ left: `calc(${pct(before)} - 1px)` }}
          aria-hidden
        />
      )}
    </div>
  );
}

export function CapabilityGap({
  beforeKeyword,
  afterKeyword,
  beforeSemantic,
  afterSemantic,
  capability,
  targetRole,
}: CapabilityGapProps) {
  const delta = capability != null ? capability - beforeKeyword : null;

  const rows: Array<{ label: string; sub: string; before?: number; after: number; anchor?: boolean }> = [
    {
      label: "Auto-screen match",
      sub: "what the hiring software reads",
      before: beforeKeyword,
      after: afterKeyword,
    },
    {
      label: "Experience overlap",
      sub: "how well your background maps to the role",
      before: beforeSemantic,
      after: afterSemantic,
    },
  ];
  if (capability != null) {
    rows.push({
      label: "Capability verdict",
      sub: "our considered judgment of your real fit — unchanged, never inflated",
      after: capability,
      anchor: true,
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>What this role sees vs. what you can do</CardTitle>
        <CardDescription>
          {targetRole ? `${targetRole}. ` : ""}
          The auto-screen scored you{" "}
          <span className="font-medium text-foreground">{beforeKeyword}</span>
          {capability != null ? (
            <>
              . Our capability verdict is{" "}
              <span className="font-medium text-blue-600">{capability}</span> — far more than the
              filter admits.
            </>
          ) : (
            <>. After translation it reads {afterKeyword}.</>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {rows.map((r) => (
          <div key={r.label}>
            <div className="flex items-baseline justify-between gap-3">
              <div>
                <div className="text-sm font-medium">{r.label}</div>
                <div className="text-xs text-muted-foreground">{r.sub}</div>
              </div>
              {r.anchor ? (
                <div className="shrink-0 text-sm">
                  <span className="text-base font-medium text-blue-600">{r.after}</span>
                  <span className="text-muted-foreground"> / 100</span>
                </div>
              ) : (
                <div className="flex shrink-0 items-center gap-1.5 text-sm text-muted-foreground">
                  <span className="text-muted-foreground/70">{r.before}</span>
                  <ArrowRight className="h-3 w-3" />
                  <span className="font-medium text-foreground">{r.after}</span>
                </div>
              )}
            </div>
            <Bar before={r.before} after={r.after} anchor={r.anchor} />
          </div>
        ))}

        {delta != null && (
          <div className="rounded-md bg-blue-50 px-3 py-2 text-sm text-blue-800">
            <span className="font-medium">Hidden-gem signal: +{delta}.</span> Your capability ({capability})
            far exceeds what the auto-screen credits ({beforeKeyword}) — exactly the gap a conventional ATS misses.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
