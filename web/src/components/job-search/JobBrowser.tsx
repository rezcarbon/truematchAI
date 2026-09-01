'use client';

/**
 * Main job browser/search component
 */

import React, { useState, useMemo } from 'react';
import { Search, Loader } from 'lucide-react';
import { JobCard } from './JobCard';
import { FilterSidebar } from './FilterSidebar';
import { ApplyModal, type ApplyFormData } from './ApplyModal';
import { JobDetailsModal } from './JobDetailsModal';
import { useJobFavorites } from '@/hooks/useJobFavorites';
import { sampleJobs, getUniqueLocations, getUniqueRoles, getUniqueLevels, getUniqueIndustries } from '@/lib/job-data';
import { calculateCapabilityMatch } from '@/lib/capability-matching';
import type { Job, JobWithCapabilityMatch, JobFilterCriteria, Skill } from '@/types/jobs';

interface JobBrowserProps {
  userSkills?: Skill[];
  yearsOfExperience?: number;
}

export function JobBrowser({
  userSkills = [
    { name: 'React', proficiency: 'advanced', yearsOfExperience: 4 },
    { name: 'TypeScript', proficiency: 'advanced', yearsOfExperience: 3 },
    { name: 'Node.js', proficiency: 'intermediate', yearsOfExperience: 2 },
    { name: 'Python', proficiency: 'intermediate', yearsOfExperience: 2 },
    { name: 'AWS', proficiency: 'beginner', yearsOfExperience: 1 },
    { name: 'Leadership', proficiency: 'intermediate', yearsOfExperience: 2 },
  ],
  yearsOfExperience = 5,
}: JobBrowserProps) {
  const { savedJobs, isSaved, toggleSave, markApplied } = useJobFavorites();
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Partial<JobFilterCriteria>>({
    sortBy: 'match',
    sortOrder: 'desc',
  });
  const [selectedJobForDetails, setSelectedJobForDetails] = useState<JobWithCapabilityMatch | null>(null);
  const [selectedJobForApply, setSelectedJobForApply] = useState<JobWithCapabilityMatch | null>(null);
  const [isApplying, setIsApplying] = useState(false);

  // Enhance jobs with capability matching
  const enhancedJobs = useMemo(() => {
    return sampleJobs.map((job) => {
      const match = calculateCapabilityMatch(userSkills, yearsOfExperience, job);
      return {
        ...job,
        capabilityMatch: match,
        skillsAlignment: calculateCapabilityMatch(userSkills, yearsOfExperience, job)
          .breakdown as any || {},
      } as JobWithCapabilityMatch;
    });
  }, [userSkills, yearsOfExperience]);

  // Apply filters
  const filteredJobs = useMemo(() => {
    let results = [...enhancedJobs];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      results = results.filter(
        (job) =>
          job.title.toLowerCase().includes(query) ||
          job.company.toLowerCase().includes(query) ||
          job.description.toLowerCase().includes(query)
      );
    }

    // Location filter
    if (filters.locations && filters.locations.length > 0) {
      results = results.filter((job) => filters.locations!.includes(job.location));
    }

    // Salary filter
    if (filters.salaryMin !== undefined) {
      results = results.filter((job) => job.salaryMax >= filters.salaryMin!);
    }
    if (filters.salaryMax !== undefined) {
      results = results.filter((job) => job.salaryMin <= filters.salaryMax!);
    }

    // Match score filter
    if (filters.matchScoreMin !== undefined) {
      results = results.filter((job) => job.capabilityMatch.score >= filters.matchScoreMin!);
    }

    // Remote filter
    if (filters.remote && filters.remote !== 'all') {
      results = results.filter((job) => job.remote === filters.remote);
    }

    // Role filter
    if (filters.roles && filters.roles.length > 0) {
      results = results.filter((job) =>
        filters.roles!.some((role) => job.title.toLowerCase().includes(role.toLowerCase()))
      );
    }

    // Level filter
    if (filters.levels && filters.levels.length > 0) {
      results = results.filter((job) => filters.levels!.includes(job.level));
    }

    // Industry filter
    if (filters.industries && filters.industries.length > 0) {
      results = results.filter((job) => filters.industries!.includes(job.industry));
    }

    // Hidden gems filter
    if (filters.includeHiddenGems === false) {
      results = results.filter((job) => !job.isHiddenGem);
    }

    // Sorting
    const sortBy = filters.sortBy || 'match';
    const sortOrder = filters.sortOrder || 'desc';
    const multiplier = sortOrder === 'asc' ? 1 : -1;

    results.sort((a, b) => {
      switch (sortBy) {
        case 'match':
          return (a.capabilityMatch.score - b.capabilityMatch.score) * multiplier;
        case 'salary':
          return (a.salaryMin - b.salaryMin) * multiplier;
        case 'recency':
          return (new Date(b.postedDate).getTime() - new Date(a.postedDate).getTime()) * multiplier;
        case 'company':
          return a.company.localeCompare(b.company) * multiplier;
        default:
          return 0;
      }
    });

    return results;
  }, [enhancedJobs, searchQuery, filters]);

  const handleApply = async (formData: ApplyFormData) => {
    try {
      setIsApplying(true);
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Mark job as applied in favorites
      if (formData.jobId) {
        await markApplied(formData.jobId);
      }
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4 mb-4">
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">Job Search</h1>
              <p className="text-sm text-gray-600">
                {filteredJobs.length} jobs match your criteria
              </p>
            </div>

            {/* Sort options */}
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">Sort by:</label>
              <select
                value={filters.sortBy || 'match'}
                onChange={(e) =>
                  setFilters({ ...filters, sortBy: e.target.value as any })
                }
                className="px-3 py-1 border border-gray-300 rounded-lg text-sm"
              >
                <option value="match">Match Score</option>
                <option value="salary">Salary</option>
                <option value="recency">Most Recent</option>
                <option value="company">Company</option>
              </select>
            </div>
          </div>

          {/* Search bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search jobs by title, company, or keywords..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <FilterSidebar
              onFilterChange={(newFilters) => setFilters({ ...filters, ...newFilters })}
              locations={getUniqueLocations()}
              roles={getUniqueRoles()}
              levels={getUniqueLevels().map((l) => l)}
              industries={getUniqueIndustries()}
            />
          </div>

          {/* Job listings */}
          <div className="lg:col-span-3">
            {filteredJobs.length === 0 ? (
              <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
                <p className="text-gray-600 mb-2">No jobs found matching your criteria</p>
                <p className="text-sm text-gray-500">Try adjusting your filters or search query</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredJobs.map((job) => (
                  <JobCard
                    key={job.id}
                    job={job}
                    onOpenDetails={setSelectedJobForDetails}
                    onOpenApply={setSelectedJobForApply}
                    isSaved={isSaved(job.id)}
                    onToggleSave={toggleSave}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      {selectedJobForDetails && (
        <JobDetailsModal
          job={selectedJobForDetails}
          isOpen={true}
          onClose={() => setSelectedJobForDetails(null)}
          onApply={() => {
            setSelectedJobForDetails(null);
            setSelectedJobForApply(selectedJobForDetails);
          }}
          isSaved={isSaved(selectedJobForDetails.id)}
          onToggleSave={toggleSave}
        />
      )}

      {selectedJobForApply && (
        <ApplyModal
          job={selectedJobForApply}
          isOpen={true}
          onClose={() => setSelectedJobForApply(null)}
          onApply={handleApply}
        />
      )}
    </div>
  );
}
