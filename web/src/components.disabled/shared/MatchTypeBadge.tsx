import { Zap, TrendingUp, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

type MatchType = "hidden_gem" | "surfaced_strong_match" | "keyword_aligned";

const CONFIG: Record<MatchType, { label: string; classes: string; icon: React.ElementType }> = {
  hidden_gem: {
    label: "Hidden gem",
    classes: "bg-amber-50 border border-amber-200 text-amber-700",
    icon: Zap,
  },
  surfaced_strong_match: {
    label: "Strong match",
    classes: "bg-emerald-50 border border-emerald-200 text-emerald-700",
    icon: TrendingUp,
  },
  keyword_aligned: {
    label: "Keyword aligned",
    classes: "bg-slate-50 border border-slate-200 text-slate-600",
    icon: Minus,
  },
};

export function MatchTypeBadge({ type, size = "sm" }: { type?: MatchType | string; size?: "sm" | "xs" }) {
  if (!type || !CONFIG[type as MatchType]) return null;
  const { label, classes, icon: Icon } = CONFIG[type as MatchType];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full font-medium",
        size === "xs" ? "px-1.5 py-0.5 text-[9px]" : "px-2 py-0.5 text-xs",
        classes
      )}
    >
      <Icon className={size === "xs" ? "h-2.5 w-2.5" : "h-3 w-3"} />
      {label}
    </span>
  );
}
