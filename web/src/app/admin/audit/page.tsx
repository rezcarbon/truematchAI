import { PageHeader } from "@/components/shared/AppShell";
import { AuditTrailViewer } from "@/components/admin/AuditTrailViewer";
import { api } from "@/lib/api";

export default async function AuditPage() {
  const entries = await api.getAudit();
  return (
    <div>
      <PageHeader title="Audit trail" subtitle="Immutable record of platform actions." />
      <AuditTrailViewer entries={entries} />
    </div>
  );
}
