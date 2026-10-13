import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";
import type { DecisionRecord } from "@/lib/types";

// Tracks recruiter decisions and highlights overrides of the assessment
// recommendation for governance/compliance visibility.
export function OverrideTracker({ decisions }: { decisions: DecisionRecord[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Decision &amp; Override Log</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="p-3 font-medium">Candidate</th>
                <th className="p-3 font-medium">Position</th>
                <th className="p-3 font-medium">Recruiter</th>
                <th className="p-3 font-medium">ATS / Cap</th>
                <th className="p-3 font-medium">Decision</th>
                <th className="p-3 font-medium">Override</th>
                <th className="p-3 font-medium">When</th>
              </tr>
            </thead>
            <tbody>
              {decisions.map((d) => (
                <tr key={d.id} className="border-b last:border-0">
                  <td className="p-3 font-medium">{d.candidateName}</td>
                  <td className="p-3 text-muted-foreground">{d.positionTitle}</td>
                  <td className="p-3 text-muted-foreground">{d.recruiter}</td>
                  <td className="p-3 tabular-nums">
                    {d.traditionalScore} / <span className="text-primary">{d.capabilityScore}</span>
                  </td>
                  <td className="p-3">
                    <StatusBadge status={d.decision === "advance" ? "pass" : d.decision === "reject" ? "fail" : "review"} />
                  </td>
                  <td className="p-3">
                    {d.overrodeRecommendation ? (
                      <Badge variant="warning">Override</Badge>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="p-3 text-muted-foreground">{formatDate(d.timestamp)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
