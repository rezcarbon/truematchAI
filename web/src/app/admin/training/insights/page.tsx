'use client';

export const dynamic = 'force-dynamic';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { PageHeader } from '@/components/shared/AppShell';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  getTrainingInsights,
  getTrainingProgress,
  getSuccessPatterns,
  TrainingInsight,
  TrainingProgress,
  SuccessPattern,
} from '@/lib/api/training';
import { AlertCircle, Brain, TrendingUp, Target, Lightbulb } from 'lucide-react';

export default function InsightsAnalyticsPage() {
  const { data: session } = useSession();
  const [insights, setInsights] = useState<TrainingInsight[]>([]);
  const [progress, setProgress] = useState<TrainingProgress[]>([]);
  const [patterns, setPatterns] = useState<SuccessPattern[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        if (!session) throw new Error('Not authenticated');

        const token = session?.user?.email || 'session-token';

        const [insightsData, progressData, patternsData] = await Promise.all([
          getTrainingInsights(token),
          getTrainingProgress(token),
          getSuccessPatterns(token),
        ]);

        setInsights(insightsData);
        setProgress(progressData);
        setPatterns(patternsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analytics');
      } finally {
        setLoading(false);
      }
    };

    if (session) {
      loadData();
    }
  }, [session]);

  if (loading) {
    return (
      <div>
        <PageHeader
          title="Insights & Analytics"
          subtitle="Generated insights from the virtual brain's learning"
        />
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-muted-foreground">Loading analytics...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <PageHeader
          title="Insights & Analytics"
          subtitle="Generated insights from the virtual brain's learning"
        />
        <Card className="border-destructive">
          <CardContent className="flex items-center gap-3 p-6">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div>
              <p className="font-semibold">Error loading analytics</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const trendingInsights = insights.filter((i) => i.is_trending);
  const topProgress = progress.sort((a, b) => b.improvement_percent - a.improvement_percent).slice(0, 3);

  return (
    <div>
      <PageHeader
        title="Insights & Analytics"
        subtitle="Generated insights from the virtual brain's learning"
      />

      <div className="space-y-6">
        {/* Trending Insights */}
        {trendingInsights.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Lightbulb className="h-5 w-5" />
              Trending Insights
            </h2>
            <div className="grid gap-4">
              {trendingInsights.slice(0, 3).map((insight) => (
                <Card key={insight.id} className="border-blue-200 bg-blue-50">
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <h3 className="font-semibold">{insight.title}</h3>
                        <p className="text-sm text-foreground mt-2">{insight.description}</p>
                        <div className="flex flex-wrap gap-2 mt-3">
                          {insight.insight_category && (
                            <Badge variant="secondary" className="text-xs">
                              {insight.insight_category}
                            </Badge>
                          )}
                          {insight.industry && (
                            <Badge variant="outline" className="text-xs">
                              {insight.industry}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-blue-600">
                          {Math.round(insight.confidence * 100)}%
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">confidence</p>
                        {insight.metric_value && (
                          <>
                            <p className="text-sm font-semibold mt-2">{insight.metric_value}</p>
                            <p className="text-xs text-muted-foreground">metric</p>
                          </>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Training Progress */}
        {topProgress.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Training Progress
            </h2>
            <div className="grid gap-4">
              {topProgress.map((item) => (
                <Card key={item.id}>
                  <CardContent className="p-5">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold">{item.metric_name}</h3>
                      <Badge variant="default" className="bg-green-600">
                        +{Math.round(item.improvement_percent)}%
                      </Badge>
                    </div>
                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <div>
                        <p className="text-xs text-muted-foreground">Baseline</p>
                        <p className="text-lg font-bold">{Math.round(item.baseline_value * 100)}%</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Current</p>
                        <p className="text-lg font-bold text-green-600">
                          {Math.round(item.current_value * 100)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Samples</p>
                        <p className="text-lg font-bold">{item.sample_count}</p>
                      </div>
                    </div>
                    <Progress value={item.current_value * 100} className="h-2" />
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Success Patterns */}
        {patterns.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Target className="h-5 w-5" />
              Success Patterns ({patterns.length})
            </h2>
            <div className="grid gap-4">
              {patterns.slice(0, 5).map((pattern) => (
                <Card key={pattern.id}>
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between gap-4 mb-3">
                      <div>
                        <h3 className="font-semibold">
                          {pattern.job_category || 'General Pattern'}
                        </h3>
                        {pattern.industry && (
                          <p className="text-sm text-muted-foreground mt-1">{pattern.industry}</p>
                        )}
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-green-600">
                          {Math.round(pattern.success_rate * 100)}%
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">success rate</p>
                      </div>
                    </div>

                    {pattern.key_capabilities.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs font-semibold text-muted-foreground mb-2">
                          Key Capabilities
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {pattern.key_capabilities.slice(0, 4).map((cap, i) => (
                            <Badge key={i} variant="secondary" className="text-xs">
                              {cap}
                            </Badge>
                          ))}
                          {pattern.key_capabilities.length > 4 && (
                            <Badge variant="secondary" className="text-xs">
                              +{pattern.key_capabilities.length - 4} more
                            </Badge>
                          )}
                        </div>
                      </div>
                    )}

                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-xs text-muted-foreground">Sample Size</p>
                        <p className="font-semibold">{pattern.sample_size}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Confidence</p>
                        <p className="font-semibold">{Math.round(pattern.confidence_level * 100)}%</p>
                      </div>
                      {pattern.average_tenure_months && (
                        <div>
                          <p className="text-xs text-muted-foreground">Avg. Tenure</p>
                          <p className="font-semibold">{pattern.average_tenure_months}mo</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* All Insights */}
        {insights.length > trendingInsights.length && (
          <div>
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Brain className="h-5 w-5" />
              All Insights ({insights.length})
            </h2>
            <div className="grid gap-4">
              {insights.slice(3).map((insight) => (
                <Card key={insight.id}>
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <h3 className="font-semibold text-sm">{insight.title}</h3>
                        <p className="text-sm text-foreground mt-1">{insight.description}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold">
                          {Math.round(insight.confidence * 100)}%
                        </div>
                        <p className="text-xs text-muted-foreground">confidence</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {insights.length === 0 && progress.length === 0 && patterns.length === 0 && (
          <Card>
            <CardContent className="p-12 text-center">
              <Brain className="h-8 w-8 mx-auto mb-4 text-muted-foreground opacity-50" />
              <p className="text-muted-foreground">
                No insights generated yet. Keep collecting training feedback to generate insights!
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
