'use client';

/**
 * QueueItemDetail Component
 *
 * Displays full details of a selected queue item with sections for:
 * - Item metadata (filename, source, created_at)
 * - Extracted text preview (scrollable, first 500 chars)
 * - Sender info (if email source)
 * - Previous notes/decisions timeline
 * - Action buttons (Approve, Reject, Hold)
 * - Notes input field
 *
 * Features:
 * - Full expandable text preview
 * - Timeline of previous decisions
 * - Error handling
 * - Loading states during actions
 */

import { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Mail,
  FileText,
  CalendarIcon,
  MessageSquare,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';

/**
 * Queue item detail type
 */
interface QueueItemDetail {
  id: string;
  name: string;
  type: 'cv' | 'jd' | 'assessment';
  source: string;
  status: string;
  created_at: string;
  awaiting_review: boolean;
  extracted_text?: string;
  sender_name?: string;
  sender_email?: string;
  notes_history?: Array<{
    timestamp: string;
    notes: string;
    action?: string;
    actor?: string;
  }>;
  review_notes?: string;
}

interface QueueItemDetailProps {
  /** The item to display */
  item: QueueItemDetail;

  /** Callback for approve action */
  onApprove: (notes: string) => Promise<void>;

  /** Callback for reject action */
  onReject: (reason: string, notes: string) => Promise<void>;

  /** Callback for hold action */
  onHold: (holdUntil: string, notes: string) => Promise<void>;

  /** Loading state during action */
  isActionLoading?: boolean;

  /** Error message from action */
  actionError?: string | null;
}

/**
 * Formatted status badge
 */
function StatusDisplay({ status }: { status: string }) {
  const config: Record<
    string,
    { className: string; label: string }
  > = {
    awaiting_review: {
      className: 'bg-amber-100 text-amber-800',
      label: 'Awaiting Review',
    },
    approved: {
      className: 'bg-green-100 text-green-800',
      label: 'Approved',
    },
    rejected: {
      className: 'bg-red-100 text-red-800',
      label: 'Rejected',
    },
    processing: {
      className: 'bg-blue-100 text-blue-800',
      label: 'Processing',
    },
    held: {
      className: 'bg-orange-100 text-orange-800',
      label: 'Held',
    },
  };

  const { className, label } = config[status] || {
    className: 'bg-gray-100 text-gray-800',
    label: status,
  };

  return <Badge className={className}>{label}</Badge>;
}

/**
 * Expandable text preview section
 */
function TextPreview({
  text,
  maxLines = 6,
}: {
  text?: string;
  maxLines?: number;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!text) {
    return (
      <div className="text-sm text-muted-foreground py-4">
        No text content available
      </div>
    );
  }

  const truncated = text.length > 500;
  const displayText = isExpanded ? text : text.substring(0, 500);
  const lineCount = displayText.split('\n').length;
  const shouldShowExpand = truncated || lineCount > maxLines;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium">Content Preview</p>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-7 w-7 p-0"
          title="Copy text"
        >
          {copied ? (
            <Check className="h-3 w-3 text-green-600" />
          ) : (
            <Copy className="h-3 w-3" />
          )}
        </Button>
      </div>

      <div
        className={`bg-muted/50 rounded-lg p-4 font-mono text-xs border border-border overflow-y-auto ${
          isExpanded ? 'max-h-96' : 'max-h-32'
        } whitespace-pre-wrap break-words transition-all`}
      >
        {displayText}
        {truncated && !isExpanded && (
          <span className="text-muted-foreground"> ...</span>
        )}
      </div>

      {shouldShowExpand && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full"
        >
          {isExpanded ? (
            <>
              <ChevronUp className="h-4 w-4 mr-1" />
              Show less
            </>
          ) : (
            <>
              <ChevronDown className="h-4 w-4 mr-1" />
              Show more ({text.length} chars)
            </>
          )}
        </Button>
      )}
    </div>
  );
}

