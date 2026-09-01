'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import Link from 'next/link';
import { PageHeader } from '@/components/shared/PageHeader';
import { ApplicationPipeline, ApplicationCard, TimelineView } from '@/components/candidate';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle, Loader2, CheckCircle2, Clock, XCircle } from 'lucide-react';

interface Application {
  id: string;
  positionTitle: string;
  company: string;
  status: 'applied' | 'reviewing' | 'interviewed' | 'offered' | 'rejected';
  appliedDate: string;
  matchScore?: number;
  feedback?: string;
  offerDetails?: {
    salary: string;
    startDate: string;
  };
}

export default function HistoryPage() {
  const { data: session } = useSession();
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('timeline');

  useEffect(() => {
    if (session?.user) {
      loadApplications();
    }
  }, [session]);

  const loadApplications = async () => {
    try {
      setLoading(true);
      setError(null);

      const accessToken = (session?.user as { accessToken?: string })?.accessToken;
      if (!accessToken) {
        throw new Error('Not authenticated');
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${apiUrl}/api/v1/candidates/applications`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load applications');
      }

      const data = await response.json();
      setApplications(Array.isArray(data) ? data : data.applications || []);
    } catch (err) {
      console.error('Error loading applications:', err);
      setError(err instanceof Error ? err.message : 'Failed to load applications');

      // Mock data for demo purposes
      setApplications([
        {
          id: 'app_001',
          positionTitle: 'Senior Backend Engineer',
          company: 'TechCorp',
          status: 'interviewed',
          appliedDate: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
          matchScore: 85,
        },
        {
          id: 'app_002',
          positionTitle: 'Platform Engineer',
          company: 'CloudSystems',
          status: 'reviewing',
          appliedDate: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
          matchScore: 78,
        },
        {
          id: 'app_003',
          positionTitle: 'Staff Engineer',
          company: 'StartupXYZ',
          status: 'offered',
          appliedDate: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
          matchScore: 92,
          offerDetails: {
            salary: '$250,000 - $300,000',
            startDate: '2026-08-15',
          },
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const organizeByStage = () => {
    const stages: { [key: string]: Application[] } = {
      applied: [],
      reviewing: [],
      interviewed: [],
      offered: [],
      rejected: [],
    };

    applications.forEach((app) => {
      stages[app.status].push(app);
    });

    return stages;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'applied':
        return <Clock className="h-4 w-4 text-blue-600" />;
      case 'reviewing':
        return <Clock className="h-4 w-4 text-amber-600" />;
      case 'interviewed':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'offered':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'rejected':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return null;
    }
  };

  const stages = organizeByStage();

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Application History"
          subtitle="Track your job applications and career progress"
          icon="History"
        />

        <div className="container mx-auto px-4 py-8">
          <Card>
            <CardContent className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary mr-2" />
              <p className="text-muted-foreground">Loading your applications...</p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Application History"
        subtitle="Track your job applications and career progress"
        icon="History"
      />

      <div className="container mx-auto px-4 py-8">
        {error && !applications.length && (
          <Card className="border-amber-200/60 bg-amber-50/30 mb-6">
            <CardContent className="flex items-start gap-3 pt-6">
              <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-amber-600">{error} (showing demo data)</p>
            </CardContent>
          </Card>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
            <TabsTrigger value="pipeline">Pipeline</TabsTrigger>
          </TabsList>

          {/* Timeline Tab */}
          <TabsContent value="timeline" className="space-y-6">
            {applications.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <p className="text-lg font-medium text-muted-foreground">No applications yet</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Start applying to jobs to see them here
                  </p>
                </CardContent>
              </Card>
            ) : (
              <TimelineView applications={applications} />
            )}
          </TabsContent>

          {/* Pipeline Tab */}
          <TabsContent value="pipeline" className="space-y-6">
            {applications.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <p className="text-lg font-medium text-muted-foreground">No applications yet</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Start applying to jobs to see them here
                  </p>
                </CardContent>
              </Card>
            ) : (
              <ApplicationPipeline stages={stages} />
            )}
          </TabsContent>
        </Tabs>

        {/* Detailed Applications List */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>All Applications</CardTitle>
          </CardHeader>
          <CardContent>
            {applications.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No applications to display
              </p>
            ) : (
              <div className="space-y-3">
                {applications.map((app) => (
                  <div
                    key={app.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <div className="p-2 bg-secondary rounded-lg">
                        {getStatusIcon(app.status)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium">{app.positionTitle}</p>
                        <p className="text-sm text-muted-foreground">
                          {app.company} • {new Date(app.appliedDate).toLocaleDateString()}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      {app.matchScore && (
                        <div className="text-center">
                          <p className="text-sm font-semibold">{app.matchScore}%</p>
                          <p className="text-xs text-muted-foreground">Match</p>
                        </div>
                      )}
                      <div className="text-center">
                        <p className="text-sm font-semibold capitalize">{app.status}</p>
                        <p className="text-xs text-muted-foreground">Status</p>
                      </div>
                      <Link href={`/candidate/application/${app.id}`}>
                        <button className="px-3 py-1 text-sm font-medium border rounded-lg hover:bg-muted transition-colors">
                          View
                        </button>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
