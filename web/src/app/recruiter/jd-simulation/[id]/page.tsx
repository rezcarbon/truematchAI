'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { JDSimulationResults } from '@/components/recruiter/JDSimulationResults';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, AlertCircle } from 'lucide-react';

interface JDSimulationResultData {
  id: string;
  jdText: string;
  positionTitle?: string;
  jdQuality: {
    score: number;
    flags: Array<{
      type: string;
      text: string;
      severity: 'high' | 'medium' | 'low';
    }>;
  };
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  createdAt: string;
}

export default function JDSimulationResultsPage({
  params,
}: {
  params: { id: string };
}) {
  const [data, setData] = useState<JDSimulationResultData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true);
        // Use backend API directly (port 8000)
        const backendUrl = `${window.location.protocol}//${window.location.hostname}:8000`;
        const response = await fetch(`${backendUrl}/api/v1/jd-simulation/${params.id}`);

        if (!response.ok) {
          throw new Error('Failed to fetch simulation results');
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
              Analyzing your job description...
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
          title="Simulation Error"
          subtitle="Failed to load your JD simulation results"
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
              Still analyzing your job description...
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
          title="Simulation Failed"
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
                  The simulation could not be completed. Please try again.
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
        title={data.positionTitle || 'JD Simulation Results'}
        subtitle="Review the analysis of your job description"
        icon="Zap"
      />

      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <Badge
            variant={
              data.jdQuality.score >= 80
                ? 'default'
                : data.jdQuality.score >= 60
                ? 'secondary'
                : 'destructive'
            }
          >
            Quality Score: {data.jdQuality.score}/100
          </Badge>
        </div>

        <JDSimulationResults
          jdQuality={data.jdQuality}
          positionTitle={data.positionTitle}
          jdText={data.jdText}
          simulationId={data.id}
        />
      </div>
    </div>
  );
}
