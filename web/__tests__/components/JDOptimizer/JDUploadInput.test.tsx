import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import JDUploadInput from '@/components/JDOptimizer/JDUploadInput';

describe('JDUploadInput', () => {
  it('renders input form', () => {
    render(<JDUploadInput onSubmit={() => {}} />);
    expect(
      screen.getByPlaceholderText('Paste your job description here...')
    ).toBeInTheDocument();
    expect(screen.getByText('Analyze JD')).toBeInTheDocument();
  });

  it('handles text input changes', async () => {
    render(<JDUploadInput onSubmit={() => {}} />);
    const textarea = screen.getByPlaceholderText(
      'Paste your job description here...'
    );

    await userEvent.type(textarea, 'Test job description');
    expect((textarea as HTMLTextAreaElement).value).toBe('Test job description');
  });

  it('disables submit button when textarea is empty', () => {
    render(<JDUploadInput onSubmit={() => {}} />);
    const analyzeButton = screen.getByText('Analyze JD');
    expect(analyzeButton).toBeDisabled();
  });

  it('enables submit button when textarea has content', async () => {
    render(<JDUploadInput onSubmit={() => {}} />);
    const textarea = screen.getByPlaceholderText(
      'Paste your job description here...'
    );
    const analyzeButton = screen.getByText('Analyze JD');

    await userEvent.type(textarea, 'Test');
    expect(analyzeButton).not.toBeDisabled();
  });

  it('calls onSubmit with textarea content', async () => {
    const mockSubmit = jest.fn();
    render(<JDUploadInput onSubmit={mockSubmit} />);
    const textarea = screen.getByPlaceholderText(
      'Paste your job description here...'
    );
    const analyzeButton = screen.getByText('Analyze JD');

    await userEvent.type(textarea, 'Test content');
    await userEvent.click(analyzeButton);

    expect(mockSubmit).toHaveBeenCalledWith('Test content');
  });

  it('clears textarea when clear button is clicked', async () => {
    render(<JDUploadInput onSubmit={() => {}} />);
    const textarea = screen.getByPlaceholderText(
      'Paste your job description here...'
    );
    const clearButton = screen.getByText('Clear');

    await userEvent.type(textarea, 'Test content');
    expect((textarea as HTMLTextAreaElement).value).toBe('Test content');

    await userEvent.click(clearButton);
    expect((textarea as HTMLTextAreaElement).value).toBe('');
  });

  it('shows loading state when loading prop is true', () => {
    render(<JDUploadInput onSubmit={() => {}} loading={true} />);
    expect(screen.getByText('Analyzing...')).toBeInTheDocument();
    expect(screen.getByText('Analyze JD')).toBeDisabled();
  });

  it('displays character count', async () => {
    render(<JDUploadInput onSubmit={() => {}} />);
    const textarea = screen.getByPlaceholderText(
      'Paste your job description here...'
    );

    await userEvent.type(textarea, 'Test');
    expect(screen.getByText('4 characters')).toBeInTheDocument();
  });

  it('alerts user when trying to submit empty description', async () => {
    const alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => {});
    render(<JDUploadInput onSubmit={() => {}} />);
    const analyzeButton = screen.getByText('Analyze JD');

    // Try clicking analyze with empty textarea
    const textarea = screen.getByPlaceholderText(
      'Paste your job description here...'
    );
    await userEvent.type(textarea, '   '); // Only whitespace
    await userEvent.click(analyzeButton);

    expect(alertSpy).toHaveBeenCalledWith(
      'Please enter or upload a job description'
    );

    alertSpy.mockRestore();
  });

  it('handles file input change', async () => {
    const mockSubmit = jest.fn();
    const { container } = render(<JDUploadInput onSubmit={mockSubmit} />);
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;

    const file = new File(['Test file content'], 'test.txt', {
      type: 'text/plain',
    });

    const mockFileReader = {
      readAsText: jest.fn(),
      onload: null as any,
      result: 'Test file content',
    };

    global.FileReader = jest.fn(() => mockFileReader) as any;

    fireEvent.change(fileInput, { target: { files: [file] } });

    // Simulate file read completion
    mockFileReader.onload({ target: { result: 'Test file content' } } as any);

    await waitFor(() => {
      const textarea = screen.getByPlaceholderText(
        'Paste your job description here...'
      );
      expect((textarea as HTMLTextAreaElement).value).toBe('Test file content');
    });
  });

  it('shows drag active state on drag enter', () => {
    const { container } = render(<JDUploadInput onSubmit={() => {}} />);
    const dropZone = container.querySelector('[role="presentation"]') || container.firstChild;

    fireEvent.dragEnter(dropZone as Element);
    expect(container.querySelector('.border-blue-500')).toBeInTheDocument();
  });

  it('handles drop event with file', async () => {
    const mockSubmit = jest.fn();
    const { container } = render(<JDUploadInput onSubmit={mockSubmit} />);
    const dropZone = container.firstChild as Element;

    const file = new File(['Test drop content'], 'test.txt', {
      type: 'text/plain',
    });

    const mockFileReader = {
      readAsText: jest.fn(),
      onload: null as any,
      result: 'Test drop content',
    };

    global.FileReader = jest.fn(() => mockFileReader) as any;

    const dropEvent = new DragEvent('drop', {
      dataTransfer: new DataTransfer(),
    } as any);
    (dropEvent as any).dataTransfer.items.add(file);
    (dropEvent as any).dataTransfer.files = [file];

    fireEvent.drop(dropZone, dropEvent);

    // Simulate file read completion
    mockFileReader.onload({ target: { result: 'Test drop content' } } as any);

    await waitFor(() => {
      const textarea = screen.getByPlaceholderText(
        'Paste your job description here...'
      );
      expect((textarea as HTMLTextAreaElement).value).toBe('Test drop content');
    });
  });
});
