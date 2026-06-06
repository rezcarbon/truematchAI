'use client';

export const dynamic = 'force-dynamic';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { PageHeader } from '@/components/shared/AppShell';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getTrainingStats, getVirtualBrainState, TrainingStats, VirtualBrainState } from '@/lib/api/training';
import { AlertCircle, TrendingUp, Brain, Database, CheckCircle2 } from 'lucide-react';

export default function TrainingSystemDashboard() {
  const { data: session } = useSession();
  const [stats, setStats] = useState<TrainingStats | null>(null);
  const [brainState, setBrainState] = useState<VirtualBrainState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        if (!session) throw new Error('Not authenticated');

        const token = (session as any)?.accessToken || (session?.user as any)?.accessToken;
        if (!token) throw new Error('No access token available');

        const [statsData, brainData] = await Promise.all([
          getTrainingStats(token),
          getVirtualBrainState(token),
        ]);

        setStats(statsData);
        setBrainState(brainData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load training data');
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
          title="Training Simulation System"
          subtitle="Virtual brain for AI-powered candidate matching"
        />
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading training system data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <PageHeader
          title="Training Simulation System"
          subtitle="Virtual brain for AI-powered candidate matching"
        />
        <Card className="border-destructive">
          <CardContent className="flex items-center gap-3 p-6">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div>
              <p className="font-semibold">Error loading training data</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!stats || !brainState) {
    return null;
  }

  const feedbackData = [
    { name: 'Hire', value: stats.feedback_by_type['hire'] || 0, color: '#10b981' },
    { name: 'Reject', value: stats.feedback_by_type['reject'] || 0, color: '#ef4444' },
    { name: 'Applied', value: stats.feedback_by_type['applied'] || 0, color: '#3b82f6' },
    { name: 'Other', value: (stats.feedback_by_type['maybe'] || 0) + (stats.feedback_by_type['interested'] || 0), color: '#f59e0b' },
  ];

  const improvementData = [
    { metric: 'Match Accuracy', current: Math.round(brainState.match_accuracy * 100), baseline: 75 },
    { metric: 'Hire Success', current: Math.round(brainState.hire_success_prediction_accuracy * 100), baseline: 70 },
  ];

  return (
    <div>
      <PageHeader
        title="Training Simulation System"
        subtitle="Virtual brain for AI-powered candidate matching"
      />

      {/* Key Metrics */}
      <div className="mb-6 grid gap-4 md:grid-cols-5">
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Training Samples</p>
                <p className="mt-2 text-2xl font-bold">{stats.total_feedback.toLocaleString()}</p>
              </div>
              <Database className="h-8 w-8 text-blue-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Capabilities Learned</p>
                <p className="mt-2 text-2xl font-bold">{stats.capability_mappings_learned}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Credentials Mapped</p>
                <p className="mt-2 text-2xl font-bold">{stats.credential_mappings_learned}</p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-green-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Success Patterns</p>
                <p className="mt-2 text-2xl font-bold">{stats.success_patterns_discovered}</p>
              </div>
              <Brain className="h-8 w-8 text-orange-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Model Version</p>
              <p className="mt-2 text-2xl font-bold">v{brainState.version}</p>
              {brainState.is_active && <Badge className="mt-2 bg-green-500">Active</Badge>}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Dashboard */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Feedback Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Feedback Distribution</CardTitle>
            <p className="text-sm text-muted-foreground">Training signals by type</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {feedbackData.map((item) => (
                <div key={item.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-3 w-3 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-sm font-medium">{item.name}</span>
                  </div>
                  <div>
                    <span className="font-semibold">{item.value.toLocaleString()}</span>
                    <span className="ml-2 text-xs text-muted-foreground">
                      {stats.total_feedback > 0
                        ? `${Math.round((item.value / stats.total_feedback) * 100)}%`
                        : '0%'
                      }
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Model Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Model Performance</CardTitle>
            <p className="text-sm text-muted-foreground">Accuracy vs baseline</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {improvementData.map((item) => (
                <div key={item.metric}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">{item.metric}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-muted-foreground">Baseline: {item.baseline}%</span>
                      <span className="font-semibold text-lg">{item.current}%</span>
                    </div>
                  </div>
                  <div className="h-2 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all"
                      style={{ width: `${(item.current / 100) * 100}%` }}
                    />
                  </div>
                  <p className="mt-1 text-xs text-green-600 font-medium">
                    ↑ {item.current - item.baseline}% improvement
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Brain State Info */}
        <Card>
          <CardHeader>
            <CardTitle>Virtual Brain Status</CardTitle>
            <p className="text-sm text-muted-foreground">Current model statistics</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center pb-4 border-b">
                <span className="text-sm text-muted-foreground">Total Feedback Samples</span>
                <span className="font-semibold">{brainState.total_feedback_samples.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center pb-4 border-b">
                <span className="text-sm text-muted-foreground">Patterns Learned</span>
                <span className="font-semibold">{brainState.total_patterns_learned}</span>
              </div>
              <div className="flex justify-between items-center pb-4 border-b">
                <span className="text-sm text-muted-foreground">Match Accuracy</span>
                <span className="font-semibold">{Math.round(brainState.match_accuracy * 100)}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Hire Success Accuracy</span>
                <span className="font-semibold">{Math.round(brainState.hire_success_prediction_accuracy * 100)}%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <p className="text-sm text-muted-foreground">Manage training system</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <a
                href="/admin/training/feedback"
                className="block p-3 rounded-lg hover:bg-muted transition-colors border border-transparent hover:border-border"
              >
                <p className="text-sm font-medium">View Feedback</p>
                <p className="text-xs text-muted-foreground">Review training data</p>
              </a>
              <a
                href="/admin/training/mappings"
                className="block p-3 rounded-lg hover:bg-muted transition-colors border border-transparent hover:border-border"
              >
                <p className="text-sm font-medium">Capability Mappings</p>
                <p className="text-xs text-muted-foreground">Manage keyword mappings</p>
              </a>
              <a
                href="/admin/training/insights"
                className="block p-3 rounded-lg hover:bg-muted transition-colors border border-transparent hover:border-border"
              >
                <p className="text-sm font-medium">Insights & Analytics</p>
                <p className="text-xs text-muted-foreground">View learning insights</p>
              </a>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
