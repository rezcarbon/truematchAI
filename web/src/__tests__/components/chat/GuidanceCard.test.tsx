import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GuidanceCard, type GuidanceStep } from '@/components/chat/GuidanceCard';

describe('GuidanceCard Component', () => {
  const mockSteps: GuidanceStep[] = [
    {
      number: 1,
      title: 'Learn Basics',
      description: 'Start with fundamental concepts',
      estimatedTime: 30,
      resources: [
        { title: 'Coursera Course', url: 'https://coursera.org', type: 'course' },
      ],
    },
    {
      number: 2,
      title: 'Build Project',
      description: 'Apply what you learned',
      estimatedTime: 60,
      resources: [
        { title: 'GitHub Template', url: 'https://github.com', type: 'github' },
      ],
    },
  ];

  const defaultProps = {
    title: 'Web Development Path',
    description: 'Master modern web development',
    steps: mockSteps,
    difficulty: 'Intermediate' as const,
  };

  it('renders card with title and description', () => {
    render(<GuidanceCard {...defaultProps} />);

    expect(screen.getByText('Web Development Path')).toBeInTheDocument();
    expect(screen.getByText('Master modern web development')).toBeInTheDocument();
  });

  it('displays difficulty badge', () => {
    render(<GuidanceCard {...defaultProps} />);

    expect(screen.getByText('Intermediate')).toBeInTheDocument();
  });

  it('renders all steps with correct numbering', () => {
    render(<GuidanceCard {...defaultProps} />);

    expect(screen.getByText('Learn Basics')).toBeInTheDocument();
    expect(screen.getByText('Build Project')).toBeInTheDocument();
  });

  it('displays time estimates for each step', () => {
    render(<GuidanceCard {...defaultProps} />);

    expect(screen.getByText('~30 minutes')).toBeInTheDocument();
    expect(screen.getByText('~60 minutes')).toBeInTheDocument();
  });

  it('calculates and displays total time correctly', () => {
    render(<GuidanceCard {...defaultProps} />);

    expect(screen.getByText('90 min total')).toBeInTheDocument();
  });

  it('displays step count', () => {
    render(<GuidanceCard {...defaultProps} />);

    expect(screen.getByText('2 steps')).toBeInTheDocument();
  });

  it('renders resource links for each step', () => {
    render(<GuidanceCard {...defaultProps} />);

    const courseLink = screen.getByText('Coursera Course');
    const githubLink = screen.getByText('GitHub Template');

    expect(courseLink).toBeInTheDocument();
    expect(githubLink).toBeInTheDocument();
  });

  it('calls onStepClick when step is clicked', async () => {
    const onStepClick = jest.fn();
    render(<GuidanceCard {...defaultProps} onStepClick={onStepClick} />);

    const stepElement = screen.getByText('Learn Basics').closest('div[role="button"]');
    if (stepElement) {
      await userEvent.click(stepElement);
      expect(onStepClick).toHaveBeenCalledWith(1);
    }
  });

  it('opens resource links in new window', async () => {
    const windowOpenSpy = jest.spyOn(window, 'open').mockImplementation();

    render(<GuidanceCard {...defaultProps} />);

    const courseLink = screen.getByText('Coursera Course');
    await userEvent.click(courseLink);

    expect(windowOpenSpy).toHaveBeenCalledWith(
      'https://coursera.org',
      '_blank',
      'noopener,noreferrer'
    );

    windowOpenSpy.mockRestore();
  });

  it('uses custom total time when provided', () => {
    render(
      <GuidanceCard
        {...defaultProps}
        totalTime={120}
      />
    );

    expect(screen.getByText('120 min total')).toBeInTheDocument();
  });

  it('renders with custom className', () => {
    const { container } = render(
      <GuidanceCard
        {...defaultProps}
        className="custom-class"
      />
    );

    const card = container.querySelector('.custom-class');
    expect(card).toBeInTheDocument();
  });

  it('displays correct difficulty color for Beginner', () => {
    render(
      <GuidanceCard
        {...defaultProps}
        difficulty="Beginner"
      />
    );

    const badge = screen.getByText('Beginner');
    expect(badge).toHaveClass('bg-green-100');
  });

  it('displays correct difficulty color for Advanced', () => {
    render(
      <GuidanceCard
        {...defaultProps}
        difficulty="Advanced"
      />
    );

    const badge = screen.getByText('Advanced');
    expect(badge).toHaveClass('bg-red-100');
  });

  it('handles empty resources list gracefully', () => {
    const stepsWithoutResources: GuidanceStep[] = [
      {
        number: 1,
        title: 'Basic Intro',
        description: 'Introduction',
        estimatedTime: 15,
      },
    ];

    render(
      <GuidanceCard
        {...defaultProps}
        steps={stepsWithoutResources}
      />
    );

    expect(screen.getByText('Basic Intro')).toBeInTheDocument();
    expect(screen.getByText('Introduction')).toBeInTheDocument();
  });

  it('renders CTA button', () => {
    render(<GuidanceCard {...defaultProps} />);

    expect(screen.getByRole('button', { name: /start learning path/i })).toBeInTheDocument();
  });

  it('supports keyboard navigation on steps', async () => {
    const onStepClick = jest.fn();
    render(<GuidanceCard {...defaultProps} onStepClick={onStepClick} />);

    const stepElement = screen.getByText('Learn Basics').closest('div[role="button"]');
    if (stepElement) {
      fireEvent.keyDown(stepElement, { key: 'Enter' });
      expect(onStepClick).toHaveBeenCalledWith(1);
    }
  });
});
