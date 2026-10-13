import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { CapabilityComponent } from "@/lib/types";

// Renders the backend-generated narrative plus a breakdown of the
// capability components (label + score bar). Display only.
export function CapabilityNarrative({
  narrative,
  components,
}: {
  narrative: string;
  components: CapabilityComponent[];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Capability Narrative</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <p className="leading-relaxed text-foreground">{narrative}</p>
        <div className="space-y-3">
          {components.map((c) => (
            <div key={c.key}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="font-medium">{c.label}</span>
                <span className="tabular-nums text-muted-foreground">
                  {c.score} · weight {Math.round(c.weight * 100)}%
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary"
                  style={{ width: `${c.score}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
