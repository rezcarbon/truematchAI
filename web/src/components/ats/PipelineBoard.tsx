'use client';

import { useState, useEffect, useCallback } from 'react';
import { useToast } from '@/components/providers/ToastProvider';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Loader2, MessageSquare, Trash2, Tag, Wifi, WifiOff } from 'lucide-react';
import { cn } from '@/lib/utils';
import { usePipelineWebSocket } from '@/hooks/useWebSocket';

const PIPELINE_STAGES = [
  { id: 'applied', label: 'Applied', color: 'bg-blue-500' },
  { id: 'phone_screen', label: 'Phone Screen', color: 'bg-purple-500' },
  { id: 'technical', label: 'Technical', color: 'bg-indigo-500' },
  { id: 'onsite', label: 'On-site', color: 'bg-pink-500' },
  { id: 'offer', label: 'Offer', color: 'bg-yellow-500' },
  { id: 'hired', label: 'Hired', color: 'bg-green-500' },
  { id: 'rejected', label: 'Rejected', color: 'bg-red-500' },
];

interface Candidate {
  id: string;
  name: string;
  stage: string;
  daysInStage: number;
  keywordScore?: number;
  semanticScore?: number;
  capabilityScore?: number;
  source?: string;
  tags?: string[];
  resumeId: string;
}

interface PipelineBoardProps {
  positionId: string;
  candidates: Candidate[];
  onStageChange: (candidateId: string, newStage: string) => Promise<void>;
  onCandidateSelect: (candidate: Candidate) => void;
  onScheduleInterview: (candidate: Candidate) => void;
  selectedCandidates?: Set<string>;
  onCandidateToggle?: (candidateId: string) => void;
}

