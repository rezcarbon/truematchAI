import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import QualityScoreGauge from '@/components/JDOptimizer/QualityScoreGauge';

describe('QualityScoreGauge', () => {
  it('renders with score 0', () => {
    render(<QualityScoreGauge score={0} />);
    expect(screen.getByText('Score')).toBeInTheDocument();
  });

  it('animates from 0 to target score', async () => {
    const { rerender } = render(<QualityScoreGauge score={0} />);

    // Initial render shows 0
    expect(screen.getByText('0')).toBeInTheDocument();

    // Update to 85
    rerender(<QualityScoreGauge score={85} />);

    // Wait for animation to complete
    await waitFor(
      () => {
        expect(screen.getByText('85')).toBeInTheDocument();
      },
      { timeout: 2000 }
    );
  });

  it('displays correct quality label for excellent score', async () => {
    render(<QualityScoreGauge score={85} />);

    await waitFor(() => {
      expect(screen.getByText('Excellent')).toBeInTheDocument();
    });
  });

  it('displays correct quality label for good score', async () => {
    render(<QualityScoreGauge score={70} />);

    await waitFor(() => {
      expect(screen.getByText('Good')).toBeInTheDocument();
    });
  });

  it('displays correct quality label for fair score', async () => {
    render(<QualityScoreGauge score={50} />);

    await waitFor(() => {
      expect(screen.getByText('Fair')).toBeInTheDocument();
    });
  });

  it('displays correct quality label for poor score', async () => {
    render(<QualityScoreGauge score={30} />);

    await waitFor(() => {
      expect(screen.getByText('Needs Improvement')).toBeInTheDocument();
    });
  });

  it('displays perfect score message', async () => {
    render(<QualityScoreGauge score={100} />);

    await waitFor(() => {
      expect(screen.getByText('Perfect job description!')).toBeInTheDocument();
    });
  });

  it('displays minor improvements message', async () => {
    render(<QualityScoreGauge score={90} />);

    await waitFor(() => {
      expect(screen.getByText('Minor improvements available')).toBeInTheDocument();
    });
  });

  it('displays some improvements message', async () => {
    render(<QualityScoreGauge score={70} />);

    await waitFor(() => {
      expect(screen.getByText('Some improvements recommended')).toBeInTheDocument();
    });
  });

  it('displays several improvements message', async () => {
    render(<QualityScoreGauge score={50} />);

    await waitFor(() => {
      expect(screen.getByText('Several improvements needed')).toBeInTheDocument();
    });
  });

  it('displays significant improvements message', async () => {
    render(<QualityScoreGauge score={30} />);

    await waitFor(() => {
      expect(screen.getByText('Significant improvements needed')).toBeInTheDocument();
    });
  });

  it('handles multiple score updates', async () => {
    const { rerender } = render(<QualityScoreGauge score={20} />);

    await waitFor(() => {
      expect(screen.getByText('20')).toBeInTheDocument();
    });

    rerender(<QualityScoreGauge score={60} />);

    await waitFor(() => {
      expect(screen.getByText('60')).toBeInTheDocument();
    });

    rerender(<QualityScoreGauge score={95} />);

    await waitFor(() => {
      expect(screen.getByText('95')).toBeInTheDocument();
    });
  });

  it('renders SVG circle for visual gauge', () => {
    const { container } = render(<QualityScoreGauge score={75} />);
    const circles = container.querySelectorAll('circle');
    // Should have at least 2 circles (background and progress)
    expect(circles.length).toBeGreaterThanOrEqual(2);
  });
});
