'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { PipelineBoard } from '@/components/ats/PipelineBoard';
import { InterviewScheduler } from '@/components/ats/InterviewScheduler';
import { CandidateDetailModal } from '@/components/ats/CandidateDetailModal';
import { ScorecardForm } from '@/components/ats/ScorecardForm';
import { FilterPanel } from '@/components/ats/FilterPanel';
import { BulkActionToolbar } from '@/components/ats/BulkActionToolbar';
import { useATSPipeline } from '@/hooks/useATSPipeline';
import { useFilteredPipeline } from '@/hooks/useFilteredPipeline';
import { useBulkActions } from '@/hooks/useBulkActions';
import { useToast } from '@/components/providers/ToastProvider';
import { Loader2, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { BulkActionRequest } from '@/hooks/useBulkActions';

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
  email?: string;
  appliedAt?: string;
  positionTitle?: string;
  resumeText?: string;
}

interface Interviewer {
  id: string;
  name: string;
  email: string;
}

export default function PipelinePage() {
  const { addToast } = useToast();
  const [selectedJob, setSelectedJob] = useState<string>('job-1');
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showScheduler, setShowScheduler] = useState(false);
  const [showScorecard, setShowScorecard] = useState(false);
  const [selectedInterviewId, setSelectedInterviewId] = useState<string | null>(null);
  const [interviewers, setInterviewers] = useState<Interviewer[]>([]);
  const [selectedCandidates, setSelectedCandidates] = useState<Set<string>>(new Set());

  // Use the API hook for pipeline data
  const { candidates: apiCandidates, loading, error, updateStage } = useATSPipeline(selectedJob);

  // Use the filtered pipeline hook for filtering
  const {
    candidates: filteredCandidates,
    filteredCount,
    totalCount,
    applyFilters,
    clearFilters
  } = useFilteredPipeline(selectedJob);

  // Use bulk actions hook
  const { executeBulkAction, loading: bulkLoading } = useBulkActions();

  // Mock interviewers data
  useEffect(() => {
    const mockInterviewers: Interviewer[] = [
      { id: 'int-1', name: 'John Smith', email: 'john@company.com' },
      { id: 'int-2', name: 'Emma Wilson', email: 'emma@company.com' },
      { id: 'int-3', name: 'David Lee', email: 'david@company.com' },
    ];
    setInterviewers(mockInterviewers);
  }, []);

  // Transform API candidates to component format
  const candidates: Candidate[] = apiCandidates.map(c => {
    const stageEntered = c.stage_entered_at ? new Date(c.stage_entered_at) : new Date();
    const now = new Date();
    const daysInStage = Math.floor((now.getTime() - stageEntered.getTime()) / (1000 * 60 * 60 * 24));

    return {
      id: c.id,
      name: `Candidate ${c.id.slice(0, 8)}`, // Placeholder name
      stage: c.stage,
      daysInStage,
      keywordScore: Math.round(c.keywordScore || 0),
      semanticScore: Math.round(c.semanticScore || 0),
      capabilityScore: Math.round(c.capabilityScore || 0),
      source: c.source,
      tags: [],
      resumeId: c.resume_id,
      appliedAt: c.applied_at,
      positionTitle: 'Senior Backend Engineer', // Placeholder
      resumeText: 'Resume content placeholder',
    };
  });

  const handleStageChange = async (candidateId: string, newStage: string) => {
    try {
      await updateStage(candidateId, newStage);
    } catch (err) {
      // Error already handled by hook
      throw err;
    }
  };

  const handleCandidateToggle = (candidateId: string) => {
    const newSelected = new Set(selectedCandidates);
    if (newSelected.has(candidateId)) {
      newSelected.delete(candidateId);
    } else {
      newSelected.add(candidateId);
    }
    setSelectedCandidates(newSelected);
  };

  const handleSelectAll = () => {
    const allIds = new Set(candidates.map(c => c.id));
    setSelectedCandidates(allIds);
  };

  const handleDeselectAll = () => {
    setSelectedCandidates(new Set());
  };

  const handleBulkAction = async (action: BulkActionRequest) => {
    try {
      const request: BulkActionRequest = {
        ...action,
        candidateIds: Array.from(selectedCandidates),
      };
      await executeBulkAction(request);
      setSelectedCandidates(new Set()); // Clear selection after action
      await (candidates as any).refetch(); // Refetch to update UI
    } catch (err) {
      // Error already handled by hook
      throw err;
    }
  };

  const handleScheduleInterview = async (data: {
    scheduledAt: Date;
    interviewerIds: string[];
    meetingPlatform: string;
  }) => {
    try {
      // In a real app, call API endpoint
      // POST /api/v1/ats/interviews
      // with interview data

      if (!selectedCandidate) return;

      addToast(
        `Interview scheduled for ${selectedCandidate.name} with ${data.interviewerIds.length} interviewer(s)`,
        'success'
      );
      setShowScheduler(false);
    } catch (err) {
      throw new Error('Failed to schedule interview');
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Recruitment Pipeline"
        subtitle="Manage candidates through the hiring process"
        icon="Briefcase"
      />

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Job Selection */}
      <div className="flex-1 min-w-[200px] max-w-xs">
        <select
          value={selectedJob}
          onChange={e => setSelectedJob(e.target.value)}
          className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
        >
          <option value="job-1">Senior Backend Engineer</option>
          <option value="job-2">Product Manager</option>
          <option value="job-3">Design Lead</option>
        </select>
      </div>

      {/* Filter Panel */}
      <FilterPanel
        onFiltersChange={applyFilters}
        onClearFilters={clearFilters}
        filteredCount={filteredCount}
        totalCount={totalCount}
      />

      {/* Pipeline Board */}
      <PipelineBoard
        positionId={selectedJob}
        candidates={filteredCandidates.length > 0 ? filteredCandidates : candidates}
        onStageChange={handleStageChange}
        onCandidateSelect={candidate => {
          setSelectedCandidate(candidate);
          setShowDetailModal(true);
        }}
        onScheduleInterview={candidate => {
          setSelectedCandidate(candidate);
          setShowScheduler(true);
        }}
        selectedCandidates={selectedCandidates}
        onCandidateToggle={handleCandidateToggle}
      />

      {/* Bulk Action Toolbar */}
      {selectedCandidates.size > 0 && (
        <BulkActionToolbar
          selectedCount={selectedCandidates.size}
          onSelectAll={handleSelectAll}
          onDeselectAll={handleDeselectAll}
          onExecuteAction={handleBulkAction}
        />
      )}

      {/* Candidate Detail Modal */}
      {showDetailModal && selectedCandidate && (
        <CandidateDetailModal
          applicationId={selectedCandidate.id}
          candidateName={selectedCandidate.name}
          candidateEmail={selectedCandidate.email}
          positionTitle={selectedCandidate.positionTitle}
          keywordScore={selectedCandidate.keywordScore}
          semanticScore={selectedCandidate.semanticScore}
          capabilityScore={selectedCandidate.capabilityScore}
          resumeText={selectedCandidate.resumeText}
          appliedAt={selectedCandidate.appliedAt}
          source={selectedCandidate.source}
          stage={selectedCandidate.stage}
          onClose={() => {
            setShowDetailModal(false);
            setSelectedCandidate(null);
          }}
          onScheduleInterview={() => {
            setShowDetailModal(false);
            setShowScheduler(true);
          }}
        />
      )}

      {/* Interview Scheduler Modal */}
      {showScheduler && selectedCandidate && (
        <InterviewScheduler
          candidateName={selectedCandidate.name}
          candidateEmail={selectedCandidate.email}
          candidateId={selectedCandidate.id}
          positionId={selectedJob}
          interviewers={interviewers}
          onSchedule={async (data) => {
            await handleScheduleInterview(data);
            setShowScheduler(false);
          }}
          onClose={() => {
            setShowScheduler(false);
          }}
        />
      )}

      {/* Scorecard Form Modal */}
      {showScorecard && selectedInterviewId && selectedCandidate && (
        <ScorecardForm
          interviewId={selectedInterviewId}
          candidateName={selectedCandidate.name}
          positionTitle={selectedCandidate.positionTitle}
          onSuccess={() => {
            setShowScorecard(false);
            setSelectedInterviewId(null);
          }}
          onClose={() => {
            setShowScorecard(false);
            setSelectedInterviewId(null);
          }}
        />
      )}
    </div>
  );
}
