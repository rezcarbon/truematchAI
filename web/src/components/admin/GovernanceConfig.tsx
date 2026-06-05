import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Lock } from "lucide-react";

// Admin view of the active governance profile. This panel is INFORMATIONAL:
// the governance policy and any thresholds live and are enforced entirely in
// the backend. The web client never holds, computes, or edits threshold
// values — it only displays the named profile and its backend-reported state.
export function GovernanceConfig({
  profileName,
  status,
}: {
  profileName: string;
  status: "pass" | "review" | "fail";
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lock className="h-5 w-5 text-muted-foreground" />
          Governance Profile
        </CardTitle>
        <CardDescription>
          The active governance policy is managed and enforced server-side. This view is read-only.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between rounded-md border p-4">
          <div>
            <p className="font-medium">Active profile</p>
            <p className="text-sm text-muted-foreground">{profileName}</p>
          </div>
          <StatusBadge status={status} />
        </div>
        <div className="rounded-md border bg-muted/30 p-4 text-sm text-muted-foreground">
          To request a change to the governance profile, contact the platform operations team.
          Policy parameters are not exposed to or editable from the web console.
        </div>
      </CardContent>
    </Card>
  );
}
