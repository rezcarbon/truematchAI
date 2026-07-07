'use client';

import { useState, useEffect } from 'react';
import { PageHeader } from "@/components/shared/PageHeader";
import { JobCard } from "@/components/candidate/JobCard";
import { JobFilters } from "@/components/candidate/JobFilters";
import { Card, CardContent } from "@/components/ui/card";
import { JobFilterCriteria, Job } from "@/types/jobs";
import { Loader2, AlertCircle } from "lucide-react";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [filteredJobs, setFilteredJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<JobFilterCriteria>({
    locations: [],
    roles: [],
    jobTypes: [],
    levels: [],
    industries: [],
    includeHiddenGems: false,
    sortBy: 'match',
    sortOrder: 'desc',
  });
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        setLoading(true);
        setError(null);
        // TODO: Replace with actual API call
        // const response = await fetch('/api/v1/candidates/jobs', {
        //   headers: { 'Authorization': `Bearer ${accessToken}` }
        // });
        // const data = await response.json();
        // setJobs(data);

        // Placeholder data for now
        setJobs([]);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load jobs');
      } finally {
        setLoading(false);
      }
    };

    fetchJobs();
  }, []);

  useEffect(() => {
    // Apply filters to jobs
    let filtered = [...jobs];

    // Filter by search query (role)
    if (filters.searchQuery) {
      filtered = filtered.filter((job) =>
        job.title.toLowerCase().includes(filters.searchQuery!.toLowerCase()) ||
        job.company.toLowerCase().includes(filters.searchQuery!.toLowerCase())
      );
    }

    // Filter by locations
    if (filters.locations.length > 0) {
      filtered = filtered.filter((job) =>
        filters.locations.includes(job.location)
      );
    }

    // Filter by match score
    if (filters.matchScoreMin !== undefined || filters.matchScoreMax !== undefined) {
      filtered = filtered.filter((job) => {
        const score = job.capabilityMatch?.score ?? 0;
        const min = filters.matchScoreMin ?? 0;
        const max = filters.matchScoreMax ?? 100;
        return score >= min && score <= max;
      });
    }

    // Filter by salary
    if (filters.salaryMin !== undefined) {
      filtered = filtered.filter((job) => job.salaryMax >= filters.salaryMin!);
    }
    if (filters.salaryMax !== undefined) {
      filtered = filtered.filter((job) => job.salaryMin <= filters.salaryMax!);
    }

    // Filter by job types
    if (filters.jobTypes && filters.jobTypes.length > 0) {
      filtered = filtered.filter((job) =>
        filters.jobTypes!.includes(job.jobType)
      );
    }

    // Filter by levels
    if (filters.levels && filters.levels.length > 0) {
      filtered = filtered.filter((job) =>
        filters.levels!.includes(job.level)
      );
    }

    // Filter by industries
    if (filters.industries.length > 0) {
      filtered = filtered.filter((job) =>
        filters.industries.includes(job.industry)
      );
    }

    // Filter hidden gems
    if (!filters.includeHiddenGems) {
      filtered = filtered.filter((job) => !job.isHiddenGem);
    }

    // Sort
    filtered.sort((a, b) => {
      const scoreA = a.capabilityMatch?.score ?? 0;
      const scoreB = b.capabilityMatch?.score ?? 0;

      let comparison = 0;
      switch (filters.sortBy) {
        case 'match':
          comparison = scoreA - scoreB;
          break;
        case 'salary':
          comparison = (a.salaryMax ?? 0) - (b.salaryMax ?? 0);
          break;
        case 'recency':
          comparison = new Date(b.postedDate).getTime() - new Date(a.postedDate).getTime();
          break;
        case 'company':
          comparison = a.company.localeCompare(b.company);
          break;
        default:
          comparison = 0;
      }

      return filters.sortOrder === 'desc' ? -comparison : comparison;
    });

    setFilteredJobs(filtered);
  }, [jobs, filters]);

  const handleApply = async (jobId: string) => {
    try {
      setLoading(true);
      // TODO: Implement job application API call
      const response = await fetch(`/api/proxy/v1/candidates/jobs/${jobId}/apply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to apply to job');
      }

      setError(null);
      // Optionally refresh jobs or show success message
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply to job');
    } finally {
      setLoading(false);
    }
  };

  // Pagination logic
  const totalPages = Math.ceil(filteredJobs.length / itemsPerPage);
  const paginatedJobs = filteredJobs.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  return (
    <div className="min-h-screen bg-background">
      <PageHeader
        title="Job Opportunities"
        subtitle="Explore roles tailored to your skills and career goals"
        icon="Search"
      />

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Filters Sidebar */}
          <div className="lg:col-span-1">
            <JobFilters criteria={filters} onChange={setFilters} />
          </div>

          {/* Jobs Grid */}
          <div className="lg:col-span-3">
            {error ? (
              <Card className="border-red-200/60 bg-red-50/30">
                <CardContent className="flex items-start gap-3 pt-6">
                  <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-red-600">Error</p>
                    <p className="text-sm text-red-600/80">{error}</p>
                  </div>
                </CardContent>
              </Card>
            ) : loading ? (
              <Card>
                <CardContent className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary mr-2" />
                  <p className="text-muted-foreground">Loading job opportunities...</p>
                </CardContent>
              </Card>
            ) : filteredJobs.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <p className="text-lg font-medium text-muted-foreground">No jobs found</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Try adjusting your filters to see more opportunities
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">
                    Showing {paginatedJobs.length} of {filteredJobs.length} jobs
                  </p>
                  <div className="text-sm text-muted-foreground">
                    Page {currentPage} of {totalPages}
                  </div>
                </div>

                <div className="grid gap-4 grid-cols-1">
                  {paginatedJobs.map((job) => (
                    <JobCard
                      key={job.id}
                      job={job}
                      onApply={handleApply}
                    />
                  ))}
                </div>

                {/* Pagination Controls */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-between pt-4 border-t">
                    <button
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                      className="px-4 py-2 text-sm font-medium text-muted-foreground border rounded-lg hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Previous
                    </button>

                    <div className="flex gap-1">
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        const pageNum = currentPage <= 3 ? i + 1 : currentPage - 2 + i;
                        if (pageNum > totalPages) return null;
                        return (
                          <button
                            key={pageNum}
                            onClick={() => setCurrentPage(pageNum)}
                            className={`px-3 py-1 text-sm font-medium rounded-lg transition-colors ${
                              currentPage === pageNum
                                ? 'bg-primary text-primary-foreground'
                                : 'text-muted-foreground hover:bg-muted'
                            }`}
                          >
                            {pageNum}
                          </button>
                        );
                      })}
                    </div>

                    <button
                      onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                      disabled={currentPage === totalPages}
                      className="px-4 py-2 text-sm font-medium text-muted-foreground border rounded-lg hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Next
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
