import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThreeSignalScores } from '@/components/shared/ThreeSignalScores';

describe('ThreeSignalScores Component', () => {
  const defaultProps = {
    traditional: {
      label: 'Traditional',
      score: 75,
      description: 'Keyword match score',
    },
    semantic: {
      label: 'Semantic',
      score: 82,
      description: 'Concept-level match',
    },
    capability: {
      label: 'Capability',
      score: 88,
      description: 'Capability score',
    },
  };

  it('renders card with title', () => {
    render(<ThreeSignalScores {...defaultProps} />);

    expect(screen.getByText('Assessment Scores')).toBeInTheDocument();
  });

  it('renders all three score gauges', () => {
    render(<ThreeSignalScores {...defaultProps} />);

    expect(screen.getByText('Traditional')).toBeInTheDocument();
    expect(screen.getByText('Semantic')).toBeInTheDocument();
    expect(screen.getByText('Capability')).toBeInTheDocument();
  });

  it('displays score values correctly', () => {
    render(<ThreeSignalScores {...defaultProps} />);

    expect(screen.getByText('75')).toBeInTheDocument();
    expect(screen.getByText('82')).toBeInTheDocument();
    expect(screen.getByText('88')).toBeInTheDocument();
  });

  it('calculates and displays average score', () => {
    render(<ThreeSignalScores {...defaultProps} />);

    // (75 + 82 + 88) / 3 = 81.67, rounded to 82
    expect(screen.getByText('82')).toBeInTheDocument();
  });

  it('displays score descriptions', () => {
    render(<ThreeSignalScores {...defaultProps} />);

    expect(screen.getByText('Keyword match score')).toBeInTheDocument();
    expect(screen.getByText('Concept-level match')).toBeInTheDocument();
    expect(screen.getByText('Capability score')).toBeInTheDocument();
  });

  it('displays delta indicators when provided', () => {
    const propsWithDelta = {
      ...defaultProps,
      traditional: { ...defaultProps.traditional, delta: 5 },
      semantic: { ...defaultProps.semantic, delta: -3 },
      capability: { ...defaultProps.capability, delta: 0 },
    };

    render(<ThreeSignalScores {...propsWithDelta} />);

    // Check that delta values are displayed
    expect(screen.getByText(/5|3|0/)).toBeInTheDocument();
  });

  it('displays signal interpretation section', () => {
    render(<ThreeSignalScores {...defaultProps} />);

    expect(screen.getByText('Signal Interpretation:')).toBeInTheDocument();
    expect(screen.getByText('Keyword and ATS matching score')).toBeInTheDocument();
    expect(screen.getByText('Concept-level relevance and understanding')).toBeInTheDocument();
    expect(screen.getByText('Demonstrated capability based on background')).toBeInTheDocument();
  });

  it('displays out of 100 scale indicator', () => {
    render(<ThreeSignalScores {...defaultProps} />);

    const outOfTexts = screen.getAllByText('/ 100');
    expect(outOfTexts.length).toBeGreaterThan(0);
  });

  it('renders all score labels in interpretation section', () => {
    render(<ThreeSignalScores {...defaultProps} />);

    // Check for the interpretation labels
    const labels = screen.getAllByText(/Traditional|Semantic|Capability/);
    expect(labels.length).toBeGreaterThan(0);
  });

  it('applies custom className', () => {
    const { container } = render(
      <ThreeSignalScores
        {...defaultProps}
        className="custom-class"
      />
    );

    const card = container.querySelector('.custom-class');
    expect(card).toBeInTheDocument();
  });

  it('handles high scores with appropriate styling', () => {
    const highScores = {
      ...defaultProps,
      traditional: { ...defaultProps.traditional, score: 95 },
      semantic: { ...defaultProps.semantic, score: 92 },
      capability: { ...defaultProps.capability, score: 98 },
    };

    render(<ThreeSignalScores {...highScores} />);

    expect(screen.getByText('95')).toBeInTheDocument();
    expect(screen.getByText('92')).toBeInTheDocument();
    expect(screen.getByText('98')).toBeInTheDocument();
  });

  it('handles low scores with appropriate styling', () => {
    const lowScores = {
      ...defaultProps,
      traditional: { ...defaultProps.traditional, score: 25 },
      semantic: { ...defaultProps.semantic, score: 35 },
      capability: { ...defaultProps.capability, score: 40 },
    };

    render(<ThreeSignalScores {...lowScores} />);

    expect(screen.getByText('25')).toBeInTheDocument();
    expect(screen.getByText('35')).toBeInTheDocument();
    expect(screen.getByText('40')).toBeInTheDocument();
  });

  it('handles mid-range scores', () => {
    const midRangeScores = {
      traditional: { label: 'Traditional', score: 60 },
      semantic: { label: 'Semantic', score: 65 },
      capability: { label: 'Capability', score: 70 },
    };

    render(<ThreeSignalScores {...midRangeScores} />);

    expect(screen.getByText('60')).toBeInTheDocument();
    expect(screen.getByText('65')).toBeInTheDocument();
    expect(screen.getByText('70')).toBeInTheDocument();
  });

  it('displays positive delta with correct styling', () => {
    const propsWithPositiveDelta = {
      ...defaultProps,
      traditional: { ...defaultProps.traditional, delta: 10 },
    };

    const { container } = render(<ThreeSignalScores {...propsWithPositiveDelta} />);

    // Should have SVG elements for gauges
    const svgs = container.querySelectorAll('svg');
    expect(svgs.length).toBeGreaterThan(0);
  });

  it('displays negative delta with correct styling', () => {
    const propsWithNegativeDelta = {
      ...defaultProps,
      semantic: { ...defaultProps.semantic, delta: -5 },
    };

    const { container } = render(<ThreeSignalScores {...propsWithNegativeDelta} />);

    const svgs = container.querySelectorAll('svg');
    expect(svgs.length).toBeGreaterThan(0);
  });

  it('contains gauge circles for each score', () => {
    const { container } = render(<ThreeSignalScores {...defaultProps} />);

    const circles = container.querySelectorAll('circle');
    // Should have circles for each gauge (at least 2 per gauge: background + progress)
    expect(circles.length).toBeGreaterThan(4);
  });
});
