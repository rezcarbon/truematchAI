'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, AlertCircle } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface CVAnalysisResultData {
  id: string;
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  targetRole?: string;
  missingCapabilities?: string[];
  weaknessAreas?: string[];
  strengthSummary?: string;
  topMatchingPositions?: Array<{
    id: string;
    title: string;
    matchScore: number;
  }>;
  improvementSuggestions?: Array<{
    category: string;
    suggestion: string;
    priority: 'high' | 'medium' | 'low';
  }>;
  trajectoryAnalysis?: string;
  marketPositioning?: string;
  growthOpportunities?: string[];
  createdAt: string;
}

export default function CVAnalysisResultsPage({
  params,
}: {
  params: { id: string };
}) {
  const [data, setData] = useState<CVAnalysisResultData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true);
        // Use proxy which handles authentication injection
        const response = await fetch(`/api/proxy/candidates/cv-analysis/${params.id}`);

        if (!response.ok) {
          throw new Error('Failed to fetch analysis results');
        }

        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load results');
      } finally {
        setLoading(false);
      }
    };

    // Poll if status is not completed
    const interval = setInterval(fetchResults, 3000);
    fetchResults();

    return () => clearInterval(interval);
  }, [params.id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="w-full max-w-sm">
          <CardContent className="flex flex-col items-center gap-4 pt-6">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-center text-sm text-muted-foreground">
              Analyzing your CV...
            </p>
            <p className="text-center text-xs text-muted-foreground">
              This typically takes 30-60 seconds
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-background">
        <PageHeader
          title="Analysis Error"
          subtitle="Failed to load your CV analysis results"
          icon="AlertCircle"
        />

        <div className="container mx-auto px-4 py-8 max-w-2xl">
          <Card className="border-red-200/60 bg-red-50/30">
            <CardContent className="flex items-start gap-3 pt-6">
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-red-600">Error</p>
                <p className="text-sm text-red-600/80">{error || 'Unknown error'}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (data.status === 'pending' || data.status === 'analyzing') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="w-full max-w-sm">
          <CardContent className="flex flex-col items-center gap-4 pt-6">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-center text-sm text-muted-foreground">
              Still analyzing your CV...
            </p>
            <p className="text-center text-xs text-muted-foreground">
              This typically takes 30-60 seconds
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (data.status === 'failed') {
    return (
      <div className="min-h-screen bg-background">
        <PageHeader
          title="Analysis Failed"
          subtitle="Unable to complete the analysis"
          icon="AlertCircle"
        />

        <div className="container mx-auto px-4 py-8 max-w-2xl">
          <Card className="border-red-200/60 bg-red-50/30">
            <CardContent className="flex items-start gap-3 pt-6">
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-red-600">Analysis Failed</p>
                <p className="text-sm text-red-600/80">
                  The analysis could not be completed. Please try again.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <PageHeader
        title={data.targetRole || 'CV Analysis Results'}
        subtitle="Review your personalized recommendations"
        icon="Sparkles"
      />

      <div className="container mx-auto px-4 py-8">
        <Tabs defaultValue="gaps" className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-8">
            <TabsTrigger value="gaps">Skill Gaps</TabsTrigger>
            <TabsTrigger value="matches">Job Matches</TabsTrigger>
            <TabsTrigger value="improvements">Improvements</TabsTrigger>
            <TabsTrigger value="career">Career Insights</TabsTrigger>
          </TabsList>

          {/* Skill Gaps */}
          <TabsContent value="gaps" className="space-y-4">
            <Card>
              <CardContent className="pt-6 space-y-4">
                {data.missingCapabilities && data.missingCapabilities.length > 0 ? (
                  <>
                    <h3 className="font-semibold">Missing Capabilities</h3>
                    <div className="space-y-2">
                      {data.missingCapabilities.map((cap, idx) => (
                        <div key={idx} className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-red-500" />
                          <p className="text-sm">{cap}</p>
                        </div>
                      ))}
                    </div>
                  </>
                ) : null}

                {data.weaknessAreas && data.weaknessAreas.length > 0 ? (
                  <>
                    <h3 className="font-semibold mt-4">Weakness Areas</h3>
                    <div className="space-y-2">
                      {data.weaknessAreas.map((area, idx) => (
                        <div key={idx} className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-amber-500" />
                          <p className="text-sm">{area}</p>
                        </div>
                      ))}
                    </div>
                  </>
                ) : null}

                {data.strengthSummary && (
                  <>
                    <h3 className="font-semibold mt-4">Your Strengths</h3>
                    <p className="text-sm text-muted-foreground">{data.strengthSummary}</p>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Job Matches */}
          <TabsContent value="matches" className="space-y-4">
            <Card>
              <CardContent className="pt-6">
                {data.topMatchingPositions && data.topMatchingPositions.length > 0 ? (
                  <div className="space-y-3">
                    {data.topMatchingPositions.map((position) => (
                      <div
                        key={position.id}
                        className="flex items-center justify-between p-3 border rounded-lg"
                      >
                        <p className="font-medium text-sm">{position.title}</p>
                        <Badge variant="outline">
                          {Math.round(position.matchScore * 100)}% Match
                        </Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No matching positions found
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Improvements */}
          <TabsContent value="improvements" className="space-y-4">
            <Card>
              <CardContent className="pt-6">
                {data.improvementSuggestions && data.improvementSuggestions.length > 0 ? (
                  <div className="space-y-4">
                    {data.improvementSuggestions.map((sugg, idx) => (
                      <div key={idx} className="border rounded-lg p-3 space-y-2">
                        <div className="flex items-center justify-between">
                          <p className="font-medium text-sm capitalize">
                            {sugg.category}
                          </p>
                          <Badge
                            variant={
                              sugg.priority === 'high'
                                ? 'destructive'
                                : sugg.priority === 'medium'
                                ? 'secondary'
                                : 'outline'
                            }
                          >
                            {sugg.priority}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {sugg.suggestion}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No suggestions available
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Career Insights */}
          <TabsContent value="career" className="space-y-4">
            <Card>
              <CardContent className="pt-6 space-y-4">
                {data.trajectoryAnalysis && (
                  <>
                    <h3 className="font-semibold">Career Trajectory</h3>
                    <p className="text-sm text-muted-foreground">
                      {data.trajectoryAnalysis}
                    </p>
                  </>
                )}

                {data.marketPositioning && (
                  <>
                    <h3 className="font-semibold mt-4">Market Positioning</h3>
                    <p className="text-sm text-muted-foreground">
                      {data.marketPositioning}
                    </p>
                  </>
                )}

                {data.growthOpportunities && data.growthOpportunities.length > 0 && (
                  <>
                    <h3 className="font-semibold mt-4">Growth Opportunities</h3>
                    <ul className="space-y-2">
                      {data.growthOpportunities.map((opp, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm">
                          <span className="text-green-600 font-semibold">→</span>
                          <span className="text-muted-foreground">{opp}</span>
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
