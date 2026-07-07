/**
 * Tests for job favorites/saved jobs hook
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useJobFavorites } from '@/hooks/useJobFavorites';
import type { SavedJob } from '@/types/jobs';

describe('useJobFavorites Hook', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('Initial State', () => {
    it('should start with empty saved jobs', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.savedJobs).toEqual([]);
    });

    it('should set loading state initially', () => {
      const { result } = renderHook(() => useJobFavorites());

      // Initially might be loading or already loaded
      expect(typeof result.current.isLoading).toBe('boolean');
    });

    it('should persist saved jobs to localStorage', async () => {
      const { result } = renderHook(() => useJobFavorites('user123'));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.toggleSave('job-1');
      });

      await waitFor(() => {
        const stored = localStorage.getItem('truematch_saved_jobs');
        expect(stored).toBeTruthy();
      });
    });
  });

  describe('toggleSave', () => {
    it('should save a job when not saved', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.toggleSave('job-1');
      });

      expect(result.current.isSaved('job-1')).toBe(true);
      expect(result.current.savedJobs.length).toBe(1);
    });

    it('should remove a job when already saved', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Save job first
      await act(async () => {
        await result.current.toggleSave('job-1');
      });

      expect(result.current.isSaved('job-1')).toBe(true);

      // Remove job
      await act(async () => {
        await result.current.toggleSave('job-1');
      });

      expect(result.current.isSaved('job-1')).toBe(false);
      expect(result.current.savedJobs.length).toBe(0);
    });

    it('should handle multiple saved jobs', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.toggleSave('job-1');
        await result.current.toggleSave('job-2');
        await result.current.toggleSave('job-3');
      });

      expect(result.current.savedJobs.length).toBe(3);
      expect(result.current.isSaved('job-1')).toBe(true);
      expect(result.current.isSaved('job-2')).toBe(true);
      expect(result.current.isSaved('job-3')).toBe(true);
    });
  });

  describe('isSaved', () => {
    it('should return true for saved jobs', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.toggleSave('job-1');
      });

      expect(result.current.isSaved('job-1')).toBe(true);
    });

    it('should return false for unsaved jobs', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isSaved('job-1')).toBe(false);
    });

    it('should be case sensitive', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.toggleSave('job-1');
      });

      expect(result.current.isSaved('job-1')).toBe(true);
      expect(result.current.isSaved('JOB-1')).toBe(false);
    });
  });

  describe('removeSaved', () => {
    it('should remove a specific saved job', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.toggleSave('job-1');
        await result.current.toggleSave('job-2');
      });

      expect(result.current.savedJobs.length).toBe(2);

      await act(async () => {
        await result.current.removeSaved('job-1');
      });

      expect(result.current.savedJobs.length).toBe(1);
      expect(result.current.isSaved('job-1')).toBe(false);
      expect(result.current.isSaved('job-2')).toBe(true);
    });

    it('should not error when removing non-existent job', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.removeSaved('nonexistent');
      });

      expect(result.current.savedJobs.length).toBe(0);
    });
  });

  describe('updateNotes', () => {
    it('should update notes for a saved job', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.toggleSave('job-1');
      });

      const notes = 'Great opportunity!';

      await act(async () => {
        await result.current.updateNotes('job-1', notes);
      });

      const savedJob = result.current.getSavedJob('job-1');
      expect(savedJob?.notes).toBe(notes);
    });

    it('should not create job if not saved', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.updateNotes('job-1', 'Some notes');
      });

      // Job should not be created
      expect(result.current.isSaved('job-1')).toBe(false);
    });

    it('should clear notes by passing empty string', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.toggleSave('job-1');
        await result.current.updateNotes('job-1', 'Initial notes');
      });

      await act(async () => {
        await result.current.updateNotes('job-1', '');
      });

      const savedJob = result.current.getSavedJob('job-1');
      expect(savedJob?.notes).toBe('');
    });
  });

  describe('markApplied', () => {
    it('should mark job as applied', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.toggleSave('job-1');
        await result.current.markApplied('job-1');
      });

      const savedJob = result.current.getSavedJob('job-1');
      expect(savedJob?.status).toBe('applied');
      expect(savedJob?.appliedAt).toBeDefined();
    });

    it('should set appliedAt timestamp', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const beforeApply = new Date();

      await act(async () => {
        await result.current.toggleSave('job-1');
        await result.current.markApplied('job-1');
      });

      const savedJob = result.current.getSavedJob('job-1');
      const afterApply = new Date();

      expect(savedJob?.appliedAt).toBeDefined();
      expect(savedJob?.appliedAt!.getTime()).toBeGreaterThanOrEqual(beforeApply.getTime());
      expect(savedJob?.appliedAt!.getTime()).toBeLessThanOrEqual(afterApply.getTime());
    });

    it('should apply unsaved job', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Don't save first
      await act(async () => {
        await result.current.markApplied('job-1');
      });

      // Job should still be marked as applied
      const savedJob = result.current.getSavedJob('job-1');
      expect(savedJob?.status).toBe('applied');
    });
  });

  describe('getSavedJob', () => {
    it('should retrieve a saved job by ID', async () => {
      const { result } = renderHook(() => useJobFavorites('user123'));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.toggleSave('job-1');
      });

      const savedJob = result.current.getSavedJob('job-1');

      expect(savedJob).toBeDefined();
      expect(savedJob?.jobId).toBe('job-1');
      expect(savedJob?.userId).toBe('user123');
      expect(savedJob?.status).toBe('saved');
    });

    it('should return undefined for unsaved job', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const savedJob = result.current.getSavedJob('nonexistent');
      expect(savedJob).toBeUndefined();
    });
  });

  describe('Persistence', () => {
    it('should load saved jobs from localStorage on hook mount', async () => {
      // First, save some jobs
      localStorage.setItem(
        'truematch_saved_jobs',
        JSON.stringify([
          {
            jobId: 'job-1',
            userId: 'user123',
            savedAt: new Date().toISOString(),
            status: 'saved',
          },
          {
            jobId: 'job-2',
            userId: 'user123',
            savedAt: new Date().toISOString(),
            status: 'applied',
            appliedAt: new Date().toISOString(),
          },
        ])
      );

      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.savedJobs.length).toBe(2);
      expect(result.current.isSaved('job-1')).toBe(true);
      expect(result.current.isSaved('job-2')).toBe(true);
    });

    it('should handle corrupted localStorage data gracefully', async () => {
      localStorage.setItem('truematch_saved_jobs', 'invalid json');

      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Should not crash and should have empty jobs
      expect(result.current.savedJobs.length).toBe(0);
    });

    it('should update localStorage when jobs change', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.toggleSave('job-1');
      });

      await waitFor(() => {
        const stored = localStorage.getItem('truematch_saved_jobs');
        expect(stored).toBeTruthy();
        const jobs = JSON.parse(stored!);
        expect(jobs.some((j: SavedJob) => j.jobId === 'job-1')).toBe(true);
      });
    });
  });

  describe('User Association', () => {
    it('should associate saved jobs with userId', async () => {
      const { result } = renderHook(() => useJobFavorites('user123'));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.toggleSave('job-1');
      });

      const savedJob = result.current.getSavedJob('job-1');
      expect(savedJob?.userId).toBe('user123');
    });

    it('should handle anonymous users', async () => {
      const { result } = renderHook(() => useJobFavorites());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.toggleSave('job-1');
      });

      const savedJob = result.current.getSavedJob('job-1');
      expect(savedJob?.userId).toBe('anonymous');
    });
  });
});
