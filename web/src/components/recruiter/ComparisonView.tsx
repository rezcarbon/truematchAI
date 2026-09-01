import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScoreGauge } from "@/components/shared/ScoreGauge";
import { formatDelta } from "@/lib/utils";
import type { PipelineCandidate } from "@/lib/types";

// Side-by-side comparison of selected candidates. Display only.
export function ComparisonView({ candidates }: { candidates: PipelineCandidate[] }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {candidates.map((c) => (
        <Card key={c.id}>
          <CardHeader>
            <CardTitle>{c.name}</CardTitle>
            <p className="text-sm text-muted-foreground">{c.appliedFor}</p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-around">
              <ScoreGauge score={c.traditionalScore} label="ATS" size={90} />
              <ScoreGauge score={c.capabilityScore} label="Capability" size={90} />
            </div>
            <div className="rounded-md border bg-accent/40 py-2 text-center">
              <span className="text-sm text-muted-foreground">Delta </span>
              <span className={`font-bold ${c.delta >= 0 ? "text-success" : "text-destructive"}`}>
                {formatDelta(c.delta)}
              </span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
