import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Lightbulb } from "lucide-react";
import type { CounterRecommendation as CounterRec } from "@/lib/types";

// Shown when the traditional score is low but capability is high. The
// `triggered` flag and all copy come from the backend.
export function CounterRecommendation({ rec }: { rec: CounterRec }) {
  if (!rec.triggered) return null;
  return (
    <Card className="border-primary/40 bg-accent/40">
      <CardContent className="flex gap-4 p-6">
        <div className="mt-1">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
            <Lightbulb className="h-5 w-5 text-primary" />
          </div>
        </div>
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-primary">{rec.headline}</h3>
          <p className="leading-relaxed text-foreground">{rec.rationale}</p>
          {rec.suggestedRoles.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-1">
              <span className="text-sm font-medium text-muted-foreground">Consider for:</span>
              {rec.suggestedRoles.map((r) => (
                <Badge key={r} variant="outline">
                  {r}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
