'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, TrendingUp, TrendingDown } from 'lucide-react';
import { useToast } from '@/components/providers/ToastProvider';

interface RecruiterMetrics {
  recruiterId: string;
  recruiterName: string;
  metrics: {
    candidatesReviewed: number;
    interviewsScheduled: number;
    offersMade: number;
    hireRate: number;
    avgTimeToHire: number;
    avgInterviewsPerHire: number;
  };
  conversionFunnel: {
    applied: number;
    phoneScreen: number;
    technical: number;
    onsite: number;
    offer: number;
    hired: number;
  };
}

interface RecruiterAnalytics {
  recruiters: RecruiterMetrics[];
  teamAverages: {
    hireRate: number;
    timeToHire: number;
    reviewsPerHire: number;
  };
}

export default function RecruiterPerformancePage() {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState<RecruiterAnalytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch real data from API
        const response = await fetch('/api/proxy/ats/recruiter-metrics/');

        if (!response.ok) {
          throw new Error('Failed to fetch recruiter metrics');
        }

        const data = await response.json() as {
          recruiters: Array<{
            recruiter_id: string;
            recruiter_name: string;
            metrics: {
              candidates_reviewed: number;
              interviews_scheduled: number;
              offers_made: number;
              hire_rate: number;
              avg_time_to_hire: number;
              avg_interviews_per_hire: number;
            };
            conversion_funnel: {
              applied: number;
              phone_screen: number;
              technical: number;
              onsite: number;
              offer: number;
              hired: number;
            };
          }>;
          team_averages: {
            hire_rate: number;
            time_to_hire: number;
            reviews_per_hire: number;
          };
        };

        // Transform API data to component format
        const recruiters: RecruiterMetrics[] = data.recruiters.map((r) => ({
          recruiterId: r.recruiter_id,
          recruiterName: r.recruiter_name,
          metrics: {
            candidatesReviewed: r.metrics.candidates_reviewed,
            interviewsScheduled: r.metrics.interviews_scheduled,
            offersMade: r.metrics.offers_made,
            hireRate: r.metrics.hire_rate,
            avgTimeToHire: r.metrics.avg_time_to_hire,
            avgInterviewsPerHire: r.metrics.avg_interviews_per_hire,
          },
          conversionFunnel: {
            applied: r.conversion_funnel.applied,
            phoneScreen: r.conversion_funnel.phone_screen,
            technical: r.conversion_funnel.technical,
            onsite: r.conversion_funnel.onsite,
            offer: r.conversion_funnel.offer,
            hired: r.conversion_funnel.hired,
          },
        }));

        const analytics: RecruiterAnalytics = {
          recruiters,
          teamAverages: {
            hireRate: data.team_averages.hire_rate,
            timeToHire: data.team_averages.time_to_hire,
            reviewsPerHire: data.team_averages.reviews_per_hire,
          },
        };

        setAnalytics(analytics);
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
        <PageHeader
          title="Recruiter Performance Analytics"
          subtitle="Track recruiter metrics and conversion funnels"
        />
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-600">
          {error || 'No data available'}
        </div>
      </div>
    );
  }

  // Sort by hire rate (descending)
  const sortedRecruiters = [...analytics.recruiters].sort(
    (a, b) => b.metrics.hireRate - a.metrics.hireRate
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Recruiter Performance Analytics"
        subtitle="Track hiring metrics and conversion funnel by recruiter"
        icon="Users"
      />

      {/* Team Averages */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Team Average Hire Rate</p>
              <p className="text-3xl font-bold">{analytics.teamAverages.hireRate.toFixed(1)}%</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Team Avg Time-to-Hire</p>
              <p className="text-3xl font-bold">{Math.round(analytics.teamAverages.timeToHire)} days</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Avg Reviews Per Hire</p>
              <p className="text-3xl font-bold">{analytics.teamAverages.reviewsPerHire.toFixed(1)}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recruiter Performance Cards */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Recruiter Metrics</h2>
        {sortedRecruiters.map((recruiter, idx) => {
          const isAboveAverage = recruiter.metrics.hireRate >= analytics.teamAverages.hireRate;
          const conveyed = recruiter.conversionFunnel;
          const totalFunnel = conveyed.applied;

          return (
            <Card key={recruiter.recruiterId}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-bold">
                      {idx + 1}
                    </div>
                    <div>
                      <CardTitle>{recruiter.recruiterName}</CardTitle>
                      <p className="text-sm text-muted-foreground">
                        {recruiter.metrics.candidatesReviewed} candidates reviewed
                      </p>
                    </div>
                  </div>
                  <Badge variant={isAboveAverage ? 'default' : 'secondary'}>
                    {isAboveAverage ? '📈 Above Average' : '📉 Below Average'}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* KPIs */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground">Interviews Scheduled</p>
                    <p className="text-2xl font-bold">{recruiter.metrics.interviewsScheduled}</p>
                    <p className="text-xs text-muted-foreground">
                      {((recruiter.metrics.interviewsScheduled / recruiter.metrics.candidatesReviewed) * 100).toFixed(0)}%
                      conversion
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-muted-foreground">Offers Made</p>
                    <p className="text-2xl font-bold">{recruiter.metrics.offersMade}</p>
                    <p className="text-xs text-muted-foreground">
                      {((recruiter.metrics.offersMade / recruiter.metrics.interviewsScheduled) * 100).toFixed(0)}%
                      of interviews
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-muted-foreground">Hire Rate</p>
                    <p className={`text-2xl font-bold ${isAboveAverage ? 'text-green-600' : 'text-orange-600'}`}>
                      {recruiter.metrics.hireRate.toFixed(1)}%
                    </p>
                    <p className="text-xs text-muted-foreground">
                      <span className={isAboveAverage ? 'text-green-600' : 'text-orange-600'}>
                        {isAboveAverage ? '+' : ''}
                        {(recruiter.metrics.hireRate - analytics.teamAverages.hireRate).toFixed(1)}pp vs avg
                      </span>
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-muted-foreground">Avg Time-to-Hire</p>
                    <p className="text-2xl font-bold">{recruiter.metrics.avgTimeToHire} days</p>
                    <p className="text-xs text-muted-foreground">
                      {recruiter.metrics.avgTimeToHire < analytics.teamAverages.timeToHire ? '🚀 Fast' : '⏱️ Slower'}
                    </p>
                  </div>
                </div>

                {/* Conversion Funnel */}
                <div>
                  <p className="text-sm font-medium mb-3">Conversion Funnel</p>
                  <div className="space-y-2">
                    {[
                      { stage: 'Applied', value: conveyed.applied },
                      { stage: 'Phone Screen', value: conveyed.phoneScreen },
                      { stage: 'Technical', value: conveyed.technical },
                      { stage: 'On-site', value: conveyed.onsite },
                      { stage: 'Offer', value: conveyed.offer },
                      { stage: 'Hired', value: conveyed.hired },
                    ].map((step) => {
                      const percentage = (step.value / totalFunnel) * 100;
                      return (
                        <div key={step.stage} className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span>{step.stage}</span>
                            <span className="font-medium">
                              {step.value} ({percentage.toFixed(0)}%)
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="h-2 rounded-full bg-blue-500 transition-all"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Insights */}
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-sm font-medium mb-2">Insights</p>
                  <ul className="text-xs space-y-1 text-muted-foreground">
                    <li>
                      • Avg {recruiter.metrics.avgInterviewsPerHire.toFixed(1)} interviews per hire
                      {recruiter.metrics.avgInterviewsPerHire < analytics.teamAverages.reviewsPerHire
                        ? ' (more efficient)'
                        : ' (needs more screening)'}
                    </li>
                    <li>
                      • {recruiter.metrics.hireRate < 10 ? '⚠️' : '✅'} Hire rate
                      {isAboveAverage ? ' is above team average' : ' is below team average'}
                    </li>
                    <li>
                      • Best conversion: {((conveyed.phoneScreen / conveyed.applied) * 100).toFixed(0)}% (Applied →
                      Phone)
                    </li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Comparison Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Recruiter</th>
                  <th className="text-right p-2">Reviewed</th>
                  <th className="text-right p-2">Interviews</th>
                  <th className="text-right p-2">Offers</th>
                  <th className="text-right p-2">Hire Rate</th>
                  <th className="text-right p-2">Avg Days</th>
                </tr>
              </thead>
              <tbody>
                {sortedRecruiters.map((recruiter) => (
                  <tr key={recruiter.recruiterId} className="border-b hover:bg-gray-50">
                    <td className="p-2 font-medium">{recruiter.recruiterName}</td>
                    <td className="text-right p-2">{recruiter.metrics.candidatesReviewed}</td>
                    <td className="text-right p-2">{recruiter.metrics.interviewsScheduled}</td>
                    <td className="text-right p-2">{recruiter.metrics.offersMade}</td>
                    <td className="text-right p-2">
                      <span
                        className={
                          recruiter.metrics.hireRate >= analytics.teamAverages.hireRate
                            ? 'text-green-600 font-medium'
                            : 'text-orange-600 font-medium'
                        }
                      >
                        {recruiter.metrics.hireRate.toFixed(1)}%
                      </span>
                    </td>
                    <td className="text-right p-2">{recruiter.metrics.avgTimeToHire}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
