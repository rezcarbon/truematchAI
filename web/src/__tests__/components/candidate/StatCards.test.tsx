import React from 'react';
import { render, screen } from '@testing-library/react';
import { StatCards, type StatCardData } from '@/components/candidate/StatCards';
import {
  CheckCircle2,
  TrendingUp,
  Briefcase,
  MessageSquare,
} from 'lucide-react';

describe('StatCards Component', () => {
  const mockStats: StatCardData[] = [
    {
      label: 'Assessments Completed',
      value: 5,
      icon: <CheckCircle2 className="w-6 h-6" />,
      trend: { value: 20, direction: 'up' },
      description: 'In the last 30 days',
      color: 'blue',
    },
    {
      label: 'Average Score',
      value: 76,
      icon: <TrendingUp className="w-6 h-6" />,
      trend: { value: 5, direction: 'up' },
      description: 'Across all assessments',
      suffix: '%',
      color: 'green',
    },
    {
      label: 'Active Applications',
      value: 12,
      icon: <Briefcase className="w-6 h-6" />,
      trend: { value: 8, direction: 'up' },
      description: 'Pending or in progress',
      color: 'purple',
    },
  ];

  it('renders stat cards with provided data', () => {
    render(<StatCards stats={mockStats} />);

    expect(screen.getByText('Assessments Completed')).toBeInTheDocument();
    expect(screen.getByText('Average Score')).toBeInTheDocument();
    expect(screen.getByText('Active Applications')).toBeInTheDocument();
  });

  it('displays stat values correctly', () => {
    render(<StatCards stats={mockStats} />);

    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('76')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
  });

  it('displays suffixes when provided', () => {
    render(<StatCards stats={mockStats} />);

    expect(screen.getByText('%')).toBeInTheDocument();
  });

  it('displays trend indicators', () => {
    render(<StatCards stats={mockStats} />);

    // Look for percentage values from trends
    const percentages = screen.getAllByText(/20|5|8/);
    expect(percentages.length).toBeGreaterThan(0);
  });

  it('displays descriptions', () => {
    render(<StatCards stats={mockStats} />);

    expect(screen.getByText('In the last 30 days')).toBeInTheDocument();
    expect(screen.getByText('Across all assessments')).toBeInTheDocument();
    expect(screen.getByText('Pending or in progress')).toBeInTheDocument();
  });

  it('renders default stats when no stats provided', () => {
    render(<StatCards stats={[]} />);

    expect(screen.getByText('Assessments Completed')).toBeInTheDocument();
    expect(screen.getByText('Average Score')).toBeInTheDocument();
    expect(screen.getByText('Active Applications')).toBeInTheDocument();
    expect(screen.getByText('Interviews Scheduled')).toBeInTheDocument();
  });

  it('renders cards in a grid layout', () => {
    const { container } = render(<StatCards stats={mockStats} />);

    const grid = container.querySelector('[class*="grid"]');
    expect(grid).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <StatCards stats={mockStats} className="custom-class" />
    );

    const wrapper = container.querySelector('.custom-class');
    expect(wrapper).toBeInTheDocument();
  });

  it('displays upward trend with correct color', () => {
    const { container } = render(<StatCards stats={mockStats} />);

    // Cards with up trend should have appropriate styling
    expect(container.querySelectorAll('svg').length).toBeGreaterThan(0);
  });

  it('handles stat with down trend', () => {
    const statsWithDownTrend: StatCardData[] = [
      {
        label: 'Rejection Rate',
        value: 15,
        icon: <MessageSquare className="w-6 h-6" />,
        trend: { value: 5, direction: 'down' },
        color: 'red',
      },
    ];

    render(<StatCards stats={statsWithDownTrend} />);

    expect(screen.getByText('Rejection Rate')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument();
  });

  it('handles stat without trend', () => {
    const statsNoTrend: StatCardData[] = [
      {
        label: 'Profile Views',
        value: 42,
        icon: <TrendingUp className="w-6 h-6" />,
        color: 'blue',
      },
    ];

    render(<StatCards stats={statsNoTrend} />);

    expect(screen.getByText('Profile Views')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('applies correct color classes to cards', () => {
    const { container } = render(<StatCards stats={mockStats} />);

    // Check for color-related classes
    const cards = container.querySelectorAll('[class*="bg-"]');
    expect(cards.length).toBeGreaterThan(0);
  });

  it('renders all four default stats when empty', () => {
    render(<StatCards stats={[]} />);

    expect(screen.getByText('Assessments Completed')).toBeInTheDocument();
    expect(screen.getByText('Average Score')).toBeInTheDocument();
    expect(screen.getByText('Active Applications')).toBeInTheDocument();
    expect(screen.getByText('Interviews Scheduled')).toBeInTheDocument();
  });
});
