import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { JDComparisonView } from '@/components/recruiter/JDComparisonView';

describe('JDComparisonView', () => {
  const mockOriginalJD = `
    We are looking for a Senior Software Engineer.
    Requirements: 5+ years experience, React, TypeScript, Node.js.
    Responsibilities: Build scalable applications, mentor junior developers.
  `;

  const mockOptimizedJD = `
    We are seeking an experienced Senior Software Engineer to join our team.
    Requirements: 5+ years of professional experience, expertise in React, TypeScript, and Node.js.
    Responsibilities: Design and build scalable applications, mentor and support junior developers.
  `;

  beforeEach(() => {
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn(() => Promise.resolve()),
      },
    });
  });

  it('renders comparison view with both versions', () => {
    render(
      <JDComparisonView
        originalJD={mockOriginalJD}
        optimizedJD={mockOptimizedJD}
        positionTitle="Senior Engineer"
      />
    );

    expect(screen.getByText(/Senior Engineer/)).toBeInTheDocument();
    expect(screen.getByText('Side by Side')).toBeInTheDocument();
    expect(screen.getByText('Diff View')).toBeInTheDocument();
  });

  it('displays original and optimized JD in side-by-side view', () => {
    render(
      <JDComparisonView
        originalJD={mockOriginalJD}
        optimizedJD={mockOptimizedJD}
        positionTitle="Engineer"
      />
    );

    expect(screen.getByText('Original')).toBeInTheDocument();
    expect(screen.getByText('Optimized')).toBeInTheDocument();
  });

  it('switches between side-by-side and diff view', async () => {
    const user = userEvent.setup();
    render(
      <JDComparisonView
        originalJD={mockOriginalJD}
        optimizedJD={mockOptimizedJD}
      />
    );

    const diffViewButton = screen.getByRole('button', { name: /Diff View/i });
    await user.click(diffViewButton);

    expect(screen.getByText('Changes Highlighted')).toBeInTheDocument();
  });

  it('copies text to clipboard when copy button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <JDComparisonView
        originalJD={mockOriginalJD}
        optimizedJD={mockOptimizedJD}
      />
    );

    const copyButtons = screen.getAllByText('Copy');
    await user.click(copyButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Copied!')).toBeInTheDocument();
    });
  });

  it('shows legend in diff view', async () => {
    const user = userEvent.setup();
    render(
      <JDComparisonView
        originalJD={mockOriginalJD}
        optimizedJD={mockOptimizedJD}
      />
    );

    const diffViewButton = screen.getByRole('button', { name: /Diff View/i });
    await user.click(diffViewButton);

    expect(screen.getByText('Added')).toBeInTheDocument();
    expect(screen.getByText('Removed')).toBeInTheDocument();
  });

  it('calls onClose callback when close button is clicked', async () => {
    const mockOnClose = jest.fn();
    const user = userEvent.setup();

    render(
      <JDComparisonView
        originalJD={mockOriginalJD}
        optimizedJD={mockOptimizedJD}
        onClose={mockOnClose}
      />
    );

    const closeButton = screen.getByRole('button', { name: /Close/i });
    await user.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('downloads optimized JD when download button is clicked', async () => {
    const user = userEvent.setup();

    // Mock createElement and appendChild
    const mockLink = {
      setAttribute: jest.fn(),
      style: { display: '' },
      click: jest.fn(),
    };
    jest.spyOn(document, 'createElement').mockReturnValue(mockLink as any);
    jest.spyOn(document, 'appendChild').mockImplementation();
    jest.spyOn(document, 'removeChild').mockImplementation();

    render(
      <JDComparisonView
        originalJD={mockOriginalJD}
        optimizedJD={mockOptimizedJD}
        positionTitle="TestPosition"
      />
    );

    const downloadButton = screen.getByRole('button', { name: /Download/i });
    await user.click(downloadButton);

    expect(mockLink.click).toHaveBeenCalled();
  });

  it('renders with default position title when not provided', () => {
    render(
      <JDComparisonView
        originalJD={mockOriginalJD}
        optimizedJD={mockOptimizedJD}
      />
    );

    expect(screen.getByText(/Job Description/)).toBeInTheDocument();
  });

  it('hides unchanged text in diff view with toggle', async () => {
    const user = userEvent.setup();
    render(
      <JDComparisonView
        originalJD={mockOriginalJD}
        optimizedJD={mockOptimizedJD}
      />
    );

    // Switch to diff view
    const diffViewButton = screen.getByRole('button', { name: /Diff View/i });
    await user.click(diffViewButton);

    // Toggle hide unchanged
    const toggleButton = screen.getByRole('button', { name: /Hide Unchanged/i });
    await user.click(toggleButton);

    expect(screen.getByText('Show All')).toBeInTheDocument();
  });

  it('handles empty JD text gracefully', () => {
    render(
      <JDComparisonView
        originalJD=""
        optimizedJD=""
        positionTitle="Empty"
      />
    );

    expect(screen.getByText(/Empty/)).toBeInTheDocument();
  });

  it('handles very long JD text', () => {
    const longText = 'Lorem ipsum dolor sit amet. '.repeat(100);
    render(
      <JDComparisonView
        originalJD={longText}
        optimizedJD={longText + ' Added text.'}
        positionTitle="Long"
      />
    );

    expect(screen.getByText(/Long/)).toBeInTheDocument();
    // Should render with scrollable container
    const containers = screen.getAllByText(/Changes Highlighted/, {
      selector: '*'
    });
    expect(containers.length).toBeGreaterThan(0);
  });
});
