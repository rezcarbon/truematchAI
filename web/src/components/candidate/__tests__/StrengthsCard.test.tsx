import React from 'react';
import { render, screen } from '@testing-library/react';
import { StrengthsCard } from '../StrengthsCard';

describe('StrengthsCard', () => {
  it('renders loading state', () => {
    render(<StrengthsCard strengths={[]} loading={true} />);
    expect(screen.getByText('Strengths')).toBeInTheDocument();
  });

  it('renders empty state when no strengths', () => {
    render(<StrengthsCard strengths={[]} />);
    expect(screen.getByText('No verified strengths identified yet.')).toBeInTheDocument();
  });

  it('renders strengths with proficiency levels', () => {
    const strengths = [
      {
        name: 'JavaScript',
        proficiency: 9,
        evidence: [
          {
            type: 'GitHub' as const,
            url: 'https://github.com',
            description: 'JavaScript projects',
          },
        ],
      },
    ];

    render(<StrengthsCard strengths={strengths} />);
    expect(screen.getByText('JavaScript')).toBeInTheDocument();
    expect(screen.getByText('Expert')).toBeInTheDocument();
  });

  it('renders evidence badges with links', () => {
    const strengths = [
      {
        name: 'Python',
        proficiency: 7,
        evidence: [
          {
            type: 'GitHub' as const,
            url: 'https://github.com/user/python-project',
          },
        ],
      },
    ];

    render(<StrengthsCard strengths={strengths} />);
    const link = screen.getByRole('link', { name: /View evidence on GitHub/i });
    expect(link).toHaveAttribute('href', 'https://github.com/user/python-project');
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('displays correct proficiency labels', () => {
    const strengths = [
      { name: 'Skill1', proficiency: 9, evidence: [] },
      { name: 'Skill2', proficiency: 7, evidence: [] },
      { name: 'Skill3', proficiency: 5, evidence: [] },
      { name: 'Skill4', proficiency: 2, evidence: [] },
    ];

    render(<StrengthsCard strengths={strengths} />);
    expect(screen.getByText('Expert')).toBeInTheDocument();
    expect(screen.getByText('Advanced')).toBeInTheDocument();
    expect(screen.getAllByText('Intermediate')[0]).toBeInTheDocument();
    expect(screen.getByText('Beginner')).toBeInTheDocument();
  });

  it('renders multiple evidence sources', () => {
    const strengths = [
      {
        name: 'System Design',
        proficiency: 8,
        evidence: [
          { type: 'GitHub' as const, url: 'https://github.com/project' },
          { type: 'LinkedIn' as const, url: 'https://linkedin.com/in/user' },
          { type: 'Patents' as const, url: 'https://patents.com/patent123' },
        ],
      },
    ];

    render(<StrengthsCard strengths={strengths} />);
    expect(screen.getByText('System Design')).toBeInTheDocument();
    expect(screen.getByText('GitHub')).toBeInTheDocument();
    expect(screen.getByText('LinkedIn')).toBeInTheDocument();
    expect(screen.getByText('Patents')).toBeInTheDocument();
  });

  it('has correct accessibility attributes', () => {
    const strengths = [
      {
        name: 'TypeScript',
        proficiency: 9,
        evidence: [
          { type: 'GitHub' as const, url: 'https://github.com/ts-project' },
        ],
      },
    ];

    render(<StrengthsCard strengths={strengths} />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('aria-label');
  });
});
