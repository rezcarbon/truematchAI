import { PageHeader } from "@/components/shared/AppShell";
import { GovernanceConfig } from "@/components/admin/GovernanceConfig";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function ConfigurationPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader title="Configuration" subtitle="Platform and governance settings." />
      <GovernanceConfig profileName="Standard Hiring Profile v3" status="pass" />
      <Card>
        <CardHeader>
          <CardTitle>Workspace settings</CardTitle>
          <CardDescription>Branding and notification preferences (editable here).</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-medium">Organization name</label>
            <input defaultValue="Acme Corp" className="w-full rounded-md border bg-background px-3 py-2 text-sm" />
          </div>
          <div className="flex items-center justify-between rounded-md border p-3">
            <div>
              <p className="text-sm font-medium">Email recruiters on new high-delta candidates</p>
              <p className="text-xs text-muted-foreground">Notifies when capability strongly exceeds keyword match.</p>
            </div>
            <input type="checkbox" defaultChecked className="h-4 w-4" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
