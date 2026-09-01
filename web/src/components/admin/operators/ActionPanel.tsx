'use client';

/**
 * ActionPanel Component
 *
 * Modal-based action handler for queue item decisions.
 * Provides separate workflows for approve, reject, and hold actions.
 *
 * Features:
 * - Modal form management
 * - Action-specific fields
 * - Loading states during submission
 * - Success/error feedback
 * - Validation and required fields
 * - Toast notifications for results
 */

import { useState, useCallback } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  X,
  ChevronRight,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';

/**
 * Action type enum
 */
type ActionType = 'approve' | 'reject' | 'hold' | null;

/**
 * Action payload sent to parent
 */
interface ActionPayload {
  action: ActionType;
  notes?: string;
  reason?: string;
  holdUntil?: string;
}

interface ActionPanelProps {
  /** Callback when action is submitted */
  onAction: (payload: ActionPayload) => Promise<void>;

  /** Currently loading action request */
  isLoading?: boolean;

  /** Error from last action */
  error?: string | null;

  /** Success message from last action */
  success?: string | null;

  /** Optional callback for success handling */
  onSuccess?: (action: ActionType) => void;

  /** Optional callback for error handling */
  onError?: (error: string) => void;

  /** Queue item ID for context */
  itemId: string;

  /** Current item status */
  itemStatus: string;
}

/**
 * Toast notification component
 */
