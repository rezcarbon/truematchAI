import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatDelta } from "@/lib/utils";
import { TrendingUp, TrendingDown } from "lucide-react";
import type { PipelineCandidate } from "@/lib/types";

export function CandidateCard({ candidate }: { candidate: PipelineCandidate }) {
  const positive = candidate.delta >= 0;
  return (
    <Link href={`/recruiter/candidates/${candidate.id}`}>
      <Card className="transition-shadow hover:shadow-md">
        <CardContent className="flex items-center justify-between gap-4 p-4">
          <div className="min-w-0">
            <p className="truncate font-semibold">{candidate.name}</p>
            <p className="truncate text-sm text-muted-foreground">{candidate.appliedFor}</p>
            <div className="mt-2 flex items-center gap-2">
              <StatusBadge status={candidate.stage} />
              <StatusBadge status={candidate.governanceStatus} />
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-5 text-center">
            <div>
              <div className="text-lg font-bold tabular-nums text-muted-foreground">{candidate.traditionalScore}</div>
              <div className="text-[10px] uppercase text-muted-foreground">ATS</div>
            </div>
            <div>
              <div className="text-lg font-bold tabular-nums text-primary">{candidate.capabilityScore}</div>
              <div className="text-[10px] uppercase text-muted-foreground">Capability</div>
            </div>
            <div className={positive ? "text-success" : "text-destructive"}>
              <div className="flex items-center gap-1 text-lg font-bold tabular-nums">
                {positive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                {formatDelta(candidate.delta)}
              </div>
              <div className="text-[10px] uppercase text-muted-foreground">Delta</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
