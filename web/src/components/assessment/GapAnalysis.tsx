import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { CheckCircle2, AlertCircle, XCircle } from "lucide-react";
import type { GapItem } from "@/lib/types";

const icon = {
  met: <CheckCircle2 className="h-5 w-5 text-success" />,
  partial: <AlertCircle className="h-5 w-5 text-warning" />,
  gap: <XCircle className="h-5 w-5 text-destructive" />,
};

export function GapAnalysis({ gaps }: { gaps: GapItem[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Gap Analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {gaps.map((g, i) => (
          <div key={i} className="flex items-start gap-3 rounded-md border p-3">
            <div className="mt-0.5">{icon[g.status]}</div>
            <div className="flex-1">
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium">{g.area}</span>
                <StatusBadge status={g.status} />
              </div>
              <p className="text-sm text-muted-foreground">{g.detail}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
