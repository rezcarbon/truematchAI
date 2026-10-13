'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useSession } from 'next-auth/react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  AssessmentSummary,
  ActivityFeed,
  StatCards,
} from '@/components/candidate';
import { Loader2, AlertCircle, X, FileText, Briefcase, TrendingUp } from 'lucide-react';

interface DashboardData {
  assessmentCount: number;
  averageScore: number;
  activeApplications: number;
  lastAssessment?: {
    id: string;
    positionTitle: string;
    score: number;
    date: string;
  };
  recentActivity: Array<{
    id: string;
    type: 'assessment' | 'message' | 'application' | 'update';
    title: string;
    description: string;
    timestamp: string;
  }>;
}

export default function CandidateDashboard() {
  const { data: session } = useSession();
  const [showProfileBanner, setShowProfileBanner] = useState(false);
  const [profileIncomplete, setProfileIncomplete] = useState(false);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (session?.user) {
      checkProfileCompletion();
      loadDashboardData();
    }
  }, [session]);

  const checkProfileCompletion = async () => {
    try {
      const accessToken = (session?.user as { accessToken?: string })?.accessToken;
      if (!accessToken) return;

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${apiUrl}/api/v1/profile/user/me`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (response.ok) {
        const profile = await response.json();
        const isIncomplete = !profile.display_name || profile.display_name.trim() === '';
        setProfileIncomplete(isIncomplete);
        setShowProfileBanner(isIncomplete);
      }
    } catch (error) {
      console.error('Failed to check profile:', error);
    }
  };

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const accessToken = (session?.user as { accessToken?: string })?.accessToken;
      if (!accessToken) {
        throw new Error('Not authenticated');
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${apiUrl}/api/v1/candidates/dashboard`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      } else {
        throw new Error('Failed to load dashboard data');
      }
    } catch (err) {
      console.error('Error loading dashboard:', err);
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');

      // Mock data for demo
      setDashboardData({
        assessmentCount: 3,
        averageScore: 84,
        activeApplications: 2,
        lastAssessment: {
          id: 'asm_001',
          positionTitle: 'Senior Backend Engineer',
          score: 88,
          date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        },
        recentActivity: [
          {
            id: '1',
            type: 'assessment',
            title: 'Assessment completed',
            description: 'You completed the assessment for Senior Backend Engineer',
            timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          },
          {
            id: '2',
            type: 'application',
            title: 'Application submitted',
            description: 'You applied to Platform Engineer at TechCorp',
            timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
          },
          {
            id: '3',
            type: 'message',
            title: 'New message from recruiter',
            description: 'Jocelyn Tan sent you a message about your application',
            timestamp: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
          },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    {
      icon: FileText,
      label: 'Upload Resume',
      description: 'Add a new resume version',
      href: '/candidate/upload',
      color: 'bg-blue-50 text-blue-600',
    },
    {
      icon: Briefcase,
      label: 'Browse Jobs',
      description: 'Explore job opportunities',
      href: '/candidate/jobs',
      color: 'bg-green-50 text-green-600',
    },
    {
      icon: TrendingUp,
      label: 'CV Analysis',
      description: 'Analyze your resume',
      href: '/candidate/cv-analysis',
      color: 'bg-purple-50 text-purple-600',
    },
  ];

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Your Dashboard"
          subtitle="A capability-first view of how you match open roles"
          icon="LayoutDashboard"
        />

        <div className="container mx-auto px-4 py-8">
          <Card>
            <CardContent className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary mr-2" />
              <p className="text-muted-foreground">Loading your dashboard...</p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Your Dashboard"
        subtitle="A capability-first view of how you match open roles"
        icon="LayoutDashboard"
      />

      <div className="container mx-auto px-4 py-8 space-y-6">
        {/* Profile Completion Banner */}
        {showProfileBanner && profileIncomplete && (
          <div className="flex items-start gap-3 rounded-lg bg-amber-50/60 border border-amber-200/60 p-4">
            <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-amber-900">Complete your profile</p>
              <p className="text-xs text-amber-700 mt-1">
                Add your name and professional details to unlock all features and appear more credible to recruiters.
              </p>
              <div className="mt-3 flex gap-2">
                <Link href="/candidate/profile">
                  <Button size="sm" variant="default" className="h-8">
                    Complete now
                  </Button>
                </Link>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-8"
                  onClick={() => setShowProfileBanner(false)}
                >
                  Dismiss
                </Button>
              </div>
            </div>
            <button
              onClick={() => setShowProfileBanner(false)}
              className="text-amber-600 hover:text-amber-700 flex-shrink-0"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Error Banner */}
        {error && !dashboardData && (
          <Card className="border-amber-200/60 bg-amber-50/30">
            <CardContent className="flex items-start gap-3 pt-6">
              <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-amber-600">{error} (showing demo data)</p>
            </CardContent>
          </Card>
        )}

        {dashboardData && (
          <>
            {/* Stats Cards */}
            <StatCards
              assessmentCount={dashboardData.assessmentCount}
              averageScore={dashboardData.averageScore}
              activeApplications={dashboardData.activeApplications}
            />

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {quickActions.map((action) => {
                const Icon = action.icon;
                return (
                  <Link key={action.href} href={action.href}>
                    <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer">
                      <CardContent className="flex items-center gap-3 pt-6">
                        <div className={`p-2 rounded-lg ${action.color}`}>
                          <Icon className="h-5 w-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium">{action.label}</p>
                          <p className="text-xs text-muted-foreground">{action.description}</p>
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                );
              })}
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column: Assessment & History */}
              <div className="lg:col-span-2 space-y-6">
                {/* Latest Assessment */}
                {dashboardData.lastAssessment && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Latest Assessment</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="font-medium">{dashboardData.lastAssessment.positionTitle}</p>
                          <p className="text-sm text-muted-foreground">
                            {new Date(dashboardData.lastAssessment.date).toLocaleDateString()}
                          </p>
                        </div>
                        <div className="text-center">
                          <p className="text-3xl font-bold text-primary">
                            {dashboardData.lastAssessment.score}
                          </p>
                          <p className="text-xs text-muted-foreground">Score</p>
                        </div>
                      </div>
                      <Button className="w-full mt-4">View Assessment</Button>
                    </CardContent>
                  </Card>
                )}

                {/* Assessment Summary */}
                <AssessmentSummary
                  totalAssessments={dashboardData.assessmentCount}
                  averageScore={dashboardData.averageScore}
                  bestScore={95}
                  lowestScore={72}
                />
              </div>

              {/* Right Column: Recent Activity & Stats */}
              <div className="space-y-6">
                {/* Recent Activity */}
                <Card>
                  <CardHeader>
                    <CardTitle>Recent Activity</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ActivityFeed activities={dashboardData.recentActivity} />
                  </CardContent>
                </Card>

                {/* Applications Status */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Applications</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Active</span>
                      <Badge variant="default">{dashboardData.activeApplications}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Total</span>
                      <Badge variant="outline">12</Badge>
                    </div>
                    <Link href="/candidate/history">
                      <Button variant="outline" className="w-full mt-2">
                        View All
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
