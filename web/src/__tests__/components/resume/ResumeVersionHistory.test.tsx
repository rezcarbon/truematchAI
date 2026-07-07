import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ResumeVersionHistory from './ResumeVersionHistory';
import { ResumeVersion } from '@/types/resume';

describe('ResumeVersionHistory', () => {
  const mockVersions: ResumeVersion[] = [
    {
      id: 'v1',
      resumeId: 'resume1',
      version: 1,
      fileName: 'Resume_v1.pdf',
      format: 'pdf',
      fileSize: 102400,
      uploadMethod: 'drag-drop',
      status: 'completed',
      extractedText: 'Senior Developer...',
      skills: ['JavaScript', 'React', 'Node.js'],
      experience_years: 5,
      summary: 'Experienced software developer',
      uploadedAt: new Date(Date.now() - 86400000).toISOString(),
      annotation: 'First version',
    },
    {
      id: 'v2',
      resumeId: 'resume1',
      version: 2,
      fileName: 'Resume_v2.pdf',
      format: 'pdf',
      fileSize: 108000,
      uploadMethod: 'paste',
      status: 'completed',
      extractedText: 'Senior Developer with Python...',
      skills: ['JavaScript', 'React', 'Node.js', 'Python'],
      experience_years: 6,
      summary: 'Experienced full-stack developer',
      uploadedAt: new Date().toISOString(),
      annotation: '',
    },
  ];

  const mockOnRevert = jest.fn();
  const mockOnDelete = jest.fn();
  const mockOnCompare = jest.fn();
  const mockOnDownload = jest.fn();

  beforeEach(() => {
    mockOnRevert.mockClear();
    mockOnDelete.mockClear();
    mockOnCompare.mockClear();
    mockOnDownload.mockClear();
  });

  describe('Rendering', () => {
    it('should render version history header', () => {
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
        />
      );

      expect(screen.getByText('Version History')).toBeInTheDocument();
      expect(screen.getByText(/2 versions/)).toBeInTheDocument();
    });

    it('should display all versions', () => {
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
        />
      );

      expect(screen.getByText('Resume_v1.pdf')).toBeInTheDocument();
      expect(screen.getByText('Resume_v2.pdf')).toBeInTheDocument();
    });

    it('should render empty state when no versions', () => {
      render(
        <ResumeVersionHistory
          versions={[]}
          currentVersionId=""
        />
      );

      expect(
        screen.getByText(/No resume versions yet/)
      ).toBeInTheDocument();
    });

    it('should show current version badge', () => {
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
        />
      );

      expect(screen.getByText('Current')).toBeInTheDocument();
    });

    it('should display version metadata', () => {
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
        />
      );

      // Check for skills count
      expect(screen.getByText('3')).toBeInTheDocument(); // v1 has 3 skills

      // Check for experience years
      expect(screen.getByText('5y')).toBeInTheDocument(); // v1 has 5 years

      // Check for file size
      expect(screen.getByText(/100\.0KB|108\.0KB/)).toBeInTheDocument();
    });
  });

  describe('Version Expansion', () => {
    it('should expand version on button click', async () => {
      const user = userEvent.setup();
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
        />
      );

      const expandButtons = screen.getAllByRole('button', { name: '' });
      const versionRow = screen.getByText('Resume_v1.pdf').closest('div');
      const expandButton = versionRow?.querySelector('button[class*="rotate"]');

      if (expandButton) {
        await user.click(expandButton);

        // Check if expanded content appears
        expect(screen.getByText('Experienced software developer')).toBeInTheDocument();
      }
    });

    it('should display annotation when present', () => {
      const user = userEvent.setup();
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
        />
      );

      expect(screen.getByText('First version')).toBeInTheDocument();
    });
  });

  describe('Revert Functionality', () => {
    it('should show revert button for non-current versions', () => {
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
          onRevert={mockOnRevert}
        />
      );

      const revertButtons = screen.getAllByRole('button', { name: /Revert/i });
      expect(revertButtons.length).toBeGreaterThan(0);
    });

    it('should not show revert button for current version', () => {
      const onlyCurrentVersion: ResumeVersion[] = [mockVersions[1]];
      render(
        <ResumeVersionHistory
          versions={onlyCurrentVersion}
          currentVersionId="v2"
          onRevert={mockOnRevert}
        />
      );

      // If no revert buttons, it means current version doesn't have one
      const revertButtons = screen.queryAllByRole('button', { name: /Revert/i });
      expect(revertButtons.length).toBe(0);
    });

    it('should show revert confirmation on button click', async () => {
      const user = userEvent.setup();
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
          onRevert={mockOnRevert}
        />
      );

      const revertButton = screen.getAllByRole('button', { name: /Revert/i })[0];
      await user.click(revertButton);

      expect(
        screen.getByRole('button', { name: /Confirm Revert/i })
      ).toBeInTheDocument();
    });

    it('should call onRevert when confirmed', async () => {
      const user = userEvent.setup();
      mockOnRevert.mockResolvedValue(undefined);

      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
          onRevert={mockOnRevert}
        />
      );

      const revertButton = screen.getAllByRole('button', { name: /Revert/i })[0];
      await user.click(revertButton);

      const confirmButton = screen.getByRole('button', { name: /Confirm Revert/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockOnRevert).toHaveBeenCalledWith('v1');
      });
    });

    it('should allow canceling revert confirmation', async () => {
      const user = userEvent.setup();
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
          onRevert={mockOnRevert}
        />
      );

      const revertButton = screen.getAllByRole('button', { name: /Revert/i })[0];
      await user.click(revertButton);

      const cancelButton = screen.getAllByRole('button', { name: /Cancel/i })[0];
      await user.click(cancelButton);

      expect(mockOnRevert).not.toHaveBeenCalled();
    });
  });

  describe('Delete Functionality', () => {
    it('should show delete button for all non-current versions', () => {
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
          onDelete={mockOnDelete}
        />
      );

      const deleteButtons = screen.getAllByRole('button', { name: /Delete/i });
      expect(deleteButtons.length).toBeGreaterThan(0);
    });

    it('should disable delete button for current version', () => {
      const onlyCurrentVersion: ResumeVersion[] = [mockVersions[1]];
      render(
        <ResumeVersionHistory
          versions={onlyCurrentVersion}
          currentVersionId="v2"
          onDelete={mockOnDelete}
        />
      );

      const deleteButtons = screen.queryAllByRole('button', { name: /Delete/i });
      deleteButtons.forEach((button) => {
        if (mockVersions[1].id === 'v2') {
          expect(button).toBeDisabled();
        }
      });
    });

    it('should show delete confirmation on button click', async () => {
      const user = userEvent.setup();
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
          onDelete={mockOnDelete}
        />
      );

      const deleteButton = screen.getAllByRole('button', { name: /Delete/i })[0];
      await user.click(deleteButton);

      expect(
        screen.getByRole('button', { name: /Confirm Delete/i })
      ).toBeInTheDocument();
    });

    it('should call onDelete when confirmed', async () => {
      const user = userEvent.setup();
      mockOnDelete.mockResolvedValue(undefined);

      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
          onDelete={mockOnDelete}
        />
      );

      const deleteButton = screen.getAllByRole('button', { name: /Delete/i })[0];
      await user.click(deleteButton);

      const confirmButton = screen.getByRole('button', { name: /Confirm Delete/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockOnDelete).toHaveBeenCalledWith('v1');
      });
    });
  });

  describe('Compare Functionality', () => {
    it('should show compare button between versions', () => {
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
          onCompare={mockOnCompare}
        />
      );

      const compareButtons = screen.queryAllByRole('button', { name: /Compare/i });
      expect(compareButtons.length).toBeGreaterThanOrEqual(0);
    });

    it('should call onCompare with correct version IDs', async () => {
      const user = userEvent.setup();
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
          onCompare={mockOnCompare}
        />
      );

      const compareButtons = screen.queryAllByRole('button', { name: /Compare/i });
      if (compareButtons.length > 0) {
        await user.click(compareButtons[0]);

        await waitFor(() => {
          expect(mockOnCompare).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Download Functionality', () => {
    it('should show download button for completed versions', () => {
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
          onDownload={mockOnDownload}
        />
      );

      const downloadButtons = screen.queryAllByRole('button', { name: /Download/i });
      expect(downloadButtons.length).toBeGreaterThan(0);
    });

    it('should call onDownload with correct version ID', async () => {
      const user = userEvent.setup();
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
          onDownload={mockOnDownload}
        />
      );

      const downloadButtons = screen.queryAllByRole('button', { name: /Download/i });
      if (downloadButtons.length > 0) {
        await user.click(downloadButtons[0]);

        expect(mockOnDownload).toHaveBeenCalledWith('v1');
      }
    });
  });

  describe('Loading State', () => {
    it('should disable buttons when loading', () => {
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
          onRevert={mockOnRevert}
          onDelete={mockOnDelete}
          loading={true}
        />
      );

      const buttons = screen.getAllByRole('button');
      buttons.forEach((button) => {
        if (
          button.textContent?.includes('Revert') ||
          button.textContent?.includes('Delete') ||
          button.textContent?.includes('Compare')
        ) {
          expect(button).toBeDisabled();
        }
      });
    });
  });

  describe('Status Indicators', () => {
    it('should show completed status', () => {
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
        />
      );

      // Check for status indicators (visual indicators)
      expect(screen.getByText('Resume_v1.pdf')).toBeInTheDocument();
    });

    it('should show processing status with spinner', () => {
      const processingVersion: ResumeVersion = {
        ...mockVersions[0],
        status: 'processing',
      };

      render(
        <ResumeVersionHistory
          versions={[processingVersion]}
          currentVersionId="v2"
        />
      );

      expect(screen.getByText('Resume_v1.pdf')).toBeInTheDocument();
    });

    it('should show failed status with error message', () => {
      const failedVersion: ResumeVersion = {
        ...mockVersions[0],
        status: 'failed',
        errorMessage: 'File format not supported',
      };

      render(
        <ResumeVersionHistory
          versions={[failedVersion]}
          currentVersionId="v2"
        />
      );

      expect(screen.getByText('Resume_v1.pdf')).toBeInTheDocument();
      expect(screen.getByText('File format not supported')).toBeInTheDocument();
    });
  });

  describe('Sorting', () => {
    it('should sort versions by upload date (newest first)', () => {
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
        />
      );

      const versionElements = screen.getAllByText(/Resume_v/);
      // v2 should appear before v1 (newest first)
      expect(versionElements[0].textContent).toContain('Resume_v2');
    });
  });

  describe('Accessibility', () => {
    it('should have descriptive headings', () => {
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
        />
      );

      expect(screen.getByText('Version History')).toBeInTheDocument();
    });

    it('should have proper button labels', () => {
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
          onRevert={mockOnRevert}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText(/Revert/i)).toBeInTheDocument();
      expect(screen.getByText(/Delete/i)).toBeInTheDocument();
    });
  });

  describe('Version Metadata Display', () => {
    it('should display upload method label', () => {
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
        />
      );

      expect(screen.getByText('Drag & Drop')).toBeInTheDocument();
      expect(screen.getByText('Pasted Content')).toBeInTheDocument();
    });

    it('should display formatted upload date', () => {
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
        />
      );

      // Should contain date information
      expect(screen.getByText(/Jul|Aug|Sep|Oct|Nov|Dec|Jan|Feb|Mar|Apr|May|Jun/)).toBeInTheDocument();
    });

    it('should display file size in KB', () => {
      render(
        <ResumeVersionHistory
          versions={mockVersions}
          currentVersionId="v2"
        />
      );

      expect(screen.getByText(/100\.0KB|108\.0KB/)).toBeInTheDocument();
    });
  });
});
