"use client";
import * as React from "react";
import { CandidateCard } from "./CandidateCard";
import { Button } from "@/components/ui/button";
import { ArrowUpDown } from "lucide-react";
import type { PipelineCandidate } from "@/lib/types";

type SortKey = "capabilityScore" | "traditionalScore" | "delta";

// Sortable pipeline. Sorting is a pure UI affordance over backend-supplied
// scores; it does not alter or compute any score.
export function CandidatePipeline({ candidates }: { candidates: PipelineCandidate[] }) {
  const [sortKey, setSortKey] = React.useState<SortKey>("capabilityScore");
  const [desc, setDesc] = React.useState(true);

  const sorted = React.useMemo(() => {
    const arr = [...candidates].sort((a, b) => a[sortKey] - b[sortKey]);
    return desc ? arr.reverse() : arr;
  }, [candidates, sortKey, desc]);

  const keys: { key: SortKey; label: string }[] = [
    { key: "capabilityScore", label: "Capability" },
    { key: "traditionalScore", label: "Traditional" },
    { key: "delta", label: "Delta" },
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-medium text-muted-foreground">Sort by</span>
        {keys.map((k) => (
          <Button
            key={k.key}
            size="sm"
            variant={sortKey === k.key ? "default" : "outline"}
            onClick={() => {
              if (sortKey === k.key) setDesc((d) => !d);
              else {
                setSortKey(k.key);
                setDesc(true);
              }
            }}
          >
            {k.label}
            {sortKey === k.key && <ArrowUpDown className="h-3 w-3" />}
          </Button>
        ))}
      </div>
      <div className="space-y-3">
        {sorted.map((c) => (
          <CandidateCard key={c.id} candidate={c} />
        ))}
      </div>
    </div>
  );
}
