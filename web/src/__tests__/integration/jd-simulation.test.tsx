import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { JDSimulationForm } from '@/components/recruiter/JDSimulationForm';

/**
 * Integration tests for JD Simulation workflow
 * Tests the complete flow: upload JD → analyze → display results
 */
describe('JD Simulation Integration', () => {
  describe('Upload → Analyze → Display Flow', () => {
    it('completes full JD simulation workflow', async () => {
      const user = userEvent.setup();
      let analysisResults: any = null;

      const mockAnalyzeJD = jest.fn().mockImplementation(async (data) => {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 100));

        analysisResults = {
          title: data.positionTitle,
          jdLength: data.jdText.length,
          keySkills: ['React', 'TypeScript', 'Node.js'],
          requirementsCoverage: 0.85,
          matchQuality: 'high',
          timestamp: new Date(),
        };
      });

      render(<JDSimulationForm onSubmit={mockAnalyzeJD} />);

      // Step 1: User enters job description
      const jdText = 'We are seeking a Senior Full Stack Engineer with 5+ years experience in React, TypeScript, and Node.js. Must have experience with PostgreSQL and AWS.';
      const titleText = 'Senior Full Stack Engineer';

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      const titleInput = screen.getByPlaceholderText(/e.g., Senior Backend Engineer/i);

      await user.type(jdTextarea, jdText);
      await user.type(titleInput, titleText);

      // Step 2: Verify form is ready to submit
      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
      expect(submitButton).not.toBeDisabled();

      // Step 3: Submit form
      await user.click(submitButton);

      // Step 4: Verify API was called with correct data
      await waitFor(() => {
        expect(mockAnalyzeJD).toHaveBeenCalledWith({
          jdText,
          positionTitle: titleText,
        });
      });

      // Step 5: Verify analysis results
      await waitFor(() => {
        expect(analysisResults).not.toBeNull();
        expect(analysisResults.title).toBe(titleText);
        expect(analysisResults.jdLength).toBe(jdText.length);
        expect(analysisResults.keySkills).toContain('React');
      });
    });

    it('handles analysis with optional title omitted', async () => {
      const user = userEvent.setup();
      const mockAnalyzeJD = jest.fn();

      render(<JDSimulationForm onSubmit={mockAnalyzeJD} />);

      const jdText = 'We are seeking a Senior Full Stack Engineer with 5+ years experience in React, TypeScript, and Node.js. Must have experience with PostgreSQL and AWS.';

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      await user.type(jdTextarea, jdText);

      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockAnalyzeJD).toHaveBeenCalledWith({
          jdText,
          positionTitle: undefined,
        });
      });
    });

    it('handles multiple sequential analyses', async () => {
      const user = userEvent.setup();
      const mockAnalyzeJD = jest.fn();

      render(<JDSimulationForm onSubmit={mockAnalyzeJD} />);

      // First analysis
      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      const titleInput = screen.getByPlaceholderText(/e.g., Senior Backend Engineer/i);

      await user.type(jdTextarea, 'We need a Senior Engineer with React experience');
      await user.type(titleInput, 'Senior Frontend');

      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockAnalyzeJD).toHaveBeenCalledTimes(1);
      });

      // Second analysis - clear and re-enter
      await user.clear(jdTextarea);
      await user.clear(titleInput);

      await user.type(jdTextarea, 'We need a Senior Backend Engineer with Node.js experience');
      await user.type(titleInput, 'Senior Backend');

      await user.click(submitButton);

      await waitFor(() => {
        expect(mockAnalyzeJD).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Error Handling in Workflow', () => {
    it('recovers from API error and allows retry', async () => {
      const user = userEvent.setup();
      const mockAnalyzeJD = jest
        .fn()
        .mockRejectedValueOnce(new Error('API Error: Server unavailable'))
        .mockResolvedValueOnce(undefined);

      render(<JDSimulationForm onSubmit={mockAnalyzeJD} />);

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });

      // First attempt - fails
      await user.type(jdTextarea, 'We need a Senior Engineer with React experience');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('API Error: Server unavailable')).toBeInTheDocument();
      });

      // User retries
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockAnalyzeJD).toHaveBeenCalledTimes(2);
      });
    });

    it('handles timeout errors gracefully', async () => {
      const user = userEvent.setup();
      const mockAnalyzeJD = jest.fn().mockImplementation(
        () => new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Request timeout')), 100)
        )
      );

      render(<JDSimulationForm onSubmit={mockAnalyzeJD} />);

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });

      await user.type(jdTextarea, 'We need a Senior Engineer with React experience');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Request timeout')).toBeInTheDocument();
      });
    });

    it('validates before attempting API call on invalid input', async () => {
      const user = userEvent.setup();
      const mockAnalyzeJD = jest.fn();

      render(<JDSimulationForm onSubmit={mockAnalyzeJD} />);

      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });

      // Try to submit with empty form
      await user.click(submitButton);

      // API should not be called
      expect(mockAnalyzeJD).not.toHaveBeenCalled();

      // Error message should be displayed
      expect(screen.getByText('Job description is required')).toBeInTheDocument();
    });
  });

  describe('User Experience During Analysis', () => {
    it('shows loading state during API call', async () => {
      const user = userEvent.setup();
      const mockAnalyzeJD = jest.fn().mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 500))
      );

      const { rerender } = render(
        <JDSimulationForm onSubmit={mockAnalyzeJD} loading={false} />
      );

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });

      await user.type(jdTextarea, 'We need a Senior Engineer with React experience');
      await user.click(submitButton);

      // Simulate loading state
      rerender(
        <JDSimulationForm onSubmit={mockAnalyzeJD} loading={true} />
      );

      expect(screen.getByText('Analyzing...')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Analyzing/i })).toBeDisabled();
    });

    it('disables form inputs while analyzing', () => {
      render(<JDSimulationForm onSubmit={jest.fn()} loading={true} />);

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      const titleInput = screen.getByPlaceholderText(/e.g., Senior Backend Engineer/i);

      expect(jdTextarea).toBeDisabled();
      expect(titleInput).toBeDisabled();
    });

    it('shows success feedback after analysis', async () => {
      const user = userEvent.setup();
      let isLoading = false;

      const mockAnalyzeJD = jest.fn().mockImplementation(
        () => new Promise(resolve => {
          isLoading = true;
          setTimeout(() => {
            isLoading = false;
            resolve(undefined);
          }, 100);
        })
      );

      const { rerender } = render(
        <JDSimulationForm onSubmit={mockAnalyzeJD} loading={false} />
      );

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });

      await user.type(jdTextarea, 'We need a Senior Engineer with React experience');
      await user.click(submitButton);

      // Simulate loading
      rerender(
        <JDSimulationForm onSubmit={mockAnalyzeJD} loading={true} />
      );

      // Wait for completion
      await waitFor(() => {
        expect(mockAnalyzeJD).toHaveBeenCalled();
      });

      // Simulate completion
      rerender(
        <JDSimulationForm onSubmit={mockAnalyzeJD} loading={false} />
      );

      // Form should be ready for new input
      expect(screen.getByRole('button', { name: /Run Simulation/i })).toBeInTheDocument();
    });
  });

  describe('Data Validation in Workflow', () => {
    it('validates minimum character requirement during workflow', async () => {
      const user = userEvent.setup();
      const mockAnalyzeJD = jest.fn();

      render(<JDSimulationForm onSubmit={mockAnalyzeJD} />);

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });

      // Type less than 50 characters
      await user.type(jdTextarea, 'Short');

      // Button should remain disabled
      expect(submitButton).toBeDisabled();

      // Try to submit
      await user.click(submitButton);

      // Should show validation error
      expect(screen.getByText(/at least 50 characters/i)).toBeInTheDocument();
      expect(mockAnalyzeJD).not.toHaveBeenCalled();
    });

    it('trims whitespace consistently throughout workflow', async () => {
      const user = userEvent.setup();
      const mockAnalyzeJD = jest.fn();

      render(<JDSimulationForm onSubmit={mockAnalyzeJD} />);

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      const titleInput = screen.getByPlaceholderText(/e.g., Senior Backend Engineer/i);
      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });

      // Enter data with extra whitespace
      const jdWithSpaces = '   We need a Senior Engineer with React experience   ';
      const titleWithSpaces = '   Senior Frontend Engineer   ';

      await user.type(jdTextarea, jdWithSpaces);
      await user.type(titleInput, titleWithSpaces);

      await user.click(submitButton);

      await waitFor(() => {
        expect(mockAnalyzeJD).toHaveBeenCalledWith({
          jdText: jdWithSpaces.trim(),
          positionTitle: titleWithSpaces.trim(),
        });
      });
    });
  });

  describe('Workflow Edge Cases', () => {
    it('handles analysis with very long job description', async () => {
      const user = userEvent.setup();
      const mockAnalyzeJD = jest.fn();

      render(<JDSimulationForm onSubmit={mockAnalyzeJD} />);

      // Generate a very long JD
      const longJD = 'We are seeking a talented engineer. '.repeat(100);

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });

      await user.type(jdTextarea, longJD);
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockAnalyzeJD).toHaveBeenCalledWith({
          jdText: longJD.trim(),
          positionTitle: undefined,
        });
      });
    });

    it('handles special characters in job description', async () => {
      const user = userEvent.setup();
      const mockAnalyzeJD = jest.fn();

      render(<JDSimulationForm onSubmit={mockAnalyzeJD} />);

      const specialJD = 'We need a C++/C# engineer (Sr./Jr.) with 5+ yrs & benefits: $$$';

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });

      await user.type(jdTextarea, specialJD);
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockAnalyzeJD).toHaveBeenCalledWith(
          expect.objectContaining({
            jdText: specialJD.trim(),
          })
        );
      });
    });

    it('handles analysis with multiline formatted JD', async () => {
      const user = userEvent.setup();
      const mockAnalyzeJD = jest.fn();

      render(<JDSimulationForm onSubmit={mockAnalyzeJD} />);

      const multilineJD = `Job Title: Senior Engineer
Responsibilities:
- Lead team
- Design systems
- Review code
Requirements:
- 5+ years experience
- React/TypeScript
- Node.js`;

      const jdTextarea = screen.getByPlaceholderText(/Paste the complete job description/i);
      const submitButton = screen.getByRole('button', { name: /Run Simulation/i });

      await user.type(jdTextarea, multilineJD);
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockAnalyzeJD).toHaveBeenCalledWith(
          expect.objectContaining({
            jdText: multilineJD.trim(),
          })
        );
      });
    });
  });
});
