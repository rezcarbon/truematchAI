'use client';

import React, { useState } from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface ActionItem {
  id: string;
  description: string;
  type: 'delete' | 'email' | 'schedule' | 'modify' | 'approve' | 'send';
  details?: Record<string, unknown>;
  requiresConfirmation?: boolean;
}

interface ActionConfirmationProps {
  actions: ActionItem[];
  onConfirm: (actionIds: string[]) => Promise<void>;
  onReject: (actionIds: string[]) => void;
  onModify?: (actionId: string, details: Record<string, unknown>) => void;
}

/**
 * Action Confirmation Dialog
 *
 * Shows the user pending actions that require confirmation before execution.
 * Displays action details and allows:
 * - Confirm all
 * - Reject all
 * - Confirm individual actions
 * - Reject individual actions
 * - Modify action details (if applicable)
 */
export function ActionConfirmation({
  actions,
  onConfirm,
  onReject,
  onModify,
}: ActionConfirmationProps) {
  const [selectedActionId, setSelectedActionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [confirmedIds, setConfirmedIds] = useState<Set<string>>(new Set());
  const [rejectedIds, setRejectedIds] = useState<Set<string>>(new Set());

  // Filter actions that require confirmation
  const pendingActions = actions.filter(
    (a) => a.requiresConfirmation !== false && !confirmedIds.has(a.id) && !rejectedIds.has(a.id)
  );

  if (pendingActions.length === 0) {
    return null;
  }

  const selectedAction = pendingActions.find((a) => a.id === selectedActionId) || pendingActions[0];

  const handleConfirmAction = async (actionId: string) => {
    setIsLoading(true);
    try {
      // Actually execute this single action via the parent (which calls the
      // backend confirm endpoint), then mark it locally resolved.
      await onConfirm([actionId]);
      setConfirmedIds((prev) => new Set([...prev, actionId]));
      setSelectedActionId(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRejectAction = (actionId: string) => {
    onReject([actionId]);
    setRejectedIds((prev) => new Set([...prev, actionId]));
    setSelectedActionId(null);
  };

  const handleConfirmAll = async () => {
    setIsLoading(true);
    try {
      const allIds = pendingActions.map((a) => a.id);
      await onConfirm(allIds);
      setConfirmedIds((prev) => new Set([...prev, ...allIds]));
    } finally {
      setIsLoading(false);
    }
  };

  const handleRejectAll = () => {
    const allIds = pendingActions.map((a) => a.id);
    onReject(allIds);
    setRejectedIds((prev) => new Set([...prev, ...allIds]));
  };

  const getActionIcon = (type: string) => {
    const icons: Record<string, string> = {
      delete: '🗑️',
      email: '📧',
      schedule: '📅',
      modify: '✏️',
      approve: '✅',
      send: '📤',
    };
    return icons[type] || '⚙️';
  };

  const getActionColor = (type: string) => {
    const colors: Record<string, string> = {
      delete: 'bg-red-50 border-red-200',
      email: 'bg-blue-50 border-blue-200',
      schedule: 'bg-purple-50 border-purple-200',
      modify: 'bg-yellow-50 border-yellow-200',
      approve: 'bg-green-50 border-green-200',
      send: 'bg-cyan-50 border-cyan-200',
    };
    return colors[type] || 'bg-gray-50 border-gray-200';
  };

  return (
    <AlertDialog open={pendingActions.length > 0}>
      <AlertDialogContent className="max-w-2xl">
        <AlertDialogTitle>Confirm Actions</AlertDialogTitle>
        <AlertDialogDescription>
          The agent is about to perform {pendingActions.length} action
          {pendingActions.length !== 1 ? 's' : ''}. Please review and confirm.
        </AlertDialogDescription>

        <div className="my-4 space-y-3 max-h-96 overflow-y-auto">
          {pendingActions.map((action) => (
            <Card
              key={action.id}
              className={`cursor-pointer transition-all ${getActionColor(action.type)} ${selectedActionId === action.id ? 'ring-2 ring-blue-500' : ''}`}
              onClick={() => setSelectedActionId(action.id)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{getActionIcon(action.type)}</span>
                    <div>
                      <CardTitle className="text-sm capitalize">
                        {action.type.replace('_', ' ')}
                      </CardTitle>
                      <CardDescription className="text-xs">
                        {action.description}
                      </CardDescription>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleConfirmAction(action.id);
                      }}
                      disabled={isLoading}
                    >
                      ✓
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRejectAction(action.id);
                      }}
                    >
                      ✕
                    </Button>
                  </div>
                </div>
              </CardHeader>

              {selectedActionId === action.id && action.details && (
                <CardContent className="text-xs space-y-1">
                  {Object.entries(action.details).map(([key, value]) => (
                    <div key={key} className="flex gap-2">
                      <span className="font-medium">{key}:</span>
                      <span className="text-muted-foreground">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </span>
                    </div>
                  ))}
                </CardContent>
              )}
            </Card>
          ))}
        </div>

        <div className="flex gap-2 justify-end">
          <AlertDialogCancel onClick={handleRejectAll} disabled={isLoading}>
            Reject All
          </AlertDialogCancel>
          <AlertDialogAction onClick={handleConfirmAll} disabled={isLoading}>
            {isLoading ? 'Confirming...' : 'Confirm All'}
          </AlertDialogAction>
        </div>
      </AlertDialogContent>
    </AlertDialog>
  );
}
