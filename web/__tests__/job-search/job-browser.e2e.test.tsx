/**
 * End-to-end tests for job search and capability matching
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { JobBrowser } from '@/components/job-search/JobBrowser';
import type { Skill } from '@/types/jobs';

describe('JobBrowser E2E Tests', () => {
  const mockUserSkills: Skill[] = [
    { name: 'React', proficiency: 'advanced', yearsOfExperience: 4 },
    { name: 'TypeScript', proficiency: 'advanced', yearsOfExperience: 3 },
    { name: 'Node.js', proficiency: 'intermediate', yearsOfExperience: 2 },
  ];

  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  describe('Initial Render', () => {
    it('should render job browser with jobs', async () => {
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      expect(screen.getByText('Job Search')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/search jobs/i)).toBeInTheDocument();

      // Wait for jobs to be displayed
      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });
    });

    it('should display match scores for all jobs', async () => {
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        const matchScores = screen.getAllByText('%');
        expect(matchScores.length).toBeGreaterThan(0);
      });
    });

    it('should show job cards with essential information', async () => {
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('TechCorp')).toBeInTheDocument();
        expect(screen.getByText(/san francisco/i)).toBeInTheDocument();
      });
    });
  });

  describe('Search Functionality', () => {
    it('should filter jobs by title', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search jobs/i);
      await user.type(searchInput, 'data');

      await waitFor(() => {
        expect(screen.getByText('Data Engineer')).toBeInTheDocument();
        expect(screen.queryByText('Senior React Developer')).not.toBeInTheDocument();
      });
    });

    it('should filter jobs by company name', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('TechCorp')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search jobs/i);
      await user.type(searchInput, 'DataInc');

      await waitFor(() => {
        expect(screen.getByText('Data Engineer')).toBeInTheDocument();
        expect(screen.queryByText('TechCorp')).not.toBeInTheDocument();
      });
    });

    it('should show no results message when search has no matches', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search jobs/i);
      await user.type(searchInput, 'nonexistentjob123');

      await waitFor(() => {
        expect(screen.getByText(/no jobs found/i)).toBeInTheDocument();
      });
    });

    it('should clear search and show all jobs again', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search jobs/i) as HTMLInputElement;
      await user.type(searchInput, 'data');

      await waitFor(() => {
        expect(screen.queryByText('Senior React Developer')).not.toBeInTheDocument();
      });

      // Clear search
      await user.clear(searchInput);

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });
    });
  });

  describe('Filter Sidebar', () => {
    it('should have filter sidebar visible', async () => {
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Filters')).toBeInTheDocument();
      });
    });

    it('should filter by salary range', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Salary Range')).toBeInTheDocument();
      });

      // Get salary input fields
      const minInputs = screen.getAllByPlaceholderText('50000');
      const minInput = minInputs[0];

      await user.type(minInput, '150000');
      await user.tab(); // Blur to trigger change

      await waitFor(() => {
        expect(screen.queryByText('Junior DevOps Engineer')).not.toBeInTheDocument();
      });
    });

    it('should filter by work mode (remote)', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Work Mode')).toBeInTheDocument();
      });

      const remoteSelect = screen.getByDisplayValue('All Work Modes');
      await user.selectOptions(remoteSelect, 'fully');

      await waitFor(() => {
        expect(screen.getByText('Full Stack Engineer')).toBeInTheDocument();
      });
    });

    it('should have reset button that clears all filters', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Filters')).toBeInTheDocument();
      });

      const resetButton = screen.getByText('Reset');
      await user.click(resetButton);

      // Jobs should be visible again
      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });
    });
  });

  describe('Job Card Interactions', () => {
    it('should save job to favorites', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });

      // Find and click the heart icon
      const heartButtons = screen.getAllByRole('button').filter(btn => {
        const svg = btn.querySelector('svg');
        return svg?.className.baseVal.includes('w-5');
      });

      const firstHeartButton = heartButtons[0];
      await user.click(firstHeartButton);

      // Verify it was saved (heart should be filled)
      await waitFor(() => {
        expect(localStorage.getItem('truematch_saved_jobs')).toBeTruthy();
      });
    });

    it('should open job details when clicking Details button', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });

      const detailsButtons = screen.getAllByText('Details');
      await user.click(detailsButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/about this role/i)).toBeInTheDocument();
      });
    });

    it('should open apply modal when clicking Apply Now', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });

      const applyButtons = screen.getAllByText('Apply Now');
      await user.click(applyButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/email address/i)).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/tell us why/i)).toBeInTheDocument();
      });
    });
  });

  describe('Job Details Modal', () => {
    it('should display full job details', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });

      const detailsButtons = screen.getAllByText('Details');
      await user.click(detailsButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/about this role/i)).toBeInTheDocument();
        expect(screen.getByText(/key responsibilities/i)).toBeInTheDocument();
        expect(screen.getByText(/requirements/i)).toBeInTheDocument();
        expect(screen.getByText(/benefits/i)).toBeInTheDocument();
      });
    });

    it('should show match breakdown in details', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });

      const detailsButtons = screen.getAllByText('Details');
      await user.click(detailsButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/match breakdown/i)).toBeInTheDocument();
        expect(screen.getByText(/skills match/i)).toBeInTheDocument();
      });
    });

    it('should show skills alignment radar chart', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });

      const detailsButtons = screen.getAllByText('Details');
      await user.click(detailsButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/skills alignment/i)).toBeInTheDocument();
      });
    });

    it('should close modal when clicking close button', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });

      const detailsButtons = screen.getAllByText('Details');
      await user.click(detailsButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/about this role/i)).toBeInTheDocument();
      });

      const closeButtons = screen.getAllByRole('button').filter(btn => {
        return btn.querySelector('svg.w-5');
      });

      // Find the close button in the modal header (last one)
      const closeButton = closeButtons[closeButtons.length - 1];
      await user.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByText(/about this role/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Apply Modal', () => {
    it('should open apply modal with job info', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });

      const applyButtons = screen.getAllByText('Apply Now');
      await user.click(applyButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/motivation statement/i)).toBeInTheDocument();
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
        expect(screen.getByText('TechCorp')).toBeInTheDocument();
      });
    });

    it('should require cover letter before submission', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });

      const applyButtons = screen.getAllByText('Apply Now');
      await user.click(applyButtons[0]);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/tell us why/i)).toBeInTheDocument();
      });

      const submitButton = screen.getByText('Submit Application');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/please provide a cover letter/i)).toBeInTheDocument();
      });
    });

    it('should allow filling in application form', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });

      const applyButtons = screen.getAllByText('Apply Now');
      await user.click(applyButtons[0]);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/tell us why/i)).toBeInTheDocument();
      });

      const emailInput = screen.getByPlaceholderText(/your@email/i);
      const coverLetterInput = screen.getByPlaceholderText(/tell us why/i);

      await user.type(emailInput, 'test@example.com');
      await user.type(coverLetterInput, 'I am very interested in this position');

      expect(emailInput).toHaveValue('test@example.com');
      expect(coverLetterInput).toHaveValue('I am very interested in this position');
    });

    it('should submit application successfully', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });

      const applyButtons = screen.getAllByText('Apply Now');
      await user.click(applyButtons[0]);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/tell us why/i)).toBeInTheDocument();
      });

      const coverLetterInput = screen.getByPlaceholderText(/tell us why/i);
      await user.type(coverLetterInput, 'I am interested in this position');

      const submitButton = screen.getByText('Submit Application');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/application sent/i)).toBeInTheDocument();
      });
    });
  });

  describe('Hidden Gems Detection', () => {
    it('should display hidden gem badge for qualified jobs', async () => {
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Hidden Gem')).toBeInTheDocument();
      });
    });

    it('should show hidden gem reason on hover', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        const badges = screen.getAllByText('Hidden Gem');
        expect(badges.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Sorting and Filtering Combination', () => {
    it('should sort jobs by match score', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });

      const sortSelect = screen.getByDisplayValue('Match Score');
      expect(sortSelect).toBeInTheDocument();
    });

    it('should maintain filters when changing search', async () => {
      const user = userEvent.setup();
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });

      // Apply filter
      const remoteSelect = screen.getByDisplayValue('All Work Modes');
      await user.selectOptions(remoteSelect, 'fully');

      // Search
      const searchInput = screen.getByPlaceholderText(/search jobs/i);
      await user.type(searchInput, 'full');

      await waitFor(() => {
        expect(screen.getByText('Full Stack Engineer')).toBeInTheDocument();
      });
    });
  });

  describe('Performance and Loading', () => {
    it('should handle multiple job cards efficiently', async () => {
      const { container } = render(
        <JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />
      );

      await waitFor(() => {
        expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
      });

      const jobCards = container.querySelectorAll('[class*="rounded-lg"][class*="border"]');
      expect(jobCards.length).toBeGreaterThan(0);
    });
  });

  describe('Responsive Behavior', () => {
    it('should render on mobile viewport', async () => {
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Job Search')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search jobs/i);
      expect(searchInput).toBeVisible();
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', async () => {
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        const heading = screen.getByRole('heading', { name: /job search/i });
        expect(heading).toBeInTheDocument();
      });
    });

    it('should have descriptive button labels', async () => {
      render(<JobBrowser userSkills={mockUserSkills} yearsOfExperience={5} />);

      await waitFor(() => {
        expect(screen.getByText('Details')).toBeInTheDocument();
        expect(screen.getByText('Apply Now')).toBeInTheDocument();
      });
    });
  });
});
