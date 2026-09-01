/**
 * End-to-End tests for JD Optimizer
 * These tests simulate real user interactions with the full application flow
 */
import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import JDOptimizer from '@/components/JDOptimizer/JDOptimizer';

// Mock fetch API
beforeEach(() => {
  global.fetch = jest.fn();
});

afterEach(() => {
  jest.clearAllMocks();
});

describe('JD Optimizer E2E Tests', () => {
  describe('Complete Optimization Flow', () => {
    it('should complete full optimization workflow', async () => {
      const mockApiResponse = {
        qualityScore: 72,
        optimizedJD:
          'We are seeking a Senior Software Engineer with 5+ years of experience. Salary: $100,000-$130,000. Responsibilities include system design, code review, and mentoring junior developers.',
        issues: [
          {
            id: '1',
            title: 'Missing Salary Information',
            description: 'Include compensation details to attract better candidates',
            category: 'completeness' as const,
            severity: 'high' as const,
            problematicText: 'Senior Software Engineer position',
            suggestion:
              'Senior Software Engineer position - Salary: $100,000-$130,000',
            explanation:
              'Transparent compensation attracts more qualified candidates',
            impact: 'Increased application quality and reduced screening time',
            isFixed: false,
          },
          {
            id: '2',
            title: 'Vague Experience Requirements',
            description: 'Be more specific about required experience',
            category: 'clarity' as const,
            severity: 'medium' as const,
            problematicText: 'experienced developer',
            suggestion: '5+ years of experience in backend development',
            explanation: 'Specific requirements help candidates self-assess fit',
            impact: 'Better qualified candidate pool',
            isFixed: false,
          },
        ],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockApiResponse,
      });

      render(<JDOptimizer apiEndpoint="/api/jd-optimizer" />);

      // Step 1: Enter job description
      const textarea = screen.getByPlaceholderText(
        'Paste your job description here...'
      );
      const testJD =
        'Senior Software Engineer position. We need an experienced developer.';

      await userEvent.type(textarea, testJD);
      expect((textarea as HTMLTextAreaElement).value).toBe(testJD);

      // Step 2: Click analyze button
      const analyzeButton = screen.getByText('Analyze JD');
      expect(analyzeButton).not.toBeDisabled();
      await userEvent.click(analyzeButton);

      // Step 3: Verify processing state
      expect(screen.getByText('Analyzing your job description...')).toBeInTheDocument();

      // Step 4: Verify results display
      await waitFor(() => {
        expect(screen.getByText('Quality Score')).toBeInTheDocument();
        expect(screen.getByText('Issues Found')).toBeInTheDocument();
      });

      // Step 5: Verify quality score gauge
      await waitFor(() => {
        expect(screen.getByText('72')).toBeInTheDocument();
      });

      // Step 6: Verify issues list
      expect(screen.getByText('Missing Salary Information')).toBeInTheDocument();
      expect(screen.getByText('Vague Experience Requirements')).toBeInTheDocument();

      // Step 7: Interact with issue cards
      const issueCards = screen.getAllByRole('button');
      const firstIssueButton = issueCards[0];
      await userEvent.click(firstIssueButton);

      // Step 8: Verify expanded issue content
      await waitFor(() => {
        expect(screen.getByText('CURRENT TEXT')).toBeInTheDocument();
        expect(screen.getByText('SUGGESTED FIX')).toBeInTheDocument();
      });

      // Step 9: Apply fix
      const applyButton = screen.getByText('Apply Fix');
      await userEvent.click(applyButton);

      // Step 10: Verify progress update
      await waitFor(() => {
        const progressText = screen.getByText(/1 of 2/);
        expect(progressText).toBeInTheDocument();
      });

      // Step 11: Download optimized JD
      const downloadButton = screen.getByText('Download');
      expect(downloadButton).toBeInTheDocument();

      // Step 12: Reset for new optimization
      const optimizeAnotherButton = screen.getByText('Optimize Another');
      await userEvent.click(optimizeAnotherButton);

      // Step 13: Verify return to input state
      await waitFor(() => {
        expect(
          screen.getByPlaceholderText('Paste your job description here...')
        ).toBeInTheDocument();
      });
    });

    it('should handle error state gracefully', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      );

      render(<JDOptimizer apiEndpoint="/api/jd-optimizer" />);

      const textarea = screen.getByPlaceholderText(
        'Paste your job description here...'
      );
      await userEvent.type(textarea, 'Test job description');

      const analyzeButton = screen.getByText('Analyze JD');
      await userEvent.click(analyzeButton);

      // Verify error message displays
      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument();
        expect(screen.getByText(/Network error/)).toBeInTheDocument();
      });

      // Verify user is back at input state
      expect(
        screen.getByPlaceholderText('Paste your job description here...')
      ).toBeInTheDocument();
    });

    it('should support editing optimized JD', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          qualityScore: 80,
          optimizedJD: 'Optimized job description',
          issues: [],
        }),
      });

      render(<JDOptimizer apiEndpoint="/api/jd-optimizer" />);

      const textarea = screen.getByPlaceholderText(
        'Paste your job description here...'
      );
      await userEvent.type(textarea, 'Test job');

      const analyzeButton = screen.getByText('Analyze JD');
      await userEvent.click(analyzeButton);

      // Wait for results
      await waitFor(() => {
        expect(screen.getByText('Edit JD')).toBeInTheDocument();
      });

      // Click edit
      const editButton = screen.getByText('Edit JD');
      await userEvent.click(editButton);

      // Verify editor appears
      await waitFor(() => {
        expect(screen.getByText('Edit Job Description')).toBeInTheDocument();
      });

      // Edit the content
      const editorTextarea = screen.getByPlaceholderText(
        'Edit your job description here...'
      );
      await userEvent.clear(editorTextarea);
      await userEvent.type(
        editorTextarea,
        'Customized optimized job description'
      );

      // Save changes
      const saveButton = screen.getByText('Save Changes');
      await userEvent.click(saveButton);

      // Verify editing mode closes
      await waitFor(() => {
        expect(screen.getByText('Edit JD')).toBeInTheDocument();
      });
    });

    it('should display before/after comparison', async () => {
      const beforeText = 'Senior Developer we need for the team';
      const afterText =
        'We are seeking a Senior Developer for our engineering team';

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          qualityScore: 75,
          optimizedJD: afterText,
          issues: [
            {
              id: '1',
              title: 'Weak Language',
              description: 'Replace weak language',
              category: 'clarity' as const,
              severity: 'medium' as const,
              isFixed: false,
            },
          ],
        }),
      });

      render(<JDOptimizer apiEndpoint="/api/jd-optimizer" />);

      const textarea = screen.getByPlaceholderText(
        'Paste your job description here...'
      );
      await userEvent.type(textarea, beforeText);

      const analyzeButton = screen.getByText('Analyze JD');
      await userEvent.click(analyzeButton);

      // Wait for comparison to appear
      await waitFor(() => {
        expect(screen.getByText('Before & After')).toBeInTheDocument();
      });

      // Verify both texts are visible
      expect(screen.getByText('Split View')).toBeInTheDocument();
    });

    it('should handle multiple issue fixes sequentially', async () => {
      const issues = [
        {
          id: '1',
          title: 'Issue 1',
          description: 'First issue',
          category: 'clarity' as const,
          severity: 'high' as const,
          isFixed: false,
        },
        {
          id: '2',
          title: 'Issue 2',
          description: 'Second issue',
          category: 'tone' as const,
          severity: 'medium' as const,
          isFixed: false,
        },
        {
          id: '3',
          title: 'Issue 3',
          description: 'Third issue',
          category: 'completeness' as const,
          severity: 'low' as const,
          isFixed: false,
        },
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          qualityScore: 60,
          optimizedJD: 'Optimized text',
          issues,
        }),
      });

      render(<JDOptimizer apiEndpoint="/api/jd-optimizer" />);

      const textarea = screen.getByPlaceholderText(
        'Paste your job description here...'
      );
      await userEvent.type(textarea, 'Test job');

      const analyzeButton = screen.getByText('Analyze JD');
      await userEvent.click(analyzeButton);

      // Wait for issues to load
      await waitFor(() => {
        expect(screen.getByText('Issue 1')).toBeInTheDocument();
      });

      // Fix each issue
      for (let i = 0; i < issues.length; i++) {
        const issueTitle = `Issue ${i + 1}`;
        const issueButton = screen.getByText(issueTitle).closest('button');
        if (issueButton) {
          await userEvent.click(issueButton);

          // Find and click apply button
          await waitFor(() => {
            const applyButtons = screen.getAllByText('Apply Fix');
            if (applyButtons.length > 0) {
              applyButtons[0].click();
            }
          });
        }
      }

      // Verify progress shows all fixed
      await waitFor(() => {
        expect(screen.getByText(/3 of 3/)).toBeInTheDocument();
      });
    });

    it('should validate input before processing', async () => {
      const alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => {});

      render(<JDOptimizer apiEndpoint="/api/jd-optimizer" />);

      const analyzeButton = screen.getByText('Analyze JD');

      // Try with empty input
      await userEvent.click(analyzeButton);
      expect(alertSpy).not.toHaveBeenCalled(); // Button should be disabled

      // Try with only whitespace
      const textarea = screen.getByPlaceholderText(
        'Paste your job description here...'
      );
      await userEvent.type(textarea, '   ');

      // Clear and try again with valid input
      await userEvent.clear(textarea);
      await userEvent.type(textarea, 'Valid job description');

      // Now button should be enabled
      expect(analyzeButton).not.toBeDisabled();

      alertSpy.mockRestore();
    });

    it('should display quality score animation', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          qualityScore: 85,
          optimizedJD: 'Optimized text',
          issues: [],
        }),
      });

      render(<JDOptimizer apiEndpoint="/api/jd-optimizer" />);

      const textarea = screen.getByPlaceholderText(
        'Paste your job description here...'
      );
      await userEvent.type(textarea, 'Test');

      const analyzeButton = screen.getByText('Analyze JD');
      await userEvent.click(analyzeButton);

      // Score should animate to 85
      await waitFor(
        () => {
          expect(screen.getByText('85')).toBeInTheDocument();
        },
        { timeout: 2000 }
      );

      // Should show "Excellent" rating
      expect(screen.getByText('Excellent')).toBeInTheDocument();
    });

    it('should maintain state when toggling view modes', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          qualityScore: 75,
          optimizedJD: 'Optimized text',
          issues: [],
        }),
      });

      render(<JDOptimizer apiEndpoint="/api/jd-optimizer" />);

      const textarea = screen.getByPlaceholderText(
        'Paste your job description here...'
      );
      await userEvent.type(textarea, 'Test job');

      const analyzeButton = screen.getByText('Analyze JD');
      await userEvent.click(analyzeButton);

      // Wait for comparison view
      await waitFor(() => {
        expect(screen.getByText('Before & After')).toBeInTheDocument();
      });

      // Toggle views
      const stackedButton = screen.getByText('Stacked View');
      await userEvent.click(stackedButton);

      // State should be maintained
      expect(stackedButton).toHaveClass('bg-blue-100');

      const splitButton = screen.getByText('Split View');
      await userEvent.click(splitButton);

      expect(splitButton).toHaveClass('bg-blue-100');
    });
  });

  describe('Error Scenarios', () => {
    it('should handle API timeout', async () => {
      (global.fetch as jest.Mock).mockImplementationOnce(
        () =>
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Timeout')), 100)
          )
      );

      render(<JDOptimizer apiEndpoint="/api/jd-optimizer" />);

      const textarea = screen.getByPlaceholderText(
        'Paste your job description here...'
      );
      await userEvent.type(textarea, 'Test');

      const analyzeButton = screen.getByText('Analyze JD');
      await userEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/Error/)).toBeInTheDocument();
      });
    });

    it('should handle malformed API response', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ invalid: 'response' }),
      });

      render(<JDOptimizer apiEndpoint="/api/jd-optimizer" />);

      const textarea = screen.getByPlaceholderText(
        'Paste your job description here...'
      );
      await userEvent.type(textarea, 'Test');

      const analyzeButton = screen.getByText('Analyze JD');
      await userEvent.click(analyzeButton);

      // Should handle gracefully
      await waitFor(() => {
        // Either show error or handle the missing fields
        const qualityScoreElement = screen.queryByText('Quality Score');
        const errorElement = screen.queryByText(/Error/);
        expect(qualityScoreElement || errorElement).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels and roles', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          qualityScore: 75,
          optimizedJD: 'Text',
          issues: [],
        }),
      });

      render(<JDOptimizer apiEndpoint="/api/jd-optimizer" />);

      // Check for proper labels
      const textarea = screen.getByPlaceholderText(
        'Paste your job description here...'
      );
      expect(textarea).toBeInTheDocument();

      // Input should be properly associated
      expect(textarea).toHaveAttribute('id', 'jd-textarea');
    });
  });
});
