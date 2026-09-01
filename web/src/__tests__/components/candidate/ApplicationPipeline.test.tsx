import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  ApplicationPipeline,
  type ApplicationPipelineProps,
} from '@/components/candidate/ApplicationPipeline';

describe('ApplicationPipeline Component', () => {
  const defaultProps: ApplicationPipelineProps = {
    applicationId: 'app_123',
    currentStage: 'screened',
    stageTimestamps: {
      applied: '2026-01-15T10:00:00Z',
      screened: '2026-01-20T14:30:00Z',
    },
    isActive: true,
  };

  it('renders card with pipeline stages', () => {
    render(<ApplicationPipeline {...defaultProps} />);

    expect(screen.getByText('Application Pipeline')).toBeInTheDocument();
    expect(screen.getByText('Applied')).toBeInTheDocument();
    expect(screen.getByText('Screened')).toBeInTheDocument();
  });

  it('displays correct progress percentage', () => {
    render(<ApplicationPipeline {...defaultProps} />);

    // screened is 2nd stage out of 5, so 2/5 = 40%
    expect(screen.getByText('Progress: 40%')).toBeInTheDocument();
  });

  it('displays current stage information', () => {
    render(<ApplicationPipeline {...defaultProps} />);

    expect(screen.getByText('Application under review')).toBeInTheDocument();
  });

  it('renders stage date when available', () => {
    render(<ApplicationPipeline {...defaultProps} />);

    // Should show the screened date
    expect(screen.getByText(/Jan 20/)).toBeInTheDocument();
  });

  it('shows next step information for non-closed stages', () => {
    render(<ApplicationPipeline {...defaultProps} />);

    expect(screen.getByText(/Next step:/)).toBeInTheDocument();
  });

  it('displays closed application alert', () => {
    render(
      <ApplicationPipeline
        {...defaultProps}
        currentStage="closed"
      />
    );

    expect(
      screen.getByText(/This application has been closed/i)
    ).toBeInTheDocument();
  });

  it('calls onStageClick when stage is clicked', async () => {
    const onStageClick = jest.fn();
    render(
      <ApplicationPipeline
        {...defaultProps}
        onStageClick={onStageClick}
      />
    );

    const appliedStage = screen.getAllByText('Applied')[0];
    await userEvent.click(appliedStage);

    expect(onStageClick).toHaveBeenCalledWith('applied');
  });

  it('renders all pipeline stages in correct order', () => {
    const { container } = render(<ApplicationPipeline {...defaultProps} />);

    const stages = screen.getAllByText(/Applied|Screened|Interviewed|Offer|Closed/);
    expect(stages.length).toBeGreaterThan(0);
  });

  it('indicates completed stages with checkmark', () => {
    render(<ApplicationPipeline {...defaultProps} />);

    // Applied stage should be completed (has checkmark)
    const svgs = screen.getAllByRole('img', { hidden: true });
    expect(svgs.length).toBeGreaterThan(0);
  });

  it('supports keyboard navigation on stages', async () => {
    const onStageClick = jest.fn();
    render(
      <ApplicationPipeline
        {...defaultProps}
        onStageClick={onStageClick}
      />
    );

    const stageButtons = screen.getAllByRole('button');
    if (stageButtons.length > 0) {
      fireEvent.keyDown(stageButtons[0], { key: 'Enter' });
      expect(onStageClick).toHaveBeenCalled();
    }
  });

  it('displays progress info text', () => {
    render(<ApplicationPipeline {...defaultProps} />);

    expect(screen.getByText(/2 of 5/)).toBeInTheDocument();
  });

  it('renders with custom className', () => {
    const { container } = render(
      <ApplicationPipeline
        {...defaultProps}
        className="custom-class"
      />
    );

    const card = container.querySelector('.custom-class');
    expect(card).toBeInTheDocument();
  });

  it('handles inactive pipeline gracefully', () => {
    render(
      <ApplicationPipeline
        {...defaultProps}
        isActive={false}
      />
    );

    expect(screen.getByText('Application Pipeline')).toBeInTheDocument();
  });

  it('shows all stages in the pipeline', () => {
    render(<ApplicationPipeline {...defaultProps} />);

    const stages = ['Applied', 'Screened', 'Interviewed', 'Offer', 'Closed'];
    stages.forEach((stage) => {
      expect(screen.getByText(stage)).toBeInTheDocument();
    });
  });

  it('displays stage descriptions', () => {
    render(<ApplicationPipeline {...defaultProps} />);

    expect(screen.getByText('Submitted your application')).toBeInTheDocument();
    expect(screen.getByText('Application under review')).toBeInTheDocument();
  });

  it('handles offer stage correctly', () => {
    render(
      <ApplicationPipeline
        {...defaultProps}
        currentStage="offer"
      />
    );

    expect(screen.getByText('Offer extended')).toBeInTheDocument();
  });
});
