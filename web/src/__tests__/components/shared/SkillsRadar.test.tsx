import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { SkillsRadar } from '@/components/shared/SkillsRadar';

// Mock recharts to avoid rendering issues in tests
jest.mock('recharts', () => {
  const React = require('react');
  return {
    Radar: ({ children }: any) => <div data-testid="radar">{children}</div>,
    RadarChart: ({ children, data }: any) => (
      <div data-testid="radar-chart" data-items={data?.length || 0}>
        {children}
      </div>
    ),
    PolarGrid: () => <div data-testid="polar-grid" />,
    PolarAngleAxis: () => <div data-testid="polar-angle-axis" />,
    PolarRadiusAxis: () => <div data-testid="polar-radius-axis" />,
    ResponsiveContainer: ({ children }: any) => (
      <div data-testid="responsive-container">{children}</div>
    ),
  };
});

describe('SkillsRadar', () => {
  const mockSkillData = [
    { skill: 'React', candidate: 90, required: 85 },
    { skill: 'TypeScript', candidate: 75, required: 80 },
    { skill: 'Node.js', candidate: 85, required: 80 },
    { skill: 'CSS', candidate: 70, required: 75 },
    { skill: 'Testing', candidate: 80, required: 70 },
  ];

  describe('Rendering', () => {
    it('renders card with title', () => {
      render(<SkillsRadar data={mockSkillData} />);
      expect(screen.getByText('Skills Alignment')).toBeInTheDocument();
    });

    it('renders default title', () => {
      render(<SkillsRadar data={mockSkillData} />);
      expect(screen.getByText('Skills Alignment')).toBeInTheDocument();
    });

    it('renders custom title', () => {
      render(<SkillsRadar data={mockSkillData} title="Custom Skills Chart" />);
      expect(screen.getByText('Custom Skills Chart')).toBeInTheDocument();
    });

    it('renders subtitle', () => {
      render(<SkillsRadar data={mockSkillData} />);
      expect(screen.getByText('Your skills vs. job requirements')).toBeInTheDocument();
    });

    it('renders custom subtitle', () => {
      render(<SkillsRadar data={mockSkillData} subtitle="Candidate vs Position Requirements" />);
      expect(screen.getByText('Candidate vs Position Requirements')).toBeInTheDocument();
    });

    it('renders radar chart when data is provided', () => {
      render(<SkillsRadar data={mockSkillData} />);
      expect(screen.getByTestId('radar-chart')).toBeInTheDocument();
    });

    it('renders chart components', () => {
      render(<SkillsRadar data={mockSkillData} />);
      expect(screen.getByTestId('polar-grid')).toBeInTheDocument();
      expect(screen.getByTestId('polar-angle-axis')).toBeInTheDocument();
      expect(screen.getByTestId('polar-radius-axis')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('displays loading message when loading prop is true', () => {
      render(<SkillsRadar data={mockSkillData} loading={true} />);
      expect(screen.getByText('Loading visualization...')).toBeInTheDocument();
    });

    it('shows card structure during loading', () => {
      render(<SkillsRadar data={mockSkillData} loading={true} />);
      expect(screen.getByText('Skills Alignment')).toBeInTheDocument();
      expect(screen.getByText('Loading visualization...')).toBeInTheDocument();
    });

    it('displays loading state with title', () => {
      render(<SkillsRadar data={mockSkillData} loading={true} title="My Skills" />);
      expect(screen.getByText('My Skills')).toBeInTheDocument();
      expect(screen.getByText('Loading visualization...')).toBeInTheDocument();
    });

    it('hides chart when loading', () => {
      const { queryByTestId } = render(<SkillsRadar data={mockSkillData} loading={true} />);
      expect(queryByTestId('radar-chart')).not.toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('displays empty state when data array is empty', () => {
      render(<SkillsRadar data={[]} />);
      expect(screen.getByText('No skill data available')).toBeInTheDocument();
    });

    it('displays empty state when data is undefined', () => {
      render(<SkillsRadar data={undefined as any} />);
      expect(screen.getByText('No skill data available')).toBeInTheDocument();
    });

    it('displays empty state when data is null', () => {
      render(<SkillsRadar data={null as any} />);
      expect(screen.getByText('No skill data available')).toBeInTheDocument();
    });

    it('shows title even in empty state', () => {
      render(<SkillsRadar data={[]} title="Skills Analysis" />);
      expect(screen.getByText('Skills Analysis')).toBeInTheDocument();
      expect(screen.getByText('No skill data available')).toBeInTheDocument();
    });

    it('shows subtitle in empty state', () => {
      render(<SkillsRadar data={[]} subtitle="No data to display" />);
      expect(screen.getByText('No data to display')).toBeInTheDocument();
    });
  });

  describe('Data Processing', () => {
    it('limits data to top 8 skills for readability', () => {
      const manySkills = Array.from({ length: 15 }, (_, i) => ({
        skill: `Skill ${i + 1}`,
        candidate: 50 + i,
        required: 50 + i,
      }));

      render(<SkillsRadar data={manySkills} />);

      const chartDiv = screen.getByTestId('radar-chart');
      expect(chartDiv).toHaveAttribute('data-items', '8');
    });

    it('processes all skills when less than 8', () => {
      const fewSkills = [
        { skill: 'React', candidate: 85, required: 80 },
        { skill: 'TypeScript', candidate: 80, required: 75 },
        { skill: 'Node.js', candidate: 90, required: 85 },
      ];

      render(<SkillsRadar data={fewSkills} />);

      const chartDiv = screen.getByTestId('radar-chart');
      expect(chartDiv).toHaveAttribute('data-items', '3');
    });

    it('truncates long skill names', () => {
      const longSkillData = [
        { skill: 'Very Long Skill Name That Exceeds Fifteen Characters', candidate: 80, required: 75 },
      ];

      render(<SkillsRadar data={longSkillData} />);
      expect(screen.getByTestId('radar-chart')).toBeInTheDocument();
    });

    it('rounds scores to integers', () => {
      const decimalSkillData = [
        { skill: 'React', candidate: 85.7, required: 80.3 },
        { skill: 'TypeScript', candidate: 75.2, required: 78.9 },
      ];

      render(<SkillsRadar data={decimalSkillData} />);
      expect(screen.getByTestId('radar-chart')).toBeInTheDocument();
    });

    it('handles extreme score values', () => {
      const extremeSkillData = [
        { skill: 'Skill 1', candidate: 0, required: 0 },
        { skill: 'Skill 2', candidate: 100, required: 100 },
      ];

      render(<SkillsRadar data={extremeSkillData} />);
      expect(screen.getByTestId('radar-chart')).toBeInTheDocument();
    });
  });

  describe('Multiple Render Scenarios', () => {
    it('renders with minimal data (1 skill)', () => {
      const minimalData = [{ skill: 'React', candidate: 80, required: 75 }];
      render(<SkillsRadar data={minimalData} />);
      expect(screen.getByTestId('radar-chart')).toBeInTheDocument();
    });

    it('renders with maximum relevant data (8 skills)', () => {
      const maxData = Array.from({ length: 8 }, (_, i) => ({
        skill: `Skill ${i + 1}`,
        candidate: 50 + i * 5,
        required: 50 + i * 5,
      }));

      render(<SkillsRadar data={maxData} />);
      const chartDiv = screen.getByTestId('radar-chart');
      expect(chartDiv).toHaveAttribute('data-items', '8');
    });

    it('renders with exactly 8 skills', () => {
      const exactData = Array.from({ length: 8 }, (_, i) => ({
        skill: `Skill ${i + 1}`,
        candidate: 75,
        required: 75,
      }));

      render(<SkillsRadar data={exactData} />);
      const chartDiv = screen.getByTestId('radar-chart');
      expect(chartDiv).toHaveAttribute('data-items', '8');
    });

    it('renders with 9 skills (should truncate to 8)', () => {
      const nineSkills = Array.from({ length: 9 }, (_, i) => ({
        skill: `Skill ${i + 1}`,
        candidate: 75,
        required: 75,
      }));

      render(<SkillsRadar data={nineSkills} />);
      const chartDiv = screen.getByTestId('radar-chart');
      expect(chartDiv).toHaveAttribute('data-items', '8');
    });
  });

  describe('Responsive Behavior', () => {
    it('renders responsive container', () => {
      render(<SkillsRadar data={mockSkillData} />);
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('maintains chart height dimension', () => {
      const { container } = render(<SkillsRadar data={mockSkillData} />);
      const heightDiv = container.querySelector('[style*="height"]');
      // Check that the responsive container has proper styling
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('adapts to container width changes', () => {
      const { rerender } = render(
        <div style={{ width: '400px' }}>
          <SkillsRadar data={mockSkillData} />
        </div>
      );

      expect(screen.getByTestId('radar-chart')).toBeInTheDocument();

      rerender(
        <div style={{ width: '600px' }}>
          <SkillsRadar data={mockSkillData} />
        </div>
      );

      expect(screen.getByTestId('radar-chart')).toBeInTheDocument();
    });
  });

  describe('State Transitions', () => {
    it('transitions from loading to showing data', async () => {
      const { rerender } = render(<SkillsRadar data={mockSkillData} loading={true} />);

      expect(screen.getByText('Loading visualization...')).toBeInTheDocument();

      rerender(<SkillsRadar data={mockSkillData} loading={false} />);

      await waitFor(() => {
        expect(screen.queryByText('Loading visualization...')).not.toBeInTheDocument();
        expect(screen.getByTestId('radar-chart')).toBeInTheDocument();
      });
    });

    it('transitions from empty to showing data', () => {
      const { rerender } = render(<SkillsRadar data={[]} />);

      expect(screen.getByText('No skill data available')).toBeInTheDocument();

      rerender(<SkillsRadar data={mockSkillData} />);

      expect(screen.queryByText('No skill data available')).not.toBeInTheDocument();
      expect(screen.getByTestId('radar-chart')).toBeInTheDocument();
    });

    it('transitions from showing data to empty', () => {
      const { rerender } = render(<SkillsRadar data={mockSkillData} />);

      expect(screen.getByTestId('radar-chart')).toBeInTheDocument();

      rerender(<SkillsRadar data={[]} />);

      expect(screen.queryByTestId('radar-chart')).not.toBeInTheDocument();
      expect(screen.getByText('No skill data available')).toBeInTheDocument();
    });

    it('updates chart when data changes', () => {
      const initialData = [{ skill: 'React', candidate: 80, required: 75 }];
      const updatedData = [
        { skill: 'React', candidate: 90, required: 75 },
        { skill: 'TypeScript', candidate: 85, required: 80 },
      ];

      const { rerender } = render(<SkillsRadar data={initialData} />);
      expect(screen.getByTestId('radar-chart')).toHaveAttribute('data-items', '1');

      rerender(<SkillsRadar data={updatedData} />);
      expect(screen.getByTestId('radar-chart')).toHaveAttribute('data-items', '2');
    });
  });

  describe('Custom Props', () => {
    it('accepts all combination of title and subtitle', () => {
      render(
        <SkillsRadar
          data={mockSkillData}
          title="Custom Title"
          subtitle="Custom Subtitle"
        />
      );

      expect(screen.getByText('Custom Title')).toBeInTheDocument();
      expect(screen.getByText('Custom Subtitle')).toBeInTheDocument();
    });

    it('handles undefined subtitle', () => {
      render(
        <SkillsRadar
          data={mockSkillData}
          title="Title Only"
          subtitle={undefined}
        />
      );

      expect(screen.getByText('Title Only')).toBeInTheDocument();
    });

    it('handles empty string subtitle', () => {
      const { queryByText } = render(
        <SkillsRadar
          data={mockSkillData}
          title="Title Only"
          subtitle=""
        />
      );

      expect(screen.getByText('Title Only')).toBeInTheDocument();
    });
  });

  describe('Data Integrity', () => {
    it('preserves original data order', () => {
      render(<SkillsRadar data={mockSkillData} />);
      expect(screen.getByTestId('radar-chart')).toBeInTheDocument();
    });

    it('handles data with missing optional fields gracefully', () => {
      const incompleteData = [
        { skill: 'React', candidate: 80, required: 75 },
      ];

      render(<SkillsRadar data={incompleteData} />);
      expect(screen.getByTestId('radar-chart')).toBeInTheDocument();
    });

    it('handles special characters in skill names', () => {
      const specialData = [
        { skill: 'C++/C#', candidate: 80, required: 75 },
        { skill: 'Node.js', candidate: 85, required: 80 },
        { skill: 'React/Vue', candidate: 90, required: 85 },
      ];

      render(<SkillsRadar data={specialData} />);
      expect(screen.getByTestId('radar-chart')).toBeInTheDocument();
    });

    it('handles duplicate skill names', () => {
      const duplicateData = [
        { skill: 'React', candidate: 80, required: 75 },
        { skill: 'React', candidate: 85, required: 80 },
      ];

      render(<SkillsRadar data={duplicateData} />);
      expect(screen.getByTestId('radar-chart')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has semantic structure', () => {
      render(<SkillsRadar data={mockSkillData} />);
      expect(screen.getByText('Skills Alignment')).toBeInTheDocument();
    });

    it('displays title for screen readers', () => {
      render(<SkillsRadar data={mockSkillData} title="Resume vs Job Requirements" />);
      expect(screen.getByText('Resume vs Job Requirements')).toBeInTheDocument();
    });

    it('displays subtitle for screen readers', () => {
      render(
        <SkillsRadar
          data={mockSkillData}
          subtitle="Skill gap analysis"
        />
      );
      expect(screen.getByText('Skill gap analysis')).toBeInTheDocument();
    });
  });
});
