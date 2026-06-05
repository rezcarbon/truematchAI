import Link from "next/link";
import { PageHeader } from "@/components/shared/AppShell";
import { Card, CardContent } from "@/components/ui/card";
import { formatDelta, formatDate } from "@/lib/utils";
import { mockAssessment } from "@/lib/mock";

// Illustrative history list derived from the mock assessment.
const rows = [
  mockAssessment,
  { ...mockAssessment, id: "asm_demo_002", positionTitle: "Platform Engineer", traditionalScore: 58, capabilityScore: { ...mockAssessment.capabilityScore, overall: 81 }, delta: 23, createdAt: "2026-04-10T09:00:00Z" },
  { ...mockAssessment, id: "asm_demo_003", positionTitle: "Staff Engineer", traditionalScore: 49, capabilityScore: { ...mockAssessment.capabilityScore, overall: 74 }, delta: 25, createdAt: "2026-03-02T09:00:00Z" },
];

export default function HistoryPage() {
  return (
    <div>
      <PageHeader title="Assessment history" subtitle="Every assessment you've received." />
      <div className="space-y-3">
        {rows.map((a) => (
          <Link key={a.id} href={`/candidate/assessment/${a.id}`}>
            <Card className="transition-shadow hover:shadow-md">
              <CardContent className="flex items-center justify-between p-4">
                <div>
                  <p className="font-medium">{a.positionTitle}</p>
                  <p className="text-sm text-muted-foreground">{formatDate(a.createdAt)}</p>
                </div>
                <div className="flex items-center gap-6 text-center text-sm">
                  <div><div className="font-bold text-muted-foreground">{a.traditionalScore}</div><div className="text-[10px] uppercase text-muted-foreground">ATS</div></div>
                  <div><div className="font-bold text-primary">{a.capabilityScore.overall}</div><div className="text-[10px] uppercase text-muted-foreground">Capability</div></div>
                  <div><div className={`font-bold ${a.delta >= 0 ? "text-success" : "text-destructive"}`}>{formatDelta(a.delta)}</div><div className="text-[10px] uppercase text-muted-foreground">Delta</div></div>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
