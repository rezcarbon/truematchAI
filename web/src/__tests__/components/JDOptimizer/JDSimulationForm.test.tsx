import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import JDSimulationForm from './JDSimulationForm';

describe('JDSimulationForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  describe('Rendering', () => {
    it('should render form with all essential elements', () => {
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      expect(screen.getByText('Analyze Job Description')).toBeInTheDocument();
      expect(screen.getByLabelText(/Job Description/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Analyze/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Clear/i })).toBeInTheDocument();
    });

    it('should display character counter', () => {
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      expect(screen.getByText(/0 \/ 10000 characters/)).toBeInTheDocument();
    });

    it('should accept custom placeholder', () => {
      const customPlaceholder = 'Custom placeholder text';
      render(
        <JDSimulationForm
          onSubmit={mockOnSubmit}
          placeholder={customPlaceholder}
        />
      );

      const textarea = screen.getByPlaceholderText(customPlaceholder);
      expect(textarea).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('should show error when submitting empty form', async () => {
      const user = userEvent.setup();
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const submitButton = screen.getByRole('button', { name: /Analyze/i });
      await user.click(submitButton);

      expect(screen.getByText(/Job description is required/i)).toBeInTheDocument();
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should show error when text is below minimum length', async () => {
      const user = userEvent.setup();
      const minLength = 50;
      render(
        <JDSimulationForm
          onSubmit={mockOnSubmit}
          minLength={minLength}
        />
      );

      const textarea = screen.getByLabelText(/Job Description/i);
      await user.type(textarea, 'short text');

      const submitButton = screen.getByRole('button', { name: /Analyze/i });
      await user.click(submitButton);

      expect(
        screen.getByText(new RegExp(`must be at least ${minLength} characters`))
      ).toBeInTheDocument();
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should show error when text exceeds maximum length', async () => {
      const user = userEvent.setup();
      const maxLength = 100;
      const longText = 'a'.repeat(maxLength + 1);

      render(
        <JDSimulationForm
          onSubmit={mockOnSubmit}
          maxLength={maxLength}
        />
      );

      const textarea = screen.getByLabelText(/Job Description/i);
      await user.type(textarea, longText);

      const submitButton = screen.getByRole('button', { name: /Analyze/i });
      await user.click(submitButton);

      expect(
        screen.getByText(new RegExp(`cannot exceed ${maxLength} characters`))
      ).toBeInTheDocument();
    });

    it('should disable submit button when form is invalid', async () => {
      const user = userEvent.setup();
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const submitButton = screen.getByRole('button', { name: /Analyze/i });

      expect(submitButton).toBeDisabled();

      const textarea = screen.getByLabelText(/Job Description/i);
      await user.type(textarea, 'Valid job description content for testing'.repeat(2));

      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('Form Submission', () => {
    it('should call onSubmit with textarea content on valid submit', async () => {
      const user = userEvent.setup();
      const testContent = 'Valid job description content for testing'.repeat(2);

      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const textarea = screen.getByLabelText(/Job Description/i);
      await user.type(textarea, testContent);

      const submitButton = screen.getByRole('button', { name: /Analyze/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(testContent);
        expect(mockOnSubmit).toHaveBeenCalledTimes(1);
      });
    });

    it('should show success message after successful submission', async () => {
      const user = userEvent.setup();
      const testContent = 'Valid job description content for testing'.repeat(2);

      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const textarea = screen.getByLabelText(/Job Description/i);
      await user.type(textarea, testContent);

      const submitButton = screen.getByRole('button', { name: /Analyze/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/Job description submitted successfully/i)
        ).toBeInTheDocument();
      });
    });

    it('should clear textarea after successful submission', async () => {
      const user = userEvent.setup();
      const testContent = 'Valid job description content for testing'.repeat(2);

      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const textarea = screen.getByLabelText(/Job Description/i) as HTMLTextAreaElement;
      await user.type(textarea, testContent);

      const submitButton = screen.getByRole('button', { name: /Analyze/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(textarea.value).toBe('');
      });
    });

    it('should show error message if submission fails', async () => {
      const user = userEvent.setup();
      const errorMessage = 'Network error occurred';
      mockOnSubmit.mockRejectedValueOnce(new Error(errorMessage));

      const testContent = 'Valid job description content for testing'.repeat(2);
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const textarea = screen.getByLabelText(/Job Description/i);
      await user.type(textarea, testContent);

      const submitButton = screen.getByRole('button', { name: /Analyze/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });

    it('should disable submit button while loading', async () => {
      const user = userEvent.setup();
      render(<JDSimulationForm onSubmit={mockOnSubmit} loading={true} />);

      const submitButton = screen.getByRole('button', { name: /Analyzing/i });

      expect(submitButton).toBeDisabled();
    });

    it('should show loading state in submit button', () => {
      render(<JDSimulationForm onSubmit={mockOnSubmit} loading={true} />);

      expect(screen.getByText(/Analyzing/i)).toBeInTheDocument();
    });
  });

  describe('Clear Button', () => {
    it('should clear textarea when clear button is clicked', async () => {
      const user = userEvent.setup();
      const testContent = 'Valid job description content for testing'.repeat(2);

      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const textarea = screen.getByLabelText(/Job Description/i) as HTMLTextAreaElement;
      await user.type(textarea, testContent);

      expect(textarea.value).toBe(testContent);

      const clearButton = screen.getByRole('button', { name: /Clear/i });
      await user.click(clearButton);

      expect(textarea.value).toBe('');
    });

    it('should disable clear button when textarea is empty', () => {
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const clearButton = screen.getByRole('button', { name: /Clear/i });

      expect(clearButton).toBeDisabled();
    });

    it('should clear error messages when clear button is clicked', async () => {
      const user = userEvent.setup();
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const submitButton = screen.getByRole('button', { name: /Analyze/i });
      await user.click(submitButton);

      expect(screen.getByText(/Job description is required/i)).toBeInTheDocument();

      const clearButton = screen.getByRole('button', { name: /Clear/i });
      await user.click(clearButton);

      expect(screen.queryByText(/Job description is required/i)).not.toBeInTheDocument();
    });
  });

  describe('Character Counter', () => {
    it('should update character count as user types', async () => {
      const user = userEvent.setup();
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const textarea = screen.getByLabelText(/Job Description/i);

      expect(screen.getByText(/0 \/ 10000 characters/)).toBeInTheDocument();

      await user.type(textarea, 'Test');

      expect(screen.getByText(/4 \/ 10000 characters/)).toBeInTheDocument();
    });

    it('should show progress bar', async () => {
      const user = userEvent.setup();
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '0');

      const textarea = screen.getByLabelText(/Job Description/i);
      await user.type(textarea, 'x'.repeat(1000));

      expect(progressBar).toHaveAttribute('aria-valuenow', '1000');
    });

    it('should show warning when approaching max length', async () => {
      const user = userEvent.setup();
      const maxLength = 100;
      render(
        <JDSimulationForm
          onSubmit={mockOnSubmit}
          maxLength={maxLength}
        />
      );

      const textarea = screen.getByLabelText(/Job Description/i);
      await user.type(textarea, 'x'.repeat(95));

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar.parentElement).toHaveClass('mt-2');
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels and descriptions', () => {
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const textarea = screen.getByLabelText(/Job Description/i);
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveAttribute('aria-invalid', 'false');
    });

    it('should link error message to textarea with aria-describedby', async () => {
      const user = userEvent.setup();
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const submitButton = screen.getByRole('button', { name: /Analyze/i });
      await user.click(submitButton);

      const textarea = screen.getByLabelText(/Job Description/i);
      expect(textarea).toHaveAttribute('aria-invalid', 'true');
      expect(textarea).toHaveAttribute('aria-describedby', 'jd-error');
    });

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const textarea = screen.getByLabelText(/Job Description/i);
      textarea.focus();
      expect(textarea).toHaveFocus();

      await user.type(textarea, 'Valid job description content for testing'.repeat(2));

      const submitButton = screen.getByRole('button', { name: /Analyze/i });
      await user.keyboard('{Tab}');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalled();
      });
    });
  });
});
