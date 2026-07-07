'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { PageHeader } from '@/components/shared/PageHeader';
import { JDSimulationForm } from '@/components/recruiter/JDSimulationForm';
import { JDSimulationResults } from '@/components/recruiter/JDSimulationResults';
import { Card, CardContent } from '@/components/ui/card';
import { AlertCircle, Loader2 } from 'lucide-react';

interface SimulationData {
  id: string;
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  jdText: string;
  positionTitle?: string;
  jdQuality?: {
    score: number;
    flags: Array<{
      type: string;
      text: string;
      severity: 'high' | 'medium' | 'low';
    }>;
  };
  createdAt: string;
}

export default function JDSimulationPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [simulationData, setSimulationData] = useState<SimulationData | null>(null);
  const [polling, setPolling] = useState(false);

  const handleSubmit = async (data: {
    jdText: string;
    positionTitle?: string;
  }) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/proxy/v1/jd-simulation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jd_text: data.jdText,
          simulation_type: 'requirement_fit',
          position_title: data.positionTitle || null,
          position_id: null,
          target_candidate_profile: null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to start simulation');
      }

      const result = await response.json();
      setSimulationData({
        id: result.simulation_id || result.id,
        status: result.status || 'pending',
        jdText: data.jdText,
        positionTitle: data.positionTitle,
        createdAt: new Date().toISOString(),
      });

      // Start polling for results
      pollSimulationResults(result.simulation_id || result.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setLoading(false);
    }
  };

  const pollSimulationResults = async (simulationId: string) => {
    setPolling(true);
    const maxAttempts = 60; // 2 minutes with 2-second intervals
    let attempts = 0;

    const checkStatus = async () => {
      try {
        const response = await fetch(`/api/proxy/v1/jd-simulation/${simulationId}`);

        if (!response.ok) {
          throw new Error('Failed to fetch simulation status');
        }

        const result = await response.json();

        setSimulationData((prev) =>
          prev ? { ...prev, ...result, status: result.status || 'pending' } : null
        );

        if (result.status === 'completed' || result.status === 'failed') {
          setLoading(false);
          setPolling(false);
          return;
        }

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(checkStatus, 2000);
        } else {
          setError('Simulation analysis timed out');
          setLoading(false);
          setPolling(false);
        }
      } catch (err) {
        console.error('Polling error:', err);
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(checkStatus, 2000);
        } else {
          setError('Failed to retrieve simulation results');
          setLoading(false);
          setPolling(false);
        }
      }
    };

    setTimeout(checkStatus, 2000);
  };

  // Loading state
  if (loading && !simulationData) {
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

  // Show results when analysis is complete
  if (simulationData && simulationData.status === 'completed' && simulationData.jdQuality) {
    return (
      <div className="min-h-screen bg-background">
        <PageHeader
          title={simulationData.positionTitle || 'JD Simulation Results'}
          subtitle="Review the analysis of your job description"
          icon="Zap"
        />

        <div className="container mx-auto px-4 py-8">
          <JDSimulationResults
            jdQuality={simulationData.jdQuality}
            positionTitle={simulationData.positionTitle}
            jdText={simulationData.jdText}
            simulationId={simulationData.id}
          />
        </div>
      </div>
    );
  }

  // Show error
  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <PageHeader
          title="Analysis Error"
          subtitle="Failed to analyze your job description"
          icon="AlertCircle"
        />

        <div className="container mx-auto px-4 py-8 max-w-2xl">
          <Card className="border-red-200/60 bg-red-50/30">
            <CardContent className="flex items-start gap-3 pt-6">
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-red-600">Error</p>
                <p className="text-sm text-red-600/80">{error}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Form for initial submission
  return (
    <div className="space-y-6">
      <PageHeader
        title="Test Your Job Description"
        subtitle="Analyze your job posting to identify capability gaps, requirement creep, and optimization opportunities"
        icon="Zap"
      />

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        <JDSimulationForm
          onSubmit={handleSubmit}
          loading={loading}
          error={error || undefined}
        />
      </div>
    </div>
  );
}
