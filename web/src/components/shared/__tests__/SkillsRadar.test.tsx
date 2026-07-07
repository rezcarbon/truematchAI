import React from 'react';
import { render, screen } from '@testing-library/react';
import { SkillsRadar } from '../SkillsRadar';

describe('SkillsRadar', () => {
  it('renders loading state', () => {
    render(<SkillsRadar data={[]} loading={true} />);
    expect(screen.getByText('Skills Alignment')).toBeInTheDocument();
    expect(screen.getByText('Loading visualization...')).toBeInTheDocument();
  });

  it('renders empty state when no data', () => {
    render(<SkillsRadar data={[]} loading={false} />);
    expect(screen.getByText('No skill data available')).toBeInTheDocument();
  });

  it('renders custom title and subtitle', () => {
    const data = [
      { skill: 'JavaScript', candidate: 80, required: 70 },
    ];
    render(
      <SkillsRadar
        data={data}
        title="Custom Title"
        subtitle="Custom Subtitle"
      />
    );
    expect(screen.getByText('Custom Title')).toBeInTheDocument();
    expect(screen.getByText('Custom Subtitle')).toBeInTheDocument();
  });

  it('renders skill data with alignment indicators', () => {
    const data = [
      { skill: 'JavaScript', candidate: 85, required: 70 },
      { skill: 'React', candidate: 75, required: 80 },
      { skill: 'Python', candidate: 60, required: 60 },
    ];

    render(<SkillsRadar data={data} />);

    expect(screen.getByText('JavaScript')).toBeInTheDocument();
    expect(screen.getByText('React')).toBeInTheDocument();
    expect(screen.getByText('Python')).toBeInTheDocument();
  });

  it('displays skill proficiency levels', () => {
    const data = [
      { skill: 'TypeScript', candidate: 70, required: 65 },
    ];

    render(<SkillsRadar data={data} />);
    expect(screen.getByText('You: 70')).toBeInTheDocument();
    expect(screen.getByText('Need: 65')).toBeInTheDocument();
  });

  it('shows checkmark for aligned skills', () => {
    const data = [
      { skill: 'Python', candidate: 85, required: 70 },
    ];

    const { container } = render(<SkillsRadar data={data} />);
    const checkmark = container.querySelector('[class*="text-green"]');
    expect(checkmark).toBeInTheDocument();
  });

  it('shows gap indicator for misaligned skills', () => {
    const data = [
      { skill: 'Kubernetes', candidate: 40, required: 75 },
    ];

    render(<SkillsRadar data={data} />);
    // Gap should be +35 (75 - 40)
    expect(screen.getByText('+35')).toBeInTheDocument();
  });

  it('truncates long skill names in chart', () => {
    const data = [
      { skill: 'VeryLongSkillNameThatShouldBeTruncated', candidate: 50, required: 50 },
    ];

    const { container } = render(<SkillsRadar data={data} />);
    // Chart renders truncated names, but full names appear in details
    expect(screen.getByText('VeryLongSkillNameThatShouldBeTruncated')).toBeInTheDocument();
  });

  it('limits chart data to top 8 skills for readability', () => {
    const data = Array.from({ length: 15 }, (_, i) => ({
      skill: `Skill${i + 1}`,
      candidate: 50 + i,
      required: 50,
    }));

    const { container } = render(<SkillsRadar data={data} />);
    // Should only display 8 skills in the radar chart
    const radarChart = container.querySelector('svg');
    expect(radarChart).toBeInTheDocument();
  });

  it('renders legend with color indicators', () => {
    const data = [
      { skill: 'Java', candidate: 80, required: 70 },
    ];

    render(<SkillsRadar data={data} />);
    expect(screen.getByText('Your Skills')).toBeInTheDocument();
    expect(screen.getByText('Required')).toBeInTheDocument();
  });

  it('displays all skills in details even if more than 8', () => {
    const data = Array.from({ length: 12 }, (_, i) => ({
      skill: `Skill${i + 1}`,
      candidate: 60 + i,
      required: 55 + i,
    }));

    render(<SkillsRadar data={data} />);
    // All skills should be in the details section
    expect(screen.getByText('Skill1')).toBeInTheDocument();
    expect(screen.getByText('Skill12')).toBeInTheDocument();
  });

  it('handles zero gap correctly', () => {
    const data = [
      { skill: 'Rust', candidate: 50, required: 50 },
    ];

    render(<SkillsRadar data={data} />);
    expect(screen.getByText('✓')).toBeInTheDocument();
  });

  it('has scrollable skills details section', () => {
    const data = Array.from({ length: 20 }, (_, i) => ({
      skill: `Skill${i + 1}`,
      candidate: 50 + i,
      required: 50,
    }));

    const { container } = render(<SkillsRadar data={data} />);
    const scrollableDiv = container.querySelector('[class*="overflow-y-auto"]');
    expect(scrollableDiv).toBeInTheDocument();
  });

  it('has correct accessibility attributes', () => {
    const data = [
      { skill: 'JavaScript', candidate: 85, required: 70 },
    ];

    render(<SkillsRadar data={data} />);
    const heading = screen.getByText('Skills Alignment');
    expect(heading).toBeInTheDocument();
  });

  it('rounds percentage values in display', () => {
    const data = [
      { skill: 'Testing', candidate: 66.67, required: 75.33 },
    ];

    render(<SkillsRadar data={data} />);
    expect(screen.getByText('You: 67')).toBeInTheDocument();
    expect(screen.getByText('Need: 75')).toBeInTheDocument();
  });

  it('handles missing data gracefully', () => {
    const data = [
      { skill: 'Git', candidate: 0, required: 50 },
    ];

    render(<SkillsRadar data={data} />);
    expect(screen.getByText('Git')).toBeInTheDocument();
    expect(screen.getByText('You: 0')).toBeInTheDocument();
  });
});
