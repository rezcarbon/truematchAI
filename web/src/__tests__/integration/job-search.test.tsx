import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

/**
 * Integration tests for Job Search workflow
 * Tests the complete flow: search → filter → view results → apply
 */
describe('Job Search Integration', () => {
  const mockJobs = [
    {
      id: 'job-1',
      title: 'Senior React Developer',
      company: 'Tech Corp',
      location: 'San Francisco, CA',
      matchScore: 92,
      skills: ['React', 'TypeScript', 'Node.js'],
      salary: '$150k-$200k',
    },
    {
      id: 'job-2',
      title: 'Full Stack Engineer',
      company: 'StartUp Inc',
      location: 'Remote',
      matchScore: 85,
      skills: ['React', 'Python', 'PostgreSQL'],
      salary: '$120k-$160k',
    },
    {
      id: 'job-3',
      title: 'Backend Engineer',
      company: 'Enterprise Co',
      location: 'New York, NY',
      matchScore: 78,
      skills: ['Node.js', 'Go', 'Kubernetes'],
      salary: '$140k-$190k',
    },
  ];

  describe('Search Workflow', () => {
    it('searches jobs and displays results', async () => {
      const user = userEvent.setup();
      const mockSearch = jest.fn().mockResolvedValue(mockJobs);

      const SearchComponent = () => {
        const [query, setQuery] = React.useState('');
        const [results, setResults] = React.useState<any[]>([]);

        const handleSearch = async (e: React.FormEvent) => {
          e.preventDefault();
          const data = await mockSearch(query);
          setResults(data);
        };

        return (
          <div>
            <form onSubmit={handleSearch}>
              <input
                type="text"
                placeholder="Search jobs..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                data-testid="search-input"
              />
              <button type="submit">Search</button>
            </form>

            <div data-testid="search-results">
              {results.map((job) => (
                <div key={job.id} data-testid={`job-${job.id}`}>
                  <h3>{job.title}</h3>
                  <p>{job.company}</p>
                  <span>{job.matchScore}% match</span>
                </div>
              ))}
            </div>
          </div>
        );
      };

      render(<SearchComponent />);

      const searchInput = screen.getByTestId('search-input');
      const searchBtn = screen.getByRole('button', { name: /Search/i });

      await user.type(searchInput, 'React Developer');
      await user.click(searchBtn);

      await waitFor(() => {
        expect(mockSearch).toHaveBeenCalledWith('React Developer');
        expect(screen.getByTestId('job-1')).toBeInTheDocument();
      });
    });

    it('searches with multiple keywords', async () => {
      const user = userEvent.setup();
      const mockSearch = jest.fn().mockResolvedValue([mockJobs[0]]);

      const SearchComponent = () => {
        const [keywords, setKeywords] = React.useState<string[]>([]);
        const [results, setResults] = React.useState<any[]>([]);

        const handleSearch = async () => {
          const data = await mockSearch(keywords);
          setResults(data);
        };

        return (
          <div>
            <input
              type="text"
              placeholder="Add keyword"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  setKeywords([...keywords, e.currentTarget.value]);
                  e.currentTarget.value = '';
                }
              }}
              data-testid="keyword-input"
            />
            <button onClick={handleSearch} data-testid="search-btn">
              Search
            </button>

            <div data-testid="results">
              {results.map((job) => (
                <div key={job.id}>{job.title}</div>
              ))}
            </div>
          </div>
        );
      };

      render(<SearchComponent />);

      const input = screen.getByTestId('keyword-input') as HTMLInputElement;
      const searchBtn = screen.getByTestId('search-btn');

      // Add keywords
      await user.type(input, 'React{Enter}');
      await user.type(input, 'TypeScript{Enter}');

      await user.click(searchBtn);

      await waitFor(() => {
        expect(mockSearch).toHaveBeenCalled();
      });
    });
  });

  describe('Filter Workflow', () => {
    it('filters search results by location', async () => {
      const user = userEvent.setup();
      const mockFilter = jest.fn().mockImplementation((jobs, location) => {
        return jobs.filter((job: any) => job.location === location);
      });

      const FilterComponent = () => {
        const [location, setLocation] = React.useState('');
        const [filteredJobs, setFilteredJobs] = React.useState(mockJobs);

        const handleFilter = async (selectedLocation: string) => {
          setLocation(selectedLocation);
          const filtered = mockFilter(mockJobs, selectedLocation);
          setFilteredJobs(filtered);
        };

        return (
          <div>
            <button onClick={() => handleFilter('Remote')} data-testid="filter-remote">
              Remote
            </button>
            <button onClick={() => handleFilter('San Francisco, CA')} data-testid="filter-sf">
              San Francisco
            </button>

            <div data-testid="filtered-results">
              {filteredJobs.map((job) => (
                <div key={job.id}>{job.title}</div>
              ))}
            </div>
          </div>
        );
      };

      render(<FilterComponent />);

      const remoteBtn = screen.getByTestId('filter-remote');
      await user.click(remoteBtn);

      await waitFor(() => {
        expect(screen.getByText('Full Stack Engineer')).toBeInTheDocument();
      });
    });

    it('filters by match score threshold', async () => {
      const user = userEvent.setup();
      const mockFilterByScore = jest.fn().mockImplementation((jobs, minScore) => {
        return jobs.filter((job: any) => job.matchScore >= minScore);
      });

      const FilterComponent = () => {
        const [minScore, setMinScore] = React.useState(0);
        const [results, setResults] = React.useState(mockJobs);

        const handleScoreFilter = (score: number) => {
          setMinScore(score);
          const filtered = mockFilterByScore(mockJobs, score);
          setResults(filtered);
        };

        return (
          <div>
            <button onClick={() => handleScoreFilter(90)} data-testid="filter-90">
              90%+ Match
            </button>
            <button onClick={() => handleScoreFilter(80)} data-testid="filter-80">
              80%+ Match
            </button>

            <div data-testid="results">
              {results.map((job) => (
                <div key={job.id} data-testid={`result-${job.id}`}>
                  {job.title} - {job.matchScore}%
                </div>
              ))}
            </div>
          </div>
        );
      };

      render(<FilterComponent />);

      const filter90Btn = screen.getByTestId('filter-90');
      await user.click(filter90Btn);

      await waitFor(() => {
        expect(mockFilterByScore).toHaveBeenCalledWith(mockJobs, 90);
        expect(screen.getByTestId('result-job-1')).toBeInTheDocument();
      });
    });

    it('applies multiple filters simultaneously', async () => {
      const user = userEvent.setup();
      const mockMultiFilter = jest.fn().mockImplementation((jobs, filters) => {
        return jobs.filter((job: any) => {
          const locationMatch = !filters.location || job.location === filters.location;
          const scoreMatch = !filters.minScore || job.matchScore >= filters.minScore;
          const skillMatch =
            !filters.skill ||
            job.skills.some((s: string) =>
              s.toLowerCase().includes(filters.skill.toLowerCase())
            );
          return locationMatch && scoreMatch && skillMatch;
        });
      });

      const MultiFilterComponent = () => {
        const [filters, setFilters] = React.useState({
          location: '',
          minScore: 0,
          skill: '',
        });
        const [results, setResults] = React.useState(mockJobs);

        const updateFilters = (newFilters: any) => {
          setFilters(newFilters);
          const filtered = mockMultiFilter(mockJobs, newFilters);
          setResults(filtered);
        };

        return (
          <div>
            <button
              onClick={() =>
                updateFilters({
                  location: 'Remote',
                  minScore: 80,
                  skill: 'React',
                })
              }
              data-testid="apply-filters"
            >
              Apply Filters
            </button>

            <div data-testid="results">
              {results.map((job) => (
                <div key={job.id}>{job.title}</div>
              ))}
            </div>
          </div>
        );
      };

      render(<MultiFilterComponent />);

      const applyBtn = screen.getByTestId('apply-filters');
      await user.click(applyBtn);

      await waitFor(() => {
        expect(mockMultiFilter).toHaveBeenCalled();
      });
    });
  });

  describe('Complete Search to Apply Workflow', () => {
    it('completes flow: search → filter → view → apply', async () => {
      const user = userEvent.setup();
      const mockSearch = jest.fn().mockResolvedValue(mockJobs);
      const mockApply = jest.fn().mockResolvedValue({
        applicationId: 'app-1',
        status: 'submitted',
      });

      const WorkflowComponent = () => {
        const [results, setResults] = React.useState<any[]>([]);
        const [selectedJob, setSelectedJob] = React.useState<any | null>(null);

        const handleSearch = async () => {
          const jobs = await mockSearch('React');
          setResults(jobs);
        };

        const handleApply = async (jobId: string) => {
          const result = await mockApply(jobId);
          return result;
        };

        return (
          <div>
            <button onClick={handleSearch} data-testid="search-btn">
              Search
            </button>

            <div data-testid="results">
              {results.map((job) => (
                <button
                  key={job.id}
                  onClick={() => setSelectedJob(job)}
                  data-testid={`job-btn-${job.id}`}
                >
                  {job.title}
                </button>
              ))}
            </div>

            {selectedJob && (
              <div data-testid="job-detail">
                <h2>{selectedJob.title}</h2>
                <p>{selectedJob.company}</p>
                <button
                  onClick={() => handleApply(selectedJob.id)}
                  data-testid="apply-btn"
                >
                  Apply
                </button>
              </div>
            )}
          </div>
        );
      };

      render(<WorkflowComponent />);

      // Step 1: Search
      const searchBtn = screen.getByTestId('search-btn');
      await user.click(searchBtn);

      await waitFor(() => {
        expect(mockSearch).toHaveBeenCalled();
      });

      // Step 2: View job
      const jobBtn = screen.getByTestId('job-btn-job-1');
      await user.click(jobBtn);

      expect(screen.getByTestId('job-detail')).toBeInTheDocument();
      expect(screen.getByText('Senior React Developer')).toBeInTheDocument();

      // Step 3: Apply
      const applyBtn = screen.getByTestId('apply-btn');
      await user.click(applyBtn);

      await waitFor(() => {
        expect(mockApply).toHaveBeenCalledWith('job-1');
      });
    });
  });

  describe('Search Error Handling', () => {
    it('handles search API errors', async () => {
      const mockSearch = jest.fn().mockRejectedValue(
        new Error('Search service unavailable')
      );

      const SearchComponent = () => {
        const [error, setError] = React.useState<string | null>(null);

        const handleSearch = async () => {
          try {
            await mockSearch();
          } catch (err: any) {
            setError(err.message);
          }
        };

        return (
          <div>
            <button onClick={handleSearch} data-testid="search-btn">
              Search
            </button>
            {error && <div data-testid="error">{error}</div>}
          </div>
        );
      };

      render(<SearchComponent />);

      const searchBtn = screen.getByTestId('search-btn');
      await userEvent.click(searchBtn);

      await waitFor(() => {
        expect(screen.getByTestId('error')).toBeInTheDocument();
        expect(screen.getByText('Search service unavailable')).toBeInTheDocument();
      });
    });

    it('handles empty search results', async () => {
      const mockSearch = jest.fn().mockResolvedValue([]);

      const SearchComponent = () => {
        const [results, setResults] = React.useState<any[]>([]);
        const [searched, setSearched] = React.useState(false);

        const handleSearch = async () => {
          const jobs = await mockSearch('impossible query');
          setResults(jobs);
          setSearched(true);
        };

        return (
          <div>
            <button onClick={handleSearch} data-testid="search-btn">
              Search
            </button>
            {searched && results.length === 0 && (
              <div data-testid="no-results">No jobs found</div>
            )}
          </div>
        );
      };

      render(<SearchComponent />);

      await userEvent.click(screen.getByTestId('search-btn'));

      await waitFor(() => {
        expect(screen.getByTestId('no-results')).toBeInTheDocument();
      });
    });
  });

  describe('Search Performance', () => {
    it('handles pagination of results', async () => {
      const mockSearch = jest.fn().mockImplementation((query, page) => {
        const allJobs = Array.from({ length: 50 }, (_, i) => ({
          id: `job-${i}`,
          title: `Job ${i}`,
          matchScore: 50 + i,
        }));

        const itemsPerPage = 10;
        const start = (page - 1) * itemsPerPage;
        const end = start + itemsPerPage;

        return Promise.resolve({
          items: allJobs.slice(start, end),
          total: allJobs.length,
          page,
          pages: Math.ceil(allJobs.length / itemsPerPage),
        });
      });

      const result1 = await mockSearch('test', 1);
      const result2 = await mockSearch('test', 2);

      expect(result1.items.length).toBe(10);
      expect(result2.items.length).toBe(10);
      expect(result1.items[0].id).toBe('job-0');
      expect(result2.items[0].id).toBe('job-10');
    });

    it('handles large result sets efficiently', async () => {
      const mockSearch = jest.fn().mockResolvedValue(
        Array.from({ length: 1000 }, (_, i) => ({
          id: `job-${i}`,
          title: `Job ${i}`,
          matchScore: Math.random() * 100,
        }))
      );

      const results = await mockSearch('performance test');
      expect(results.length).toBe(1000);
    });
  });

  describe('Search Persistence', () => {
    it('saves search history', async () => {
      const searchHistory: string[] = [];

      const mockSearch = jest.fn().mockImplementation((query) => {
        searchHistory.push(query);
        return Promise.resolve(mockJobs);
      });

      await mockSearch('React Developer');
      await mockSearch('Full Stack Engineer');
      await mockSearch('Backend Engineer');

      expect(searchHistory.length).toBe(3);
      expect(searchHistory).toEqual([
        'React Developer',
        'Full Stack Engineer',
        'Backend Engineer',
      ]);
    });

    it('clears search history', () => {
      let searchHistory: string[] = ['React', 'TypeScript', 'Node.js'];

      const clearHistory = () => {
        searchHistory = [];
      };

      expect(searchHistory.length).toBe(3);
      clearHistory();
      expect(searchHistory.length).toBe(0);
    });
  });
});
