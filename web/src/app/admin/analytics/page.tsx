'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/AppShell';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, TrendingUp } from 'lucide-react';
import { adminApi } from '@/lib/api-admin';
import { AnalyticsResponse } from '@/types/admin';
import Link from 'next/link';

export default function AnalyticsDashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await adminApi.getAnalytics('month');
      setAnalytics(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Analytics"
        subtitle="Overview of all platform analytics and insights"
      />

      {/* Error Display */}
      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-200">
          {error}
          <button onClick={() => setError(null)} className="ml-2 underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center p-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Analytics Cards Grid */}
      {!loading && analytics && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {/* Pipeline Analytics */}
          <Link href="/admin/analytics/pipeline">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Pipeline Analytics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm text-muted-foreground">Total Assessments</p>
                  <p className="text-2xl font-bold">
                    {analytics.pipeline?.reduce((sum, m) => sum + m.assessmentsCreated, 0) || 0}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Completion Rate</p>
                  <p className="text-2xl font-bold">
                    {(analytics.pipeline?.reduce((sum, m) => sum + m.conversionRate, 0) || 0) / (analytics.pipeline?.length || 1)}%
                  </p>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Sources Analytics */}
          <Link href="/admin/analytics/sources">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Source Performance
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm text-muted-foreground">Active Sources</p>
                  <p className="text-2xl font-bold">{analytics.sources?.length || 0}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Jobs Ingested</p>
                  <p className="text-2xl font-bold">
                    {analytics.sources?.reduce((sum, s) => sum + s.jobsIngested, 0) || 0}
                  </p>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Three Signal Analytics */}
          <Link href="/admin/analytics/three-signal">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Three Signal Metrics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm text-muted-foreground">Accuracy Score</p>
                  <p className="text-2xl font-bold">{analytics.threeSignal?.accuracy}%</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Override Rate</p>
                  <p className="text-2xl font-bold">{analytics.threeSignal?.overrideRate}%</p>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Recruiter Performance */}
          <Link href="/admin/analytics/recruiter-performance">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Recruiter Performance
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm text-muted-foreground">Top Recruiters</p>
                  <p className="text-2xl font-bold">{analytics.topRecruiters?.length || 0}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Avg Delta Score</p>
                  <p className="text-2xl font-bold">
                    {(analytics.topRecruiters?.reduce((sum, r) => sum + r.averageDelta, 0) || 0) / (analytics.topRecruiters?.length || 1)}
                  </p>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* DEI Analytics */}
          <Link href="/admin/analytics/dei">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  DEI Metrics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  Diversity, Equity & Inclusion metrics and bias analysis
                </p>
                <Button variant="outline" className="w-full" size="sm">
                  View Details
                </Button>
              </CardContent>
            </Card>
          </Link>
        </div>
      )}
    </div>
  );
}
