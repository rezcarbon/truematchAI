'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertCircle, CheckCircle2, Clock, X } from 'lucide-react';

interface GovernanceReview {
  id: string;
  review_type: string;
  resource_id: string;
  user_id: string;
  failed_gates: string[];
  status: string;
  failure_reason: string;
  created_at: string;
}

interface GovernanceStats {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
  escalated: number;
}

export default function GovernanceDashboardPage() {
  const router = useRouter();
  const { data: session } = useSession();
  const [reviews, setReviews] = useState<GovernanceReview[]>([]);
  const [stats, setStats] = useState<GovernanceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('pending');
  const [error, setError] = useState<string | null>(null);

  // Check authorization
  useEffect(() => {
    if (session?.user) {
      const userRole = (session.user as { role?: string }).role;
      if (userRole !== 'admin' && userRole !== 'reviewer') {
        router.push('/dashboard');
      }
    }
  }, [session, router]);

  // Fetch reviews
  useEffect(() => {
    const fetchReviews = async () => {
      try {
        setLoading(true);
        const accessToken = (session?.user as { accessToken?: string })?.accessToken;
        if (!accessToken) {
          throw new Error('Not authenticated');
        }

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
        const response = await fetch(
          `${apiUrl}/api/v1/governance-reviews?status_filter=${filter}`,
          {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch reviews');
        }

        const data = await response.json();
        setReviews(data.items || []);
        setStats({
          total: data.total,
          pending: data.pending,
          approved: data.approved,
          rejected: data.rejected,
          escalated: data.escalated,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load governance reviews');
      } finally {
        setLoading(false);
      }
    };

    if (session?.user) {
      fetchReviews();
    }
  }, [session, filter]);

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'pending':
        return 'destructive';
      case 'approved':
        return 'default';
      case 'rejected':
        return 'secondary';
      case 'escalated':
        return 'outline';
      default:
        return 'outline';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-amber-600" />;
      case 'approved':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'rejected':
        return <X className="h-4 w-4 text-red-600" />;
      default:
        return <AlertCircle className="h-4 w-4 text-blue-600" />;
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Governance Dashboard"
          subtitle="Review and manage governance gate failures"
          icon="Shield"
        />
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-64">
            <p className="text-muted-foreground">Loading governance reviews...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Governance Dashboard"
        subtitle="Review and manage governance gate failures requiring human oversight"
        icon="Shield"
      />

      <div className="container mx-auto px-4 py-8 space-y-8">
        {error && (
          <Card className="border-red-200/60 bg-red-50/30">
            <CardContent className="flex items-start gap-3 pt-6">
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-red-600">Error</p>
                <p className="text-sm text-red-600/80">{error}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Statistics Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground">Total Reviews</p>
                <p className="text-3xl font-bold mt-2">{stats.total}</p>
              </CardContent>
            </Card>
            <Card className="border-amber-200/60 bg-amber-50/30">
              <CardContent className="pt-6">
                <p className="text-sm text-amber-900">Pending</p>
                <p className="text-3xl font-bold mt-2 text-amber-600">{stats.pending}</p>
              </CardContent>
            </Card>
            <Card className="border-green-200/60 bg-green-50/30">
              <CardContent className="pt-6">
                <p className="text-sm text-green-900">Approved</p>
                <p className="text-3xl font-bold mt-2 text-green-600">{stats.approved}</p>
              </CardContent>
            </Card>
            <Card className="border-red-200/60 bg-red-50/30">
              <CardContent className="pt-6">
                <p className="text-sm text-red-900">Rejected</p>
                <p className="text-3xl font-bold mt-2 text-red-600">{stats.rejected}</p>
              </CardContent>
            </Card>
            <Card className="border-blue-200/60 bg-blue-50/30">
              <CardContent className="pt-6">
                <p className="text-sm text-blue-900">Escalated</p>
                <p className="text-3xl font-bold mt-2 text-blue-600">{stats.escalated}</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filter Buttons */}
        <div className="flex gap-2">
          {(['all', 'pending', 'approved', 'rejected', 'escalated'] as const).map((status) => (
            <Button
              key={status}
              variant={filter === status ? 'default' : 'outline'}
              onClick={() => setFilter(status)}
              className="capitalize"
            >
              {status === 'all' ? 'All Reviews' : status}
            </Button>
          ))}
        </div>

        {/* Reviews List */}
        <div className="space-y-4">
          {reviews.length === 0 ? (
            <Card>
              <CardContent className="flex items-center justify-center h-32">
                <p className="text-muted-foreground">No governance reviews found</p>
              </CardContent>
            </Card>
          ) : (
            reviews.map((review) => (
              <Card key={review.id} className="hover:shadow-md transition-shadow">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-4 flex-1">
                      {getStatusIcon(review.status)}
                      <div className="flex-1">
                        <p className="font-semibold">{review.failure_reason}</p>
                        <p className="text-sm text-muted-foreground mt-1">
                          Resource: <code className="text-xs bg-secondary px-2 py-1 rounded">{review.resource_id}</code>
                        </p>
                        <div className="flex gap-2 mt-2">
                          {review.failed_gates.map((gate) => (
                            <Badge key={gate} variant="outline" className="capitalize">
                              {gate}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                    <Badge variant={getStatusBadgeVariant(review.status)} className="capitalize">
                      {review.status}
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <p>
                      Created: {new Date(review.created_at).toLocaleDateString()} at{' '}
                      {new Date(review.created_at).toLocaleTimeString()}
                    </p>
                    {review.status === 'pending' && (
                      <Button
                        size="sm"
                        onClick={() => router.push(`/admin/governance-reviews/${review.id}`)}
                      >
                        Review
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
