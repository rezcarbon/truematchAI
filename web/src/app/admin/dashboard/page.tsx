'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from "@/components/shared/AppShell";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2 } from 'lucide-react';
import { OutcomeAnalytics, type OutcomePoint } from "@/components/admin/OutcomeAnalytics";
import { GovernanceConfig } from "@/components/admin/GovernanceConfig";
import { DataSourceStats } from "@/components/shared/DataSourceStats";
import { ScraperHealthCard } from "@/components/shared/ScraperHealthCard";
import { adminApi } from '@/lib/api-admin';
import { AnalyticsResponse } from '@/types/admin';

const defaultOutcomes: OutcomePoint[] = [
  { month: "Jan", traditionalHires: 8, capabilityHires: 5 },
  { month: "Feb", traditionalHires: 7, capabilityHires: 9 },
  { month: "Mar", traditionalHires: 6, capabilityHires: 11 },
  { month: "Apr", traditionalHires: 5, capabilityHires: 13 },
  { month: "May", traditionalHires: 6, capabilityHires: 16 },
];

export default function AdminDashboard() {
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const data = await adminApi.getAnalytics('month');
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Admin console" subtitle="Platform health, governance, and outcomes." />
      {error && (
        <div className="mb-6 rounded-lg bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-200">
          {error}
          <button onClick={() => setError(null)} className="ml-2 underline">
            Dismiss
          </button>
        </div>
      )}
      <div className="mb-6 grid gap-6 md:grid-cols-4">
        {[
          { label: "Assessments (30d)", value: analytics?.totalCount?.toString() || "1,284" },
          { label: "Active recruiters", value: analytics?.activeCount?.toString() || "37" },
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
        <OutcomeAnalytics data={defaultOutcomes} />
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