function Toast({
  message,
  type,
  onClose,
}: {
  message: string;
  type: 'success' | 'error' | 'info';
  onClose: () => void;
}) {
  const colors = {
    success: 'bg-green-50 text-green-800 border-green-200',
    error: 'bg-red-50 text-red-800 border-red-200',
    info: 'bg-blue-50 text-blue-800 border-blue-200',
  };

  const icons = {
    success: <CheckCircle2 className="h-4 w-4" />,
    error: <AlertCircle className="h-4 w-4" />,
    info: <AlertCircle className="h-4 w-4" />,
  };

  return (
    <div
      className={`fixed bottom-4 right-4 flex items-center gap-3 px-4 py-3 rounded-lg border ${colors[type]} z-50 animate-in fade-in slide-in-from-bottom-2`}
    >
      {icons[type]}
      <span className="text-sm font-medium">{message}</span>
      <button
        onClick={onClose}
        className="ml-2 hover:opacity-70 transition-opacity"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

/**
 * Approve action modal form
 */
function ApproveForm({
  onSubmit,
  onCancel,
  isLoading,
}: {
  onSubmit: (notes: string) => void;
  onCancel: () => void;
  isLoading: boolean;
}) {
  const [notes, setNotes] = useState('');

  return (
    <div className="space-y-4">
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex gap-3">
        <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0 mt-0.5" />
        <div>
          <h3 className="font-semibold text-green-900">Approve this item</h3>
          <p className="text-sm text-green-700 mt-1">
            The item will be marked as approved and the assessment will be queued for processing.
          </p>
        </div>
      </div>

      <div className="space-y-2">
        <label htmlFor="approve-notes" className="text-sm font-medium">
          Notes (optional)
        </label>
        <Textarea
          id="approve-notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Add any notes about your approval decision..."
          className="min-h-24"
        />
        <p className="text-xs text-muted-foreground">
          These notes will be stored in the audit trail
        </p>
      </div>

      <div className="flex gap-2 justify-end border-t pt-4">
        <Button
          variant="outline"
          onClick={onCancel}
          disabled={isLoading}
        >
          Cancel
        </Button>
        <Button
          onClick={() => onSubmit(notes)}
          disabled={isLoading}
          className="bg-green-600 hover:bg-green-700"
        >
          {isLoading ? (
            <>
              <span className="animate-spin mr-2">⏳</span>
              Approving...
            </>
          ) : (
            <>
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Approve
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

/**
 * Reject action modal form
 */
function RejectForm({
  onSubmit,
  onCancel,
  isLoading,
}: {
  onSubmit: (reason: string, notes: string) => void;
  onCancel: () => void;
  isLoading: boolean;
}) {
  const [reason, setReason] = useState('');
  const [notes, setNotes] = useState('');
  const [showError, setShowError] = useState(false);

  const handleSubmit = () => {
    if (!reason) {
      setShowError(true);
      return;
    }
    onSubmit(reason, notes);
  };

  const reasons = [
    {
      value: 'insufficient_qualifications',
      label: 'Insufficient qualifications',
    },
    {
      value: 'missing_requirements',
      label: 'Missing key requirements',
    },
    {
      value: 'experience_gap',
      label: 'Experience gap too large',
    },
    {
      value: 'technical_mismatch',
      label: 'Technical skills mismatch',
    },
    {
      value: 'cultural_fit',
      label: 'Not a cultural fit',
    },
    {
      value: 'duplicate',
      label: 'Duplicate submission',
    },
    {
      value: 'other',
      label: 'Other reason',
    },
  ];

  return (
    <div className="space-y-4">
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex gap-3">
        <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
        <div>
          <h3 className="font-semibold text-red-900">Reject this item</h3>
          <p className="text-sm text-red-700 mt-1">
            The candidate will be notified of the rejection via email.
          </p>
        </div>
      </div>

      {showError && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 flex gap-2">
          <AlertCircle className="h-4 w-4 text-yellow-600 shrink-0 mt-0.5" />
          <p className="text-sm text-yellow-800">
            Please select a rejection reason
          </p>
        </div>
      )}

      <div className="space-y-2">
        <label htmlFor="reject-reason" className="text-sm font-medium block">
          Reason for rejection <span className="text-red-600">*</span>
        </label>
        <select
          id="reject-reason"
          value={reason}
          onChange={(e) => {
            setReason(e.target.value);
            setShowError(false);
          }}
          className="w-full px-3 py-2 border rounded-lg text-sm bg-background hover:border-primary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">Select a reason...</option>
          {reasons.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-2">
        <label htmlFor="reject-notes" className="text-sm font-medium">
          Additional notes (optional)
        </label>
        <Textarea
          id="reject-notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Add any additional context or feedback..."
          className="min-h-20"
        />
      </div>

      <div className="flex gap-2 justify-end border-t pt-4">
        <Button
          variant="outline"
          onClick={onCancel}
          disabled={isLoading}
        >
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          disabled={isLoading}
          className="bg-red-600 hover:bg-red-700"
        >
          {isLoading ? (
            <>
              <span className="animate-spin mr-2">⏳</span>
              Rejecting...
            </>
          ) : (
            <>
              <AlertCircle className="h-4 w-4 mr-2" />
              Reject
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

/**
 * Hold action modal form
 */
function HoldForm({
  onSubmit,
  onCancel,
  isLoading,
}: {
  onSubmit: (holdUntil: string, notes: string) => void;
  onCancel: () => void;
  isLoading: boolean;
}) {
  const [holdUntil, setHoldUntil] = useState('');
  const [notes, setNotes] = useState('');
  const [showError, setShowError] = useState(false);

  const handleSubmit = () => {
    if (!holdUntil) {
      setShowError(true);
      return;
    }
    onSubmit(holdUntil, notes);
  };

  // Get min datetime (now + 1 hour)
  const now = new Date();
  const minDateTime = new Date(now.getTime() + 3600000)
    .toISOString()
    .slice(0, 16);

  return (
    <div className="space-y-4">
      <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 flex gap-3">
        <AlertCircle className="h-5 w-5 text-orange-600 shrink-0 mt-0.5" />
        <div>
          <h3 className="font-semibold text-orange-900">Hold this item</h3>
          <p className="text-sm text-orange-700 mt-1">
            The item will be moved to pending status and reviewed later.
          </p>
        </div>
      </div>

      {showError && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 flex gap-2">
          <AlertCircle className="h-4 w-4 text-yellow-600 shrink-0 mt-0.5" />
          <p className="text-sm text-yellow-800">
            Please specify when to hold until
          </p>
        </div>
      )}

      <div className="space-y-2">
        <label htmlFor="hold-until" className="text-sm font-medium block">
          Hold until <span className="text-red-600">*</span>
        </label>
        <input
          id="hold-until"
          type="datetime-local"
          value={holdUntil}
          onChange={(e) => {
            setHoldUntil(e.target.value);
            setShowError(false);
          }}
          min={minDateTime}
          className="w-full px-3 py-2 border rounded-lg text-sm bg-background hover:border-primary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        />
        <p className="text-xs text-muted-foreground">
          Must be at least 1 hour from now
        </p>
      </div>

      <div className="space-y-2">
        <label htmlFor="hold-notes" className="text-sm font-medium">
          Reason for hold (optional)
        </label>
        <Textarea
          id="hold-notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Why are you putting this on hold?"
          className="min-h-20"
        />
      </div>

      <div className="flex gap-2 justify-end border-t pt-4">
        <Button
          variant="outline"
          onClick={onCancel}
          disabled={isLoading}
        >
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          disabled={isLoading}
          className="bg-orange-600 hover:bg-orange-700"
        >
          {isLoading ? (
            <>
              <span className="animate-spin mr-2">⏳</span>
              Holding...
            </>
          ) : (
            <>
              <ChevronRight className="h-4 w-4 mr-2" />
              Hold
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

export function ActionPanel({
  onAction,
  isLoading = false,
  error = null,
  success = null,
  onSuccess,
  onError,
  itemId,
  itemStatus,
}: ActionPanelProps) {
  const [activeAction, setActiveAction] = useState<ActionType>(null);
  const [toastMessage, setToastMessage] = useState<{
    message: string;
    type: 'success' | 'error' | 'info';
  } | null>(null);

  const isReadOnly = itemStatus !== 'awaiting_review';

  /**
   * Handle action submission
   */
  const handleAction = useCallback(
    async (payload: ActionPayload) => {
      try {
        await onAction(payload);
        setToastMessage({
          message: `Item ${payload.action}d successfully`,
          type: 'success',
        });
        if (onSuccess) {
          onSuccess(payload.action);
        }
        setActiveAction(null);
      } catch (err) {
        const errorMsg =
          err instanceof Error ? err.message : 'Action failed';
        setToastMessage({
          message: errorMsg,
          type: 'error',
        });
        if (onError) {
          onError(errorMsg);
        }
      }
    },
    [onAction, onSuccess, onError]
  );

  return (
    <>
      {/* Action buttons */}
      {!activeAction && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Take Action</CardTitle>
            {error && (
              <div className="mt-2 flex items-center gap-2 text-sm text-red-600">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            )}
            {success && (
              <div className="mt-2 flex items-center gap-2 text-sm text-green-600">
                <CheckCircle2 className="h-4 w-4" />
                {success}
              </div>
            )}
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">
              {isReadOnly
                ? 'This item is no longer awaiting review'
                : 'Choose an action to process this item:'}
            </p>

            <div className="grid grid-cols-3 gap-2">
              <Button
                onClick={() => setActiveAction('approve')}
                disabled={isLoading || isReadOnly}
                className="bg-green-600 hover:bg-green-700"
              >
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Approve
              </Button>
              <Button
                onClick={() => setActiveAction('reject')}
                disabled={isLoading || isReadOnly}
                className="bg-red-600 hover:bg-red-700"
              >
                <AlertCircle className="h-4 w-4 mr-2" />
                Reject
              </Button>
              <Button
                onClick={() => setActiveAction('hold')}
                disabled={isLoading || isReadOnly}
                className="bg-orange-600 hover:bg-orange-700"
              >
                <ChevronRight className="h-4 w-4 mr-2" />
                Hold
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action modals */}
      {activeAction === 'approve' && (
        <Card className="border-green-200 bg-green-50/50">
          <CardContent className="pt-6">
            <ApproveForm
              onSubmit={(notes) =>
                handleAction({ action: 'approve', notes })
              }
              onCancel={() => setActiveAction(null)}
              isLoading={isLoading}
            />
          </CardContent>
        </Card>
      )}

      {activeAction === 'reject' && (
        <Card className="border-red-200 bg-red-50/50">
          <CardContent className="pt-6">
            <RejectForm
              onSubmit={(reason, notes) =>
                handleAction({ action: 'reject', reason, notes })
              }
              onCancel={() => setActiveAction(null)}
              isLoading={isLoading}
            />
          </CardContent>
        </Card>
      )}

      {activeAction === 'hold' && (
        <Card className="border-orange-200 bg-orange-50/50">
          <CardContent className="pt-6">
            <HoldForm
              onSubmit={(holdUntil, notes) =>
                handleAction({ action: 'hold', holdUntil, notes })
              }
              onCancel={() => setActiveAction(null)}
              isLoading={isLoading}
            />
          </CardContent>
        </Card>
      )}

      {/* Toast notifications */}
      {toastMessage && (
        <Toast
          message={toastMessage.message}
          type={toastMessage.type}
          onClose={() => setToastMessage(null)}
        />
      )}
    </>
  );
}
