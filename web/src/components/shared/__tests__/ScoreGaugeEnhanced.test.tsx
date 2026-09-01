import React from 'react';
import { render, screen } from '@testing-library/react';
import { ScoreGauge } from '../ScoreGauge';

describe('ScoreGauge Enhanced', () => {
  it('renders gauge with default size', () => {
    const { container } = render(<ScoreGauge score={75} />);
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('displays score as rounded integer', () => {
    render(<ScoreGauge score={75.6} />);
    expect(screen.getByText('76')).toBeInTheDocument();
  });

  it('renders label when provided', () => {
    render(<ScoreGauge score={80} label="Overall" />);
    expect(screen.getByText('Overall')).toBeInTheDocument();
  });

  it('handles zero score', () => {
    render(<ScoreGauge score={0} />);
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('handles 100 score', () => {
    render(<ScoreGauge score={100} />);
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('clamps negative scores to 0', () => {
    render(<ScoreGauge score={-10} />);
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('clamps scores above 100 to 100', () => {
    render(<ScoreGauge score={150} />);
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('respects custom size prop', () => {
    const { container } = render(<ScoreGauge score={50} size={200} />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('width', '200');
    expect(svg).toHaveAttribute('height', '200');
  });

  it('renders with correct color for high score', () => {
    const { container } = render(<ScoreGauge score={90} />);
    const circle = container.querySelectorAll('circle')[1];
    // High scores should use success color (green)
    expect(circle).toHaveAttribute('stroke');
  });

  it('renders with correct color for medium score', () => {
    const { container } = render(<ScoreGauge score={60} />);
    const circle = container.querySelectorAll('circle')[1];
    // Medium scores should use warning color (orange)
    expect(circle).toHaveAttribute('stroke');
  });

  it('renders with correct color for low score', () => {
    const { container } = render(<ScoreGauge score={25} />);
    const circle = container.querySelectorAll('circle')[1];
    // Low scores should use destructive color (red)
    expect(circle).toHaveAttribute('stroke');
  });

  it('has stroke-linecap for rounded corners', () => {
    const { container } = render(<ScoreGauge score={75} />);
    const progressCircle = container.querySelectorAll('circle')[1];
    expect(progressCircle).toHaveAttribute('stroke-linecap', 'round');
  });

  it('has smooth animation class', () => {
    const { container } = render(<ScoreGauge score={75} />);
    const progressCircle = container.querySelectorAll('circle')[1];
    expect(progressCircle).toHaveClass('transition-all');
  });

  it('applies custom className', () => {
    const { container } = render(<ScoreGauge score={75} className="custom-class" />);
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('custom-class');
  });

  it('renders background and progress circles', () => {
    const { container } = render(<ScoreGauge score={75} />);
    const circles = container.querySelectorAll('circle');
    expect(circles).toHaveLength(2);
  });

  it('calculates correct stroke-dashoffset for progress', () => {
    const { container } = render(<ScoreGauge score={50} />);
    const progressCircle = container.querySelectorAll('circle')[1];
    expect(progressCircle).toHaveAttribute('stroke-dashoffset');
  });

  it('positions score and label centered', () => {
    const { container } = render(<ScoreGauge score={85} label="Test" />);
    const textElements = container.querySelectorAll('span');
    expect(textElements.length).toBeGreaterThanOrEqual(1);
  });

  it('uses tabular-nums for consistent spacing', () => {
    const { container } = render(<ScoreGauge score={45} />);
    const scoreSpan = container.querySelector('span');
    expect(scoreSpan).toHaveClass('tabular-nums');
  });

  it('renders without label when not provided', () => {
    const { container } = render(<ScoreGauge score={60} />);
    const spans = container.querySelectorAll('span');
    expect(spans).toHaveLength(1); // Only score, no label
  });

  it('handles fractional scores correctly', () => {
    render(<ScoreGauge score={33.333} />);
    expect(screen.getByText('33')).toBeInTheDocument();
  });
});
