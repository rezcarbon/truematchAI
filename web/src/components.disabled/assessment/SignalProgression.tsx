import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight } from "lucide-react";

const MATCH_LABEL: Record<string, { label: string; variant: "default" | "secondary" | "warning" }> = {
  hidden_gem: { label: "Hidden gem", variant: "warning" },
  surfaced_strong_match: { label: "Surfaced strong match", variant: "default" },
  keyword_aligned: { label: "Keyword-aligned", variant: "secondary" },
};

function Bar({ label, score, hint, accent }: { label: string; score?: number; hint: string; accent: string }) {
  const v = typeof score === "number" ? score : 0;
  return (
    <div className="flex-1">
      <div className="mb-1 flex items-baseline justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</span>
        <span className="text-lg font-bold tabular-nums">{typeof score === "number" ? score : "—"}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div className={`h-full rounded-full ${accent}`} style={{ width: `${v}%` }} />
      </div>
      <p className="mt-1 text-[11px] text-muted-foreground">{hint}</p>
    </div>
  );
}

// The three independent signals, in the order they reveal a candidate:
// keyword (literal) -> semantic (conceptual) -> capability (evidence-reasoned).
export function SignalProgression({
  traditionalScore,
  semanticScore,
  capabilityScore,
  matchType,
}: {
  traditionalScore: number;
  semanticScore?: number;
  capabilityScore: number;
  matchType?: string;
}) {
  const m = matchType ? MATCH_LABEL[matchType] : undefined;
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
        <div>
          <CardTitle>Three-signal progression</CardTitle>
          <CardDescription>Keyword baseline → semantic concept match → demonstrated capability.</CardDescription>
        </div>
        {m && <Badge variant={m.variant}>{m.label}</Badge>}
      </CardHeader>
      <CardContent className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-end">
        <Bar label="Keyword" score={traditionalScore} hint="Literal JD-vs-CV term match (deterministic)" accent="bg-muted-foreground/50" />
        <ArrowRight className="mx-auto hidden h-4 w-4 shrink-0 self-center text-muted-foreground sm:block" />
        <Bar label="Semantic" score={semanticScore} hint="Concept-level match (embeddings)" accent="bg-amber-500/70" />
        <ArrowRight className="mx-auto hidden h-4 w-4 shrink-0 self-center text-muted-foreground sm:block" />
        <Bar label="Capability" score={capabilityScore} hint="Evidence-reasoned ability for the role" accent="bg-primary" />
      </CardContent>
    </Card>
  );
}
