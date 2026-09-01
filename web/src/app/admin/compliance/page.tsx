'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/AppShell';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Download } from 'lucide-react';
import { adminApi } from '@/lib/api-admin';
import { ComplianceReportResponse } from '@/types/admin';
import { formatDate } from '@/lib/utils';
import { ComplianceReport, type ComplianceItem } from '@/components/admin/ComplianceReport';
import { BiasReport, type BiasMetric } from '@/components/admin/BiasReport';

const statusColors = {
  pass: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  fail: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  review: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  pending: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
};

export default function CompliancePage() {
  const [report, setReport] = useState<ComplianceReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    fetchComplianceReport();
  }, []);

  const fetchComplianceReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminApi.getComplianceReport();
      setReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load compliance report');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      setIsExporting(true);
      const blob = await adminApi.exportComplianceReport('pdf');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `compliance-report-${new Date().toISOString()}.pdf`;
      a.click();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setIsExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <PageHeader title="Compliance" subtitle="Governance, fairness, and regulatory posture." />
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-200">
          {error}
          <button onClick={() => setError(null)} className="ml-2 underline">
            Dismiss
          </button>
        </div>
      </div>
    );
  }

  if (!report) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader title="Compliance" subtitle="Governance, fairness, and regulatory posture." />
        <Button onClick={handleExport} disabled={isExporting}>
          <Download className="mr-2 h-4 w-4" />
          {isExporting ? 'Exporting...' : 'Export Report'}
        </Button>
      </div>

      {/* Compliance Status Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Total Assessments</p>
            <p className="mt-2 text-3xl font-bold">{report.totalAssessments}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Governed</p>
            <p className="mt-2 text-3xl font-bold">{report.governedAssessments}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Bias Flags</p>
            <p className="mt-2 text-3xl font-bold">{report.biasFlagsRaised}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Status</p>
            <Badge className={statusColors[report.status] + ' mt-2'}>
              {report.status.toUpperCase()}
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Compliance Items */}
      <ComplianceReport items={report.items || []} />

      {/* Bias Metrics */}
      <BiasReport metrics={report.biasMetrics || []} />

      {/* Detailed Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-3">
            <div>
              <p className="text-sm text-muted-foreground">Counter-Recommendations</p>
              <p className="mt-2 text-2xl font-bold">{report.counterRecommendations}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {((report.counterRecommendations / report.totalAssessments) * 100).toFixed(1)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Overrides</p>
              <p className="mt-2 text-2xl font-bold">{report.overrideCount}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {((report.overrideCount / report.governedAssessments) * 100).toFixed(1)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Generated</p>
              <p className="mt-2 text-sm font-mono">{formatDate(report.generatedAt)}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
