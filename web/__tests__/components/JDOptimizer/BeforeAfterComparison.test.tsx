import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BeforeAfterComparison from '@/components/JDOptimizer/BeforeAfterComparison';

// Mock window.innerWidth for viewport testing
Object.defineProperty(window, 'innerWidth', {
  writable: true,
  configurable: true,
  value: 1024,
});

describe('BeforeAfterComparison', () => {
  const beforeText = 'Before text content';
  const afterText = 'After text content with improvements';

  it('renders comparison component', () => {
    render(
      <BeforeAfterComparison
        before={beforeText}
        after={afterText}
      />
    );
    expect(screen.getByText('Split View')).toBeInTheDocument();
    expect(screen.getByText('Stacked View')).toBeInTheDocument();
  });

  it('displays both before and after content in split view', () => {
    render(
      <BeforeAfterComparison
        before={beforeText}
        after={afterText}
      />
    );

    expect(screen.getByText('Before')).toBeInTheDocument();
    expect(screen.getByText('After')).toBeInTheDocument();
    expect(screen.getByText(beforeText)).toBeInTheDocument();
    expect(screen.getByText(afterText)).toBeInTheDocument();
  });

  it('switches to stacked view when button clicked', async () => {
    const { container } = render(
      <BeforeAfterComparison
        before={beforeText}
        after={afterText}
      />
    );

    const stackedButton = screen.getByText('Stacked View');
    await userEvent.click(stackedButton);

    // Check if stacked view is active
    expect(stackedButton).toHaveClass('bg-blue-100');
  });

  it('switches back to split view', async () => {
    render(
      <BeforeAfterComparison
        before={beforeText}
        after={afterText}
      />
    );

    const stackedButton = screen.getByText('Stacked View');
    const splitButton = screen.getByText('Split View');

    await userEvent.click(stackedButton);
    expect(stackedButton).toHaveClass('bg-blue-100');

    await userEvent.click(splitButton);
    expect(splitButton).toHaveClass('bg-blue-100');
  });

  it('displays copy buttons for before and after', () => {
    render(
      <BeforeAfterComparison
        before={beforeText}
        after={afterText}
      />
    );

    const copyButtons = screen.getAllByRole('button').filter(
      (btn) => btn.getAttribute('title') === 'Copy text'
    );
    expect(copyButtons.length).toBeGreaterThanOrEqual(2);
  });

  it('copies before text to clipboard', async () => {
    const clipboardSpy = jest.spyOn(navigator.clipboard, 'writeText');

    render(
      <BeforeAfterComparison
        before={beforeText}
        after={afterText}
      />
    );

    const copyButtons = screen.getAllByRole('button').filter(
      (btn) => btn.getAttribute('title') === 'Copy text'
    );

    await userEvent.click(copyButtons[0]);

    expect(clipboardSpy).toHaveBeenCalledWith(beforeText);
    clipboardSpy.mockRestore();
  });

  it('shows check icon after copy', async () => {
    jest.spyOn(navigator.clipboard, 'writeText').mockResolvedValueOnce(undefined);

    render(
      <BeforeAfterComparison
        before={beforeText}
        after={afterText}
      />
    );

    const copyButtons = screen.getAllByRole('button').filter(
      (btn) => btn.getAttribute('title') === 'Copy text'
    );

    await userEvent.click(copyButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument();
    });
  });

  it('displays line and character counts', () => {
    render(
      <BeforeAfterComparison
        before={beforeText}
        after={afterText}
      />
    );

    expect(screen.getAllByText(/lines/)).toHaveLength(2);
    expect(screen.getAllByText(/characters/)).toHaveLength(2);
  });

  it('displays summary stats', () => {
    render(
      <BeforeAfterComparison
        before={beforeText}
        after={afterText}
      />
    );

    expect(screen.getByText('Words Improved')).toBeInTheDocument();
    expect(screen.getByText('Length Change')).toBeInTheDocument();
    expect(screen.getByText('Readability')).toBeInTheDocument();
  });

  it('calculates words improved correctly', () => {
    const before = 'one two three';
    const after = 'one two three four five';
    render(
      <BeforeAfterComparison
        before={before}
        after={after}
      />
    );

    expect(screen.getByText('2')).toBeInTheDocument(); // 5-3 = 2 words improved
  });

  it('calculates length change percentage', () => {
    const before = 'test';
    const after = 'test text';
    render(
      <BeforeAfterComparison
        before={before}
        after={after}
      />
    );

    // (9-4)/4 * 100 = 125%
    expect(screen.getByText('125%')).toBeInTheDocument();
  });

  it('handles negative length change', () => {
    const before = 'This is a long text';
    const after = 'Short';
    render(
      <BeforeAfterComparison
        before={before}
        after={after}
      />
    );

    // Should show negative percentage
    expect(screen.getByText('-74%')).toBeInTheDocument();
  });

  it('displays readability enhanced message', () => {
    render(
      <BeforeAfterComparison
        before={beforeText}
        after={afterText}
      />
    );

    expect(screen.getByText('Enhanced')).toBeInTheDocument();
  });

  it('handles empty before text', () => {
    render(
      <BeforeAfterComparison
        before=""
        after={afterText}
      />
    );

    expect(screen.getByText(afterText)).toBeInTheDocument();
  });

  it('handles empty after text', () => {
    render(
      <BeforeAfterComparison
        before={beforeText}
        after=""
      />
    );

    expect(screen.getByText(beforeText)).toBeInTheDocument();
  });

  it('handles multiline content', () => {
    const multilineBefore = 'Line 1\nLine 2\nLine 3';
    const multilineAfter = 'Line 1\nLine 2\nLine 3\nLine 4';

    render(
      <BeforeAfterComparison
        before={multilineBefore}
        after={multilineAfter}
      />
    );

    expect(screen.getByText(multilineBefore)).toBeInTheDocument();
    expect(screen.getByText(multilineAfter)).toBeInTheDocument();
  });

  it('maintains state when switching views', async () => {
    render(
      <BeforeAfterComparison
        before={beforeText}
        after={afterText}
      />
    );

    const stackedButton = screen.getByText('Stacked View');
    await userEvent.click(stackedButton);

    // Content should still be visible
    expect(screen.getByText(beforeText)).toBeInTheDocument();
    expect(screen.getByText(afterText)).toBeInTheDocument();
  });
});
