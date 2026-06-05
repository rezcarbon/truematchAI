'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2 } from 'lucide-react';
import { useToast } from '@/components/providers/ToastProvider';

interface StageMetrics {
  stage: string;
  count: number;
  averageDaysInStage: number;
  medianDaysInStage: number;
}

interface Analytics {
  positionId: string;
  totalApplications: number;
  byStage: StageMetrics[];
  averageTimeToHire: number;
}

const STAGE_LABELS: Record<string, string> = {
  applied: '📥 Applied',
  phone_screen: '☎️ Phone Screen',
  technical: '⚙️ Technical',
  onsite: '🏢 On-site',
  offer: '💼 Offer',
  hired: '✅ Hired',
  rejected: '❌ Rejected',
};

const STAGE_COLORS: Record<string, string> = {
  applied: 'bg-blue-500',
  phone_screen: 'bg-purple-500',
  technical: 'bg-indigo-500',
  onsite: 'bg-pink-500',
  offer: 'bg-yellow-500',
  hired: 'bg-green-500',
  rejected: 'bg-red-500',
};

export default function PipelineAnalyticsPage() {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        setLoading(true);
        setError(null);

        // In a real app, fetch from API
        // GET /api/v1/ats/positions/{position_id}/pipeline-analytics

        // Mock data
        const mockAnalytics: Analytics = {
          positionId: 'position-1',
          totalApplications: 42,
          byStage: [
            { stage: 'applied', count: 18, averageDaysInStage: 5.2, medianDaysInStage: 4 },
            { stage: 'phone_screen', count: 12, averageDaysInStage: 3.1, medianDaysInStage: 3 },
            { stage: 'technical', count: 8, averageDaysInStage: 7.5, medianDaysInStage: 7 },
            { stage: 'onsite', count: 3, averageDaysInStage: 2.0, medianDaysInStage: 2 },
            { stage: 'offer', count: 1, averageDaysInStage: 1.0, medianDaysInStage: 1 },
            { stage: 'hired', count: 0, averageDaysInStage: 0, medianDaysInStage: 0 },
            { stage: 'rejected', count: 0, averageDaysInStage: 0, medianDaysInStage: 0 },
          ],
          averageTimeToHire: 18.5,
        };

        setAnalytics(mockAnalytics);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load analytics';
        setError(message);
        addToast(message, 'error');
      } finally {
        setLoading(false);
      }
    };

    loadAnalytics();
  }, [addToast]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="space-y-6">
        <PageHeader title="Pipeline Analytics" subtitle="Monitor hiring funnel metrics" />
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-600">
          {error || 'No data available'}
        </div>
      </div>
    );
  }

  // Calculate conversion rates
  const conversionRates: Record<string, number> = {};
  for (let i = 0; i < analytics.byStage.length - 1; i++) {
    const current = analytics.byStage[i];
    const next = analytics.byStage[i + 1];
    const rate = current.count > 0 ? (next.count / current.count) * 100 : 0;
    conversionRates[`${current.stage}_to_${next.stage}`] = rate;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Pipeline Analytics"
        subtitle="Real-time hiring funnel metrics and performance indicators"
        icon="BarChart3"
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Total Applications</p>
              <p className="text-3xl font-bold">{analytics.totalApplications}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Avg Time to Hire</p>
              <p className="text-3xl font-bold">{analytics.averageTimeToHire.toFixed(1)}</p>
              <p className="text-xs text-muted-foreground">days</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Applied → Phone</p>
              <p className="text-3xl font-bold">
                {conversionRates['applied_to_phone_screen']?.toFixed(0) || 0}%
              </p>
              <p className="text-xs text-muted-foreground">conversion rate</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">In Progress</p>
              <p className="text-3xl font-bold">
                {analytics.byStage
                  .filter(s => !['hired', 'rejected'].includes(s.stage))
                  .reduce((sum, s) => sum + s.count, 0)}
              </p>
              <p className="text-xs text-muted-foreground">active candidates</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pipeline Stages */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Stages</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {analytics.byStage.map(stage => (
            <div key={stage.stage} className="space-y-2">
              {/* Stage header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`h-3 w-3 rounded-full ${STAGE_COLORS[stage.stage]}`} />
                  <span className="font-medium">{STAGE_LABELS[stage.stage]}</span>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <span className="font-bold">{stage.count}</span>
                  <Badge variant="secondary" className="min-w-[80px] text-center">
                    {stage.averageDaysInStage.toFixed(1)}d avg
                  </Badge>
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${STAGE_COLORS[stage.stage]}`}
                  style={{
                    width: `${(stage.count / analytics.totalApplications) * 100}%`,
                  }}
                />
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-2 gap-4 text-xs text-muted-foreground ml-4 mb-2">
                <div>
                  <p className="font-medium">Avg Days in Stage</p>
                  <p>{stage.averageDaysInStage.toFixed(1)} days</p>
                </div>
                <div>
                  <p className="font-medium">Median Days in Stage</p>
                  <p>{stage.medianDaysInStage.toFixed(1)} days</p>
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Conversion Funnel */}
      <Card>
        <CardHeader>
          <CardTitle>Conversion Funnel</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {Object.entries(conversionRates).map(([key, rate]) => {
            const [from, to] = key.replace('_to_', ',').split(',');
            return (
              <div key={key} className="flex items-center gap-4">
                <span className="text-sm min-w-[150px]">
                  {STAGE_LABELS[from]} → {STAGE_LABELS[to]}
                </span>
                <div className="flex-1 bg-gray-200 rounded-full h-6">
                  <div
                    className="bg-primary rounded-full h-6 flex items-center justify-end pr-2 transition-all"
                    style={{ width: `${Math.max(rate, 5)}%` }}
                  >
                    <span className="text-xs font-bold text-white">
                      {rate.toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>

      {/* Insights */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Insights</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex items-start gap-3">
            <span className="text-lg">⚠️</span>
            <div>
              <p className="font-medium">Bottleneck Detected</p>
              <p className="text-muted-foreground">
                Technical stage has highest average duration ({analytics.byStage.find(s => s.stage === 'technical')?.averageDaysInStage.toFixed(1)}d).
                Consider adding more interviewers.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <span className="text-lg">📈</span>
            <div>
              <p className="font-medium">Strong Early Conversion</p>
              <p className="text-muted-foreground">
                Applied → Phone conversion rate is {conversionRates['applied_to_phone_screen']?.toFixed(0)}%, indicating good
                resume quality.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <span className="text-lg">⏱️</span>
            <div>
              <p className="font-medium">Overall Time-to-Hire</p>
              <p className="text-muted-foreground">
                Average {analytics.averageTimeToHire.toFixed(1)} days from application to hire.
                Industry average is 45-60 days.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
