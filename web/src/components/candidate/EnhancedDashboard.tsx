'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScoreGauge } from '@/components/shared/ScoreGauge';
import { ScoreTrio } from '@/components/shared/ScoreTrio';
import { DeltaVisualization } from '@/components/assessment/DeltaVisualization';
import {
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Target,
  Zap,
  CheckCircle,
  AlertCircle,
  Clock,
  MessageSquare,
  Award,
  BookOpen,
  Calendar,
} from 'lucide-react';
import type { Assessment } from '@/lib/types';

interface EnhancedDashboardProps {
  assessment: Assessment;
  assessmentCount: number;
  averageScore: number;
  activeApplications: number;
  recentActivity?: Array<{
    id: string;
    type: 'assessment' | 'application' | 'message' | 'update';
    title: string;
    description: string;
    timestamp: string;
    icon?: React.ReactNode;
  }>;
}

export function EnhancedDashboard({
  assessment,
  assessmentCount,
  averageScore,
  activeApplications,
  recentActivity = [],
}: EnhancedDashboardProps) {
  const [selectedAssessment, setSelectedAssessment] = useState<Assessment | null>(assessment);

  useEffect(() => {
    setSelectedAssessment(assessment);
  }, [assessment]);

  // Extract strengths from capability score components
  const strengths = selectedAssessment?.capabilityScore.components
    ?.filter((c) => c.score >= 70)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3) || [];

  // Extract gaps from capability score components
  const gaps = selectedAssessment?.capabilityScore.components
    ?.filter((c) => c.score < 70)
    .sort((a, b) => a.score - b.score) || [];

  // Calculate recommended next steps
  const nextSteps = [
    {
      title: 'Explore active roles',
      description: `Apply to roles matching your ${selectedAssessment?.capabilityScore.overall}+ capability score`,
      icon: Target,
      actionText: 'Browse roles',
      actionHref: '/candidate/jobs',
    },
    {
      title: 'Complete your profile',
      description: 'Add portfolio links and additional experience to increase visibility',
      icon: CheckCircle,
      actionText: 'Update profile',
      actionHref: '/candidate/profile',
    },
    {
      title: 'View detailed insights',
      description: 'Dive deeper into your assessment results and capability breakdown',
      icon: BookOpen,
      actionText: 'See details',
      actionHref: `/candidate/assessment/${selectedAssessment?.id}`,
    },
  ];

  // Mock activity feed data if none provided
  const activityFeed = recentActivity.length > 0
    ? recentActivity
    : [
        {
          id: '1',
          type: 'assessment' as const,
          title: 'Assessment completed',
          description: `You completed the assessment for ${selectedAssessment?.positionTitle}`,
          timestamp: selectedAssessment?.createdAt || new Date().toISOString(),
          icon: Award,
        },
        {
          id: '2',
          type: 'message' as const,
          title: 'New message from recruiter',
          description: 'Jocelyn Tan sent you a message about your application',
          timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          icon: MessageSquare,
        },
      ];

  const getMatchTypeLabel = (matchType?: string) => {
    const labels: Record<string, string> = {
      hidden_gem: 'Hidden gem — unlisted capability',
      surfaced_strong_match: 'Strong match — clear fit',
      keyword_aligned: 'Keyword aligned — surface match',
    };
    return labels[matchType || ''] || 'Unrated';
  };

  const getMatchTypeBadgeClass = (matchType?: string) => {
    const classes: Record<string, string> = {
      hidden_gem: 'bg-amber-50 text-amber-700 border-amber-200',
      surfaced_strong_match: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      keyword_aligned: 'bg-slate-50 text-slate-600 border-slate-200',
    };
    return classes[matchType || ''] || 'bg-slate-50 text-slate-600 border-slate-200';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      if (diffHours === 0) return 'Today';
      return `${diffHours}h ago`;
    }
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    });
  };

  return (
    <div className="space-y-6">
      {/* Assessment Summary Card */}
      <Card className="overflow-hidden border-l-4 border-l-primary">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-2xl">{selectedAssessment?.positionTitle}</CardTitle>
              <CardDescription className="mt-2">
                Assessment completed {formatDate(selectedAssessment?.createdAt || new Date().toISOString())}
              </CardDescription>
            </div>
            <Badge className={getMatchTypeBadgeClass(selectedAssessment?.matchType)}>
              {getMatchTypeLabel(selectedAssessment?.matchType)}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {selectedAssessment && (
              <ScoreTrio
                traditional={selectedAssessment.traditionalScore}
                semantic={selectedAssessment.semanticScore}
                capability={selectedAssessment.capabilityScore.overall}
                delta={selectedAssessment.delta}
                matchType={selectedAssessment.matchType as any}
              />
            )}
            <p className="text-sm text-muted-foreground italic border-t pt-4">
              "{selectedAssessment?.narrative}"
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Three-Signal Gauges (Large View) */}
      {selectedAssessment && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Traditional ATS Score</CardTitle>
              <CardDescription className="text-xs">Keyword match</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center gap-4">
              <ScoreGauge score={selectedAssessment.traditionalScore} size={140} />
              <div className="text-center">
                <p className="text-2xl font-bold tabular-nums">
                  {selectedAssessment.traditionalScore}
                </p>
                <p className="text-xs text-muted-foreground mt-1">out of 100</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Delta</CardTitle>
              <CardDescription className="text-xs">Capability gap</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center justify-center gap-4">
              <div className="flex items-center gap-2">
                {selectedAssessment.delta >= 0 ? (
                  <TrendingUp className="h-6 w-6 text-emerald-600" />
                ) : (
                  <TrendingDown className="h-6 w-6 text-red-600" />
                )}
                <span
                  className={`text-4xl font-extrabold tabular-nums ${
                    selectedAssessment.delta >= 0 ? 'text-emerald-600' : 'text-red-600'
                  }`}
                >
                  {selectedAssessment.delta >= 0 ? '+' : ''}
                  {selectedAssessment.delta}
                </span>
              </div>
              <p className="text-xs text-muted-foreground text-center">
                {selectedAssessment.delta >= 0
                  ? 'Capability exceeds keyword match'
                  : 'Keyword match exceeds capability'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Capability Score</CardTitle>
              <CardDescription className="text-xs">Demonstrated ability</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center gap-4">
              <ScoreGauge score={selectedAssessment.capabilityScore.overall} size={140} />
              <div className="text-center">
                <p className="text-2xl font-bold tabular-nums">
                  {selectedAssessment.capabilityScore.overall}
                </p>
                <p className="text-xs text-muted-foreground mt-1">overall</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground font-medium">Assessments</p>
                <p className="mt-2 text-3xl font-bold">{assessmentCount}</p>
              </div>
              <Award className="h-8 w-8 text-primary/30" />
            </div>
            <p className="text-xs text-muted-foreground mt-4">Completed evaluations</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground font-medium">Avg. Score</p>
                <p className="mt-2 text-3xl font-bold">{Math.round(averageScore)}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-primary/30" />
            </div>
            <p className="text-xs text-muted-foreground mt-4">Average capability</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground font-medium">Active</p>
                <p className="mt-2 text-3xl font-bold">{activeApplications}</p>
              </div>
              <Zap className="h-8 w-8 text-primary/30" />
            </div>
            <p className="text-xs text-muted-foreground mt-4">Open applications</p>
          </CardContent>
        </Card>
      </div>

      {/* Delta Visualization */}
      {selectedAssessment && (
        <DeltaVisualization
          traditionalScore={selectedAssessment.traditionalScore}
          capabilityScore={selectedAssessment.capabilityScore.overall}
        />
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Strengths Snapshot */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-amber-500" />
              Top Strengths
            </CardTitle>
            <CardDescription>Your strongest capabilities</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {strengths.length > 0 ? (
                strengths.map((strength, idx) => (
                  <div key={idx} className="flex items-center justify-between gap-4 rounded-lg border p-3">
                    <div className="flex-1">
                      <p className="font-medium text-sm">{strength.label}</p>
                      <p className="text-xs text-muted-foreground">
                        Weight: {Math.round(strength.weight * 100)}%
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-emerald-600 tabular-nums">
                        {strength.score}
                      </p>
                      <p className="text-xs text-muted-foreground">score</p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No strength data available</p>
              )}
            </div>
            <Button variant="outline" className="w-full mt-4" size="sm">
              <BookOpen className="h-4 w-4 mr-2" />
              Full Breakdown
            </Button>
          </CardContent>
        </Card>

        {/* Key Gaps */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-orange-500" />
              Key Gaps
            </CardTitle>
            <CardDescription>Areas for development</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {gaps.length > 0 ? (
                gaps.map((gap, idx) => (
                  <div key={idx} className="flex items-center justify-between gap-4 rounded-lg border p-3">
                    <div className="flex-1">
                      <p className="font-medium text-sm">{gap.label}</p>
                      <p className="text-xs text-muted-foreground">
                        Development opportunity
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-orange-500 tabular-nums">
                        {gap.score}
                      </p>
                      <p className="text-xs text-muted-foreground">score</p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No gaps detected</p>
              )}
            </div>
            <Button variant="outline" className="w-full mt-4" size="sm">
              <BookOpen className="h-4 w-4 mr-2" />
              Learning Paths
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Next Steps Guidance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-blue-500" />
            Recommended Next Steps
          </CardTitle>
          <CardDescription>Maximize your opportunities</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            {nextSteps.map((step, idx) => {
              const Icon = step.icon;
              return (
                <div
                  key={idx}
                  className="rounded-lg border p-4 hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <Icon className="h-5 w-5 text-primary flex-shrink-0 mt-1" />
                    <div className="flex-1">
                      <h4 className="font-medium text-sm mb-1">{step.title}</h4>
                      <p className="text-xs text-muted-foreground mb-3">{step.description}</p>
                      <Link href={step.actionHref}>
                        <Button variant="ghost" size="sm" className="h-7 text-xs px-2">
                          {step.actionText}
                          <ArrowRight className="h-3 w-3 ml-1" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Activity Feed */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-slate-500" />
            Recent Activity
          </CardTitle>
          <CardDescription>Your latest updates</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {activityFeed.length > 0 ? (
              activityFeed.map((activity) => {
                const ActivityIcon = activity.icon || Clock;
                return (
                  <div
                    key={activity.id}
                    className="flex gap-4 py-3 border-b last:border-b-0"
                  >
                    <div className="flex-shrink-0 mt-1">
                      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                        <ActivityIcon className="h-5 w-5 text-primary" />
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm">{activity.title}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {activity.description}
                      </p>
                      <p className="text-xs text-muted-foreground mt-2">
                        {formatDate(activity.timestamp)}
                      </p>
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="text-sm text-muted-foreground py-4">No recent activity</p>
            )}
          </div>
          <Link href="/candidate/history">
            <Button variant="ghost" className="w-full mt-4" size="sm">
              View all activity
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </CardContent>
      </Card>

      {/* Quick Action Buttons */}
      <div className="grid gap-3 md:grid-cols-3">
        <Link href="/candidate/jobs">
          <Button variant="outline" className="w-full" size="lg">
            <Target className="h-4 w-4 mr-2" />
            Browse Roles
          </Button>
        </Link>
        <Link href="/candidate/profile">
          <Button variant="outline" className="w-full" size="lg">
            <CheckCircle className="h-4 w-4 mr-2" />
            Update Profile
          </Button>
        </Link>
        <Link href="/candidate/settings">
          <Button variant="outline" className="w-full" size="lg">
            <Clock className="h-4 w-4 mr-2" />
            Preferences
          </Button>
        </Link>
      </div>
    </div>
  );
}
