import { PageHeader } from "@/components/shared/AppShell";
import { OutcomeAnalytics, type OutcomePoint } from "@/components/admin/OutcomeAnalytics";
import { BiasReport, type BiasMetric } from "@/components/admin/BiasReport";

const outcomes: OutcomePoint[] = [
  { month: "Jan", traditionalHires: 8, capabilityHires: 5 },
  { month: "Feb", traditionalHires: 7, capabilityHires: 9 },
  { month: "Mar", traditionalHires: 6, capabilityHires: 11 },
  { month: "Apr", traditionalHires: 5, capabilityHires: 13 },
  { month: "May", traditionalHires: 6, capabilityHires: 16 },
];

const bias: BiasMetric[] = [
  { group: "Group A", selectionRate: 22 },
  { group: "Group B", selectionRate: 21 },
  { group: "Group C", selectionRate: 23 },
  { group: "Group D", selectionRate: 20 },
];

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Analytics" subtitle="Outcomes and fairness over time." />
      <OutcomeAnalytics data={outcomes} />
      <BiasReport metrics={bias} />
    </div>
  );
}
