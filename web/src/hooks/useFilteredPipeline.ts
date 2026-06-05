import { useState, useCallback, useEffect } from 'react';
import { useToast } from '@/components/providers/ToastProvider';

export interface PipelineFilters {
  stages?: string[];
  scoreRange?: {
    keyword?: { min: number; max: number };
    semantic?: { min: number; max: number };
    capability?: { min: number; max: number };
    overall?: { min: number; max: number };
  };
  sources?: string[];
  dateRange?: {
    start?: Date;
    end?: Date;
  };
  searchText?: string;
}

export interface FilteredCandidate {
  id: string;
  name: string;
  stage: string;
  daysInStage: number;
  keywordScore?: number;
  semanticScore?: number;
  capabilityScore?: number;
  source?: string;
  appliedAt?: string;
}

interface UseFilteredPipelineResult {
  candidates: FilteredCandidate[];
  filteredCount: number;
  totalCount: number;
  loading: boolean;
  error: string | null;
  applyFilters: (filters: PipelineFilters) => Promise<void>;
  clearFilters: () => Promise<void>;
  currentFilters: PipelineFilters;
}

/**
 * Hook to fetch and filter candidates based on search criteria
 * Supports filtering by stage, score range, source, date range, and text search
 */
export function useFilteredPipeline(positionId: string): UseFilteredPipelineResult {
  const { addToast } = useToast();
  const [candidates, setCandidates] = useState<FilteredCandidate[]>([]);
  const [filteredCount, setFilteredCount] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentFilters, setCurrentFilters] = useState<PipelineFilters>({});

  // Fetch all candidates
  const fetchAllCandidates = useCallback(async (): Promise<FilteredCandidate[]> => {
    try {
      const response = await fetch(`/api/proxy/ats/positions/${positionId}/pipeline`);
      if (!response.ok) {
        throw new Error('Failed to fetch pipeline');
      }

      const data = await response.json();
      return Array.isArray(data) ? data : data.items || [];
    } catch (err) {
      console.error('Error fetching pipeline:', err);
      throw err;
    }
  }, [positionId]);

  // Apply filters to candidates in memory
  const filterCandidates = useCallback(
    (candidates: FilteredCandidate[], filters: PipelineFilters): FilteredCandidate[] => {
      return candidates.filter(candidate => {
        // Stage filter
        if (filters.stages && filters.stages.length > 0) {
          if (!filters.stages.includes(candidate.stage)) {
            return false;
          }
        }

        // Score range filters
        if (filters.scoreRange) {
          if (filters.scoreRange.keyword) {
            const score = candidate.keywordScore || 0;
            if (
              score < filters.scoreRange.keyword.min ||
              score > filters.scoreRange.keyword.max
            ) {
              return false;
            }
          }

          if (filters.scoreRange.semantic) {
            const score = candidate.semanticScore || 0;
            if (
              score < filters.scoreRange.semantic.min ||
              score > filters.scoreRange.semantic.max
            ) {
              return false;
            }
          }

          if (filters.scoreRange.capability) {
            const score = candidate.capabilityScore || 0;
            if (
              score < filters.scoreRange.capability.min ||
              score > filters.scoreRange.capability.max
            ) {
              return false;
            }
          }

          if (filters.scoreRange.overall) {
            const overallScore =
              candidate.keywordScore && candidate.semanticScore && candidate.capabilityScore
                ? (candidate.keywordScore + candidate.semanticScore + candidate.capabilityScore) / 3
                : 0;
            if (
              overallScore < filters.scoreRange.overall.min ||
              overallScore > filters.scoreRange.overall.max
            ) {
              return false;
            }
          }
        }

        // Source filter
        if (filters.sources && filters.sources.length > 0) {
          if (!candidate.source || !filters.sources.includes(candidate.source)) {
            return false;
          }
        }

        // Date range filter
        if (filters.dateRange) {
          if (candidate.appliedAt) {
            const appliedDate = new Date(candidate.appliedAt);
            if (filters.dateRange.start && appliedDate < filters.dateRange.start) {
              return false;
            }
            if (filters.dateRange.end && appliedDate > filters.dateRange.end) {
              return false;
            }
          }
        }

        // Text search filter
        if (filters.searchText && filters.searchText.trim()) {
          const searchLower = filters.searchText.toLowerCase();
          const matchesName = candidate.name.toLowerCase().includes(searchLower);
          if (!matchesName) {
            return false;
          }
        }

        return true;
      });
    },
    []
  );

  // Initial load
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        const allCandidates = await fetchAllCandidates();
        setCandidates(allCandidates);
        setTotalCount(allCandidates.length);
        setFilteredCount(allCandidates.length);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load pipeline';
        setError(message);
        addToast(message, 'error');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [positionId, fetchAllCandidates, addToast]);

  // Apply filters
  const applyFilters = useCallback(
    async (filters: PipelineFilters) => {
      try {
        setCurrentFilters(filters);
        const filtered = filterCandidates(candidates, filters);
        setFilteredCount(filtered.length);

        if (filtered.length === 0) {
          addToast('No candidates match your filters', 'info');
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to apply filters';
        addToast(message, 'error');
      }
    },
    [candidates, filterCandidates, addToast]
  );

  // Clear filters
  const clearFilters = useCallback(async () => {
    try {
      setCurrentFilters({});
      setFilteredCount(totalCount);
      addToast('Filters cleared', 'success');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to clear filters';
      addToast(message, 'error');
    }
  }, [totalCount, addToast]);

  // Return filtered candidates based on current filters
  const getFilteredCandidates = useCallback(() => {
    return filterCandidates(candidates, currentFilters);
  }, [candidates, currentFilters, filterCandidates]);

  return {
    candidates: getFilteredCandidates(),
    filteredCount,
    totalCount,
    loading,
    error,
    applyFilters,
    clearFilters,
    currentFilters,
  };
}
