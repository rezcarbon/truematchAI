"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// Recruiter-facing ranked matrix: one row per candidate (or role), each showing
// the gap between the ATS keyword score and the capability verdict — ranked by
// that gap so hidden gems rise to the top. The recruiter mirror of the
// candidate CapabilityGap.
export interface GapMatrixRow {
  id?: string;
  label: string;
  sublabel?: string;
  keyword: number; // ATS / traditional
  capability: number; // verdict
  verdict?: "hidden_gem" | "surfaced_strong_match" | "keyword_aligned" | string;
}

const VERDICT: Record<string, { text: string; variant: "success" | "secondary" | "outline" }> = {
  hidden_gem: { text: "Hidden gem", variant: "success" },
  surfaced_strong_match: { text: "Strong match", variant: "secondary" },
  keyword_aligned: { text: "Keyword-aligned", variant: "outline" },
};

export function GapMatrix({
  rows,
  title = "Capability gap — ranked",
  description = "Grey = ATS keyword score · blue = capability verdict · shaded span = what the ATS misses.",
}: {
  rows: GapMatrixRow[];
  title?: string;
  description?: string;
}) {
  const pct = (n: number) => `${Math.max(0, Math.min(100, n))}%`;
  const sorted = [...rows].sort(
    (a, b) => b.capability - b.keyword - (a.capability - a.keyword),
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {sorted.map((r) => {
          const gap = r.capability - r.keyword;
          const v = r.verdict ? VERDICT[r.verdict] : undefined;
          return (
            <div key={r.id ?? r.label} className="border-b pb-3 last:border-0 last:pb-0">
              <div className="flex items-baseline justify-between gap-3">
                <div className="text-sm font-medium">
                  {r.label}
                  {r.sublabel && (
                    <span className="ml-2 text-xs font-normal text-muted-foreground">{r.sublabel}</span>
                  )}
                </div>
                <div className="flex shrink-0 items-center gap-2 text-xs text-muted-foreground">
                  <span>
                    ATS <span className="font-medium text-foreground">{r.keyword}</span>
                  </span>
                  <span>·</span>
                  <span>
                    cap <span className="font-medium text-blue-600">{r.capability}</span>
                  </span>
                  <span className="text-green-600">{gap >= 0 ? `+${gap}` : gap}</span>
                  {v && <Badge variant={v.variant}>{v.text}</Badge>}
                </div>
              </div>
              <div className="relative mt-2 h-2 w-full rounded-full bg-muted">
                <div
                  className="absolute inset-y-0 rounded-full bg-blue-500/30"
                  style={{ left: pct(r.keyword), width: pct(Math.max(0, gap)) }}
                />
                <div
                  className="absolute inset-y-[-2px] h-3 w-3 rounded-full border-2 border-background bg-muted-foreground"
                  style={{ left: `calc(${pct(r.keyword)} - 6px)` }}
                  aria-hidden
                />
                <div
                  className="absolute inset-y-[-2px] h-3 w-3 rounded-full border-2 border-background bg-blue-500"
                  style={{ left: `calc(${pct(r.capability)} - 6px)` }}
                  aria-hidden
                />
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
