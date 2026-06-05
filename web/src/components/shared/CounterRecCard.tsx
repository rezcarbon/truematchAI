"use client";
import { Zap, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface Props {
  headline: string;
  rationale: string;
  suggestedRoles?: string[];
  compact?: boolean;
}

export function CounterRecCard({ headline, rationale, suggestedRoles, compact }: Props) {
  const [open, setOpen] = useState(!compact);
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50/60">
      <button
        onClick={() => compact && setOpen((v) => !v)}
        className={cn(
          "flex w-full items-start gap-3 p-4 text-left",
          compact && "cursor-pointer hover:bg-amber-50"
        )}
      >
        <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-amber-100">
          <Zap className="h-4 w-4 text-amber-600" />
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-amber-900">{headline}</p>
          {open && (
            <p className="mt-1.5 text-sm leading-relaxed text-amber-800/90">{rationale}</p>
          )}
          {open && suggestedRoles && suggestedRoles.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {suggestedRoles.map((r) => (
                <span key={r} className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
                  {r}
                </span>
              ))}
            </div>
          )}
        </div>
        {compact && (
          <span className="ml-2 mt-0.5 text-amber-500">
            {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </span>
        )}
      </button>
    </div>
  );
}
