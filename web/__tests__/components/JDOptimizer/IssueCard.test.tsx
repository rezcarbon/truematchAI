import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import IssueCard from '@/components/JDOptimizer/IssueCard';
import { OptimizationIssue } from '@/types/jd-optimizer';

describe('IssueCard', () => {
  const mockIssue: OptimizationIssue = {
    id: '1',
    title: 'Weak Language',
    description: 'Replace weak language with stronger alternatives',
    category: 'clarity',
    severity: 'medium',
    problematicText: 'we need',
    suggestion: 'we require',
    explanation: 'Strong language improves engagement',
    impact: 'Better candidate attraction',
    isFixed: false,
  };

  it('renders issue title and description', () => {
    render(
      <IssueCard issue={mockIssue} />
    );
    expect(screen.getByText('Weak Language')).toBeInTheDocument();
    expect(screen.getByText('Replace weak language with stronger alternatives')).toBeInTheDocument();
  });

  it('displays severity badge', () => {
    render(<IssueCard issue={mockIssue} />);
    expect(screen.getByText('MEDIUM')).toBeInTheDocument();
  });

  it('displays category badge', () => {
    render(<IssueCard issue={mockIssue} />);
    expect(screen.getByText('clarity')).toBeInTheDocument();
  });

  it('expands on click', async () => {
    render(<IssueCard issue={mockIssue} />);
    const button = screen.getByRole('button');

    expect(screen.queryByText('CURRENT TEXT')).not.toBeInTheDocument();

    await userEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText('CURRENT TEXT')).toBeInTheDocument();
    });
  });

  it('shows expanded content when selected', () => {
    render(<IssueCard issue={mockIssue} isSelected={true} />);
    expect(screen.getByText('CURRENT TEXT')).toBeInTheDocument();
    expect(screen.getByText('SUGGESTED FIX')).toBeInTheDocument();
    expect(screen.getByText('WHY THIS MATTERS')).toBeInTheDocument();
  });

  it('displays problematic text', () => {
    render(<IssueCard issue={mockIssue} isSelected={true} />);
    expect(screen.getByText('we need')).toBeInTheDocument();
  });

  it('displays suggestion', () => {
    render(<IssueCard issue={mockIssue} isSelected={true} />);
    expect(screen.getByText('we require')).toBeInTheDocument();
  });

  it('displays explanation', () => {
    render(<IssueCard issue={mockIssue} isSelected={true} />);
    expect(screen.getByText('Strong language improves engagement')).toBeInTheDocument();
  });

  it('displays impact', () => {
    render(<IssueCard issue={mockIssue} isSelected={true} />);
    expect(screen.getByText('EXPECTED IMPACT')).toBeInTheDocument();
    expect(screen.getByText('Better candidate attraction')).toBeInTheDocument();
  });

  it('calls onApplyFix when apply button clicked', async () => {
    const mockApplyFix = jest.fn();
    render(
      <IssueCard
        issue={mockIssue}
        isSelected={true}
        onApplyFix={mockApplyFix}
      />
    );

    const applyButton = screen.getByText('Apply Fix');
    await userEvent.click(applyButton);

    expect(mockApplyFix).toHaveBeenCalled();
  });

  it('shows fixed state when issue is marked as fixed', () => {
    const fixedIssue = { ...mockIssue, isFixed: true };
    render(<IssueCard issue={fixedIssue} isSelected={true} />);
    expect(screen.getByText('Fixed')).toBeInTheDocument();
    expect(screen.queryByText('Apply Fix')).not.toBeInTheDocument();
  });

  it('displays different severity colors', () => {
    const { container: highContainer } = render(
      <IssueCard issue={{ ...mockIssue, severity: 'high' }} />
    );
    expect(highContainer.querySelector('.bg-red-50')).toBeInTheDocument();

    const { container: lowContainer } = render(
      <IssueCard issue={{ ...mockIssue, severity: 'low' }} />
    );
    expect(lowContainer.querySelector('.bg-blue-50')).toBeInTheDocument();
  });

  it('toggles expansion on multiple clicks', async () => {
    render(<IssueCard issue={mockIssue} />);
    const button = screen.getByRole('button');

    // First click - expand
    await userEvent.click(button);
    await waitFor(() => {
      expect(screen.getByText('CURRENT TEXT')).toBeInTheDocument();
    });

    // Second click - collapse
    await userEvent.click(button);
    await waitFor(() => {
      expect(screen.queryByText('CURRENT TEXT')).not.toBeInTheDocument();
    });
  });

  it('renders without optional fields', () => {
    const minimalIssue: OptimizationIssue = {
      id: '2',
      title: 'Issue',
      description: 'Test description',
      category: 'tone',
      severity: 'low',
      isFixed: false,
    };

    render(<IssueCard issue={minimalIssue} isSelected={true} />);
    expect(screen.getByText('Issue')).toBeInTheDocument();
    expect(screen.getByText('Test description')).toBeInTheDocument();
    // Optional fields should not crash
    expect(screen.queryByText('CURRENT TEXT')).not.toBeInTheDocument();
  });

  it('handles high severity issue styling', () => {
    const highSeverityIssue = { ...mockIssue, severity: 'high' as const };
    const { container } = render(<IssueCard issue={highSeverityIssue} />);
    expect(container.querySelector('.bg-red-50')).toBeInTheDocument();
  });

  it('displays multiple category types', () => {
    const categories = [
      'clarity',
      'tone',
      'completeness',
      'structure',
      'engagement',
    ];

    categories.forEach((category) => {
      const { container } = render(
        <IssueCard
          issue={{ ...mockIssue, category: category as any }}
        />
      );
      expect(screen.getByText(category)).toBeInTheDocument();
    });
  });
});
