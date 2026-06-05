'use client';

export const dynamic = 'force-dynamic';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { PageHeader } from '@/components/shared/AppShell';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { getTrainingFeedback, TrainingFeedback } from '@/lib/api/training';
import { AlertCircle, Calendar, MessageSquare, Star, TrendingUp } from 'lucide-react';

const FEEDBACK_TYPE_COLORS: Record<string, { bg: string; text: string }> = {
  hire: { bg: 'bg-green-100', text: 'text-green-700' },
  reject: { bg: 'bg-red-100', text: 'text-red-700' },
  applied: { bg: 'bg-blue-100', text: 'text-blue-700' },
  interested: { bg: 'bg-purple-100', text: 'text-purple-700' },
  not_interested: { bg: 'bg-gray-100', text: 'text-gray-700' },
  maybe: { bg: 'bg-yellow-100', text: 'text-yellow-700' },
};

export default function TrainingFeedbackPage() {
  const { data: session } = useSession();
  const [feedback, setFeedback] = useState<TrainingFeedback[]>([]);
  const [selectedType, setSelectedType] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadFeedback = async () => {
      try {
        if (!session) throw new Error('Not authenticated');

        const token = session?.user?.email || 'session-token';
        const data = await getTrainingFeedback(token, selectedType || undefined);
        setFeedback(data.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load feedback');
      } finally {
        setLoading(false);
      }
    };

    if (session) {
      loadFeedback();
    }
  }, [session, selectedType]);

  const feedbackTypes = ['hire', 'reject', 'applied', 'interested', 'not_interested', 'maybe'];
  const typeCounts = feedbackTypes.reduce((acc, type) => {
    acc[type] = feedback.filter((f) => f.feedback_type === type).length;
    return acc;
  }, {} as Record<string, number>);

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getTypeColors = (type: string) => {
    return FEEDBACK_TYPE_COLORS[type] || { bg: 'bg-gray-100', text: 'text-gray-700' };
  };

  return (
    <div>
      <PageHeader
        title="Training Feedback"
        subtitle="View and manage training signals from recruiters and candidates"
      />

      {/* Filter Stats */}
      <div className="mb-6 grid gap-3 grid-cols-2 md:grid-cols-6">
        <button
          onClick={() => setSelectedType('')}
          className={`p-3 rounded-lg border-2 transition-all text-left ${
            selectedType === ''
              ? 'border-blue-500 bg-blue-50'
              : 'border-border hover:border-border hover:bg-muted'
          }`}
        >
          <p className="text-sm font-medium">All</p>
          <p className="text-lg font-bold">{feedback.length}</p>
        </button>
        {feedbackTypes.map((type) => (
          <button
            key={type}
            onClick={() => setSelectedType(type)}
            className={`p-3 rounded-lg border-2 transition-all text-left capitalize ${
              selectedType === type
                ? 'border-blue-500 bg-blue-50'
                : 'border-border hover:border-border hover:bg-muted'
            }`}
          >
            <p className="text-sm font-medium">{type.replace('_', ' ')}</p>
            <p className="text-lg font-bold">{typeCounts[type]}</p>
          </button>
        ))}
      </div>

      {/* Feedback List */}
      {loading ? (
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-muted-foreground">Loading feedback...</p>
          </CardContent>
        </Card>
      ) : error ? (
        <Card className="border-destructive">
          <CardContent className="flex items-center gap-3 p-6">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div>
              <p className="font-semibold">Error loading feedback</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </CardContent>
        </Card>
      ) : feedback.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <MessageSquare className="h-8 w-8 mx-auto mb-4 text-muted-foreground opacity-50" />
            <p className="text-muted-foreground">No feedback found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {feedback.map((item) => {
            const colors = getTypeColors(item.feedback_type);
            return (
              <Card key={item.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <Badge className={`${colors.bg} ${colors.text} border-0 capitalize`}>
                          {item.feedback_type.replace('_', ' ')}
                        </Badge>
                        {item.outcome && (
                          <Badge variant="secondary">{item.outcome}</Badge>
                        )}
                        {item.rating && (
                          <div className="flex items-center gap-1">
                            {Array.from({ length: item.rating }).map((_, i) => (
                              <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                            ))}
                          </div>
                        )}
                      </div>

                      {item.comments && (
                        <p className="text-sm text-foreground mb-3 italic">"{item.comments}"</p>
                      )}

                      <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {formatDate(item.created_at)}
                        </div>
                        {item.time_to_action_seconds && (
                          <div className="flex items-center gap-1">
                            <TrendingUp className="h-4 w-4" />
                            {Math.round(item.time_to_action_seconds / 60)} min to decide
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="text-right">
                      <p className="text-xs text-muted-foreground">ID:</p>
                      <p className="text-xs font-mono text-foreground">{item.id.slice(0, 8)}...</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
