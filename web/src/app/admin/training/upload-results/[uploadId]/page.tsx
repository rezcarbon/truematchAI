'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useParams } from 'next/navigation';
import { PageHeader } from '@/components/shared/AppShell';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { CheckCircle, Clock, AlertTriangle, Brain, TrendingUp, Zap } from 'lucide-react';

interface UploadResult {
  upload_id: string;
  items_processed: number;
  items_failed: number;
  insights_extracted: number;
  new_capabilities: string[];
  updated_mappings: any[];
  improvement_delta: Record<string, number>;
  processing_time_seconds: number;
}

export default function UploadResultsPage() {
  const { data: session } = useSession();
  const params = useParams();
  const uploadId = params.uploadId as string;

  const [result, setResult] = useState<UploadResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadResults = async () => {
      if (!session || !uploadId) return;

      try {
        const token = (session as any)?.accessToken || (session?.user as any)?.accessToken;
        if (!token) throw new Error('No access token');

        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/training/data/upload/${uploadId}/status`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        if (!response.ok) throw new Error('Failed to load results');
        const data = await response.json();
        setResult(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    const interval = setInterval(loadResults, 2000);
    loadResults();
    return () => clearInterval(interval);
  }, [session, uploadId]);

  if (loading) {
    return (
      <div>
        <PageHeader
          title="Upload Processing"
          subtitle="Processing training data..."
        />
        <Card>
          <CardContent className="p-12 text-center">
            <Clock className="h-8 w-8 mx-auto mb-4 text-blue-600 animate-spin" />
            <p className="text-muted-foreground">Processing your training data...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div>
        <PageHeader
          title="Upload Results"
          subtitle="Training data processing"
        />
        <Card className="border-destructive">
          <CardContent className="p-6 flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            <div>
              <p className="font-semibold">Error loading results</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const successRate = result.items_processed > 0
    ? ((result.items_processed - result.items_failed) / result.items_processed) * 100
    : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Upload Results"
        subtitle={`Processed ${result.items_processed} items from training file`}
      />

      {/* Processing Summary */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Items Processed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{result.items_processed}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {result.items_failed > 0 && `${result.items_failed} failed`}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Success Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{successRate.toFixed(0)}%</div>
            <Progress value={successRate} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              New Capabilities
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{result.new_capabilities.length}</div>
            <p className="text-xs text-muted-foreground mt-1">Discovered</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Processing Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{result.processing_time_seconds.toFixed(1)}s</div>
            <p className="text-xs text-muted-foreground mt-1">Elapsed</p>
          </CardContent>
        </Card>
      </div>

      {/* New Capabilities */}
      {result.new_capabilities.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              New Capabilities Discovered
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {result.new_capabilities.slice(0, 10).map((cap, i) => (
                <Badge key={i} variant="default">
                  {cap}
                </Badge>
              ))}
              {result.new_capabilities.length > 10 && (
                <Badge variant="outline">
                  +{result.new_capabilities.length - 10} more
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Improvement Metrics */}
      {Object.keys(result.improvement_delta).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Improvement Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(result.improvement_delta).map(([metric, value]) => (
                <div key={metric} className="flex items-center justify-between">
                  <span className="text-sm capitalize">{metric.replace(/_/g, ' ')}</span>
                  <div className="flex items-center gap-2">
                    <span className={`font-semibold ${value > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {value > 0 ? '+' : ''}{(value * 100).toFixed(1)}%
                    </span>
                    {value > 0 && <TrendingUp className="h-4 w-4 text-green-600" />}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Next Steps */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Virtual Brain Updates
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-3">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <span>Training data processed and stored</span>
          </div>
          <div className="flex items-center gap-3">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <span>Capabilities extracted from feedback</span>
          </div>
          <div className="flex items-center gap-3">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <span>Success patterns discovered and learned</span>
          </div>
          <div className="flex items-center gap-3">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <span>Virtual brain state updated</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
