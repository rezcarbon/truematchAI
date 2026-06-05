'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, TrendingUp, TrendingDown } from 'lucide-react';
import { useToast } from '@/components/providers/ToastProvider';

interface CandidateSignal {
  candidateId: string;
  candidateName: string;
  position: string;
  keywordScore: number;
  semanticScore: number;
  capabilityScore: number;
  overallScore: number;
  stage: string;
}

interface SignalAnalytics {
  candidates: CandidateSignal[];
  avgKeywordScore: number;
  avgSemanticScore: number;
  avgCapabilityScore: number;
  avgOverallScore: number;
  scoreDistribution: {
    keyword: Record<string, number>;
    semantic: Record<string, number>;
    capability: Record<string, number>;
  };
  insights: string[];
}

export default function ThreeSignalAnalyticsPage() {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState<SignalAnalytics | null>(null);
  const [selectedSignal, setSelectedSignal] = useState<'keyword' | 'semantic' | 'capability'>('keyword');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        setLoading(true);
        setError(null);

        // Mock data - in a real app, fetch from API
        const mockAnalytics: SignalAnalytics = {
          candidates: [
            {
              candidateId: '1',
              candidateName: 'Sarah Chen',
              position: 'Senior Backend Engineer',
              keywordScore: 85,
              semanticScore: 90,
              capabilityScore: 88,
              overallScore: 88,
              stage: 'applied',
            },
            {
              candidateId: '2',
              candidateName: 'Marcus Johnson',
              position: 'Senior Backend Engineer',
              keywordScore: 72,
              semanticScore: 78,
              capabilityScore: 81,
              overallScore: 77,
              stage: 'phone_screen',
            },
            {
              candidateId: '3',
              candidateName: 'Priya Patel',
              position: 'Senior Backend Engineer',
              keywordScore: 88,
              semanticScore: 92,
              capabilityScore: 94,
              overallScore: 91,
              stage: 'technical',
            },
            {
              candidateId: '4',
              candidateName: 'Alex Rivera',
              position: 'Senior Backend Engineer',
              keywordScore: 79,
              semanticScore: 85,
              capabilityScore: 87,
              overallScore: 84,
              stage: 'onsite',
            },
          ],
          avgKeywordScore: 81,
          avgSemanticScore: 86,
          avgCapabilityScore: 87.5,
          avgOverallScore: 85,
          scoreDistribution: {
            keyword: { '80-100': 2, '60-79': 2, '0-59': 0 },
            semantic: { '80-100': 3, '60-79': 1, '0-59': 0 },
            capability: { '80-100': 4, '60-79': 0, '0-59': 0 },
          },
          insights: [
            '🎯 Capability Assessment shows the strongest signal (87.5 avg), suggesting candidates have genuine skills',
            '🔍 Semantic matching (86 avg) is ahead of keyword matching (81 avg), indicating candidates understand concepts deeply',
            '⚠️ Keyword-Capability gap: Sarah has 3pt spread - may need soft skills coaching on communication',
            '✅ Top performers (Priya): All signals aligned (88+ across board) - highly confident hire',
            '💡 Consider expanding semantic/capability criteria for sourcing - less keyword-dependent candidates available',
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
        <PageHeader
          title="Three-Signal Analytics"
          subtitle="Analyze candidate evaluation across all three signals"
        />
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-600">
          {error || 'No data available'}
        </div>
      </div>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score: number) => {
    if (score >= 80) return 'bg-green-50';
    if (score >= 60) return 'bg-yellow-50';
    return 'bg-red-50';
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Three-Signal Analytics"
        subtitle="Understand candidate quality through keyword, semantic, and capability matching"
        icon="BarChart3"
      />

      {/* Average Scores */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Avg Keyword Match</p>
              <p className={`text-3xl font-bold ${getScoreColor(analytics.avgKeywordScore)}`}>
                {Math.round(analytics.avgKeywordScore)}%
              </p>
              <p className="text-xs text-muted-foreground">Resume keywords matching JD</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Avg Semantic Match</p>
              <p className={`text-3xl font-bold ${getScoreColor(analytics.avgSemanticScore)}`}>
                {Math.round(analytics.avgSemanticScore)}%
              </p>
              <p className="text-xs text-muted-foreground">Concept/meaning alignment</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Avg Capability Score</p>
              <p className={`text-3xl font-bold ${getScoreColor(analytics.avgCapabilityScore)}`}>
                {Math.round(analytics.avgCapabilityScore)}%
              </p>
              <p className="text-xs text-muted-foreground">LLM capability assessment</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Overall Fit Score</p>
              <p className={`text-3xl font-bold ${getScoreColor(analytics.avgOverallScore)}`}>
                {Math.round(analytics.avgOverallScore)}%
              </p>
              <p className="text-xs text-muted-foreground">Aggregate of all signals</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Signal Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Signal Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Score Distribution</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              { label: 'Keyword Match', key: 'keyword' as const, color: 'bg-blue-100 text-blue-700' },
              { label: 'Semantic Match', key: 'semantic' as const, color: 'bg-purple-100 text-purple-700' },
              { label: 'Capability', key: 'capability' as const, color: 'bg-green-100 text-green-700' },
            ].map(({ label, key, color }) => {
              const dist = analytics.scoreDistribution[key];
              const total = Object.values(dist).reduce((a, b) => a + b, 0);
              return (
                <div key={key} className="space-y-2">
                  <p className="text-sm font-medium">{label}</p>
                  <div className="flex gap-2">
                    {[
                      { range: '80-100', value: dist['80-100'] || 0, color: 'bg-green-500' },
                      { range: '60-79', value: dist['60-79'] || 0, color: 'bg-yellow-500' },
                      { range: '0-59', value: dist['0-59'] || 0, color: 'bg-red-500' },
                    ].map(({ range, value }) => (
                      <div key={range} className="flex-1">
                        <div className={`h-6 rounded ${value > 0 ? 'bg-gray-200' : 'bg-gray-100'}`}>
                          <div
                            className={`h-6 rounded ${total > 0 ? (value / total) * 100 + '%' : '0%'} ${color} transition-all`}
                          />
                        </div>
                        <p className="text-xs mt-1 text-center">{value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Signal Correlation */}
        <Card>
          <CardHeader>
            <CardTitle>Signal Alignment</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Comparison of how aligned the three signals are for each candidate
            </p>
            {analytics.candidates.map(candidate => {
              const scores = [candidate.keywordScore, candidate.semanticScore, candidate.capabilityScore];
              const max = Math.max(...scores);
              const min = Math.min(...scores);
              const spread = max - min;
              const alignment = spread <= 5 ? 'Perfect' : spread <= 10 ? 'Good' : 'Divergent';

              return (
                <div key={candidate.candidateId} className="space-y-2 pb-3 border-b last:border-0">
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-sm">{candidate.candidateName}</p>
                    <Badge variant={alignment === 'Perfect' ? 'default' : alignment === 'Good' ? 'secondary' : 'outline'}>
                      {alignment}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { label: 'K', score: candidate.keywordScore, color: 'bg-blue-100 text-blue-700' },
                      { label: 'S', score: candidate.semanticScore, color: 'bg-purple-100 text-purple-700' },
                      { label: 'C', score: candidate.capabilityScore, color: 'bg-green-100 text-green-700' },
                    ].map(({ label, score, color }) => (
                      <div key={label} className={`p-2 rounded text-center text-sm font-medium ${color}`}>
                        {label}: {score}%
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>

      {/* Candidate Ranking */}
      <Card>
        <CardHeader>
          <CardTitle>Candidates by Overall Fit</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...analytics.candidates].sort((a, b) => b.overallScore - a.overallScore).map((candidate, idx) => (
              <div key={candidate.candidateId} className={`p-4 rounded-lg ${getScoreBg(candidate.overallScore)}`}>
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span className="text-lg font-bold text-muted-foreground">{idx + 1}</span>
                      <div>
                        <p className="font-medium">{candidate.candidateName}</p>
                        <p className="text-xs text-muted-foreground">{candidate.position}</p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <p className={`text-2xl font-bold ${getScoreColor(candidate.overallScore)}`}>
                        {candidate.overallScore}%
                      </p>
                      <p className="text-xs text-muted-foreground">Overall</p>
                    </div>

                    <div className="flex gap-4">
                      {[
                        { label: 'Keyword', score: candidate.keywordScore, avg: analytics.avgKeywordScore },
                        { label: 'Semantic', score: candidate.semanticScore, avg: analytics.avgSemanticScore },
                        { label: 'Capability', score: candidate.capabilityScore, avg: analytics.avgCapabilityScore },
                      ].map(({ label, score, avg }) => {
                        const trend = score >= avg ? 'up' : 'down';
                        const diff = Math.abs(score - avg);

                        return (
                          <div key={label} className="text-right">
                            <p className="text-sm font-medium">{score}%</p>
                            <div className="flex items-center gap-1 justify-end text-xs">
                              {trend === 'up' ? (
                                <TrendingUp className="h-3 w-3 text-green-600" />
                              ) : (
                                <TrendingDown className="h-3 w-3 text-red-600" />
                              )}
                              <span className={trend === 'up' ? 'text-green-600' : 'text-red-600'}>
                                {diff}pp
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Insights */}
      <Card>
        <CardHeader>
          <CardTitle>Key Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {analytics.insights.map((insight, idx) => (
              <div key={idx} className="flex items-start gap-3 pb-3 border-b last:border-0 last:pb-0">
                <span className="text-lg flex-shrink-0">{insight.split(' ')[0]}</span>
                <p className="text-sm text-muted-foreground">{insight.slice(2)}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
