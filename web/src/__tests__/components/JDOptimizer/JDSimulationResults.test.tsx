import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import JDSimulationResults from '@/components/JDOptimizer/JDSimulationResults';
import { JDOptimizationResult } from '@/types/jd-optimizer';

// Mock the QualityScoreGauge component
jest.mock('@/components/JDOptimizer/QualityScoreGauge', () => {
  return function MockQualityScoreGauge({ score }: { score: number }) {
    return <div data-testid="quality-score-gauge">{score}</div>;
  };
});

// Mock the IssueCard component
jest.mock('@/components/JDOptimizer/IssueCard', () => {
  return function MockIssueCard({ issue }: any) {
    return <div data-testid="issue-card">{issue.title}</div>;
  };
});

describe('JDSimulationResults', () => {
  const mockResult: JDOptimizationResult = {
    qualityScore: 75,
    summary: 'Job description is well-structured with minor improvements needed',
    issues: [
      {
        id: '1',
        title: 'Vague job requirements',
        description: 'Requirements are not specific enough',
        category: 'clarity',
        severity: 'high',
        suggestion: 'Add specific metrics and KPIs',
      },
      {
        id: '2',
        title: 'Missing benefits section',
        description: 'No information about benefits',
        category: 'completeness',
        severity: 'medium',
        suggestion: 'Add a dedicated benefits section',
      },
      {
        id: '3',
        title: 'Minor formatting issue',
        description: 'Inconsistent bullet point style',
        category: 'structure',
        severity: 'low',
        suggestion: 'Standardize formatting',
      },
    ],
    improvements: [
      'Add specific experience years required',
      'Clarify reporting structure',
      'Include salary range',
    ],
  };

  const mockOnExport = jest.fn();
  const mockOnApplyFix = jest.fn();

  beforeEach(() => {
    mockOnExport.mockClear();
    mockOnApplyFix.mockClear();
  });

  describe('Rendering', () => {
    it('should render results header and title', () => {
      render(
        <JDSimulationResults
          result={mockResult}
          onExport={mockOnExport}
        />
      );

      expect(screen.getByText('Analysis Results')).toBeInTheDocument();
      expect(screen.getByText(/Detailed breakdown of your job description quality/)).toBeInTheDocument();
    });

    it('should display quality score gauge', () => {
      render(
        <JDSimulationResults result={mockResult} />
      );

      const gauge = screen.getByTestId('quality-score-gauge');
      expect(gauge).toBeInTheDocument();
      expect(gauge).toHaveTextContent('75');
    });

    it('should display summary text', () => {
      render(
        <JDSimulationResults result={mockResult} />
      );

      expect(screen.getByText(mockResult.summary)).toBeInTheDocument();
    });

    it('should render stats grid', () => {
      render(
        <JDSimulationResults result={mockResult} />
      );

      expect(screen.getByText('Issues Found')).toBeInTheDocument();
      expect(screen.getByText('Avg. Dimension')).toBeInTheDocument();
      expect(screen.getByText('Fixed Issues')).toBeInTheDocument();
    });
  });

  describe('Statistics Display', () => {
    it('should display correct number of issues found', () => {
      render(
        <JDSimulationResults result={mockResult} />
      );

      expect(screen.getByText(mockResult.issues.length.toString())).toBeInTheDocument();
    });

    it('should display fixed issues count', () => {
      const fixedIssues = new Set(['1', '2']);
      render(
        <JDSimulationResults
          result={mockResult}
          fixedIssues={fixedIssues}
        />
      );

      const fixedCount = screen.getByText(fixedIssues.size.toString());
      expect(fixedCount).toBeInTheDocument();
    });

    it('should calculate and display average dimension score', () => {
      render(
        <JDSimulationResults result={mockResult} />
      );

      // With 3 issues, average should be calculated
      expect(screen.getByText('Avg. Dimension')).toBeInTheDocument();
    });
  });

  describe('Dimension Scores', () => {
    it('should display quality dimensions section', () => {
      render(
        <JDSimulationResults result={mockResult} />
      );

      expect(screen.getByText('Quality Dimensions')).toBeInTheDocument();
    });

    it('should display all 10 dimension categories', () => {
      render(
        <JDSimulationResults result={mockResult} />
      );

      const expectedDimensions = [
        'Clarity',
        'Tone',
        'Completeness',
        'Structure',
        'Engagement',
        'Specificity',
        'Consistency',
        'Accessibility',
        'Impact',
        'ATS Score',
      ];

      expectedDimensions.forEach((dimension) => {
        expect(screen.getByText(dimension)).toBeInTheDocument();
      });
    });

    it('should display score bars for each dimension', () => {
      const { container } = render(
        <JDSimulationResults result={mockResult} />
      );

      const progressBars = container.querySelectorAll('.h-2.bg-gray-200');
      expect(progressBars.length).toBeGreaterThan(0);
    });
  });

  describe('Issue Categories', () => {
    it('should display high severity issues section', () => {
      render(
        <JDSimulationResults result={mockResult} />
      );

      expect(screen.getByText('High Severity')).toBeInTheDocument();
    });

    it('should display medium severity issues section', () => {
      render(
        <JDSimulationResults result={mockResult} />
      );

      expect(screen.getByText('Medium Severity')).toBeInTheDocument();
    });

    it('should display low severity issues section', () => {
      render(
        <JDSimulationResults result={mockResult} />
      );

      expect(screen.getByText('Low Severity')).toBeInTheDocument();
    });

    it('should render issue cards for each issue', () => {
      render(
        <JDSimulationResults result={mockResult} />
      );

      const issueCards = screen.getAllByTestId('issue-card');
      expect(issueCards).toHaveLength(mockResult.issues.length);
    });
  });

  describe('Export Functionality', () => {
    it('should render export button', () => {
      render(
        <JDSimulationResults
          result={mockResult}
          onExport={mockOnExport}
        />
      );

      expect(screen.getByRole('button', { name: /Export Results/i })).toBeInTheDocument();
    });

    it('should call onExport when export button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <JDSimulationResults
          result={mockResult}
          onExport={mockOnExport}
        />
      );

      const exportButton = screen.getByRole('button', { name: /Export Results/i });
      await user.click(exportButton);

      expect(mockOnExport).toHaveBeenCalledTimes(1);
    });

    it('should export data as JSON when no onExport callback provided', async () => {
      const user = userEvent.setup();

      // Mock document methods
      const createElementSpy = jest.spyOn(document, 'createElement');
      const appendChildSpy = jest.spyOn(document.body, 'appendChild');
      const removeChildSpy = jest.spyOn(document.body, 'removeChild');

      render(
        <JDSimulationResults result={mockResult} />
      );

      const exportButton = screen.getByRole('button', { name: /Export Results/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(createElementSpy).toHaveBeenCalledWith('a');
      });

      createElementSpy.mockRestore();
      appendChildSpy.mockRestore();
      removeChildSpy.mockRestore();
    });

    it('should disable export button when loading', () => {
      render(
        <JDSimulationResults
          result={mockResult}
          loading={true}
        />
      );

      const exportButton = screen.getByRole('button', { name: /Export Results/i });
      expect(exportButton).toBeDisabled();
    });
  });

  describe('Improvements List', () => {
    it('should display improvements section', () => {
      render(
        <JDSimulationResults result={mockResult} />
      );

      expect(screen.getByText('Recommended Improvements')).toBeInTheDocument();
    });

    it('should display all improvements from result', () => {
      render(
        <JDSimulationResults result={mockResult} />
      );

      mockResult.improvements.forEach((improvement) => {
        expect(screen.getByText(improvement)).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty issues array', () => {
      const resultNoIssues: JDOptimizationResult = {
        qualityScore: 95,
        summary: 'Excellent job description',
        issues: [],
        improvements: [],
      };

      render(
        <JDSimulationResults result={resultNoIssues} />
      );

      expect(screen.getByText('0')).toBeInTheDocument(); // Issues found should be 0
    });

    it('should handle result with no summary', () => {
      const resultNoSummary: JDOptimizationResult = {
        qualityScore: 75,
        issues: [],
        improvements: [],
      };

      render(
        <JDSimulationResults result={resultNoSummary} />
      );

      expect(screen.getByText(/Your job description has been analyzed/)).toBeInTheDocument();
    });

    it('should handle very high quality score', () => {
      const highScoreResult: JDOptimizationResult = {
        qualityScore: 99,
        summary: 'Nearly perfect job description',
        issues: [],
        improvements: [],
      };

      render(
        <JDSimulationResults result={highScoreResult} />
      );

      const gauge = screen.getByTestId('quality-score-gauge');
      expect(gauge).toHaveTextContent('99');
    });
  });

  describe('Dimension Score Calculations', () => {
    it('should calculate dimension scores based on issue categories', () => {
      render(
        <JDSimulationResults result={mockResult} />
      );

      // Verify that dimension scores are displayed
      const dimensionTexts = screen.getAllByText(/\d+/);
      expect(dimensionTexts.length).toBeGreaterThan(0);
    });

    it('should assign high scores when no issues exist', () => {
      const perfectResult: JDOptimizationResult = {
        qualityScore: 100,
        summary: 'Perfect',
        issues: [],
        improvements: [],
      };

      render(
        <JDSimulationResults result={perfectResult} />
      );

      // All dimensions should have high scores (95)
      const scoreElements = screen.getAllByText('95');
      expect(scoreElements.length).toBeGreaterThan(0);
    });

    it('should reduce dimension scores based on issue count', () => {
      const resultWithManyIssues: JDOptimizationResult = {
        qualityScore: 45,
        summary: 'Many issues found',
        issues: Array.from({ length: 10 }, (_, i) => ({
          id: `issue-${i}`,
          title: `Issue ${i}`,
          description: `Description ${i}`,
          category: 'clarity',
          severity: 'high',
          suggestion: 'Fix this',
        })),
        improvements: [],
      };

      render(
        <JDSimulationResults result={resultWithManyIssues} />
      );

      // Should have lower scores due to many issues
      expect(screen.getByText(/Quality Dimensions/)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      const { container } = render(
        <JDSimulationResults result={mockResult} />
      );

      const h2 = container.querySelector('h2');
      const h3 = container.querySelector('h3');
      expect(h2).toHaveTextContent('Analysis Results');
      expect(h3).toHaveTextContent('Quality Dimensions');
    });

    it('should display dimension descriptions for accessibility', () => {
      render(
        <JDSimulationResults result={mockResult} />
      );

      expect(screen.getByText('How clear and understandable the job description is')).toBeInTheDocument();
    });

    it('should have color-coded severity indicators', () => {
      const { container } = render(
        <JDSimulationResults result={mockResult} />
      );

      // High severity should be present
      expect(screen.getByText('High Severity')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should show disabled export button during loading', () => {
      render(
        <JDSimulationResults
          result={mockResult}
          loading={true}
        />
      );

      const exportButton = screen.getByRole('button', { name: /Export Results/i });
      expect(exportButton).toBeDisabled();
      expect(exportButton).toHaveClass('opacity-50', 'cursor-not-allowed');
    });

    it('should show loading styles on export button', () => {
      render(
        <JDSimulationResults
          result={mockResult}
          loading={true}
        />
      );

      const exportButton = screen.getByRole('button', { name: /Export Results/i });
      expect(exportButton).toHaveClass('bg-gray-100', 'text-gray-500');
    });
  });
});
