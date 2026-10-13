import Link from "next/link";
'use client';
function cn(...inputs: any[]) {
  return twMerge(clsx(inputs));
}

// import { JDQualityCard } from "@/components/recruiter/JDQualityCard"; (needs manual conversion)
// import { PipelineKanban } from "@/components/recruiter/PipelineKanban"; (needs manual conversion)
// api removed - use fetch directly;
import { LayoutList, Kanban, Plus } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
    </div>
  );
}

function Button({ className, variant = "default", size = "default", ...props }: any) {
  const variants: any = { default: "bg-blue-600 text-white hover:bg-blue-700", outline: "border border-gray-300 bg-white hover:bg-gray-50", ghost: "hover:bg-gray-100" };
  const sizes: any = { default: "px-4 py-2", sm: "px-3 py-1 text-sm", lg: "px-6 py-3 text-lg" };
  return <button className={cn("inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none", variants[variant], sizes[size], className)} {...props} />;
}

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


