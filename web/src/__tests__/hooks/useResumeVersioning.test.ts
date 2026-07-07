/**
 * Hook Test Example: useResumeVersioning
 *
 * This demonstrates how to test custom React hooks using react-hooks-testing-library
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useResumeVersioning } from '@/hooks/useResumeVersioning';
import { createMockResume } from '../utils/test-utils';

/**
 * Note: This is an example test. The actual implementation depends on
 * what the useResumeVersioning hook does.
 */
describe('useResumeVersioning Hook', () => {
  it('should initialize with empty versions', () => {
    const { result } = renderHook(() => useResumeVersioning('resume-123'));

    expect(result.current.versions).toEqual([]);
    expect(result.current.currentVersion).toBeNull();
  });

  it('should fetch resume versions', async () => {
    const { result } = renderHook(() => useResumeVersioning('resume-123'));

    // Trigger fetch
    act(() => {
      result.current.fetchVersions?.();
    });

    // Wait for versions to load
    await waitFor(() => {
      expect(result.current.versions).toHaveLength(2);
    });

    expect(result.current.versions[0]).toHaveProperty('id');
    expect(result.current.versions[0]).toHaveProperty('versionNumber');
  });

  it('should create new version', async () => {
    const mockResume = createMockResume();
    const { result } = renderHook(() => useResumeVersioning(mockResume.id));

    const newContent = 'Updated resume content';

    act(() => {
      result.current.createVersion?.(newContent, 'Updated version');
    });

    await waitFor(() => {
      expect(result.current.versions).toHaveLength(1);
    });

    expect(result.current.versions[0].content).toContain('Updated');
  });

  it('should compare versions', async () => {
    const { result } = renderHook(() => useResumeVersioning('resume-123'));

    // Fetch versions first
    act(() => {
      result.current.fetchVersions?.();
    });

    await waitFor(() => {
      expect(result.current.versions.length).toBeGreaterThan(0);
    });

    // Compare versions
    act(() => {
      result.current.compareVersions?.(
        result.current.versions[0].id,
        result.current.versions[1].id
      );
    });

    // Check comparison result
    await waitFor(() => {
      expect(result.current.comparison).toBeDefined();
    });

    expect(result.current.comparison).toHaveProperty('added');
    expect(result.current.comparison).toHaveProperty('removed');
  });

  it('should revert to previous version', async () => {
    const { result } = renderHook(() => useResumeVersioning('resume-123'));

    // Fetch versions
    act(() => {
      result.current.fetchVersions?.();
    });

    await waitFor(() => {
      expect(result.current.versions.length).toBeGreaterThan(0);
    });

    const previousVersion = result.current.versions[1];

    // Revert
    act(() => {
      result.current.revert?.(previousVersion.id);
    });

    // Verify revert was successful
    await waitFor(() => {
      expect(result.current.currentVersion?.id).toBe(previousVersion.id);
    });
  });

  it('should handle errors when fetching versions', async () => {
    const { result } = renderHook(() => useResumeVersioning('invalid-id'));

    act(() => {
      result.current.fetchVersions?.();
    });

    await waitFor(() => {
      expect(result.current.error).toBeDefined();
    });

    expect(result.current.error).toContain('not found');
  });

  it('should show loading state', async () => {
    const { result } = renderHook(() => useResumeVersioning('resume-123'));

    expect(result.current.loading).toBe(false);

    act(() => {
      result.current.fetchVersions?.();
    });

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it('should clear error after successful operation', async () => {
    const { result } = renderHook(() => useResumeVersioning('resume-123'));

    // First operation fails
    act(() => {
      result.current.fetchVersions?.();
    });

    await waitFor(() => {
      expect(result.current.error).toBeDefined();
    });

    // Clear error
    act(() => {
      result.current.clearError?.();
    });

    expect(result.current.error).toBeNull();
  });
});
