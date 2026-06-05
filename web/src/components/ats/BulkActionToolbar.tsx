'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Trash2, Tag, Share2, FileText, ChevronDown } from 'lucide-react';
import { useToast } from '@/components/providers/ToastProvider';
import type { BulkActionRequest } from '@/hooks/useBulkActions';

interface BulkActionToolbarProps {
  selectedCount: number;
  onSelectAll?: () => void;
  onDeselectAll?: () => void;
  onExecuteAction: (action: BulkActionRequest) => Promise<void>;
  onStageSelect?: (stage: string) => void;
}

const STAGE_OPTIONS = [
  { id: 'applied', label: 'Applied' },
  { id: 'phone_screen', label: 'Phone Screen' },
  { id: 'technical', label: 'Technical' },
  { id: 'onsite', label: 'On-site' },
  { id: 'offer', label: 'Offer' },
  { id: 'hired', label: 'Hired' },
];

export function BulkActionToolbar({
  selectedCount,
  onSelectAll,
  onDeselectAll,
  onExecuteAction,
  onStageSelect,
}: BulkActionToolbarProps) {
  const { addToast } = useToast();
  const [showStageMenu, setShowStageMenu] = useState(false);
  const [showTagMenu, setShowTagMenu] = useState(false);
  const [newTag, setNewTag] = useState('');

  if (selectedCount === 0) {
    return null;
  }

  const handleMoveToStage = async (stage: string) => {
    try {
      await onExecuteAction({
        type: 'stage',
        candidateIds: [], // Would be passed from parent
        payload: { newStage: stage },
      });
      setShowStageMenu(false);
      onStageSelect?.(stage);
    } catch (err) {
      // Error handled by hook
    }
  };

  const handleAddTag = async () => {
    if (!newTag.trim()) {
      addToast('Please enter a tag', 'warning');
      return;
    }

    try {
      await onExecuteAction({
        type: 'tag',
        candidateIds: [], // Would be passed from parent
        payload: { tagsToAdd: [newTag] },
      });
      setNewTag('');
      setShowTagMenu(false);
    } catch (err) {
      // Error handled by hook
    }
  };

  const handleRejectAll = async () => {
    const confirmed = window.confirm(
      `Are you sure you want to reject ${selectedCount} candidate(s)? This action cannot be undone.`
    );

    if (!confirmed) return;

    try {
      await onExecuteAction({
        type: 'reject',
        candidateIds: [], // Would be passed from parent
      });
    } catch (err) {
      // Error handled by hook
    }
  };

  return (
    <Card className="sticky bottom-4 p-4 shadow-lg border-primary/20 bg-white">
      <div className="flex items-center justify-between gap-4">
        {/* Selection Info */}
        <div className="flex items-center gap-3">
          <Badge variant="default" className="px-3">
            {selectedCount} selected
          </Badge>
          {onSelectAll && onDeselectAll && (
            <div className="flex gap-2">
              <Button size="sm" variant="ghost" onClick={onSelectAll} className="h-8 px-2 text-xs">
                Select All
              </Button>
              <Button size="sm" variant="ghost" onClick={onDeselectAll} className="h-8 px-2 text-xs">
                Deselect All
              </Button>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {/* Move to Stage */}
          <div className="relative">
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowStageMenu(!showStageMenu)}
              className="gap-2"
            >
              <ChevronDown className="h-4 w-4" />
              Move to...
            </Button>

            {showStageMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white border rounded-lg shadow-lg z-10">
                <div className="p-2 space-y-1">
                  {STAGE_OPTIONS.map(stage => (
                    <button
                      key={stage.id}
                      onClick={() => handleMoveToStage(stage.id)}
                      className="w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm"
                    >
                      {stage.label}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Add Tag */}
          <div className="relative">
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowTagMenu(!showTagMenu)}
              className="gap-2"
            >
              <Tag className="h-4 w-4" />
              Add Tag
            </Button>

            {showTagMenu && (
              <div className="absolute right-0 mt-2 w-56 bg-white border rounded-lg shadow-lg z-10 p-3 space-y-2">
                <input
                  type="text"
                  value={newTag}
                  onChange={e => setNewTag(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') {
                      handleAddTag();
                    }
                  }}
                  placeholder="Enter tag name..."
                  className="w-full px-3 py-2 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                  autoFocus
                />
                <div className="flex gap-2">
                  <Button size="sm" onClick={handleAddTag} className="flex-1 h-8">
                    Add
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setShowTagMenu(false);
                      setNewTag('');
                    }}
                    className="flex-1 h-8"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Schedule Interview */}
          <Button size="sm" variant="outline" className="gap-2" disabled>
            <Share2 className="h-4 w-4" />
            Schedule Interview
          </Button>

          {/* Export */}
          <Button size="sm" variant="outline" className="gap-2" disabled>
            <FileText className="h-4 w-4" />
            Export
          </Button>

          {/* Reject */}
          <Button
            size="sm"
            variant="destructive"
            onClick={handleRejectAll}
            className="gap-2"
          >
            <Trash2 className="h-4 w-4" />
            Reject All
          </Button>
        </div>
      </div>

      {/* Info */}
      <p className="text-xs text-muted-foreground mt-2">
        💡 Tip: Select candidates and use actions above to bulk manage your pipeline
      </p>
    </Card>
  );
}
