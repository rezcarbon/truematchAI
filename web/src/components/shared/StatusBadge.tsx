import { Badge } from "@/components/ui/badge";
import type { GovernanceStatus } from "@/lib/types";

// Maps a backend-supplied status string to a badge variant. The status value
// itself is decided by the backend; this only chooses a color.
const statusVariant: Record<string, "success" | "warning" | "destructive" | "secondary"> = {
  pass: "success",
  review: "warning",
  fail: "destructive",
  met: "success",
  partial: "warning",
  gap: "destructive",
  active: "success",
  invited: "warning",
  suspended: "destructive",
  open: "success",
  paused: "warning",
  closed: "secondary",
};

export function StatusBadge({ status }: { status: GovernanceStatus | string }) {
  return (
    <Badge variant={statusVariant[status] ?? "secondary"} className="capitalize">
      {status}
    </Badge>
  );
}
