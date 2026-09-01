import { PageHeader } from "@/components/shared/AppShell";
import { ComplianceReport, type ComplianceItem } from "@/components/admin/ComplianceReport";
import { BiasReport, type BiasMetric } from "@/components/admin/BiasReport";

const items: ComplianceItem[] = [
  { area: "Data retention", status: "pass", detail: "Assessment artifacts retained within policy window." },
  { area: "Candidate consent", status: "pass", detail: "All active assessments have recorded consent." },
  { area: "Adverse-impact review", status: "review", detail: "One position pending quarterly review." },
  { area: "Explainability records", status: "pass", detail: "Narrative + gap rationale stored for every decision." },
];

const bias: BiasMetric[] = [
  { group: "Group A", selectionRate: 22 },
  { group: "Group B", selectionRate: 21 },
  { group: "Group C", selectionRate: 23 },
  { group: "Group D", selectionRate: 20 },
];

export default function CompliancePage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Compliance" subtitle="Governance, fairness, and regulatory posture." />
      <ComplianceReport items={items} />
      <BiasReport metrics={bias} />
    </div>
  );
}
