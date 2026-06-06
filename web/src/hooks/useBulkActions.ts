import { useState, useCallback } from 'react';
import { useToast } from '@/components/providers/ToastProvider';

export interface BulkActionRequest {
  type: 'stage' | 'tag' | 'interview' | 'reject';
  candidateIds: string[];
  payload?: {
    newStage?: string;
    tagsToAdd?: string[];
    tagsToRemove?: string[];
    interviewData?: {
      meetingPlatform: string;
      scheduledAt: Date;
      interviewerIds: string[];
    };
  };
}

interface BulkActionResult {
  successful: number;
  failed: number;
  errors?: string[];
}

interface UseBulkActionsResult {
  executeBulkAction: (request: BulkActionRequest) => Promise<BulkActionResult>;
  loading: boolean;
  error: string | null;
}

/**
 * Hook for executing bulk actions on multiple candidates
 * Supports: stage updates, tag assignments, interview scheduling, rejections
 */
export function useBulkActions(): UseBulkActionsResult {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeBulkAction = useCallback(
    async (request: BulkActionRequest): Promise<BulkActionResult> => {
      try {
        setLoading(true);
        setError(null);

        if (request.candidateIds.length === 0) {
          throw new Error('No candidates selected');
        }

        let endpoint = '';
        const body: Record<string, unknown> = {
          candidate_ids: request.candidateIds,
          ...request.payload,
        };

        switch (request.type) {
          case 'stage':
            if (!request.payload?.newStage) {
              throw new Error('New stage is required');
            }
            endpoint = '/api/proxy/ats/bulk-actions/stage';
            body.new_stage = request.payload.newStage;
            break;

          case 'tag':
            if (!request.payload?.tagsToAdd && !request.payload?.tagsToRemove) {
              throw new Error('Tags to add or remove are required');
            }
            endpoint = '/api/proxy/ats/bulk-actions/tags';
            body.tags_to_add = request.payload.tagsToAdd || [];
            body.tags_to_remove = request.payload.tagsToRemove || [];
            break;

          case 'interview':
            if (!request.payload?.interviewData) {
              throw new Error('Interview data is required');
            }
            endpoint = '/api/proxy/ats/bulk-actions/interviews';
            body.interview_data = {
              meeting_platform: request.payload.interviewData.meetingPlatform,
              scheduled_at: request.payload.interviewData.scheduledAt.toISOString(),
              interviewer_ids: request.payload.interviewData.interviewerIds,
            };
            break;

          case 'reject':
            endpoint = '/api/proxy/ats/bulk-actions/reject';
            break;

          default:
            throw new Error(`Unknown action type: ${request.type}`);
        }

        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });

        if (!response.ok) {
          throw new Error('Bulk action failed');
        }

        const result: BulkActionResult = await response.json();

        const message = `${result.successful} candidate(s) updated${
          result.failed > 0 ? `, ${result.failed} failed` : ''
        }`;
        addToast(message, result.failed > 0 ? 'warning' : 'success');

        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Bulk action failed';
        setError(message);
        addToast(message, 'error');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [addToast]
  );

  return {
    executeBulkAction,
    loading,
    error,
  };
}