/**
 * Timeline of previous notes/decisions
 */
function NotesTimeline({
  history,
}: {
  history?: Array<{
    timestamp: string;
    notes: string;
    action?: string;
    actor?: string;
  }>;
}) {
  if (!history || history.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-4">
        No previous notes or decisions
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {history.map((entry, idx) => (
        <div key={idx} className="border-l-2 border-primary/30 pl-4 pb-3">
          <div className="flex items-center justify-between gap-2">
            <time className="text-xs text-muted-foreground">
              {new Date(entry.timestamp).toLocaleString()}
            </time>
            {entry.action && (
              <Badge variant="outline" className="text-xs">
                {entry.action}
              </Badge>
            )}
          </div>
          {entry.actor && (
            <p className="text-xs text-muted-foreground mt-1">By {entry.actor}</p>
          )}
          {entry.notes && (
            <p className="text-sm mt-2 text-foreground">{entry.notes}</p>
          )}
        </div>
      ))}
    </div>
  );
}

export function QueueItemDetail({
  item,
  onApprove,
  onReject,
  onHold,
  isActionLoading = false,
  actionError = null,
}: QueueItemDetailProps) {
  // Local state
  const [notes, setNotes] = useState(item.review_notes || '');
  const [selectedAction, setSelectedAction] = useState<
    'approve' | 'reject' | 'hold' | null
  >(null);
  const [rejectReason, setRejectReason] = useState('');
  const [holdUntil, setHoldUntil] = useState('');
  const [showActionForm, setShowActionForm] = useState(false);

  /**
   * Handle approve action
   */
  const handleApprove = async () => {
    try {
      await onApprove(notes);
      setNotes('');
      setShowActionForm(false);
      setSelectedAction(null);
    } catch (err) {
      console.error('Approve failed:', err);
    }
  };

  /**
   * Handle reject action
   */
  const handleReject = async () => {
    if (!rejectReason) {
      alert('Please select a rejection reason');
      return;
    }
    try {
      await onReject(rejectReason, notes);
      setNotes('');
      setRejectReason('');
      setShowActionForm(false);
      setSelectedAction(null);
    } catch (err) {
      console.error('Reject failed:', err);
    }
  };

  /**
   * Handle hold action
   */
  const handleHold = async () => {
    if (!holdUntil) {
      alert('Please specify when to hold until');
      return;
    }
    try {
      await onHold(holdUntil, notes);
      setNotes('');
      setHoldUntil('');
      setShowActionForm(false);
      setSelectedAction(null);
    } catch (err) {
      console.error('Hold failed:', err);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header with status and metadata */}
      <Card>
        <CardHeader>
          <div className="space-y-3">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <h2 className="text-xl font-bold truncate">{item.name}</h2>
                <div className="flex items-center gap-2 mt-2 flex-wrap">
                  <Badge variant="secondary" className="capitalize">
                    {item.type}
                  </Badge>
                  <StatusDisplay status={item.status} />
                </div>
              </div>
            </div>

            {/* Metadata grid */}
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase">
                  Source
                </p>
                <p className="capitalize mt-1">{item.source}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase">
                  Created
                </p>
                <p className="mt-1">
                  {new Date(item.created_at).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
              {item.sender_email && (
                <div className="col-span-2">
                  <p className="text-xs font-medium text-muted-foreground uppercase flex items-center gap-1">
                    <Mail className="h-3 w-3" />
                    From
                  </p>
                  <p className="mt-1">
                    {item.sender_name && `${item.sender_name} <`}
                    {item.sender_email}
                    {item.sender_name && '>'}
                  </p>
                </div>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Content preview */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Content
          </CardTitle>
        </CardHeader>
        <CardContent>
          <TextPreview text={item.extracted_text} />
        </CardContent>
      </Card>

      {/* Previous notes and timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            Notes History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <NotesTimeline history={item.notes_history} />
        </CardContent>
      </Card>

      {/* Action panel */}
      <Card className="border-primary/50 bg-primary/5">
        <CardHeader>
          <CardTitle className="text-base">Action</CardTitle>
          {actionError && (
            <div className="text-sm text-red-600 mt-2">{actionError}</div>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Action form */}
          {showActionForm && selectedAction && (
            <div className="space-y-4 border-t pt-4">
              {selectedAction === 'approve' && (
                <div className="space-y-2">
                  <label className="text-sm font-medium">
                    Notes (optional)
                  </label>
                  <Textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Add any notes about your approval..."
                    className="min-h-20"
                  />
                </div>
              )}

              {selectedAction === 'reject' && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">
                      Reason for rejection
                    </label>
                    <select
                      value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
                    >
                      <option value="">Select a reason...</option>
                      <option value="insufficient_qualifications">
                        Insufficient qualifications
                      </option>
                      <option value="missing_requirements">
                        Missing key requirements
                      </option>
                      <option value="experience_gap">
                        Experience gap too large
                      </option>
                      <option value="technical_mismatch">
                        Technical skills mismatch
                      </option>
                      <option value="cultural_fit">
                        Not a cultural fit
                      </option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">
                      Additional notes (optional)
                    </label>
                    <Textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Add any additional feedback..."
                      className="min-h-20"
                    />
                  </div>
                </div>
              )}

              {selectedAction === 'hold' && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium flex items-center gap-2">
                      <CalendarIcon className="h-4 w-4" />
                      Hold until
                    </label>
                    <input
                      type="datetime-local"
                      value={holdUntil}
                      onChange={(e) => setHoldUntil(e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">
                      Notes (optional)
                    </label>
                    <Textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Why are you holding this item?"
                      className="min-h-20"
                    />
                  </div>
                </div>
              )}

              {/* Action form buttons */}
              <div className="flex gap-2 justify-end border-t pt-4">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowActionForm(false);
                    setSelectedAction(null);
                    setNotes('');
                    setRejectReason('');
                    setHoldUntil('');
                  }}
                  disabled={isActionLoading}
                >
                  Cancel
                </Button>
                <Button
                  onClick={() => {
                    if (selectedAction === 'approve') handleApprove();
                    else if (selectedAction === 'reject') handleReject();
                    else if (selectedAction === 'hold') handleHold();
                  }}
                  disabled={isActionLoading}
                  className={
                    selectedAction === 'approve'
                      ? 'bg-green-600 hover:bg-green-700'
                      : selectedAction === 'reject'
                        ? 'bg-red-600 hover:bg-red-700'
                        : 'bg-orange-600 hover:bg-orange-700'
                  }
                >
                  {isActionLoading ? (
                    <>
                      <span className="animate-spin mr-2">⏳</span>
                      Processing...
                    </>
                  ) : (
                    `Confirm ${selectedAction?.charAt(0).toUpperCase() + selectedAction?.slice(1)}`
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* Action buttons */}
          {!showActionForm && (
            <div className="grid grid-cols-3 gap-2">
              <Button
                onClick={() => {
                  setSelectedAction('approve');
                  setShowActionForm(true);
                }}
                disabled={isActionLoading || item.status !== 'awaiting_review'}
                className="bg-green-600 hover:bg-green-700"
              >
                Approve
              </Button>
              <Button
                onClick={() => {
                  setSelectedAction('reject');
                  setShowActionForm(true);
                }}
                disabled={isActionLoading || item.status !== 'awaiting_review'}
                className="bg-red-600 hover:bg-red-700"
              >
                Reject
              </Button>
              <Button
                onClick={() => {
                  setSelectedAction('hold');
                  setShowActionForm(true);
                }}
                disabled={isActionLoading || item.status !== 'awaiting_review'}
                className="bg-orange-600 hover:bg-orange-700"
              >
                Hold
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
