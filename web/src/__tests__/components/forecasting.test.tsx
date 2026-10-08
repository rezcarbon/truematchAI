import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PipelineForecastChart } from '@/components/forecasting/PipelineForecastChart';
import { PositionForecastCard } from '@/components/forecasting/PositionForecastCard';

describe('PipelineForecastChart', () => {
  const mockForecasts = [
    {
      position_id: '1',
      position_title: 'Senior Engineer',
      forecasted_fill_date: '2026-11-15',
      estimated_days_to_fill: 30,
      confidence: 0.85,
      bottleneck_stage: 'interview',
      recommendations: ['Increase interview slots', 'Reach out to passive candidates'],
    },
    {
      position_id: '2',
      position_title: 'Product Manager',
      forecasted_fill_date: '2026-11-25',
      estimated_days_to_fill: 45,
      confidence: 0.72,
      bottleneck_stage: 'screening',
      recommendations: ['Improve job description', 'Expand sourcing channels'],
    },
  ];

  it('renders loading state', () => {
    render(<PipelineForecastChart forecasts={[]} isLoading={true} />);
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders forecast data', () => {
    render(<PipelineForecastChart forecasts={mockForecasts} />);
    expect(screen.getByText('Pipeline Forecast - Days to Fill')).toBeInTheDocument();
  });

  it('handles position click', () => {
    const handleClick = jest.fn();
    render(<PipelineForecastChart forecasts={mockForecasts} onPositionClick={handleClick} />);
    // Click on position card
    const cards = screen.getAllByText(/days/i);
    fireEvent.click(cards[0]);
  });
});

describe('PositionForecastCard', () => {
  const mockProps = {
    positionTitle: 'Senior Engineer',
    positionId: 'pos-1',
    estimatedDaysToFill: 30,
    forecastedFillDate: '2026-11-15',
    confidence: 0.85,
    bottleneckStage: 'interview',
    recommendations: ['Increase slots', 'Reach out to passives'],
    applicationCount: 25,
  };

  it('renders position details', () => {
    render(<PositionForecastCard {...mockProps} />);
    expect(screen.getByText('Senior Engineer')).toBeInTheDocument();
    expect(screen.getByText('30')).toBeInTheDocument();
    expect(screen.getByText('85% Confidence')).toBeInTheDocument();
  });

  it('displays recommendations', () => {
    render(<PositionForecastCard {...mockProps} />);
    expect(screen.getByText('Increase slots')).toBeInTheDocument();
  });

  it('highlights bottleneck stage', () => {
    render(<PositionForecastCard {...mockProps} />);
    expect(screen.getByText(/Bottleneck: interview/i)).toBeInTheDocument();
  });
});
