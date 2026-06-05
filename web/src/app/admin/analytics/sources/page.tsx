'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, TrendingUp, TrendingDown } from 'lucide-react';
import { useToast } from '@/components/providers/ToastProvider';

interface SourceMetric {
  source: string;
  applications: number;
  hires: number;
  hireRate: number;
  averageTimeToHire: number;
}

interface Analytics {
  bySources: SourceMetric[];
}

const SOURCE_ICONS: Record<string, string> = {
  linkedin: '💼',
  referral: '👥',
  indeed: '📌',
  glassdoor: '⭐',
  company_website: '🌐',
  recruiter_outreach: '📧',
  university: '🎓',
  unknown: '❓',
};

export default function SourceAnalyticsPage() {
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
        // GET /api/v1/ats/source-analytics

        // Mock data
        const mockAnalytics: Analytics = {
          bySources: [
            { source: 'linkedin', applications: 45, hires: 8, hireRate: 17.8, averageTimeToHire: 16 },
            { source: 'referral', applications: 28, hires: 7, hireRate: 25.0, averageTimeToHire: 12 },
            { source: 'indeed', applications: 32, hires: 4, hireRate: 12.5, averageTimeToHire: 22 },
            { source: 'glassdoor', applications: 18, hires: 2, hireRate: 11.1, averageTimeToHire: 24 },
            { source: 'recruiter_outreach', applications: 12, hires: 3, hireRate: 25.0, averageTimeToHire: 14 },
            { source: 'company_website', applications: 8, hires: 1, hireRate: 12.5, averageTimeToHire: 28 },
          ],
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
        <PageHeader title="Source Analytics" subtitle="Track hiring effectiveness by source" />
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-600">
          {error || 'No data available'}
        </div>
      </div>
    );
  }

  // Sort by hire rate
  const sortedSources = [...analytics.bySources].sort((a, b) => b.hireRate - a.hireRate);
  const topSource = sortedSources[0];
  const bottomSource = sortedSources[sortedSources.length - 1];
  const totalApplications = analytics.bySources.reduce((sum, s) => sum + s.applications, 0);
  const totalHires = analytics.bySources.reduce((sum, s) => sum + s.hires, 0);
  const overallHireRate = (totalHires / totalApplications) * 100;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Source Effectiveness Analytics"
        subtitle="Analyze which channels produce the best candidates"
        icon="BarChart3"
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Total Applications</p>
              <p className="text-3xl font-bold">{totalApplications}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Total Hires</p>
              <p className="text-3xl font-bold">{totalHires}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Overall Hire Rate</p>
              <p className="text-3xl font-bold">{overallHireRate.toFixed(1)}%</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Best Source</p>
              <p className="text-2xl font-bold">
                {SOURCE_ICONS[topSource.source]} {topSource.source}
              </p>
              <p className="text-xs text-green-600 font-medium">{topSource.hireRate.toFixed(1)}% hire rate</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Source Comparison Table */}
      <Card>
        <CardHeader>
          <CardTitle>Source Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sortedSources.map(source => {
              const sourcePercentage = (source.applications / totalApplications) * 100;
              const isTopSource = source.source === topSource.source;
              const trend = source.hireRate > overallHireRate ? 'up' : 'down';

              return (
                <div key={source.source} className="space-y-2">
                  {/* Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-xl">{SOURCE_ICONS[source.source]}</span>
                      <span className="font-medium capitalize">{source.source.replace(/_/g, ' ')}</span>
                      {isTopSource && <Badge className="bg-green-600">Top Performer</Badge>}
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <div className="text-right">
                        <p className="font-bold">{source.applications}</p>
                        <p className="text-xs text-muted-foreground">applications</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold">{source.hires}</p>
                        <p className="text-xs text-muted-foreground">hires</p>
                      </div>
                      <div className={`text-right flex items-center gap-1 ${
                        trend === 'up' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {trend === 'up' ? (
                          <TrendingUp className="h-4 w-4" />
                        ) : (
                          <TrendingDown className="h-4 w-4" />
                        )}
                        <div>
                          <p className="font-bold">{source.hireRate.toFixed(1)}%</p>
                          <p className="text-xs text-muted-foreground">hire rate</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Hire Rate Progress Bar */}
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full transition-all ${
                        source.hireRate > overallHireRate ? 'bg-green-500' : 'bg-orange-500'
                      }`}
                      style={{ width: `${Math.max(source.hireRate, 5)}%` }}
                    />
                  </div>

                  {/* Application Volume Bar */}
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-blue-500"
                      style={{ width: `${sourcePercentage}%` }}
                    />
                  </div>

                  {/* Details */}
                  <div className="grid grid-cols-3 gap-4 text-xs text-muted-foreground ml-4 mb-4">
                    <div>
                      <p className="font-medium">Volume</p>
                      <p>{sourcePercentage.toFixed(1)}% of all applications</p>
                    </div>
                    <div>
                      <p className="font-medium">Avg Time to Hire</p>
                      <p>{source.averageTimeToHire} days</p>
                    </div>
                    <div>
                      <p className="font-medium">vs Overall</p>
                      <p className={trend === 'up' ? 'text-green-600' : 'text-red-600'}>
                        {(source.hireRate - overallHireRate).toFixed(1)}pp {trend === 'up' ? 'above' : 'below'}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle>Strategic Recommendations</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex items-start gap-3">
            <span className="text-lg">✅</span>
            <div>
              <p className="font-medium">Maximize {topSource.source}</p>
              <p className="text-muted-foreground">
                {topSource.source} has a {topSource.hireRate.toFixed(1)}% hire rate ({(topSource.hireRate - overallHireRate).toFixed(1)}pp above average).
                Increase spend and outreach here.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <span className="text-lg">📊</span>
            <div>
              <p className="font-medium">Optimize {bottomSource.source}</p>
              <p className="text-muted-foreground">
                {bottomSource.source} has a {bottomSource.hireRate.toFixed(1)}% hire rate ({(overallHireRate - bottomSource.hireRate).toFixed(1)}pp below average).
                Review application screening criteria.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <span className="text-lg">⚡</span>
            <div>
              <p className="font-medium">Fast-Track Referrals</p>
              <p className="text-muted-foreground">
                Referrals average {
                  analytics.bySources.find(s => s.source === 'referral')?.averageTimeToHire || 'N/A'
                } days to hire.
                Create incentive program to increase referral volume.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
