import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { JobFilters } from '../JobFilters';
import { JobFilterCriteria } from '@/types/jobs';

const mockCriteria: JobFilterCriteria = {
  locations: [],
  roles: [],
  jobTypes: [],
  levels: [],
  industries: [],
  includeHiddenGems: false,
  sortBy: 'match',
  sortOrder: 'desc',
};

const mockLocations = ['Remote', 'San Francisco, CA', 'New York, NY'];
const mockIndustries = ['Technology', 'Finance', 'Healthcare'];

describe('JobFilters', () => {
  it('renders filter component with title', () => {
    const handleChange = jest.fn();
    render(
      <JobFilters
        criteria={mockCriteria}
        onChange={handleChange}
        locations={mockLocations}
        industries={mockIndustries}
      />
    );
    expect(screen.getByText('Filters')).toBeInTheDocument();
  });

  it('renders search input for role filtering', () => {
    const handleChange = jest.fn();
    render(
      <JobFilters
        criteria={mockCriteria}
        onChange={handleChange}
        locations={mockLocations}
        industries={mockIndustries}
      />
    );
    expect(screen.getByPlaceholderText('Search roles...')).toBeInTheDocument();
  });

  it('allows toggling location filters', () => {
    const handleChange = jest.fn();
    render(
      <JobFilters
        criteria={mockCriteria}
        onChange={handleChange}
        locations={mockLocations}
        industries={mockIndustries}
      />
    );

    // Click to expand locations
    fireEvent.click(screen.getByText(/Locations \(0\)/));
    expect(screen.getByLabelText('Filter by Remote')).toBeInTheDocument();
  });

  it('displays active filter count', () => {
    const criteriaWithFilters: JobFilterCriteria = {
      ...mockCriteria,
      locations: ['Remote'],
      matchScoreMin: 50,
    };

    const handleChange = jest.fn();
    render(
      <JobFilters
        criteria={criteriaWithFilters}
        onChange={handleChange}
        locations={mockLocations}
        industries={mockIndustries}
      />
    );

    expect(screen.getByText('2 active')).toBeInTheDocument();
  });

  it('allows setting salary range', () => {
    const handleChange = jest.fn();
    render(
      <JobFilters
        criteria={mockCriteria}
        onChange={handleChange}
        locations={mockLocations}
        industries={mockIndustries}
      />
    );

    const minSalaryInput = screen.getByPlaceholderText('Min salary');
    fireEvent.change(minSalaryInput, { target: { value: '100000' } });

    expect(handleChange).toHaveBeenCalled();
  });

  it('allows setting match score range', () => {
    const handleChange = jest.fn();
    render(
      <JobFilters
        criteria={mockCriteria}
        onChange={handleChange}
        locations={mockLocations}
        industries={mockIndustries}
      />
    );

    const slider = screen.getByRole('slider', { name: /Minimum match score/i });
    fireEvent.change(slider, { target: { value: '60' } });

    expect(handleChange).toHaveBeenCalled();
  });

  it('allows toggling hidden gems filter', () => {
    const handleChange = jest.fn();
    render(
      <JobFilters
        criteria={mockCriteria}
        onChange={handleChange}
        locations={mockLocations}
        industries={mockIndustries}
      />
    );

    const hiddenGemsCheckbox = screen.getByLabelText('Include hidden gem opportunities');
    fireEvent.click(hiddenGemsCheckbox);

    expect(handleChange).toHaveBeenCalled();
  });

  it('allows changing sort option', () => {
    const handleChange = jest.fn();
    render(
      <JobFilters
        criteria={mockCriteria}
        onChange={handleChange}
        locations={mockLocations}
        industries={mockIndustries}
      />
    );

    const sortSelect = screen.getByDisplayValue('Best Match');
    fireEvent.change(sortSelect, { target: { value: 'salary' } });

    expect(handleChange).toHaveBeenCalled();
  });

  it('has apply and clear buttons', () => {
    const handleChange = jest.fn();
    render(
      <JobFilters
        criteria={mockCriteria}
        onChange={handleChange}
        locations={mockLocations}
        industries={mockIndustries}
      />
    );

    expect(screen.getByRole('button', { name: /Apply/i })).toBeInTheDocument();
  });

  it('displays clear button only when filters are active', () => {
    const criteriaWithFilters: JobFilterCriteria = {
      ...mockCriteria,
      locations: ['Remote'],
    };

    const handleChange = jest.fn();
    const { rerender } = render(
      <JobFilters
        criteria={criteriaWithFilters}
        onChange={handleChange}
        locations={mockLocations}
        industries={mockIndustries}
      />
    );

    expect(screen.getByRole('button', { name: /Clear/i })).toBeInTheDocument();

    rerender(
      <JobFilters
        criteria={mockCriteria}
        onChange={handleChange}
        locations={mockLocations}
        industries={mockIndustries}
      />
    );

    expect(screen.queryByRole('button', { name: /Clear/i })).not.toBeInTheDocument();
  });

  it('allows filtering by job type', () => {
    const handleChange = jest.fn();
    render(
      <JobFilters
        criteria={mockCriteria}
        onChange={handleChange}
        locations={mockLocations}
        industries={mockIndustries}
      />
    );

    fireEvent.click(screen.getByText(/Job Type \(0\)/));
    expect(screen.getByLabelText(/Filter by full-time positions/i)).toBeInTheDocument();
  });

  it('allows filtering by seniority level', () => {
    const handleChange = jest.fn();
    render(
      <JobFilters
        criteria={mockCriteria}
        onChange={handleChange}
        locations={mockLocations}
        industries={mockIndustries}
      />
    );

    fireEvent.click(screen.getByText(/Level \(0\)/));
    expect(screen.getByLabelText(/Filter by senior positions/i)).toBeInTheDocument();
  });

  it('allows filtering by industry', () => {
    const handleChange = jest.fn();
    render(
      <JobFilters
        criteria={mockCriteria}
        onChange={handleChange}
        locations={mockLocations}
        industries={mockIndustries}
      />
    );

    fireEvent.click(screen.getByText(/Industries \(0\)/));
    expect(screen.getByLabelText(/Filter by Technology industry/i)).toBeInTheDocument();
  });

  it('expands and collapses filter sections', () => {
    const handleChange = jest.fn();
    const { container } = render(
      <JobFilters
        criteria={mockCriteria}
        onChange={handleChange}
        locations={mockLocations}
        industries={mockIndustries}
      />
    );

    const locationsButton = screen.getByText(/Locations/);
    fireEvent.click(locationsButton);

    const checkboxes = container.querySelectorAll('input[type="checkbox"]');
    expect(checkboxes.length).toBeGreaterThan(0);
  });

  it('has correct accessibility labels', () => {
    const handleChange = jest.fn();
    render(
      <JobFilters
        criteria={mockCriteria}
        onChange={handleChange}
        locations={mockLocations}
        industries={mockIndustries}
      />
    );

    expect(screen.getByLabelText('Search jobs by role')).toBeInTheDocument();
    expect(screen.getByLabelText('Minimum match score')).toBeInTheDocument();
    expect(screen.getByLabelText('Maximum match score')).toBeInTheDocument();
  });
});
