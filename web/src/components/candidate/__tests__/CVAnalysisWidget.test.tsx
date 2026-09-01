import React from 'react';
import { render, screen } from '@testing-library/react';
import { CVAnalysisWidget } from '../CVAnalysisWidget';

// Mock Next.js Link component
jest.mock('next/link', () => {
  return ({ children, href }: any) => (
    <a href={href}>{children}</a>
  );
});

describe('CVAnalysisWidget', () => {
  it('renders widget with title', () => {
    render(<CVAnalysisWidget />);
    expect(screen.getByText('CV Analysis')).toBeInTheDocument();
  });

  it('displays analyses run count', () => {
    render(<CVAnalysisWidget recentAnalysisCount={5} />);
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('displays average score', () => {
    render(<CVAnalysisWidget avgScore={75} />);
    expect(screen.getByText('75')).toBeInTheDocument();
  });

  it('displays overall capability score gauge', () => {
    render(<CVAnalysisWidget overallCapabilityScore={85} />);
    expect(screen.getByText('85')).toBeInTheDocument();
  });

  it('shows score interpretation as Excellent', () => {
    render(<CVAnalysisWidget overallCapabilityScore={85} />);
    expect(screen.getByText('Excellent Match')).toBeInTheDocument();
  });

  it('shows score interpretation as Good', () => {
    render(<CVAnalysisWidget overallCapabilityScore={70} />);
    expect(screen.getByText('Good Match')).toBeInTheDocument();
  });

  it('shows score interpretation as Fair', () => {
    render(<CVAnalysisWidget overallCapabilityScore={50} />);
    expect(screen.getByText('Fair Match')).toBeInTheDocument();
  });

  it('shows score interpretation as Poor', () => {
    render(<CVAnalysisWidget overallCapabilityScore={25} />);
    expect(screen.getByText('Poor Match')).toBeInTheDocument();
  });

  it('displays latest analysis title', () => {
    render(<CVAnalysisWidget lastAnalysisTitle="Senior Backend Engineer" />);
    expect(screen.getByText('Senior Backend Engineer')).toBeInTheDocument();
  });

  it('displays latest analysis score', () => {
    render(<CVAnalysisWidget lastAnalysisScore={82} />);
    expect(screen.getByText('82')).toBeInTheDocument();
  });

  it('shows "Start Analysis" button when no analyses run', () => {
    render(<CVAnalysisWidget recentAnalysisCount={0} />);
    expect(screen.getByRole('link', { name: /Start Analysis/i })).toBeInTheDocument();
  });

  it('shows "New Analysis" button when analyses exist', () => {
    render(<CVAnalysisWidget recentAnalysisCount={3} />);
    expect(screen.getByRole('link', { name: /New Analysis/i })).toBeInTheDocument();
  });

  it('links to CV analysis page', () => {
    render(<CVAnalysisWidget />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/candidate/cv-analysis');
  });

  it('displays helper text', () => {
    render(<CVAnalysisWidget />);
    expect(screen.getByText(/Upload your CV and compare against job descriptions/)).toBeInTheDocument();
  });

  it('shows "Analyses Run" label', () => {
    render(<CVAnalysisWidget />);
    expect(screen.getByText('ANALYSES RUN')).toBeInTheDocument();
  });

  it('shows "Avg Score" label', () => {
    render(<CVAnalysisWidget />);
    expect(screen.getByText('AVG SCORE')).toBeInTheDocument();
  });

  it('displays latest analysis section when data provided', () => {
    render(
      <CVAnalysisWidget
        lastAnalysisTitle="Test Role"
        lastAnalysisScore={78}
      />
    );
    expect(screen.getByText('Latest Analysis')).toBeInTheDocument();
  });

  it('does not display latest analysis when not provided', () => {
    render(<CVAnalysisWidget />);
    expect(screen.queryByText('Latest Analysis')).not.toBeInTheDocument();
  });

  it('renders capability score gauge only when score > 0', () => {
    const { container: container1 } = render(<CVAnalysisWidget overallCapabilityScore={0} />);
    expect(container1.querySelector('svg')).not.toBeInTheDocument();

    const { container: container2 } = render(<CVAnalysisWidget overallCapabilityScore={50} />);
    expect(container2.querySelector('svg')).toBeInTheDocument();
  });

  it('displays average score as em dash when zero', () => {
    render(<CVAnalysisWidget avgScore={0} />);
    expect(screen.getByText('—')).toBeInTheDocument();
  });

  it('displays score value when not zero', () => {
    render(<CVAnalysisWidget avgScore={68} />);
    expect(screen.getByText('68')).toBeInTheDocument();
  });

  it('has correct accessibility structure', () => {
    render(<CVAnalysisWidget />);
    expect(screen.getByRole('link', { name: /Analysis/i })).toBeInTheDocument();
  });

  it('renders with default props', () => {
    render(<CVAnalysisWidget />);
    expect(screen.getByText('CV Analysis')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('displays all provided data together', () => {
    render(
      <CVAnalysisWidget
        recentAnalysisCount={4}
        avgScore={82}
        lastAnalysisTitle="Python Developer"
        lastAnalysisScore={88}
        overallCapabilityScore={85}
      />
    );

    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('82')).toBeInTheDocument();
    expect(screen.getByText('Python Developer')).toBeInTheDocument();
    expect(screen.getByText('88')).toBeInTheDocument();
    expect(screen.getByText('Excellent Match')).toBeInTheDocument();
  });

  it('shows latest analysis score with icon', () => {
    render(<CVAnalysisWidget lastAnalysisScore={75} lastAnalysisTitle="Test" />);
    expect(screen.getByText(/Score:/)).toBeInTheDocument();
  });

  it('has border styling for emphasis', () => {
    const { container } = render(<CVAnalysisWidget />);
    const card = container.firstChild;
    expect(card).toHaveClass('border-l-4');
    expect(card).toHaveClass('border-l-blue-600');
  });
});
