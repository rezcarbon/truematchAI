import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight } from "lucide-react";
import type { Substitution } from "@/lib/types";

const strengthVariant: Record<Substitution["strength"], "default" | "secondary" | "warning"> = {
  HIGH: "default",
  MEDIUM: "secondary",
  WEAK: "warning",
};

// Pillar 6: shows where a candidate lacks a literal credential but has alternate
// evidence of the underlying capability — the engine's "no degree, BUT X" reasoning.
export function SubstitutionPanel({ substitutions }: { substitutions?: Substitution[] }) {
  if (!substitutions || substitutions.length === 0) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Credential substitutions</CardTitle>
        <CardDescription>
          Where a required credential is missing but the underlying capability is evidenced.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {substitutions.map((s, i) => (
          <div key={i} className="rounded-md border p-3">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-sm font-medium">
                <span className="text-muted-foreground line-through">{s.requirement}</span>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
                <span>{s.underlyingCapability}</span>
              </div>
              <Badge variant={strengthVariant[s.strength]}>{s.strength}</Badge>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">{s.rationale}</p>
            {s.alternateEvidence && s.alternateEvidence.length > 0 && (
              <ul className="mt-1 list-disc pl-5 text-sm text-muted-foreground">
                {s.alternateEvidence.map((e, j) => (
                  <li key={j}>{e}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
