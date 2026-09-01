import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import JDOptimizer from '@/components/JDOptimizer/JDOptimizer';

describe('JDOptimizer', () => {
  // Mock fetch
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders the initial input step', () => {
    render(<JDOptimizer />);
    expect(screen.getByText('JD Optimization Tool')).toBeInTheDocument();
    expect(
      screen.getByText('Upload or Paste Your Job Description')
    ).toBeInTheDocument();
  });

  it('displays error message when API fails', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new Error('API error: 500')
    );

    render(<JDOptimizer />);
    const textarea = screen.getByPlaceholderText('Paste your job description here...');
    const analyzeButton = screen.getByText('Analyze JD');

    await userEvent.type(textarea, 'Test job description');
    await userEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText(/Error/)).toBeInTheDocument();
      expect(screen.getByText(/API error: 500/)).toBeInTheDocument();
    });
  });

  it('shows processing state while analyzing', async () => {
    (global.fetch as jest.Mock).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                json: async () => ({
                  qualityScore: 75,
                  optimizedJD: 'Test',
                  issues: [],
                }),
              }),
            100
          )
        )
    );

    render(<JDOptimizer />);
    const textarea = screen.getByPlaceholderText('Paste your job description here...');
    const analyzeButton = screen.getByText('Analyze JD');

    await userEvent.type(textarea, 'Test job description');
    await userEvent.click(analyzeButton);

    expect(screen.getByText('Analyzing your job description...')).toBeInTheDocument();
  });

  it('displays results after successful analysis', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        qualityScore: 85,
        optimizedJD: 'Optimized job description',
        issues: [
          {
            id: '1',
            title: 'Test Issue',
            description: 'This is a test issue',
            category: 'clarity',
            severity: 'medium',
            isFixed: false,
          },
        ],
      }),
    });

    render(<JDOptimizer />);
    const textarea = screen.getByPlaceholderText('Paste your job description here...');
    const analyzeButton = screen.getByText('Analyze JD');

    await userEvent.type(textarea, 'Test job description');
    await userEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText('Quality Score')).toBeInTheDocument();
      expect(screen.getByText('Issues Found')).toBeInTheDocument();
      expect(screen.getByText('Test Issue')).toBeInTheDocument();
    });
  });

  it('handles reset button correctly', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        qualityScore: 75,
        optimizedJD: 'Optimized',
        issues: [],
      }),
    });

    render(<JDOptimizer />);
    const textarea = screen.getByPlaceholderText('Paste your job description here...');
    const analyzeButton = screen.getByText('Analyze JD');

    await userEvent.type(textarea, 'Test');
    await userEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText('Optimize Another')).toBeInTheDocument();
    });

    const resetButton = screen.getByText('Optimize Another');
    await userEvent.click(resetButton);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Paste your job description here...')).toBeInTheDocument();
    });
  });

  it('downloads optimized JD file', async () => {
    const createElementSpy = jest.spyOn(document, 'createElement');

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        qualityScore: 75,
        optimizedJD: 'Optimized text',
        issues: [],
      }),
    });

    render(<JDOptimizer />);
    const textarea = screen.getByPlaceholderText('Paste your job description here...');
    const analyzeButton = screen.getByText('Analyze JD');

    await userEvent.type(textarea, 'Test');
    await userEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText('Download')).toBeInTheDocument();
    });

    const downloadButton = screen.getByText('Download');
    await userEvent.click(downloadButton);

    expect(createElementSpy).toHaveBeenCalledWith('a');
  });

  it('toggles edit mode correctly', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        qualityScore: 75,
        optimizedJD: 'Optimized text',
        issues: [],
      }),
    });

    render(<JDOptimizer />);
    const textarea = screen.getByPlaceholderText('Paste your job description here...');
    const analyzeButton = screen.getByText('Analyze JD');

    await userEvent.type(textarea, 'Test');
    await userEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText('Edit JD')).toBeInTheDocument();
    });

    const editButton = screen.getByText('Edit JD');
    await userEvent.click(editButton);

    await waitFor(() => {
      expect(screen.getByText('Cancel Editing')).toBeInTheDocument();
    });
  });

  it('handles invalid API response', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      statusText: 'Internal Server Error',
    });

    render(<JDOptimizer />);
    const textarea = screen.getByPlaceholderText('Paste your job description here...');
    const analyzeButton = screen.getByText('Analyze JD');

    await userEvent.type(textarea, 'Test');
    await userEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText(/Error/)).toBeInTheDocument();
    });
  });
});
