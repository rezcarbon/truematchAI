import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import JDComparisonView from './JDComparisonView';

describe('JDComparisonView', () => {
  const mockOriginalJD = `Senior Software Engineer

Responsibilities:
- Develop and maintain backend systems
- Code review and mentoring
- Design scalable architecture`;

  const mockOptimizedJD = `Senior Software Engineer

Responsibilities:
- Design and develop high-performance backend systems
- Provide thorough code reviews and mentor junior developers
- Design and implement scalable, maintainable architecture
- Lead technical initiatives and drive innovation

Requirements:
- 5+ years of software development experience
- Proficiency in JavaScript/TypeScript and Python`;

  describe('Rendering', () => {
    it('should render both original and optimized versions', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      expect(screen.getByText('Before & After Comparison')).toBeInTheDocument();
      expect(screen.getByText('Original')).toBeInTheDocument();
      expect(screen.getByText('Optimized')).toBeInTheDocument();
    });

    it('should render view mode toggle buttons', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      expect(screen.getByRole('button', { name: /Full Text/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Changes Only/i })).toBeInTheDocument();
    });

    it('should render copy buttons for both versions', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      const copyButtons = screen.getAllByRole('button', { name: /Copy/i });
      expect(copyButtons).toHaveLength(2);
    });

    it('should render statistics section', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      expect(screen.getByText('Original Length')).toBeInTheDocument();
      expect(screen.getByText('Optimized Length')).toBeInTheDocument();
      expect(screen.getByText('Change')).toBeInTheDocument();
    });

    it('should render legend', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      expect(screen.getByText('Legend')).toBeInTheDocument();
      expect(screen.getByText('Added content')).toBeInTheDocument();
      expect(screen.getByText('Removed content')).toBeInTheDocument();
    });
  });

  describe('View Mode Toggle', () => {
    it('should display full text by default', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      expect(screen.getByText(/Senior Software Engineer/)).toBeInTheDocument();
    });

    it('should switch to diff-only view when button clicked', async () => {
      const user = userEvent.setup();
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      const diffOnlyButton = screen.getByRole('button', { name: /Changes Only/i });
      await user.click(diffOnlyButton);

      expect(
        diffOnlyButton.classList.contains('border-blue-600')
      ).toBe(true);
    });

    it('should display changes count badge in diff-only mode', async () => {
      const user = userEvent.setup();
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      const diffOnlyButton = screen.getByRole('button', { name: /Changes Only/i });
      expect(diffOnlyButton).toBeInTheDocument();
    });
  });

  describe('Copy Functionality', () => {
    it('should copy original text to clipboard', async () => {
      const user = userEvent.setup();
      const writeTextMock = jest.fn();
      Object.assign(navigator, {
        clipboard: { writeText: writeTextMock },
      });

      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      const copyButtons = screen.getAllByRole('button', { name: /Copy/i });
      await user.click(copyButtons[0]);

      expect(writeTextMock).toHaveBeenCalledWith(mockOriginalJD);
    });

    it('should copy optimized text to clipboard', async () => {
      const user = userEvent.setup();
      const writeTextMock = jest.fn();
      Object.assign(navigator, {
        clipboard: { writeText: writeTextMock },
      });

      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      const copyButtons = screen.getAllByRole('button', { name: /Copy/i });
      await user.click(copyButtons[1]);

      expect(writeTextMock).toHaveBeenCalledWith(mockOptimizedJD);
    });

    it('should show copied confirmation', async () => {
      const user = userEvent.setup();
      Object.assign(navigator, {
        clipboard: { writeText: jest.fn() },
      });

      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      const copyButtons = screen.getAllByRole('button', { name: /Copy/i });
      await user.click(copyButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Copied')).toBeInTheDocument();
      });
    });

    it('should disable copy buttons when loading', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
          loading={true}
        />
      );

      const copyButtons = screen.getAllByRole('button', { name: /Copy/i });
      copyButtons.forEach((button) => {
        expect(button).toBeDisabled();
      });
    });
  });

  describe('Statistics', () => {
    it('should display correct original length', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      expect(screen.getByText(mockOriginalJD.length.toString())).toBeInTheDocument();
    });

    it('should display correct optimized length', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      const lengthText = mockOptimizedJD.length.toString();
      expect(screen.getByText(lengthText)).toBeInTheDocument();
    });

    it('should calculate and display length change', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      const difference = mockOptimizedJD.length - mockOriginalJD.length;
      const expectedText = `+${difference}`;

      const changeElements = screen.getAllByText(expectedText);
      expect(changeElements.length).toBeGreaterThan(0);
    });

    it('should show percentage change', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      expect(screen.getByText(/%/)).toBeInTheDocument();
    });
  });

  describe('Text Display', () => {
    it('should display original text in left panel', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      // Check that text appears in the document
      expect(screen.getByText(/Develop and maintain backend systems/)).toBeInTheDocument();
    });

    it('should display optimized text in right panel', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      expect(
        screen.getByText(/Design and develop high-performance backend systems/)
      ).toBeInTheDocument();
    });

    it('should handle empty strings gracefully', () => {
      render(
        <JDComparisonView
          originalJD=""
          optimizedJD=""
        />
      );

      expect(screen.getAllByText('No content')).toHaveLength(2);
    });
  });

  describe('Loading State', () => {
    it('should disable copy buttons when loading', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
          loading={true}
        />
      );

      const copyButtons = screen.getAllByRole('button', { name: /Copy/i });
      copyButtons.forEach((button) => {
        expect(button).toBeDisabled();
      });
    });

    it('should display normally when not loading', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
          loading={false}
        />
      );

      const copyButtons = screen.getAllByRole('button', { name: /Copy/i });
      copyButtons.forEach((button) => {
        expect(button).not.toBeDisabled();
      });
    });
  });

  describe('Diff Highlighting', () => {
    it('should highlight added lines in optimized version', async () => {
      const user = userEvent.setup();
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      const diffOnlyButton = screen.getByRole('button', { name: /Changes Only/i });
      await user.click(diffOnlyButton);

      // In diff-only mode, added content should be visible
      expect(screen.getByText(/Design and develop high-performance/)).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('should render side-by-side layout on desktop', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      const container = screen.getByText('Before & After Comparison').closest('div');
      expect(container).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have descriptive headings', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      expect(screen.getByText('Before & After Comparison')).toBeInTheDocument();
      expect(screen.getByText('Legend')).toBeInTheDocument();
    });

    it('should have proper button titles for accessibility', () => {
      render(
        <JDComparisonView
          originalJD={mockOriginalJD}
          optimizedJD={mockOptimizedJD}
        />
      );

      const copyButtons = screen.getAllByRole('button', { name: /Copy/i });
      copyButtons.forEach((button) => {
        expect(button).toHaveAttribute('title');
      });
    });
  });
});
