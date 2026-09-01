/**
 * Hook for managing job favorites/saved jobs
 */

import { useState, useEffect, useCallback } from 'react';
import type { SavedJob } from '@/types/jobs';

const STORAGE_KEY = 'truematch_saved_jobs';

export interface UseJobFavoritesReturn {
  savedJobs: SavedJob[];
  isSaved: (jobId: string) => boolean;
  toggleSave: (jobId: string) => Promise<void>;
  removeSaved: (jobId: string) => Promise<void>;
  updateNotes: (jobId: string, notes: string) => Promise<void>;
  markApplied: (jobId: string) => Promise<void>;
  getSavedJob: (jobId: string) => SavedJob | undefined;
  isLoading: boolean;
}

export function useJobFavorites(userId?: string): UseJobFavoritesReturn {
  const [savedJobs, setSavedJobs] = useState<SavedJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load saved jobs from localStorage on mount
  useEffect(() => {
    const loadSavedJobs = () => {
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          const jobs = JSON.parse(stored);
          setSavedJobs(jobs);
        }
      } catch (error) {
        console.error('Failed to load saved jobs:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadSavedJobs();
  }, []);

  // Save to localStorage whenever savedJobs changes
  useEffect(() => {
    if (!isLoading) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(savedJobs));
      } catch (error) {
        console.error('Failed to save jobs:', error);
      }
    }
  }, [savedJobs, isLoading]);

  const isSaved = useCallback(
    (jobId: string) => {
      return savedJobs.some((job) => job.jobId === jobId);
    },
    [savedJobs]
  );

  const toggleSave = useCallback(
    async (jobId: string) => {
      if (isSaved(jobId)) {
        await removeSaved(jobId);
      } else {
        const newSavedJob: SavedJob = {
          jobId,
          userId: userId || 'anonymous',
          savedAt: new Date(),
          status: 'saved',
        };
        setSavedJobs((prev) => [...prev, newSavedJob]);
      }
    },
    [userId, isSaved]
  );

  const removeSaved = useCallback(async (jobId: string) => {
    setSavedJobs((prev) => prev.filter((job) => job.jobId !== jobId));
  }, []);

  const updateNotes = useCallback(
    async (jobId: string, notes: string) => {
      setSavedJobs((prev) =>
        prev.map((job) => (job.jobId === jobId ? { ...job, notes } : job))
      );
    },
    []
  );

  const markApplied = useCallback(
    async (jobId: string) => {
      setSavedJobs((prev) =>
        prev.map((job) =>
          job.jobId === jobId
            ? { ...job, status: 'applied', appliedAt: new Date() }
            : job
        )
      );
    },
    []
  );

  const getSavedJob = useCallback(
    (jobId: string) => {
      return savedJobs.find((job) => job.jobId === jobId);
    },
    [savedJobs]
  );

  return {
    savedJobs,
    isSaved,
    toggleSave,
    removeSaved,
    updateNotes,
    markApplied,
    getSavedJob,
    isLoading,
  };
}
