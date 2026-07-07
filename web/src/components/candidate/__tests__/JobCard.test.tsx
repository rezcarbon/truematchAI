import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { JobCard } from '../JobCard';
import { Job, CapabilityMatch } from '@/types/jobs';

const mockJob: Job & { capabilityMatch?: CapabilityMatch } = {
  id: '1',
  title: 'Senior Software Engineer',
  company: 'Tech Corp',
  location: 'San Francisco, CA',
  remote: 'hybrid',
  salaryMin: 150000,
  salaryMax: 200000,
  salary_currency: 'USD',
  description: 'We are looking for a senior engineer',
  requirements: [],
  responsibilities: [],
  benefits: [],
  yearsOfExperienceRequired: 5,
  postedDate: new Date('2024-01-01'),
  jobType: 'full-time',
  industry: 'Technology',
  companySize: 'large',
  level: 'senior',
  tags: [],
  capabilityMatch: {
    score: 85,
    matchType: 'strong',
    breakdown: {
      skillsMatch: 80,
      experienceMatch: 90,
      roleTransitionScore: 75,
      culturalFitEstimate: 85,
    },
    reasoning: ['Strong technical background', 'Relevant experience'],
  },
};

describe('JobCard', () => {
  it('renders job title and company', () => {
    render(<JobCard job={mockJob} />);
    expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
    expect(screen.getByText('Tech Corp')).toBeInTheDocument();
  });

  it('displays match score and label', () => {
    render(<JobCard job={mockJob} />);
    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByText('Strong Match')).toBeInTheDocument();
  });

  it('renders location and remote work info', () => {
    render(<JobCard job={mockJob} />);
    expect(screen.getByText('San Francisco, CA')).toBeInTheDocument();
    expect(screen.getByText('🔄 Hybrid')).toBeInTheDocument();
  });

  it('displays salary range', () => {
    render(<JobCard job={mockJob} />);
    expect(screen.getByText('150,000 - 200,000')).toBeInTheDocument();
    expect(screen.getByText('USD')).toBeInTheDocument();
  });

  it('shows experience requirement', () => {
    render(<JobCard job={mockJob} />);
    expect(screen.getByText('5 years')).toBeInTheDocument();
  });

  it('displays industry info', () => {
    render(<JobCard job={mockJob} />);
    expect(screen.getByText('Technology')).toBeInTheDocument();
  });

  it('renders match reasoning', () => {
    render(<JobCard job={mockJob} />);
    expect(screen.getByText(/Why it matches:/)).toBeInTheDocument();
    expect(screen.getByText(/Strong technical background/)).toBeInTheDocument();
  });

  it('shows hidden gem badge when applicable', () => {
    const hiddenGemJob = {
      ...mockJob,
      isHiddenGem: true,
      hiddenGemReason: 'Great opportunity from emerging company',
    };

    render(<JobCard job={hiddenGemJob} />);
    expect(screen.getByText('Hidden Gem')).toBeInTheDocument();
  });

  it('calls onApply callback when apply button clicked', () => {
    const handleApply = jest.fn();
    render(<JobCard job={mockJob} onApply={handleApply} />);

    const applyButton = screen.getByRole('button', { name: /Apply/i });
    fireEvent.click(applyButton);

    expect(handleApply).toHaveBeenCalledWith('1');
  });

  it('disables apply button when isLoading is true', () => {
    render(<JobCard job={mockJob} isLoading={true} />);
    const applyButton = screen.getByRole('button', { name: /Applying/i });
    expect(applyButton).toBeDisabled();
  });

  it('renders view details button with link', () => {
    render(<JobCard job={mockJob} />);
    const viewDetailsLink = screen.getByRole('link', { name: /View Details/i });
    expect(viewDetailsLink).toHaveAttribute('href', '/candidate/jobs/1');
  });

  it('displays correct badges for job type and level', () => {
    render(<JobCard job={mockJob} />);
    expect(screen.getByText('full-time')).toBeInTheDocument();
    expect(screen.getByText('senior')).toBeInTheDocument();
  });

  it('handles different remote work types', () => {
    const fullyRemoteJob = { ...mockJob, remote: 'fully' as const };
    const { rerender } = render(<JobCard job={fullyRemoteJob} />);
    expect(screen.getByText('🏠 Fully Remote')).toBeInTheDocument();

    const onsiteJob = { ...mockJob, remote: 'onsite' as const };
    rerender(<JobCard job={onsiteJob} />);
    expect(screen.getByText('🏢 On-site')).toBeInTheDocument();
  });

  it('applies correct color coding for match scores', () => {
    const lowMatchJob = { ...mockJob, capabilityMatch: { ...mockJob.capabilityMatch!, score: 35 } };
    const { container } = render(<JobCard job={lowMatchJob} />);
    const scoreBadge = container.querySelector('[class*="bg-gray-50"]');
    expect(scoreBadge).toBeInTheDocument();
  });

  it('shows "Apply" text with star icon for normal state', () => {
    render(<JobCard job={mockJob} />);
    expect(screen.getByRole('button', { name: /Apply/i })).toBeInTheDocument();
  });

  it('handles job without capability match', () => {
    const jobWithoutMatch = { ...mockJob, capabilityMatch: undefined };
    render(<JobCard job={jobWithoutMatch} />);
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('has correct accessibility attributes', () => {
    render(<JobCard job={mockJob} />);
    const viewDetailsLink = screen.getByRole('link', { name: /View Details/i });
    expect(viewDetailsLink).toHaveAttribute('href');
  });
});
