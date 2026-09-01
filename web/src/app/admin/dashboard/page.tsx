'use client';

import { PageHeader } from "@/components/shared/AppShell";
import { Card, CardContent } from "@/components/ui/card";
import { OutcomeAnalytics, type OutcomePoint } from "@/components/admin/OutcomeAnalytics";
import { GovernanceConfig } from "@/components/admin/GovernanceConfig";
import { DataSourceStats } from "@/components/shared/DataSourceStats";
import { ScraperHealthCard } from "@/components/shared/ScraperHealthCard";

const outcomes: OutcomePoint[] = [
  { month: "Jan", traditionalHires: 8, capabilityHires: 5 },
  { month: "Feb", traditionalHires: 7, capabilityHires: 9 },
  { month: "Mar", traditionalHires: 6, capabilityHires: 11 },
  { month: "Apr", traditionalHires: 5, capabilityHires: 13 },
  { month: "May", traditionalHires: 6, capabilityHires: 16 },
];

export default function AdminDashboard() {
  return (
    <div>
      <PageHeader title="Admin console" subtitle="Platform health, governance, and outcomes." />
      <div className="mb-6 grid gap-6 md:grid-cols-4">
        {[
          { label: "Assessments (30d)", value: "1,284" },
          { label: "Active recruiters", value: "37" },
          { label: "Avg. delta", value: "+18" },
          { label: "Open bias flags", value: "2" },
        ].map((s) => (
          <Card key={s.label}>
            <CardContent className="p-5">
              <p className="text-sm text-muted-foreground">{s.label}</p>
              <p className="mt-1 text-3xl font-bold">{s.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <OutcomeAnalytics data={outcomes} />
        <div className="space-y-6">
          <GovernanceConfig profileName="Standard Hiring Profile v3" status="pass" />
          <DataSourceStats
            jobsUploaded={342}
            jobsScraped={1156}
            activeScrapers={3}
            scraperErrors={0}
            uploadBatches={8}
          />
          <ScraperHealthCard
            scrapers={[
              { name: "USAJOBS", status: "active", lastRun: "2 hours ago", jobsFound: 156 },
              { name: "LinkedIn", status: "inactive", lastRun: "1 day ago", jobsFound: 23 },
              { name: "Indeed", status: "active", lastRun: "3 hours ago", jobsFound: 89 },
            ]}
            totalScrapers={6}
            activeScrapers={3}
            errorCount={0}
          />
        </div>
      </div>
    </div>
  );
}
