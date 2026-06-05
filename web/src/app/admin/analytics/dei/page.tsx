'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react';
import { useToast } from '@/components/providers/ToastProvider';

interface DiversityData {
  gender: Record<string, number>;
  ethnicity: Record<string, number>;
  age_group: Record<string, number>;
  geography: Record<string, number>;
}

interface DEIAnalytics {
  diversity: {
    diversity_metrics: DiversityData;
    pipeline_diversity: Record<string, Record<string, number>>;
    diversity_goals: Record<string, number>;
    progress_to_goals: Record<string, number>;
    total_candidates: number;
  };
  equity: {
    advancement_by_demographic: Record<string, any>;
    offer_rates: Record<string, number>;
    advancement_equality_index: number;
    equity_gaps: Array<any>;
  };
  inclusion: {
    team_diversity: Record<string, any>;
    retention_by_demographic: Record<string, any>;
    inclusion_score: number;
    recommendations: string[];
  };
  compliance: {
    eeoc_data: Record<string, any>;
    four_fifths_rule: Record<string, any>;
    hiring_fairness_score: number;
    compliance_status: string;
    audit_trail_complete: boolean;
  };
}

export default function DEIAnalyticsPage() {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState<DEIAnalytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch all DEI metrics in parallel
        const [diversityRes, equityRes, inclusionRes, complianceRes] = await Promise.all([
          fetch('/api/proxy/ats/dei-analytics/diversity'),
          fetch('/api/proxy/ats/dei-analytics/equity'),
          fetch('/api/proxy/ats/dei-analytics/inclusion'),
          fetch('/api/proxy/ats/dei-analytics/compliance'),
        ]);

        if (!diversityRes.ok || !equityRes.ok || !inclusionRes.ok || !complianceRes.ok) {
          throw new Error('Failed to fetch DEI analytics');
        }

        const [diversity, equity, inclusion, compliance] = await Promise.all([
          diversityRes.json(),
          equityRes.json(),
          inclusionRes.json(),
          complianceRes.json(),
        ]);

        setAnalytics({
          diversity,
          equity,
          inclusion,
          compliance,
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load DEI analytics';
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
        <PageHeader
          title="DEI Analytics"
          subtitle="Diversity, Equity, and Inclusion metrics"
        />
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-600">
          {error || 'No data available'}
        </div>
      </div>
    );
  }

  const diversityGoals = analytics.diversity.diversity_goals;
  const progress = analytics.diversity.progress_to_goals;
  const equity = analytics.equity;
  const inclusion = analytics.inclusion;
  const compliance = analytics.compliance;

  return (
    <div className="space-y-6">
      <PageHeader
        title="DEI Analytics & Compliance"
        subtitle="Track diversity, equity, inclusion, and EEOC compliance"
        icon="BarChart3"
      />

      {/* DEI Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Inclusion Score</p>
              <p className="text-3xl font-bold">{Math.round(inclusion.inclusion_score)}</p>
              <p className="text-xs text-muted-foreground">/100</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Equality Index</p>
              <p className="text-3xl font-bold">{(equity.advancement_equality_index * 100).toFixed(0)}%</p>
              <p className="text-xs text-muted-foreground">Advancement parity</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Fairness Score</p>
              <p className="text-3xl font-bold">{compliance.hiring_fairness_score.toFixed(0)}%</p>
              <p className="text-xs text-muted-foreground">Hiring practices</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Compliance Status</p>
              <Badge variant={compliance.compliance_status === 'compliant' ? 'default' : 'destructive'}>
                {compliance.compliance_status === 'compliant' ? '✅ Compliant' : '⚠️ At Risk'}
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Diversity Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Diversity Metrics & Goals</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {[
            { label: 'Women %', key: 'women', progress: progress.women, goal: diversityGoals.women_percentage },
            {
              label: 'Underrepresented Minority %',
              key: 'underrepresented_minority',
              progress: progress.underrepresented_minority,
              goal: diversityGoals.underrepresented_minority_percentage,
            },
            {
              label: 'International %',
              key: 'international',
              progress: progress.international,
              goal: diversityGoals.international_percentage,
            },
          ].map(metric => (
            <div key={metric.key} className="space-y-2">
              <div className="flex justify-between items-center">
                <p className="font-medium text-sm">{metric.label}</p>
                <div className="text-sm">
                  <span className="font-bold">{metric.progress.toFixed(1)}%</span>
                  <span className="text-muted-foreground ml-2">Goal: {metric.goal}%</span>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all ${metric.progress >= metric.goal ? 'bg-green-500' : 'bg-orange-500'}`}
                  style={{ width: `${Math.min(metric.progress, 100)}%` }}
                />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Equity Analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Equity Analysis - Advancement by Demographic</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(equity.advancement_by_demographic).map(([demo, data]: [string, any]) => (
              <div key={demo} className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <p className="font-medium capitalize">{demo.replace(/_/g, ' ')}</p>
                  <p className="text-sm text-muted-foreground">
                    {data.hired} hired from {data.total} candidates
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold">{data.rate.toFixed(1)}%</p>
                  <p className="text-xs text-muted-foreground">advancement rate</p>
                </div>
              </div>
            ))}
          </div>

          {equity.equity_gaps.length > 0 && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-600 mt-1" />
                <div>
                  <p className="font-medium text-sm text-yellow-900">Equity Gaps Detected</p>
                  {equity.equity_gaps.map((gap: any, idx: number) => (
                    <p key={idx} className="text-xs text-yellow-700 mt-1">
                      {gap.group1} vs {gap.group2}: {gap.gap_percentage}pp gap ({gap.severity} severity)
                    </p>
                  ))}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Inclusion & Retention */}
      <Card>
        <CardHeader>
          <CardTitle>Inclusion & Retention by Demographic</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(inclusion.retention_by_demographic).map(([demo, data]: [string, any]) => (
              <div key={demo} className="space-y-2">
                <div className="flex justify-between items-center">
                  <p className="font-medium text-sm capitalize">{demo.replace(/_/g, ' ')}</p>
                  <Badge variant={data.retention_rate >= 85 ? 'default' : 'secondary'}>
                    {data.retention_rate}% retention
                  </Badge>
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{data.retained} retained</span>
                  <span>{data.hired} hired</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${data.retention_rate >= 85 ? 'bg-green-500' : 'bg-orange-500'}`}
                    style={{ width: `${data.retention_rate}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* EEOC Compliance */}
      <Card>
        <CardHeader>
          <CardTitle>EEOC Compliance Report</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(analytics.compliance.eeoc_data).map(([key, value]: [string, any]) => (
              <div key={key} className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</p>
                <p className="text-lg font-bold">{value}</p>
              </div>
            ))}
          </div>

          {analytics.compliance.four_fifths_rule.groups_below_threshold.length > 0 && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-red-600 mt-1" />
                <div>
                  <p className="font-medium text-sm text-red-900">4/5 Rule Violation</p>
                  {analytics.compliance.four_fifths_rule.groups_below_threshold.map((group: string) => (
                    <p key={group} className="text-xs text-red-700 mt-1">
                      {group} - below {analytics.compliance.four_fifths_rule.threshold}% threshold
                    </p>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm font-medium text-blue-900">Audit Trail</p>
            <p className="text-xs text-blue-700 mt-1">
              Status: {analytics.compliance.audit_trail_complete ? 'Complete' : 'In Progress'}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      {inclusion.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>DEI Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {inclusion.recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start gap-3 text-sm">
                  <TrendingUp className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
