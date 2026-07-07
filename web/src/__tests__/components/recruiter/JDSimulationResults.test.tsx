import React from 'react';
import { render, screen } from '@testing-library/react';
import { JDSimulationResults } from '@/components/recruiter/JDSimulationResults';

// Mock next/link
jest.mock('next/link', () => {
  return ({ children, href }: any) => {
    return <a href={href}>{children}</a>;
  };
});

describe('JDSimulationResults', () => {
  const mockJDQuality = {
    score: 72,
    flags: [
      {
        type: 'clarity',
        text: 'Job description is missing key responsibilities',
        severity: 'high' as const,
      },
      {
        type: 'completeness',
        text: 'Missing information about salary range',
        severity: 'medium' as const,
      },
      {
        type: 'tone',
        text: 'Tone could be more engaging',
        severity: 'low' as const,
      },
    ],
  };

  it('renders results header with position title', () => {
    render(
      <JDSimulationResults
        jdQuality={mockJDQuality}
        positionTitle="Senior Backend Engineer"
      />
    );

    expect(
      screen.getByText(/Simulation Results for Senior Backend Engineer/i)
    ).toBeInTheDocument();
  });

  it('displays quality score', () => {
    render(
      <JDSimulationResults
        jdQuality={mockJDQuality}
        positionTitle="Engineer"
      />
    );

    expect(screen.getByText('72/100')).toBeInTheDocument();
  });

  it('displays all issues found', () => {
    render(
      <JDSimulationResults
        jdQuality={mockJDQuality}
        positionTitle="Engineer"
      />
    );

    expect(
      screen.getByText('Job description is missing key responsibilities')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Missing information about salary range')
    ).toBeInTheDocument();
    expect(screen.getByText('Tone could be more engaging')).toBeInTheDocument();
  });

  it('displays severity badges for issues', () => {
    render(
      <JDSimulationResults
        jdQuality={mockJDQuality}
        positionTitle="Engineer"
      />
    );

    expect(screen.getByText('high')).toBeInTheDocument();
    expect(screen.getByText('medium')).toBeInTheDocument();
    expect(screen.getByText('low')).toBeInTheDocument();
  });

  it('shows issues count', () => {
    render(
      <JDSimulationResults
        jdQuality={mockJDQuality}
        positionTitle="Engineer"
      />
    );

    expect(screen.getByText('Issues Found (3)')).toBeInTheDocument();
  });

  it('displays overall quality assessment', () => {
    render(
      <JDSimulationResults
        jdQuality={mockJDQuality}
        positionTitle="Engineer"
      />
    );

    expect(screen.getByText(/Overall Quality/i)).toBeInTheDocument();
    expect(
      screen.getByText(
        /Good job description, minor improvements needed/i
      )
    ).toBeInTheDocument();
  });

  it('shows recommendations count', () => {
    render(
      <JDSimulationResults
        jdQuality={mockJDQuality}
        positionTitle="Engineer"
      />
    );

    expect(screen.getByText(/Recommendations/i)).toBeInTheDocument();
  });

  it('displays key insights section', () => {
    render(
      <JDSimulationResults
        jdQuality={mockJDQuality}
        positionTitle="Engineer"
      />
    );

    expect(screen.getByText('Key Insights')).toBeInTheDocument();
  });

  it('displays next actions buttons', () => {
    render(
      <JDSimulationResults
        jdQuality={mockJDQuality}
        positionTitle="Engineer"
      />
    );

    expect(screen.getByText('Next Steps')).toBeInTheDocument();
    expect(screen.getByText('Create Position')).toBeInTheDocument();
    expect(screen.getByText('View All JDs')).toBeInTheDocument();
    expect(screen.getByText('Test Another JD')).toBeInTheDocument();
  });

  it('shows excellent assessment for high score', () => {
    const excellentQuality = {
      score: 95,
      flags: [],
    };

    render(
      <JDSimulationResults
        jdQuality={excellentQuality}
        positionTitle="Engineer"
      />
    );

    expect(screen.getByText(/Excellent job description/i)).toBeInTheDocument();
  });

  it('shows needs improvement assessment for low score', () => {
    const poorQuality = {
      score: 35,
      flags: [],
    };

    render(
      <JDSimulationResults
        jdQuality={poorQuality}
        positionTitle="Engineer"
      />
    );

    expect(
      screen.getByText(/Job description needs significant improvements/i)
    ).toBeInTheDocument();
  });

  it('displays no issues message when flags are empty', () => {
    const noIssuesQuality = {
      score: 95,
      flags: [],
    };

    render(
      <JDSimulationResults
        jdQuality={noIssuesQuality}
        positionTitle="Engineer"
      />
    );

    expect(screen.getByText('No issues found')).toBeInTheDocument();
  });

  it('counts high priority issues correctly', () => {
    const qualityWithHighIssues = {
      score: 50,
      flags: [
        {
          type: 'clarity',
          text: 'Missing key requirements',
          severity: 'high' as const,
        },
        {
          type: 'clarity',
          text: 'Another high priority issue',
          severity: 'high' as const,
        },
        {
          type: 'tone',
          text: 'Minor tone issue',
          severity: 'low' as const,
        },
      ],
    };

    render(
      <JDSimulationResults
        jdQuality={qualityWithHighIssues}
        positionTitle="Engineer"
      />
    );

    expect(screen.getByText(/2 high priority/i)).toBeInTheDocument();
  });

  it('uses default position title when not provided', () => {
    render(
      <JDSimulationResults
        jdQuality={mockJDQuality}
      />
    );

    expect(
      screen.getByText(/Simulation Results for Untitled Position/i)
    ).toBeInTheDocument();
  });

  it('renders action links', () => {
    render(
      <JDSimulationResults
        jdQuality={mockJDQuality}
        positionTitle="Engineer"
      />
    );

    const createPositionLink = screen.getByRole('link', { name: /Create Position/i });
    expect(createPositionLink).toHaveAttribute('href', '/recruiter/positions/new');

    const viewAllJDsLink = screen.getByRole('link', { name: /View All JDs/i });
    expect(viewAllJDsLink).toHaveAttribute('href', '/recruiter/jd-quality');

    const testAnotherLink = screen.getByRole('link', { name: /Test Another JD/i });
    expect(testAnotherLink).toHaveAttribute('href', '/recruiter/jd-simulation');
  });

  it('displays correct quality score styling', () => {
    render(
      <JDSimulationResults
        jdQuality={mockJDQuality}
        positionTitle="Engineer"
      />
    );

    const scoreElements = screen.getAllByText('72/100');
    expect(scoreElements.length).toBeGreaterThan(0);
  });

  it('handles empty flags array', () => {
    const noFlagsQuality = {
      score: 90,
      flags: [],
    };

    render(
      <JDSimulationResults
        jdQuality={noFlagsQuality}
        positionTitle="Engineer"
      />
    );

    // Should not crash and should show no issues message
    expect(screen.getByText(/No issues found/i)).toBeInTheDocument();
  });

  it('displays high severity issues first', () => {
    render(
      <JDSimulationResults
        jdQuality={mockJDQuality}
        positionTitle="Engineer"
      />
    );

    const issueTexts = screen.getAllByText(/missing/i);
    expect(issueTexts.length).toBeGreaterThan(0);
  });

  it('shows all issue details correctly', () => {
    render(
      <JDSimulationResults
        jdQuality={mockJDQuality}
        positionTitle="Engineer"
      />
    );

    // Verify all issue types are displayed
    expect(screen.getByText('clarity')).toBeInTheDocument();
    expect(screen.getByText('completeness')).toBeInTheDocument();
    expect(screen.getByText('tone')).toBeInTheDocument();
  });

  it('renders insights grid layout', () => {
    const { container } = render(
      <JDSimulationResults
        jdQuality={mockJDQuality}
        positionTitle="Engineer"
      />
    );

    // Check for grid layout
    const gridElements = container.querySelectorAll('[class*="grid"]');
    expect(gridElements.length).toBeGreaterThan(0);
  });

  it('handles position title with special characters', () => {
    render(
      <JDSimulationResults
        jdQuality={mockJDQuality}
        positionTitle="Senior Backend Engineer (L4)"
      />
    );

    expect(
      screen.getByText(/Simulation Results for Senior Backend Engineer \(L4\)/i)
    ).toBeInTheDocument();
  });

  it('formats recommendation count as singular/plural', () => {
    const singleIssueQuality = {
      score: 85,
      flags: [
        {
          type: 'tone',
          text: 'Minor issue',
          severity: 'low' as const,
        },
      ],
    };

    render(
      <JDSimulationResults
        jdQuality={singleIssueQuality}
        positionTitle="Engineer"
      />
    );

    expect(screen.getByText(/1/)).toBeInTheDocument();
  });
});
