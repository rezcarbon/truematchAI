"use client";

// ScoreTrio — the TrueMatch signature 3-signal display.
// Shows Traditional ATS → Semantic → Capability as a horizontal progression
// with delta chips and a match-type badge. Used above the fold on every
// candidate-facing recruiter screen.

import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus, Zap } from "lucide-react";

interface ScoreTrioProps {
  traditional: number;
  semantic?: number;
  capability: number;
  delta: number;
  matchType?: "hidden_gem" | "surfaced_strong_match" | "keyword_aligned";
  compact?: boolean; // pipeline card mode (smaller)
  showDeltaBar?: boolean;
}

const MATCH_CONFIG = {
  hidden_gem: {
    label: "Hidden gem",
    icon: Zap,
    bg: "bg-amber-50 border-amber-200",
    text: "text-amber-700",
    dot: "bg-amber-400",
  },
  surfaced_strong_match: {
    label: "Strong match",
    icon: TrendingUp,
    bg: "bg-emerald-50 border-emerald-200",
    text: "text-emerald-700",
    dot: "bg-emerald-400",
  },
  keyword_aligned: {
    label: "Keyword aligned",
    icon: Minus,
    bg: "bg-slate-50 border-slate-200",
    text: "text-slate-600",
    dot: "bg-slate-400",
  },
};

function scoreColor(s: number): string {
  if (s >= 70) return "text-emerald-600";
  if (s >= 50) return "text-amber-600";
  return "text-slate-500";
}

function DeltaChip({ delta }: { delta: number }) {
  const positive = delta >= 0;
  const Icon = positive ? TrendingUp : TrendingDown;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-xs font-semibold tabular-nums",
        positive
          ? "bg-emerald-50 text-emerald-700"
          : "bg-red-50 text-red-700"
      )}
    >
      <Icon className="h-3 w-3" />
      {positive ? "+" : ""}{delta}
    </span>
  );
}

function Signal({
  label,
  sublabel,
  score,
  compact,
}: {
  label: string;
  sublabel: string;
  score?: number;
  compact?: boolean;
}) {
  const barWidth = `${score ?? 0}%`;
  return (
    <div className={cn("flex flex-col gap-1", compact ? "min-w-[60px]" : "min-w-[80px] flex-1")}>
      <div className="flex items-baseline justify-between gap-1">
        <span className={cn("font-medium text-muted-foreground uppercase tracking-wide", compact ? "text-[9px]" : "text-[10px]")}>
          {label}
        </span>
        {score !== undefined && (
          <span className={cn("font-bold tabular-nums", compact ? "text-sm" : "text-lg", scoreColor(score))}>
            {score}
          </span>
        )}
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={cn("h-full rounded-full transition-all", score !== undefined && score >= 70 ? "bg-emerald-500" : score !== undefined && score >= 50 ? "bg-amber-400" : "bg-slate-300")}
          style={{ width: barWidth }}
        />
      </div>
      {!compact && (
        <span className="text-[9px] text-muted-foreground leading-tight">{sublabel}</span>
      )}
    </div>
  );
}

export function ScoreTrio({
  traditional,
  semantic,
  capability,
  delta,
  matchType,
  compact = false,
}: ScoreTrioProps) {
  const match = matchType ? MATCH_CONFIG[matchType] : null;
  const MatchIcon = match?.icon;

  return (
    <div className="space-y-2">
      {/* Signals */}
      <div className={cn("flex items-end gap-2", compact ? "gap-1.5" : "gap-3")}>
        <Signal label="ATS" sublabel="Keyword match" score={traditional} compact={compact} />
        <span className="mb-2 text-muted-foreground/40 text-xs">→</span>
        <Signal label="Sem" sublabel="Concept match" score={semantic} compact={compact} />
        <span className="mb-2 text-muted-foreground/40 text-xs">→</span>
        <Signal label="Cap" sublabel="Demonstrated ability" score={capability} compact={compact} />
        <div className="mb-1 flex flex-col items-end gap-1">
          <DeltaChip delta={delta} />
          {match && !compact && (
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium",
                match.bg,
                match.text
              )}
            >
              {MatchIcon && <MatchIcon className="h-3 w-3" />}
              {match.label}
            </span>
          )}
        </div>
      </div>

      {/* Compact match badge */}
      {match && compact && (
        <div className="flex items-center gap-1">
          <span className={cn("h-1.5 w-1.5 rounded-full", match.dot)} />
          <span className={cn("text-[9px] font-medium", match.text)}>{match.label}</span>
        </div>
      )}
    </div>
  );
}
