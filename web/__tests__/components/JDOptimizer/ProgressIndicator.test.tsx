import React from 'react';
import { render, screen } from '@testing-library/react';
import ProgressIndicator from '@/components/JDOptimizer/ProgressIndicator';

describe('ProgressIndicator', () => {
  it('renders progress indicator', () => {
    render(<ProgressIndicator totalIssues={10} fixedIssues={0} />);
    expect(screen.getByText('Issues Resolved')).toBeInTheDocument();
  });

  it('displays correct progress percentage', () => {
    render(<ProgressIndicator totalIssues={10} fixedIssues={5} />);
    expect(screen.getByText('5 of 10')).toBeInTheDocument();
  });

  it('shows 0% progress when no issues fixed', () => {
    render(<ProgressIndicator totalIssues={10} fixedIssues={0} />);
    expect(screen.getByText('0% complete')).toBeInTheDocument();
  });

  it('shows 100% progress when all issues fixed', () => {
    render(<ProgressIndicator totalIssues={10} fixedIssues={10} />);
    expect(screen.getByText('All issues resolved!')).toBeInTheDocument();
  });

  it('handles no issues case', () => {
    render(<ProgressIndicator totalIssues={0} fixedIssues={0} />);
    expect(screen.getByText('0 of 0')).toBeInTheDocument();
  });

  it('displays phase indicators', () => {
    render(<ProgressIndicator totalIssues={10} fixedIssues={3} />);
    expect(screen.getByText('Phase 1')).toBeInTheDocument();
    expect(screen.getByText('Phase 2')).toBeInTheDocument();
    expect(screen.getByText('Phase 3')).toBeInTheDocument();
  });

  it('marks phases as complete appropriately', () => {
    render(<ProgressIndicator totalIssues={9} fixedIssues={6} />);
    const completedPhases = screen.getAllByText('✓ Done');
    expect(completedPhases.length).toBeGreaterThan(0);
  });

  it('displays stats cards', () => {
    render(<ProgressIndicator totalIssues={10} fixedIssues={5} />);
    expect(screen.getByText('Total Issues')).toBeInTheDocument();
    expect(screen.getByText('Resolved')).toBeInTheDocument();
    expect(screen.getByText('Remaining')).toBeInTheDocument();
  });

  it('shows correct remaining issues count', () => {
    render(<ProgressIndicator totalIssues={10} fixedIssues={3} />);
    const remainingStats = screen.getByText('Remaining');
    expect(remainingStats.parentElement?.textContent).toContain('7');
  });

  it('calculates percentage correctly', () => {
    render(<ProgressIndicator totalIssues={4} fixedIssues={2} />);
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('rounds percentage correctly', () => {
    render(<ProgressIndicator totalIssues={3} fixedIssues={1} />);
    // 1/3 = 33.33... should round to 33%
    expect(screen.getByText('33% complete')).toBeInTheDocument();
  });

  it('displays progress bar width based on percentage', () => {
    const { container } = render(
      <ProgressIndicator totalIssues={10} fixedIssues={7} />
    );
    const progressBar = container.querySelector('[style*="width"]');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveStyle('width: 70%');
  });

  it('handles single issue', () => {
    render(<ProgressIndicator totalIssues={1} fixedIssues={0} />);
    expect(screen.getByText('1 of 1')).toBeInTheDocument();
  });

  it('displays all stats correctly', () => {
    render(<ProgressIndicator totalIssues={10} fixedIssues={3} />);
    expect(screen.getByText('10')).toBeInTheDocument(); // Total
    expect(screen.getByText('3')).toBeInTheDocument(); // Resolved
    expect(screen.getByText('7')).toBeInTheDocument(); // Remaining
  });
});
