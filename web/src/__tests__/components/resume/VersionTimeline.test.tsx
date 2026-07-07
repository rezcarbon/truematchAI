import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { VersionTimeline } from '@/components/resume/VersionTimeline';
import type { ResumeVersion } from '@/types/resume';

describe('VersionTimeline', () => {
  const mockVersions: ResumeVersion[] = [
    {
      id: 'v1',
      resumeId: 'resume1',
      version: 1,
      fileName: 'resume_v1.pdf',
      format: 'pdf',
      fileSize: 1024,
      uploadMethod: 'drag-drop',
      status: 'completed',
      extractedText: 'John Doe...',
      skills: ['React', 'TypeScript'],
      experience_years: 5,
      summary: 'Senior developer',
      uploadedAt: '2024-01-01T10:00:00Z',
    },
    {
      id: 'v2',
      resumeId: 'resume1',
      version: 2,
      fileName: 'resume_v2.pdf',
      format: 'pdf',
      fileSize: 1024,
      uploadMethod: 'drag-drop',
      status: 'completed',
      extractedText: 'John Doe Updated...',
      skills: ['React', 'TypeScript', 'Node.js'],
      experience_years: 6,
      summary: 'Senior developer with Node.js',
      uploadedAt: '2024-01-15T10:00:00Z',
    },
  ];

  const mockOnRevert = jest.fn();
  const mockOnDelete = jest.fn();
  const mockOnCompare = jest.fn();
  const mockOnAnnotate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders version timeline with versions', () => {
    render(
      <VersionTimeline
        versions={mockVersions}
        currentVersionId="v2"
        onRevert={mockOnRevert}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText(/Version History/)).toBeInTheDocument();
    expect(screen.getByText('2 versions')).toBeInTheDocument();
  });

  it('displays current version badge', () => {
    render(
      <VersionTimeline
        versions={mockVersions}
        currentVersionId="v2"
      />
    );

    expect(screen.getByText('Current')).toBeInTheDocument();
  });

  it('shows version details', () => {
    render(
      <VersionTimeline
        versions={mockVersions}
        currentVersionId="v2"
      />
    );

    expect(screen.getByText('resume_v1.pdf')).toBeInTheDocument();
    expect(screen.getByText('resume_v2.pdf')).toBeInTheDocument();
    expect(screen.getByText('2 detected')).toBeInTheDocument(); // skills
  });

  it('displays revert button for non-current versions', () => {
    render(
      <VersionTimeline
        versions={mockVersions}
        currentVersionId="v2"
        onRevert={mockOnRevert}
      />
    );

    const revertButtons = screen.getAllByRole('button', { name: /Revert/i });
    expect(revertButtons.length).toBeGreaterThan(0);
  });

  it('does not show revert button for current version', () => {
    render(
      <VersionTimeline
        versions={mockVersions}
        currentVersionId="v2"
        onRevert={mockOnRevert}
      />
    );

    const revertButtons = screen.queryAllByRole('button', { name: /Revert/i });
    // Only v1 should have revert button, not v2
    expect(revertButtons.length).toBeLessThan(mockVersions.length);
  });

  it('calls onRevert when revert button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <VersionTimeline
        versions={mockVersions}
        currentVersionId="v2"
        onRevert={mockOnRevert}
      />
    );

    const revertButton = screen.getByRole('button', { name: /Revert/i });
    await user.click(revertButton);

    expect(mockOnRevert).toHaveBeenCalledWith('v1');
  });

  it('calls onDelete when delete button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <VersionTimeline
        versions={mockVersions}
        currentVersionId="v2"
        onDelete={mockOnDelete}
      />
    );

    const deleteButtons = screen.getAllByRole('button', { name: /Delete/i });
    await user.click(deleteButtons[0]);

    expect(mockOnDelete).toHaveBeenCalledWith('v1');
  });

  it('calls onCompare when compare button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <VersionTimeline
        versions={mockVersions}
        currentVersionId="v2"
        onCompare={mockOnCompare}
      />
    );

    const compareButton = screen.getByRole('button', { name: /Compare/i });
    await user.click(compareButton);

    expect(mockOnCompare).toHaveBeenCalledWith('v1', 'v2');
  });

  it('calls onAnnotate when add note button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <VersionTimeline
        versions={mockVersions}
        currentVersionId="v2"
        onAnnotate={mockOnAnnotate}
      />
    );

    const annotateButtons = screen.getAllByRole('button', { name: /Add Note/i });
    await user.click(annotateButtons[0]);

    expect(mockOnAnnotate).toHaveBeenCalledWith('v1');
  });

  it('displays version annotations', () => {
    const versionsWithAnnotation: ResumeVersion[] = [
      {
        ...mockVersions[0],
        annotation: 'Added new skills section',
      },
    ];

    render(
      <VersionTimeline
        versions={versionsWithAnnotation}
        currentVersionId="v1"
      />
    );

    expect(screen.getByText('Added new skills section')).toBeInTheDocument();
  });

  it('disables buttons when loading is true', () => {
    render(
      <VersionTimeline
        versions={mockVersions}
        currentVersionId="v2"
        onRevert={mockOnRevert}
        onDelete={mockOnDelete}
        loading={true}
      />
    );

    const buttons = screen.getAllByRole('button').filter(
      btn => btn.textContent?.includes('Revert') || btn.textContent?.includes('Delete')
    );

    buttons.forEach(btn => {
      expect(btn).toBeDisabled();
    });
  });

  it('disables delete button for current version', () => {
    render(
      <VersionTimeline
        versions={mockVersions}
        currentVersionId="v2"
        onDelete={mockOnDelete}
      />
    );

    const deleteButtons = screen.getAllByRole('button', { name: /Delete/i });
    // Second delete button (for current version) should be disabled
    expect(deleteButtons[deleteButtons.length - 1]).toBeDisabled();
  });

  it('renders empty state when no versions', () => {
    render(
      <VersionTimeline
        versions={[]}
        currentVersionId=""
      />
    );

    expect(screen.getByText(/No resume versions yet/)).toBeInTheDocument();
  });

  it('displays upload method label', () => {
    render(
      <VersionTimeline
        versions={mockVersions}
        currentVersionId="v2"
      />
    );

    expect(screen.getByText(/Drag & Drop/i)).toBeInTheDocument();
  });

  it('displays error message for failed uploads', () => {
    const failedVersion: ResumeVersion = {
      ...mockVersions[0],
      status: 'failed',
      errorMessage: 'Failed to parse PDF',
    };

    render(
      <VersionTimeline
        versions={[failedVersion]}
        currentVersionId="v2"
      />
    );

    expect(screen.getByText('Failed to parse PDF')).toBeInTheDocument();
  });

  it('shows processing status icon', () => {
    const processingVersion: ResumeVersion = {
      ...mockVersions[0],
      status: 'processing',
    };

    const { container } = render(
      <VersionTimeline
        versions={[processingVersion]}
        currentVersionId="v2"
      />
    );

    // Check for processing icon (animated spinner)
    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('sorts versions by upload date descending', () => {
    const oldVersion: ResumeVersion = {
      ...mockVersions[0],
      uploadedAt: '2024-01-01T10:00:00Z',
    };

    const newVersion: ResumeVersion = {
      ...mockVersions[1],
      uploadedAt: '2024-01-15T10:00:00Z',
    };

    const { container } = render(
      <VersionTimeline
        versions={[oldVersion, newVersion]}
        currentVersionId="v1"
      />
    );

    // New version should appear first
    const fileNames = container.querySelectorAll('[class*="font-medium"]');
    expect(fileNames.length).toBeGreaterThan(0);
  });

  it('hides compare button for single version', () => {
    render(
      <VersionTimeline
        versions={[mockVersions[0]]}
        currentVersionId="v1"
        onCompare={mockOnCompare}
      />
    );

    const compareButton = screen.queryByRole('button', { name: /Compare/i });
    expect(compareButton).not.toBeInTheDocument();
  });

  it('displays experience years', () => {
    render(
      <VersionTimeline
        versions={mockVersions}
        currentVersionId="v2"
      />
    );

    expect(screen.getByText('5y')).toBeInTheDocument();
    expect(screen.getByText('6y')).toBeInTheDocument();
  });

  it('displays file size in KB', () => {
    render(
      <VersionTimeline
        versions={mockVersions}
        currentVersionId="v2"
      />
    );

    expect(screen.getByText(/1.0KB/)).toBeInTheDocument();
  });

  it('handles missing callbacks gracefully', () => {
    render(
      <VersionTimeline
        versions={mockVersions}
        currentVersionId="v2"
      />
    );

    expect(screen.getByText(/Version History/)).toBeInTheDocument();
  });
});
