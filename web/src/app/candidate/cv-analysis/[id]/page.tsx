'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, AlertCircle } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface CVAnalysisGapItem {
  capability: string;
  importance: string;
  description?: string;
  howToImprove?: string;
}

interface CVAnalysisResultData {
  analysisId: string;
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  missingCapabilities?: CVAnalysisGapItem[];
  weaknessAreas?: CVAnalysisGapItem[];
  strengthSummary?: string;
  topMatchingPositions?: Array<{
    positionId: string;
    jobTitle: string;
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
}

export default function CVAnalysisResultsPage({
  params,
}: {
  params: { id: string };
}) {
  const { data: session } = useSession();
  const [data, setData] = useState<CVAnalysisResultData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // NOTE: this is a SHARED results route — CV analysis is offered to candidates
  // AND admins/recruiters (admin/cv-analysis redirects here on completion). Do
  // NOT gate it by role; the backend enforces per-user ownership via the token.

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true);
        // Get access token from session
        const accessToken = (session?.user as { accessToken?: string })?.accessToken;
        if (!accessToken) {
          throw new Error('No access token - please log in again');
        }

        // Call backend API directly
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
        const response = await fetch(`${apiUrl}/api/v1/candidates/cv-analysis/${params.id}`, {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
          },
        });

        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }

        const result = await response.json();
        setData(result);
      } catch (err) {
        console.error('CV analysis fetch error:', err);
        setError(err instanceof Error ? err.message : 'Failed to load results');
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    if (session?.user) {
      fetchResults();
    }

    // Only poll if status is not completed
    const interval = setInterval(async () => {
      try {
        const accessToken = (session?.user as { accessToken?: string })?.accessToken;
        if (!accessToken) return;

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
        const response = await fetch(`${apiUrl}/api/v1/candidates/cv-analysis/${params.id}`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        });
        if (response.ok) {
          const result = await response.json();
          setData(result);
          // Stop polling once completed
          if (result.status === 'completed') {
            clearInterval(interval);
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [params.id, session]);

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
            {/* Progress bar */}
            <div className="w-full mt-4">
              <div className="h-2 bg-secondary rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full animate-pulse"
                  style={{ width: '45%' }}
                />
              </div>
              <p className="text-center text-xs text-muted-foreground mt-2">
                ~45% complete
              </p>
            </div>
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
    const progress = data.status === 'pending' ? 15 : 60;
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="w-full max-w-sm">
          <CardContent className="flex flex-col items-center gap-4 pt-6">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-center text-sm text-muted-foreground">
              {data.status === 'pending' ? 'Queued for analysis...' : 'Analyzing your CV...'}
            </p>
            <p className="text-center text-xs text-muted-foreground">
              This typically takes 30-60 seconds
            </p>
            {/* Progress bar */}
            <div className="w-full mt-4">
              <div className="h-2 bg-secondary rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-center text-xs text-muted-foreground mt-2">
                ~{progress}% complete
              </p>
            </div>
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
        title="CV Analysis Results"
        subtitle="Review your personalized recommendations"
        icon="Sparkles"
      />

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2">
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
                              <div className="flex-1">
                                <p className="text-sm font-medium">{typeof cap === 'string' ? cap : cap.capability}</p>
                                {typeof cap === 'object' && cap.description && (
                                  <p className="text-xs text-muted-foreground">{cap.description}</p>
                                )}
                              </div>
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
                              <div className="flex-1">
                                <p className="text-sm font-medium">{typeof area === 'string' ? area : area.capability}</p>
                                {typeof area === 'object' && area.description && (
                                  <p className="text-xs text-muted-foreground">{area.description}</p>
                                )}
                              </div>
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
                            key={position.positionId}
                            className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                          >
                            <p className="font-medium text-sm">{position.jobTitle}</p>
                            <Badge variant="outline">
                              {Math.round(position.matchScore)}% Match
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

          {/* Sidebar - Chat */}
          <div className="lg:col-span-1">
            {/* Placeholder for follow-up chat when component is ready */}
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground text-center">
                  Chat with Claude about your analysis to get personalized advice.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