export function PipelineBoard({
  positionId,
  candidates: initialCandidates,
  onStageChange,
  onCandidateSelect,
  onScheduleInterview,
  selectedCandidates = new Set(),
  onCandidateToggle,
}: PipelineBoardProps) {
  const { addToast } = useToast();
  const [draggedCandidate, setDraggedCandidate] = useState<Candidate | null>(null);
  const [loading, setLoading] = useState(false);
  const [candidates, setCandidates] = useState<Candidate[]>(initialCandidates);
  const [wsConnected, setWsConnected] = useState(false);

  // Handle real-time WebSocket updates
  const handleWebSocketMessage = useCallback((message: any) => {
    if (message.type === 'pipeline_update') {
      // Update candidate stage in real-time
      setCandidates(prevCandidates =>
        prevCandidates.map(c =>
          c.id === message.application_id
            ? { ...c, stage: message.new_stage }
            : c
        )
      );
      addToast(
        `${message.candidate_name || 'Candidate'} moved to ${message.new_stage}`,
        'info'
      );
    } else if (message.type === 'interview_scheduled') {
      addToast(
        `Interview scheduled for ${message.candidate_name || 'candidate'}`,
        'info'
      );
    } else if (message.type === 'scorecard_submitted') {
      addToast('Scorecard submitted', 'success');
    }
  }, [addToast]);

  // Initialize WebSocket connection for pipeline updates
  const { isConnected } = usePipelineWebSocket(
    positionId,
    handleWebSocketMessage,
    true
  );

  // Update connection status
  useEffect(() => {
    setWsConnected(isConnected);
  }, [isConnected]);

  // Update candidates when initial props change
  useEffect(() => {
    setCandidates(initialCandidates);
  }, [initialCandidates]);

  const getScoreBadgeColor = (score?: number) => {
    if (!score) return 'bg-gray-100';
    if (score >= 80) return 'bg-green-100 text-green-700';
    if (score >= 60) return 'bg-yellow-100 text-yellow-700';
    return 'bg-red-100 text-red-700';
  };

  const handleDragStart = (e: React.DragEvent, candidate: Candidate) => {
    setDraggedCandidate(candidate);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = async (e: React.DragEvent, newStage: string) => {
    e.preventDefault();
    if (!draggedCandidate || draggedCandidate.stage === newStage) {
      setDraggedCandidate(null);
      return;
    }

    setLoading(true);
    try {
      await onStageChange(draggedCandidate.id, newStage);
      addToast(`Moved ${draggedCandidate.name} to ${newStage}`, 'success');
    } catch (error) {
      addToast('Failed to move candidate', 'error');
    } finally {
      setLoading(false);
      setDraggedCandidate(null);
    }
  };

  const handleDragEnd = () => {
    setDraggedCandidate(null);
  };

  const getCandidatesInStage = (stageId: string) => {
    return candidates.filter(c => c.stage === stageId);
  };

  return (
    <div className="space-y-4">
      {/* Header with stage count and WebSocket status */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-2">
          {wsConnected ? (
            <>
              <Wifi className="h-4 w-4 text-green-500" />
              <span className="text-xs text-green-600">Real-time updates active</span>
            </>
          ) : (
            <>
              <WifiOff className="h-4 w-4 text-red-500" />
              <span className="text-xs text-red-600">Real-time updates offline</span>
            </>
          )}
        </div>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-2">
        {PIPELINE_STAGES.map(stage => {
          const count = getCandidatesInStage(stage.id).length;
          return (
            <div key={stage.id} className="flex items-center gap-2 whitespace-nowrap">
              <span className="text-sm font-medium">{stage.label}</span>
              <Badge variant="secondary">{count}</Badge>
            </div>
          );
        })}
      </div>

      {/* Kanban board */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {PIPELINE_STAGES.map(stage => (
          <div
            key={stage.id}
            className="space-y-2"
            onDragOver={handleDragOver}
            onDrop={e => handleDrop(e, stage.id)}
          >
            {/* Stage header */}
            <div className={cn(
              'px-4 py-2 rounded-lg text-white font-semibold text-sm',
              stage.color
            )}>
              {stage.label}
            </div>

            {/* Candidate cards */}
            <div className="space-y-2 min-h-[200px]">
              {getCandidatesInStage(stage.id).length === 0 ? (
                <div className="text-center py-8 text-muted-foreground text-sm">
                  No candidates
                </div>
              ) : (
                getCandidatesInStage(stage.id).map(candidate => (
                  <Card
                    key={candidate.id}
                    className={cn(
                      'cursor-move hover:shadow-md transition-all',
                      draggedCandidate?.id === candidate.id && 'opacity-50'
                    )}
                    draggable
                    onDragStart={e => handleDragStart(e, candidate)}
                    onDragEnd={handleDragEnd}
                  >
                    <CardContent className="p-3 space-y-2">
                      {/* Checkbox + Candidate name */}
                      <div className="flex items-start gap-2">
                        {onCandidateToggle && (
                          <input
                            type="checkbox"
                            checked={selectedCandidates.has(candidate.id)}
                            onChange={() => onCandidateToggle(candidate.id)}
                            className="mt-1 cursor-pointer"
                          />
                        )}
                        <div className="flex-1">
                          <p
                            className="font-medium text-sm cursor-pointer hover:underline"
                            onClick={() => onCandidateSelect(candidate)}
                          >
                            {candidate.name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {candidate.daysInStage}d in {stage.label}
                          </p>
                        </div>
                      </div>
                      </div>

                      {/* Scores with three-signal visualization */}
                      {(candidate.keywordScore || candidate.semanticScore || candidate.capabilityScore) && (
                        <div className="space-y-1">
                          {candidate.keywordScore && (
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-muted-foreground">Keyword</span>
                              <Badge variant="outline" className={getScoreBadgeColor(candidate.keywordScore)}>
                                {candidate.keywordScore}
                              </Badge>
                            </div>
                          )}
                          {candidate.semanticScore && (
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-muted-foreground">Semantic</span>
                              <Badge variant="outline" className={getScoreBadgeColor(candidate.semanticScore)}>
                                {candidate.semanticScore}
                              </Badge>
                            </div>
                          )}
                          {candidate.capabilityScore && (
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-muted-foreground">Capability</span>
                              <Badge variant="outline" className={getScoreBadgeColor(candidate.capabilityScore)}>
                                {candidate.capabilityScore}
                              </Badge>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Source tag */}
                      {candidate.source && (
                        <div className="text-xs">
                          <Badge variant="secondary">{candidate.source}</Badge>
                        </div>
                      )}

                      {/* Action buttons */}
                      <div className="flex gap-2 pt-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="flex-1 h-8 text-xs"
                          onClick={() => onScheduleInterview(candidate)}
                        >
                          <MessageSquare className="h-3 w-3 mr-1" />
                          Interview
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="flex-1 h-8 text-xs"
                        >
                          <Tag className="h-3 w-3 mr-1" />
                          Tag
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Loading indicator */}
      {loading && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Moving candidate...</span>
          </div>
        </div>
      )}
    </div>
  );
}
