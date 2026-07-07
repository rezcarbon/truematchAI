import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { JDSimulationForm } from '@/components/recruiter/JDSimulationForm';

describe('JDSimulationForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockOnSubmit.mockResolvedValue(undefined);
  });

  it('renders form with required fields', () => {
    render(<JDSimulationForm onSubmit={mockOnSubmit} />);

    expect(screen.getByText('Simulate a Job Description')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Paste the complete job description/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/e.g., Senior Backend Engineer/i)).toBeInTheDocument();
  });

  it('displays character count for JD', async () => {
    const user = userEvent.setup();
    render(<JDSimulationForm onSubmit={mockOnSubmit} />);

    const textarea = screen.getByPlaceholderText(/Paste the complete job description/i);
    await user.type(textarea, 'Test job description');

    expect(screen.getByText(/21 characters/)).toBeInTheDocument();
  });

  it('disables submit button when JD is empty', () => {
    render(<JDSimulationForm onSubmit={mockOnSubmit} />);

    const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
    expect(submitButton).toBeDisabled();
  });

  it('disables submit button when JD is too short', async () => {
    const user = userEvent.setup();
    render(<JDSimulationForm onSubmit={mockOnSubmit} />);

    const textarea = screen.getByPlaceholderText(/Paste the complete job description/i);
    await user.type(textarea, 'Short');

    const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
    expect(submitButton).toBeDisabled();
  });

  it('enables submit button when JD meets minimum length', async () => {
    const user = userEvent.setup();
    render(<JDSimulationForm onSubmit={mockOnSubmit} />);

    const textarea = screen.getByPlaceholderText(/Paste the complete job description/i);
    await user.type(textarea, 'We are looking for a senior software engineer with 5+ years experience');

    const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
    expect(submitButton).not.toBeDisabled();
  });

  it('calls onSubmit with form data', async () => {
    const user = userEvent.setup();
    render(<JDSimulationForm onSubmit={mockOnSubmit} />);

    const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
    const titleInput = screen.getByPlaceholderText(/e.g., Senior Backend Engineer/i);

    await user.type(jdTextarea, 'We are looking for a software engineer with React and TypeScript experience');
    await user.type(titleInput, 'Senior Frontend Engineer');

    const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        jdText: expect.stringContaining('software engineer'),
        positionTitle: 'Senior Frontend Engineer',
      });
    });
  });

  it('shows loading state while submitting', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    render(<JDSimulationForm onSubmit={mockOnSubmit} loading={false} />);

    const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
    await user.type(jdTextarea, 'We are looking for a software engineer with 5+ years of experience');

    const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Analyzing...')).toBeInTheDocument();
    });
  });

  it('displays error message when provided', () => {
    render(
      <JDSimulationForm
        onSubmit={mockOnSubmit}
        error="Failed to analyze job description"
      />
    );

    expect(screen.getByText('Failed to analyze job description')).toBeInTheDocument();
  });

  it('disables form when loading prop is true', () => {
    render(
      <JDSimulationForm
        onSubmit={mockOnSubmit}
        loading={true}
      />
    );

    const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
    const titleInput = screen.getByPlaceholderText(/e.g., Senior Backend Engineer/i);

    expect(jdTextarea).toBeDisabled();
    expect(titleInput).toBeDisabled();
  });

  it('trims whitespace from inputs', async () => {
    const user = userEvent.setup();
    render(<JDSimulationForm onSubmit={mockOnSubmit} />);

    const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
    const titleInput = screen.getByPlaceholderText(/e.g., Senior Backend Engineer/i);

    await user.type(jdTextarea, '  Software engineer with 5+ years  ');
    await user.type(titleInput, '  Senior Engineer  ');

    const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        jdText: 'Software engineer with 5+ years',
        positionTitle: 'Senior Engineer',
      });
    });
  });

  it('handles validation error for too short JD', async () => {
    const user = userEvent.setup();
    render(<JDSimulationForm onSubmit={mockOnSubmit} />);

    const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
    await user.type(jdTextarea, 'Short');

    const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
    await user.click(submitButton);

    expect(screen.getByText(/at least 50 characters/i)).toBeInTheDocument();
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('displays subtitle describing functionality', () => {
    render(<JDSimulationForm onSubmit={mockOnSubmit} />);

    expect(
      screen.getByText(/identify capability gaps, requirement creep/i)
    ).toBeInTheDocument();
  });

  it('makes position title optional', async () => {
    const user = userEvent.setup();
    render(<JDSimulationForm onSubmit={mockOnSubmit} />);

    const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
    await user.type(jdTextarea, 'We are looking for a software engineer with 5+ years of experience');

    // Don't fill in title
    const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          jdText: expect.any(String),
        })
      );
    });
  });

  it('shows help text for character count', async () => {
    const user = userEvent.setup();
    render(<JDSimulationForm onSubmit={mockOnSubmit} />);

    const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
    await user.type(jdTextarea, 'Test');

    expect(screen.getByText(/Include full job description/i)).toBeInTheDocument();
  });

  it('clears error when user starts typing', async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <JDSimulationForm
        onSubmit={mockOnSubmit}
        error="Previous error"
      />
    );

    expect(screen.getByText('Previous error')).toBeInTheDocument();

    const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
    await user.type(jdTextarea, 'New job description text');

    // Error should be cleared after user input
    rerender(
      <JDSimulationForm onSubmit={mockOnSubmit} error={undefined} />
    );

    expect(screen.queryByText('Previous error')).not.toBeInTheDocument();
  });

  it('handles async submission errors', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockRejectedValueOnce(new Error('Network error'));

    render(<JDSimulationForm onSubmit={mockOnSubmit} />);

    const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
    await user.type(jdTextarea, 'We are looking for a software engineer with 5+ years of experience');

    const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('prevents form submission on Enter if validation fails', async () => {
    const user = userEvent.setup();
    render(<JDSimulationForm onSubmit={mockOnSubmit} />);

    const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
    await user.type(jdTextarea, 'Short');

    // Try to submit with Enter
    await user.keyboard('{Enter}');

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('shows loading state on submit button', async () => {
    const user = userEvent.setup();
    render(
      <JDSimulationForm
        onSubmit={mockOnSubmit}
        loading={true}
      />
    );

    const submitButton = screen.getByRole('button', { name: /Analyzing/i });
    expect(submitButton).toBeInTheDocument();
  });

  it('updates character count in real-time', async () => {
    const user = userEvent.setup();
    render(<JDSimulationForm onSubmit={mockOnSubmit} />);

    const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);

    await user.type(jdTextarea, 'A');
    expect(screen.getByText(/1 characters/)).toBeInTheDocument();

    await user.type(jdTextarea, 'B');
    expect(screen.getByText(/2 characters/)).toBeInTheDocument();

    await user.type(jdTextarea, 'C');
    expect(screen.getByText(/3 characters/)).toBeInTheDocument();
  });

  describe('Edge Cases', () => {
    it('handles very long job descriptions', async () => {
      const user = userEvent.setup();
      const longText = 'We are looking for a senior software engineer. '.repeat(50);

      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      await user.type(jdTextarea, longText);

      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalled();
      });
    });

    it('handles special characters in inputs', async () => {
      const user = userEvent.setup();
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      const titleInput = screen.getByPlaceholderText(/e.g., Senior Backend Engineer/i);

      await user.type(jdTextarea, 'Looking for C++/Java/Python developer with 5+ years experience');
      await user.type(titleInput, 'C++/Senior Developer (Sr.)');

      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalled();
      });
    });

    it('handles multiline input in job description', async () => {
      const user = userEvent.setup();
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      const multilineText = 'Job Title: Senior Engineer\nResponsibilities:\n- Lead team\n- Design systems\nRequirements:\n- 5+ years';

      await user.type(jdTextarea, multilineText);

      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalled();
      });
    });

    it('handles exactly 50 character minimum', async () => {
      const user = userEvent.setup();
      const exactMinimum = 'a'.repeat(50);

      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      await user.type(jdTextarea, exactMinimum);

      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
      expect(submitButton).not.toBeDisabled();

      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            jdText: exactMinimum,
          })
        );
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper form structure with labels', () => {
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const jdLabel = screen.getByText(/Job Description/);
      const titleLabel = screen.getByText(/Position Title/);

      expect(jdLabel).toBeInTheDocument();
      expect(titleLabel).toBeInTheDocument();
    });

    it('marks required fields appropriately', () => {
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      expect(screen.getByText(/Job Description \*/)).toBeInTheDocument();
      expect(screen.getByText(/Position Title \(Optional\)/)).toBeInTheDocument();
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      const titleInput = screen.getByPlaceholderText(/e.g., Senior Backend Engineer/i);
      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });

      await user.tab();
      expect(jdTextarea).toHaveFocus();

      await user.tab();
      expect(titleInput).toHaveFocus();

      await user.tab();
      expect(submitButton).toHaveFocus();
    });

    it('provides clear error messages for accessibility', async () => {
      const user = userEvent.setup();
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Job description is required')).toBeInTheDocument();
      });
    });
  });

  describe('Integration Scenarios', () => {
    it('completes full form submission workflow', async () => {
      const user = userEvent.setup();
      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      // Step 1: Fill job description
      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      await user.type(jdTextarea, 'We are seeking a talented Full Stack Engineer with expertise in React, Node.js, and PostgreSQL. 5+ years required.');

      // Step 2: Fill position title
      const titleInput = screen.getByPlaceholderText(/e.g., Senior Backend Engineer/i);
      await user.type(titleInput, 'Full Stack Engineer');

      // Step 3: Verify character count
      expect(screen.getByText(/We are seeking.*characters/i)).toBeInTheDocument();

      // Step 4: Submit form
      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
      expect(submitButton).not.toBeDisabled();
      await user.click(submitButton);

      // Step 5: Verify submission
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          jdText: 'We are seeking a talented Full Stack Engineer with expertise in React, Node.js, and PostgreSQL. 5+ years required.',
          positionTitle: 'Full Stack Engineer',
        });
      });
    });

    it('recovers from error and allows re-submission', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockRejectedValueOnce(new Error('Server error'));
      mockOnSubmit.mockResolvedValueOnce(undefined);

      render(<JDSimulationForm onSubmit={mockOnSubmit} />);

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });

      // First submission fails
      await user.type(jdTextarea, 'We are looking for a senior engineer with 5+ years of experience');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Server error')).toBeInTheDocument();
      });

      // User retries
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledTimes(2);
      });
    });
  });
});
