import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { JobCard } from '../JobCard';
import { Job, CapabilityMatch } from '@/types/jobs';

// Mock Next.js Link
jest.mock('next/link', () => {
  return ({ children, href }: any) => <a href={href}>{children}</a>;
});

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
  describe('Display', () => {
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

  describe('Match Score Variants', () => {
    it('shows "Perfect Match" for exact match type', () => {
      const perfectMatchJob = {
        ...mockJob,
        capabilityMatch: { ...mockJob.capabilityMatch!, matchType: 'exact', score: 100 },
      };
      render(<JobCard job={perfectMatchJob} />);
      expect(screen.getByText('Perfect Match')).toBeInTheDocument();
    });

    it('shows "Possible Match" for partial match type', () => {
      const partialJob = {
        ...mockJob,
        capabilityMatch: { ...mockJob.capabilityMatch!, matchType: 'partial', score: 55 },
      };
      render(<JobCard job={partialJob} />);
      expect(screen.getByText('Possible Match')).toBeInTheDocument();
    });

    it('shows "Hidden Gem" match label', () => {
      const hiddenGemJob = {
        ...mockJob,
        capabilityMatch: { ...mockJob.capabilityMatch!, matchType: 'hidden_gem', score: 72 },
      };
      render(<JobCard job={hiddenGemJob} />);
      expect(screen.getByText('Hidden Gem')).toBeInTheDocument();
    });
  });

  describe('Color Coding by Score', () => {
    it('applies green styling for scores 80+', () => {
      const highScoreJob = { ...mockJob, capabilityMatch: { ...mockJob.capabilityMatch!, score: 85 } };
      const { container } = render(<JobCard job={highScoreJob} />);
      expect(container.querySelector('.bg-green-50')).toBeInTheDocument();
      expect(container.querySelector('.text-green-700')).toBeInTheDocument();
    });

    it('applies blue styling for scores 60-79', () => {
      const goodScoreJob = { ...mockJob, capabilityMatch: { ...mockJob.capabilityMatch!, score: 70 } };
      const { container } = render(<JobCard job={goodScoreJob} />);
      expect(container.querySelector('.bg-blue-50')).toBeInTheDocument();
    });

    it('applies amber styling for scores 40-59', () => {
      const fairScoreJob = { ...mockJob, capabilityMatch: { ...mockJob.capabilityMatch!, score: 50 } };
      const { container } = render(<JobCard job={fairScoreJob} />);
      expect(container.querySelector('.bg-amber-50')).toBeInTheDocument();
    });

    it('applies gray styling for scores below 40', () => {
      const lowScoreJob = { ...mockJob, capabilityMatch: { ...mockJob.capabilityMatch!, score: 25 } };
      const { container } = render(<JobCard job={lowScoreJob} />);
      expect(container.querySelector('.bg-gray-50')).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    it('handles apply button click with async operation', async () => {
      const user = userEvent.setup();
      const handleApply = jest.fn().mockResolvedValue(undefined);
      render(<JobCard job={mockJob} onApply={handleApply} />);

      const applyButton = screen.getByRole('button', { name: /Apply/i });
      await user.click(applyButton);

      await waitFor(() => {
        expect(handleApply).toHaveBeenCalledWith('1');
      });
    });

    it('prevents multiple apply clicks during loading', () => {
      const handleApply = jest.fn();
      const { rerender } = render(<JobCard job={mockJob} onApply={handleApply} />);

      const applyButton = screen.getByRole('button', { name: /Apply/i });
      fireEvent.click(applyButton);

      rerender(<JobCard job={mockJob} onApply={handleApply} isLoading={true} />);

      const loadingButton = screen.getByRole('button', { name: /Applying/i });
      expect(loadingButton).toBeDisabled();
    });

    it('navigates to job details when title is clicked', () => {
      render(<JobCard job={mockJob} />);
      const titleLink = screen.getByRole('link', { name: 'Senior Software Engineer' });
      expect(titleLink).toHaveAttribute('href', '/candidate/jobs/1');
    });

    it('navigates to job details when view details button is clicked', () => {
      render(<JobCard job={mockJob} />);
      const viewDetailsButton = screen.getByRole('link', { name: /View Details/i });
      expect(viewDetailsButton).toHaveAttribute('href', '/candidate/jobs/1');
    });
  });

  describe('Salary Handling', () => {
    it('handles missing salary data gracefully', () => {
      const jobNoSalary = { ...mockJob, salaryMin: undefined, salaryMax: undefined };
      const { container } = render(<JobCard job={jobNoSalary} />);
      // Salary section should not appear
      const salaryElements = container.querySelectorAll('[data-testid="salary"]');
      expect(salaryElements.length).toBe(0);
    });

    it('displays salary with proper formatting', () => {
      render(<JobCard job={mockJob} />);
      expect(screen.getByText('150,000 - 200,000')).toBeInTheDocument();
    });

    it('shows currency code when provided', () => {
      render(<JobCard job={mockJob} />);
      expect(screen.getByText('USD')).toBeInTheDocument();
    });
  });

  describe('Empty States', () => {
    it('handles no match reasoning', () => {
      const jobNoReasoning = {
        ...mockJob,
        capabilityMatch: { ...mockJob.capabilityMatch!, reasoning: [] },
      };
      render(<JobCard job={jobNoReasoning} />);
      expect(screen.queryByText(/Why it matches:/)).not.toBeInTheDocument();
    });

    it('renders correctly without hidden gem', () => {
      const normalJob = { ...mockJob, isHiddenGem: false };
      render(<JobCard job={normalJob} />);
      const hiddenGemBadges = screen.queryAllByText('Hidden Gem');
      expect(hiddenGemBadges).toHaveLength(0);
    });
  });

  describe('Accessibility', () => {
    it('has semantic button elements for actions', () => {
      render(<JobCard job={mockJob} />);
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('has semantic link elements for navigation', () => {
      render(<JobCard job={mockJob} />);
      const links = screen.getAllByRole('link');
      expect(links.length).toBeGreaterThan(0);
    });

    it('provides context for all visual indicators', () => {
      render(<JobCard job={mockJob} />);
      // Verify text labels exist alongside icons
      expect(screen.getByText('Tech Corp')).toBeInTheDocument(); // Company context
      expect(screen.getByText(/San Francisco, CA/)).toBeInTheDocument(); // Location context
      expect(screen.getByText('Technology')).toBeInTheDocument(); // Industry context
    });

    it('maintains focus management for interactive elements', () => {
      render(<JobCard job={mockJob} />);
      const applyButton = screen.getByRole('button', { name: /Apply/i });
      expect(applyButton).toBeInTheDocument();
      // Button should be focusable
      expect(applyButton.tagName).toBe('BUTTON');
    });
  });

  describe('Loading States', () => {
    it('shows loading text in apply button', () => {
      render(<JobCard job={mockJob} isLoading={true} />);
      expect(screen.getByText('Applying...')).toBeInTheDocument();
    });

    it('displays loading indicator', () => {
      render(<JobCard job={mockJob} isLoading={true} />);
      const applyButton = screen.getByRole('button', { name: /Applying/i });
      expect(applyButton).toHaveAttribute('disabled');
    });

    it('maintains button visibility during loading', () => {
      render(<JobCard job={mockJob} isLoading={true} />);
      const applyButton = screen.getByRole('button', { name: /Applying/i });
      expect(applyButton).toBeVisible();
    });
  });
});
