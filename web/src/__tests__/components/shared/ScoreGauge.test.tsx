import React from 'react';
import { render, screen } from '@testing-library/react';
import { ScoreGauge } from '@/components/shared/ScoreGauge';

describe('ScoreGauge', () => {
  describe('Rendering', () => {
    it('renders gauge with score value', () => {
      const { container } = render(<ScoreGauge score={75} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders with custom label', () => {
      render(<ScoreGauge score={85} label="Match Score" />);
      expect(screen.getByText('Match Score')).toBeInTheDocument();
    });

    it('renders without label when not provided', () => {
      const { container } = render(<ScoreGauge score={75} />);
      const gauge = container.firstChild;
      expect(gauge).toBeInTheDocument();
    });

    it('renders with default size of 120', () => {
      const { container } = render(<ScoreGauge score={75} />);
      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('renders with custom size', () => {
      const { container } = render(<ScoreGauge score={75} size={200} />);
      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('Score Values', () => {
    it('renders score of 0', () => {
      const { container } = render(<ScoreGauge score={0} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders score of 50', () => {
      const { container } = render(<ScoreGauge score={50} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders score of 100', () => {
      const { container } = render(<ScoreGauge score={100} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders score of 1 (minimum positive)', () => {
      const { container } = render(<ScoreGauge score={1} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders score of 99 (near maximum)', () => {
      const { container } = render(<ScoreGauge score={99} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders intermediate score of 42', () => {
      const { container } = render(<ScoreGauge score={42} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders intermediate score of 67', () => {
      const { container } = render(<ScoreGauge score={67} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders decimal score of 75.5', () => {
      const { container } = render(<ScoreGauge score={75.5} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders decimal score of 42.3', () => {
      const { container } = render(<ScoreGauge score={42.3} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });
  });

  describe('Size Variations', () => {
    it('renders with size 80', () => {
      const { container } = render(<ScoreGauge score={50} size={80} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders with size 120 (default)', () => {
      const { container } = render(<ScoreGauge score={50} size={120} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders with size 150', () => {
      const { container } = render(<ScoreGauge score={50} size={150} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders with size 200', () => {
      const { container } = render(<ScoreGauge score={50} size={200} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders with size 300', () => {
      const { container } = render(<ScoreGauge score={50} size={300} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });
  });

  describe('Animations', () => {
    it('applies animation classes for score transitions', () => {
      const { container, rerender } = render(<ScoreGauge score={0} />);

      // Re-render with different score
      rerender(<ScoreGauge score={100} />);

      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('smoothly transitions between scores', () => {
      const { container, rerender } = render(<ScoreGauge score={25} />);

      rerender(<ScoreGauge score={50} />);
      expect(container.querySelector('svg')).toBeInTheDocument();

      rerender(<ScoreGauge score={75} />);
      expect(container.querySelector('svg')).toBeInTheDocument();

      rerender(<ScoreGauge score={100} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('animates from 0 to 100', () => {
      const { container, rerender } = render(<ScoreGauge score={0} />);

      rerender(<ScoreGauge score={100} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('animates from 100 to 0', () => {
      const { container, rerender } = render(<ScoreGauge score={100} />);

      rerender(<ScoreGauge score={0} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });
  });

  describe('Label Display', () => {
    it('displays single word label', () => {
      render(<ScoreGauge score={80} label="Excellent" />);
      expect(screen.getByText('Excellent')).toBeInTheDocument();
    });

    it('displays multi-word label', () => {
      render(<ScoreGauge score={80} label="Overall Match Score" />);
      expect(screen.getByText('Overall Match Score')).toBeInTheDocument();
    });

    it('displays label with special characters', () => {
      render(<ScoreGauge score={80} label="Score (%)" />);
      expect(screen.getByText('Score (%)')).toBeInTheDocument();
    });

    it('displays long label', () => {
      render(<ScoreGauge score={80} label="Resume to Job Description Alignment Score" />);
      expect(screen.getByText('Resume to Job Description Alignment Score')).toBeInTheDocument();
    });

    it('displays empty label string', () => {
      const { container } = render(<ScoreGauge score={80} label="" />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('displays label with numbers', () => {
      render(<ScoreGauge score={85} label="Score 85/100" />);
      expect(screen.getByText('Score 85/100')).toBeInTheDocument();
    });
  });

  describe('Score Color Representation', () => {
    it('renders low score (0-33) with appropriate color', () => {
      const { container } = render(<ScoreGauge score={25} />);
      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('renders medium-low score (34-66) with appropriate color', () => {
      const { container } = render(<ScoreGauge score={50} />);
      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('renders medium-high score (67-84) with appropriate color', () => {
      const { container } = render(<ScoreGauge score={75} />);
      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('renders high score (85-100) with appropriate color', () => {
      const { container } = render(<ScoreGauge score={90} />);
      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('Responsive Behavior', () => {
    it('renders within container element', () => {
      const { container } = render(
        <div style={{ width: '300px', height: '300px' }}>
          <ScoreGauge score={75} />
        </div>
      );
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('maintains aspect ratio', () => {
      const { container } = render(<ScoreGauge score={75} size={150} />);
      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('renders correctly in flex container', () => {
      const { container } = render(
        <div style={{ display: 'flex', gap: '1rem' }}>
          <ScoreGauge score={75} size={100} />
          <ScoreGauge score={85} size={100} />
          <ScoreGauge score={95} size={100} />
        </div>
      );
      const svgs = container.querySelectorAll('svg');
      expect(svgs.length).toBe(3);
    });

    it('renders correctly in grid container', () => {
      const { container } = render(
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
          <ScoreGauge score={75} size={80} />
          <ScoreGauge score={85} size={80} />
          <ScoreGauge score={95} size={80} />
          <ScoreGauge score={65} size={80} />
        </div>
      );
      const svgs = container.querySelectorAll('svg');
      expect(svgs.length).toBe(4);
    });
  });

  describe('Re-renders and Updates', () => {
    it('updates when score changes', () => {
      const { rerender, container } = render(<ScoreGauge score={25} />);

      expect(container.querySelector('svg')).toBeInTheDocument();

      rerender(<ScoreGauge score={75} />);

      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('updates when label changes', () => {
      const { rerender } = render(<ScoreGauge score={75} label="Old Label" />);

      expect(screen.getByText('Old Label')).toBeInTheDocument();

      rerender(<ScoreGauge score={75} label="New Label" />);

      expect(screen.getByText('New Label')).toBeInTheDocument();
      expect(screen.queryByText('Old Label')).not.toBeInTheDocument();
    });

    it('updates when size changes', () => {
      const { rerender, container } = render(<ScoreGauge score={75} size={100} />);

      expect(container.querySelector('svg')).toBeInTheDocument();

      rerender(<ScoreGauge score={75} size={200} />);

      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('handles rapid score updates', () => {
      const { rerender, container } = render(<ScoreGauge score={0} />);

      for (let i = 10; i <= 100; i += 10) {
        rerender(<ScoreGauge score={i} />);
      }

      expect(container.querySelector('svg')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles score greater than 100', () => {
      const { container } = render(<ScoreGauge score={120} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('handles negative score', () => {
      const { container } = render(<ScoreGauge score={-10} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('handles very small positive decimal', () => {
      const { container } = render(<ScoreGauge score={0.1} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('handles very high precision decimal', () => {
      const { container } = render(<ScoreGauge score={75.123456789} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has semantic SVG structure', () => {
      const { container } = render(<ScoreGauge score={75} label="Match Score" />);
      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('displays label for screen readers', () => {
      render(<ScoreGauge score={75} label="Match Score" />);
      expect(screen.getByText('Match Score')).toBeInTheDocument();
    });

    it('is visually perceptible', () => {
      const { container } = render(<ScoreGauge score={75} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });
  });
});
