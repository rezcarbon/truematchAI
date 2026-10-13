import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ScoreGauge } from "@/components/shared/ScoreGauge";
import { Badge } from "@/components/ui/badge";
import { Flag } from "lucide-react";
import type { JDQuality } from "@/lib/types";

const flagVariant: Record<string, "destructive" | "warning" | "secondary"> = {
  proxy: "warning",
  impossible: "destructive",
  ambiguous: "secondary",
  exclusionary: "destructive",
};

// JD quality score + proxy / impossible-requirement flags. All values from
// the backend's JD analysis.
export function JDQualityCard({ jd }: { jd: JDQuality }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Job Description Quality</CardTitle>
        <CardDescription>
          Surfaces proxy requirements, impossible asks, and ambiguity that can suppress strong applicants.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-6 md:flex-row md:items-center">
        <div className="flex flex-col items-center">
          <ScoreGauge score={jd.score} label="JD Quality" />
        </div>
        <div className="flex-1 space-y-2">
          {jd.flags.length === 0 ? (
            <p className="text-sm text-muted-foreground">No quality issues detected.</p>
          ) : (
            jd.flags.map((f) => (
              <div key={f.id} className="flex items-start gap-3 rounded-md border p-3">
                <Flag className="mt-0.5 h-4 w-4 text-muted-foreground" />
                <div className="flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium">{f.field}</span>
                    <Badge variant={flagVariant[f.type]} className="capitalize">
                      {f.type}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{f.message}</p>
                  {f.recommendation && (
                    <p className="mt-1 text-sm text-primary">
                      <span className="font-medium">Fix:</span> {f.recommendation}
                    </p>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
