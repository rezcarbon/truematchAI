import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
'use client';
function cn(...inputs: any[]) {
  return twMerge(clsx(inputs));
}

import { AlertCircle, CheckCircle2, Clock, X, Loader2 } from 'lucide-react';
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function Badge({ variant = "default", className, ...props }: any) {
  const variants: any = {
    default: "bg-blue-100 text-blue-800",
    secondary: "bg-gray-100 text-gray-800",
    success: "bg-green-100 text-green-800",
    danger: "bg-red-100 text-red-800",
    warning: "bg-yellow-100 text-yellow-800",
  };
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-1 text-xs font-medium", variants[variant], className)} {...props} />
  );
}

function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
    </div>
  );
}

function Button({ className, variant = "default", size = "default", ...props }: any) {
  const variants: any = { default: "bg-blue-600 text-white hover:bg-blue-700", outline: "border border-gray-300 bg-white hover:bg-gray-50", ghost: "hover:bg-gray-100" };
  const sizes: any = { default: "px-4 py-2", sm: "px-3 py-1 text-sm", lg: "px-6 py-3 text-lg" };
  return <button className={cn("inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none", variants[variant], sizes[size], className)} {...props} />;
}

function Card({ className, ...props }: any) {
  return (
    <div className={cn("rounded-lg border border-gray-200 bg-white shadow-sm", className)} {...props} />
  );
}
function CardHeader({ className, ...props }: any) {
  return <div className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />;
}
function CardTitle({ className, ...props }: any) {
  return <h2 className={cn("text-2xl font-semibold leading-none tracking-tight", className)} {...props} />;
}
function CardDescription({ className, ...props }: any) {
  return <p className={cn("text-sm text-gray-500", className)} {...props} />;
}
function CardContent({ className, ...props }: any) {
  return <div className={cn("p-6 pt-0", className)} {...props} />;
}
// adminApi removed - use fetch directly;

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
  const [reviews, setReviews] = useState<GovernanceReview[]>([]);
  const [stats, setStats] = useState<GovernanceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('pending');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchReviews = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await adminApi.getGovernanceConfig();
        setReviews(data.reviews || []);
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

    fetchReviews();
  }, [filter]);

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
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
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


