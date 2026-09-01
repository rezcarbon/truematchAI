'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/AppShell';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, Download } from 'lucide-react';
import { adminApi } from '@/lib/api-admin';
import { AnalyticsResponse, PipelineMetric } from '@/types/admin';
import { formatDate } from '@/lib/utils';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';

export default function PipelineAnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [period, setPeriod] = useState<'day' | 'week' | 'month'>('month');

  useEffect(() => {
    fetchAnalytics();
  }, [period]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await adminApi.getPipelineAnalytics(
        startDate || undefined,
        endDate || undefined
      );
      setAnalytics(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load pipeline analytics');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      setIsExporting(true);
      const blob = await adminApi.exportComplianceReport('csv');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `pipeline-analytics-${new Date().toISOString()}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setIsExporting(false);
    }
  };

  const handleDateRangeSubmit = () => {
    fetchAnalytics();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="Pipeline Analytics"
          subtitle="Monitor hiring funnel metrics and performance"
        />
        <Button onClick={handleExport} disabled={isExporting}>
          <Download className="mr-2 h-4 w-4" />
          {isExporting ? 'Exporting...' : 'Export'}
        </Button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-200">
          {error}
          <button onClick={() => setError(null)} className="ml-2 underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Period</label>
              <Select value={period} onValueChange={(v) => setPeriod(v as any)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="day">Daily</SelectItem>
                  <SelectItem value="week">Weekly</SelectItem>
                  <SelectItem value="month">Monthly</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Start Date</label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">End Date</label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
            <div className="flex items-end">
              <Button onClick={handleDateRangeSubmit} className="w-full">
                Apply
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center p-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Empty State */}
      {!loading && !analytics && (
        <Card>
          <CardContent className="p-8 text-center text-muted-foreground">
            No analytics data available
          </CardContent>
        </Card>
      )}

      {/* Metrics Display */}
      {!loading && analytics && (
        <>
          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Total Assessments Created</p>
                  <p className="text-3xl font-bold">
                    {analytics.pipeline?.reduce((sum, m: PipelineMetric) => sum + m.assessmentsCreated, 0) || 0}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Completed</p>
                  <p className="text-3xl font-bold">
                    {analytics.pipeline?.reduce((sum: number, m: PipelineMetric) => sum + m.assessmentsCompleted, 0) || 0}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Passed</p>
                  <p className="text-3xl font-bold">
                    {analytics.pipeline?.reduce((sum: number, m: PipelineMetric) => sum + m.assessmentsPassed, 0) || 0}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Avg Conversion</p>
                  <p className="text-3xl font-bold">
                    {(analytics.pipeline?.reduce((sum: number, m: PipelineMetric) => sum + m.conversionRate, 0) || 0) / (analytics.pipeline?.length || 1)}%
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Pipeline Metrics Table */}
          <Card>
            <CardHeader>
              <CardTitle>Pipeline Metrics by Period</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b bg-muted/50">
                    <tr>
                      <th className="px-6 py-3 text-left font-semibold">Period</th>
                      <th className="px-6 py-3 text-left font-semibold">Created</th>
                      <th className="px-6 py-3 text-left font-semibold">Completed</th>
                      <th className="px-6 py-3 text-left font-semibold">Passed</th>
                      <th className="px-6 py-3 text-left font-semibold">Conversion Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analytics.pipeline?.map((metric: PipelineMetric) => (
                      <tr key={metric.month} className="border-b hover:bg-muted/30">
                        <td className="px-6 py-3 font-medium">{metric.month}</td>
                        <td className="px-6 py-3">{metric.assessmentsCreated}</td>
                        <td className="px-6 py-3">{metric.assessmentsCompleted}</td>
                        <td className="px-6 py-3">{metric.assessmentsPassed}</td>
                        <td className="px-6 py-3">
                          <Badge variant="secondary">{metric.conversionRate}%</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Funnel View */}
          <Card>
            <CardHeader>
              <CardTitle>Conversion Funnel</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {analytics.pipeline?.map((metric: PipelineMetric) => {
                const maxCreated = Math.max(...(analytics.pipeline?.map((m: PipelineMetric) => m.assessmentsCreated) || [1]));
                return (
                  <div key={metric.month} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium">{metric.month}</span>
                      <span className="text-muted-foreground">{metric.conversionRate}% conversion</span>
                    </div>
                    <div className="space-y-1">
                      <div className="flex gap-2 text-xs">
                        <span className="min-w-20">Created</span>
                        <div className="flex-1 bg-blue-200 rounded h-6 flex items-center px-2">
                          {metric.assessmentsCreated}
                        </div>
                      </div>
                      <div className="flex gap-2 text-xs">
                        <span className="min-w-20">Completed</span>
                        <div
                          className="bg-green-200 rounded h-6 flex items-center px-2"
                          style={{
                            width: `${(metric.assessmentsCompleted / metric.assessmentsCreated) * 100}%`,
                          }}
                        >
                          {metric.assessmentsCompleted}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
