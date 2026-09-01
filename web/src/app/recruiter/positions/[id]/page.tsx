import Link from "next/link";
import { PageHeader } from "@/components/shared/AppShell";
import { JDQualityCard } from "@/components/recruiter/JDQualityCard";
import { PipelineKanban } from "@/components/recruiter/PipelineKanban";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { LayoutList, Kanban, Plus } from "lucide-react";

export default async function PositionDetailPage({ params }: { params: { id: string } }) {
  const [positions, pipeline, jd] = await Promise.all([
    api.getPositions(),
    api.getPipeline(params.id),
    api.getPositionJD(params.id),
  ]);
  const p = positions.find((x) => x.id === params.id) ?? positions[0];

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <PageHeader
          title={p.title}
          subtitle={`${p.department} · ${p.location} · ${p.candidateCount} candidates`}
        />
        <div className="flex items-center gap-2 shrink-0 pt-1">
          <Button variant="outline" size="sm"><Kanban className="mr-1.5 h-4 w-4" /> Kanban</Button>
          <Link href={`/recruiter/positions/${params.id}?view=list`}>
            <Button variant="ghost" size="sm"><LayoutList className="mr-1.5 h-4 w-4" /> List</Button>
          </Link>
          <Button size="sm"><Plus className="mr-1.5 h-4 w-4" /> Add candidate</Button>
        </div>
      </div>

      {/* JD quality banner */}
      <JDQualityCard jd={jd} />

      {/* Kanban pipeline */}
      <div>
        <h2 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Pipeline — {pipeline.length} candidates
        </h2>
        <div className="overflow-x-auto pb-4">
          <PipelineKanban candidates={pipeline} />
        </div>
      </div>
    </div>
  );
}
