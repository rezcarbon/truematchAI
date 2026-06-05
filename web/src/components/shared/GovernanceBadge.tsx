import { CheckCircle2, AlertTriangle, XCircle, Shield } from "lucide-react";
import { cn } from "@/lib/utils";

type GovStatus = "pass" | "review" | "fail" | "ungoverned";

const CONFIG: Record<GovStatus, { icon: React.ElementType; classes: string; label: string }> = {
  pass:        { icon: CheckCircle2, classes: "bg-emerald-50 text-emerald-700 border-emerald-200", label: "Governed · All gates passed" },
  review:      { icon: AlertTriangle, classes: "bg-amber-50 text-amber-700 border-amber-200",   label: "Under review" },
  fail:        { icon: XCircle,      classes: "bg-red-50 text-red-700 border-red-200",           label: "Gate failed" },
  ungoverned:  { icon: Shield,       classes: "bg-slate-50 text-slate-500 border-slate-200",     label: "Ungoverned (config pending)" },
};

export function GovernanceBadge({
  status,
  label,
  size = "sm",
}: {
  status: GovStatus | string;
  label?: string;
  size?: "sm" | "lg";
}) {
  const cfg = CONFIG[(status as GovStatus) ?? "ungoverned"] ?? CONFIG.ungoverned;
  const Icon = cfg.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border font-medium",
        size === "lg" ? "px-3 py-1 text-sm" : "px-2 py-0.5 text-xs",
        cfg.classes
      )}
    >
      <Icon className={size === "lg" ? "h-4 w-4" : "h-3 w-3"} />
      {label ?? cfg.label}
    </span>
  );
}
