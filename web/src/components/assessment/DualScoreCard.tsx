import { Card, CardContent } from "@/components/ui/card";
import { ScoreGauge } from "@/components/shared/ScoreGauge";
import { ArrowRight, TrendingUp, TrendingDown } from "lucide-react";
import { formatDelta } from "@/lib/utils";

// The signature insight: Traditional ATS Score vs TrueMatch Capability Score
// shown side by side with the delta highlighted. All three numbers are
// supplied by the backend.
export function DualScoreCard({
  traditionalScore,
  capabilityScore,
  delta,
}: {
  traditionalScore: number;
  capabilityScore: number;
  delta: number;
}) {
  const positive = delta >= 0;
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-0">
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr]">
          <div className="flex flex-col items-center justify-center gap-3 p-8">
            <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Traditional ATS Score
            </span>
            <ScoreGauge score={traditionalScore} />
            <span className="text-xs text-muted-foreground">Keyword / JD match</span>
          </div>

          <div className="flex flex-col items-center justify-center gap-2 border-y bg-accent/40 px-8 py-6 md:border-x md:border-y-0">
            <span className="text-xs font-semibold uppercase tracking-wide text-accent-foreground">
              Delta
            </span>
            <div className="flex items-center gap-2">
              {positive ? (
                <TrendingUp className="h-7 w-7 text-success" />
              ) : (
                <TrendingDown className="h-7 w-7 text-destructive" />
              )}
              <span
                className={`text-4xl font-extrabold tabular-nums ${
                  positive ? "text-success" : "text-destructive"
                }`}
              >
                {formatDelta(delta)}
              </span>
            </div>
            <p className="max-w-[10rem] text-center text-xs text-muted-foreground">
              {positive
                ? "Capability exceeds the keyword match"
                : "Keyword match overstates capability"}
            </p>
          </div>

          <div className="flex flex-col items-center justify-center gap-3 p-8">
            <span className="text-xs font-semibold uppercase tracking-wide text-primary">
              TrueMatch Capability Score
            </span>
            <ScoreGauge score={capabilityScore} />
            <span className="text-xs text-muted-foreground">Demonstrated capability</span>
          </div>
        </div>
        <div className="flex items-center justify-center gap-2 border-t bg-muted/30 py-2 text-xs text-muted-foreground">
          ATS keyword view <ArrowRight className="h-3 w-3" /> capability view
        </div>
      </CardContent>
    </Card>
  );
}
