import React from 'react';
import { render, screen } from '@testing-library/react';
import { SkillGapsCard } from '../SkillGapsCard';

describe('SkillGapsCard', () => {
  it('renders loading state', () => {
    render(<SkillGapsCard gaps={[]} loading={true} />);
    expect(screen.getByText('Skill Gaps')).toBeInTheDocument();
  });

  it('renders empty state when no gaps', () => {
    render(<SkillGapsCard gaps={[]} />);
    expect(screen.getByText('No significant skill gaps identified!')).toBeInTheDocument();
  });

  it('renders gaps with importance levels', () => {
    const gaps = [
      {
        name: 'Kubernetes',
        importance: 'Critical' as const,
        weeksToLearn: 4,
        learningResources: [],
      },
    ];

    render(<SkillGapsCard gaps={gaps} />);
    expect(screen.getByText('Kubernetes')).toBeInTheDocument();
    expect(screen.getByText('Critical')).toBeInTheDocument();
  });

  it('displays learning time estimates', () => {
    const gaps = [
      {
        name: 'Docker',
        importance: 'Important' as const,
        weeksToLearn: 2,
        learningResources: [],
      },
      {
        name: 'GraphQL',
        importance: 'Nice-to-have' as const,
        weeksToLearn: 1,
        learningResources: [],
      },
    ];

    render(<SkillGapsCard gaps={gaps} />);
    expect(screen.getByText('2 weeks')).toBeInTheDocument();
    expect(screen.getByText('1 week')).toBeInTheDocument();
  });

  it('renders learning resources with links', () => {
    const gaps = [
      {
        name: 'React',
        importance: 'Critical' as const,
        weeksToLearn: 3,
        learningResources: [
          {
            title: 'React Official Tutorial',
            url: 'https://react.dev',
            type: 'Tutorial' as const,
          },
          {
            title: 'React for Beginners',
            url: 'https://udemy.com/react-course',
            type: 'Course' as const,
          },
        ],
      },
    ];

    render(<SkillGapsCard gaps={gaps} />);
    const links = screen.getAllByRole('link');
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute('href', 'https://react.dev');
    expect(links[1]).toHaveAttribute('href', 'https://udemy.com/react-course');
  });

  it('sorts gaps by importance', () => {
    const gaps = [
      {
        name: 'Nice Skill',
        importance: 'Nice-to-have' as const,
        weeksToLearn: 1,
        learningResources: [],
      },
      {
        name: 'Critical Skill',
        importance: 'Critical' as const,
        weeksToLearn: 2,
        learningResources: [],
      },
      {
        name: 'Important Skill',
        importance: 'Important' as const,
        weeksToLearn: 1,
        learningResources: [],
      },
    ];

    const { container } = render(<SkillGapsCard gaps={gaps} />);
    const skillElements = container.querySelectorAll('h4');
    expect(skillElements[0].textContent).toBe('Critical Skill');
    expect(skillElements[1].textContent).toBe('Important Skill');
    expect(skillElements[2].textContent).toBe('Nice Skill');
  });

  it('displays gap descriptions', () => {
    const gaps = [
      {
        name: 'AWS',
        importance: 'Important' as const,
        weeksToLearn: 4,
        description: 'Cloud infrastructure and deployment',
        learningResources: [],
      },
    ];

    render(<SkillGapsCard gaps={gaps} />);
    expect(screen.getByText('Cloud infrastructure and deployment')).toBeInTheDocument();
  });

  it('applies correct badge variants for importance', () => {
    const gaps = [
      {
        name: 'Skill1',
        importance: 'Critical' as const,
        weeksToLearn: 1,
        learningResources: [],
      },
      {
        name: 'Skill2',
        importance: 'Important' as const,
        weeksToLearn: 1,
        learningResources: [],
      },
      {
        name: 'Skill3',
        importance: 'Nice-to-have' as const,
        weeksToLearn: 1,
        learningResources: [],
      },
    ];

    const { container } = render(<SkillGapsCard gaps={gaps} />);
    const badges = container.querySelectorAll('[class*="badge"]');
    expect(badges.length).toBeGreaterThanOrEqual(3);
  });

  it('has correct accessibility attributes', () => {
    const gaps = [
      {
        name: 'Rust',
        importance: 'Critical' as const,
        weeksToLearn: 6,
        learningResources: [
          {
            title: 'Rust Programming Language',
            url: 'https://doc.rust-lang.org',
            type: 'Documentation' as const,
          },
        ],
      },
    ];

    render(<SkillGapsCard gaps={gaps} />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('aria-label');
  });
});
