'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { JobFilterCriteria } from '@/types/jobs';
import { X, ChevronDown } from 'lucide-react';

interface JobFiltersProps {
  criteria: JobFilterCriteria;
  onChange: (criteria: JobFilterCriteria) => void;
  locations?: string[];
  industries?: string[];
}

export function JobFilters({
  criteria,
  onChange,
  locations = [
    'Remote',
    'San Francisco, CA',
    'New York, NY',
    'Austin, TX',
    'Seattle, WA',
    'Los Angeles, CA',
    'Chicago, IL',
  ],
  industries = [
    'Technology',
    'Finance',
    'Healthcare',
    'Retail',
    'Telecommunications',
    'Manufacturing',
    'Energy',
  ],
}: JobFiltersProps) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [localCriteria, setLocalCriteria] = useState(criteria);

  useEffect(() => {
    setLocalCriteria(criteria);
  }, [criteria]);

  const handleApplyFilters = () => {
    onChange(localCriteria);
  };

  const handleClearFilters = () => {
    const cleared: JobFilterCriteria = {
      locations: [],
      roles: [],
      jobTypes: [],
      levels: [],
      industries: [],
      includeHiddenGems: false,
      sortBy: 'match',
      sortOrder: 'desc',
    };
    setLocalCriteria(cleared);
    onChange(cleared);
  };

  const toggleLocation = (location: string) => {
    setLocalCriteria((prev) => ({
      ...prev,
      locations: prev.locations.includes(location)
        ? prev.locations.filter((l) => l !== location)
        : [...prev.locations, location],
    }));
  };

  const toggleIndustry = (industry: string) => {
    setLocalCriteria((prev) => ({
      ...prev,
      industries: prev.industries.includes(industry)
        ? prev.industries.filter((i) => i !== industry)
        : [...prev.industries, industry],
    }));
  };

  const toggleJobType = (type: string) => {
    setLocalCriteria((prev) => ({
      ...prev,
      jobTypes: (prev.jobTypes as string[]).includes(type)
        ? (prev.jobTypes as string[]).filter((t) => t !== type)
        : [...(prev.jobTypes as string[]), type],
    }));
  };

  const toggleLevel = (level: string) => {
    setLocalCriteria((prev) => ({
      ...prev,
      levels: (prev.levels as string[]).includes(level)
        ? (prev.levels as string[]).filter((l) => l !== level)
        : [...(prev.levels as string[]), level],
    }));
  };

  const activeFilterCount =
    localCriteria.locations.length +
    localCriteria.industries.length +
    (localCriteria.jobTypes?.length ?? 0) +
    (localCriteria.levels?.length ?? 0) +
    (localCriteria.matchScoreMin ? 1 : 0) +
    (localCriteria.salaryMin ? 1 : 0);

  return (
    <Card className="sticky top-4">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Filters</CardTitle>
          {activeFilterCount > 0 && (
            <Badge variant="secondary" className="text-xs">
              {activeFilterCount} active
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Search by Role */}
        <div>
          <label className="block text-sm font-medium mb-2">Role</label>
          <input
            type="text"
            placeholder="Search roles..."
            value={localCriteria.searchQuery ?? ''}
            onChange={(e) =>
              setLocalCriteria((prev) => ({
                ...prev,
                searchQuery: e.target.value,
              }))
            }
            className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            aria-label="Search jobs by role"
          />
        </div>

        {/* Match Score Range */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Match Score: {localCriteria.matchScoreMin ?? 0}% - {localCriteria.matchScoreMax ?? 100}%
          </label>
          <div className="space-y-2">
            <input
              type="range"
              min="0"
              max="100"
              value={localCriteria.matchScoreMin ?? 0}
              onChange={(e) =>
                setLocalCriteria((prev) => ({
                  ...prev,
                  matchScoreMin: parseInt(e.target.value),
                }))
              }
              className="w-full"
              aria-label="Minimum match score"
            />
            <input
              type="range"
              min="0"
              max="100"
              value={localCriteria.matchScoreMax ?? 100}
              onChange={(e) =>
                setLocalCriteria((prev) => ({
                  ...prev,
                  matchScoreMax: parseInt(e.target.value),
                }))
              }
              className="w-full"
              aria-label="Maximum match score"
            />
          </div>
        </div>

        {/* Salary Range */}
        <div>
          <label className="block text-sm font-medium mb-2">Salary Range</label>
          <div className="space-y-2">
            <input
              type="number"
              placeholder="Min salary"
              value={localCriteria.salaryMin ?? ''}
              onChange={(e) =>
                setLocalCriteria((prev) => ({
                  ...prev,
                  salaryMin: e.target.value ? parseInt(e.target.value) : undefined,
                }))
              }
              className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              aria-label="Minimum salary"
            />
            <input
              type="number"
              placeholder="Max salary"
              value={localCriteria.salaryMax ?? ''}
              onChange={(e) =>
                setLocalCriteria((prev) => ({
                  ...prev,
                  salaryMax: e.target.value ? parseInt(e.target.value) : undefined,
                }))
              }
              className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              aria-label="Maximum salary"
            />
          </div>
        </div>

        {/* Locations */}
        <div>
          <button
            onClick={() => setExpanded(expanded === 'locations' ? null : 'locations')}
            className="w-full flex items-center justify-between py-2 font-medium text-sm"
            aria-label="Toggle location filter"
          >
            <span>Locations ({localCriteria.locations.length})</span>
            <ChevronDown
              className={`h-4 w-4 transition-transform ${
                expanded === 'locations' ? 'rotate-180' : ''
              }`}
            />
          </button>
          {expanded === 'locations' && (
            <div className="space-y-2 mt-2 pl-2 border-l">
              {locations.map((location) => (
                <label key={location} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={localCriteria.locations.includes(location)}
                    onChange={() => toggleLocation(location)}
                    className="rounded"
                    aria-label={`Filter by ${location}`}
                  />
                  <span>{location}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Job Types */}
        <div>
          <button
            onClick={() => setExpanded(expanded === 'jobTypes' ? null : 'jobTypes')}
            className="w-full flex items-center justify-between py-2 font-medium text-sm"
            aria-label="Toggle job type filter"
          >
            <span>Job Type ({localCriteria.jobTypes?.length ?? 0})</span>
            <ChevronDown
              className={`h-4 w-4 transition-transform ${
                expanded === 'jobTypes' ? 'rotate-180' : ''
              }`}
            />
          </button>
          {expanded === 'jobTypes' && (
            <div className="space-y-2 mt-2 pl-2 border-l">
              {['full-time', 'contract', 'part-time', 'temporary'].map((type) => (
                <label key={type} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={(localCriteria.jobTypes as string[]).includes(type)}
                    onChange={() => toggleJobType(type)}
                    className="rounded"
                    aria-label={`Filter by ${type} positions`}
                  />
                  <span className="capitalize">{type}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Levels */}
        <div>
          <button
            onClick={() => setExpanded(expanded === 'levels' ? null : 'levels')}
            className="w-full flex items-center justify-between py-2 font-medium text-sm"
            aria-label="Toggle seniority level filter"
          >
            <span>Level ({localCriteria.levels?.length ?? 0})</span>
            <ChevronDown
              className={`h-4 w-4 transition-transform ${
                expanded === 'levels' ? 'rotate-180' : ''
              }`}
            />
          </button>
          {expanded === 'levels' && (
            <div className="space-y-2 mt-2 pl-2 border-l">
              {['entry', 'mid', 'senior', 'lead', 'executive'].map((level) => (
                <label key={level} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={(localCriteria.levels as string[]).includes(level)}
                    onChange={() => toggleLevel(level)}
                    className="rounded"
                    aria-label={`Filter by ${level} positions`}
                  />
                  <span className="capitalize">{level}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Industries */}
        <div>
          <button
            onClick={() => setExpanded(expanded === 'industries' ? null : 'industries')}
            className="w-full flex items-center justify-between py-2 font-medium text-sm"
            aria-label="Toggle industry filter"
          >
            <span>Industries ({localCriteria.industries.length})</span>
            <ChevronDown
              className={`h-4 w-4 transition-transform ${
                expanded === 'industries' ? 'rotate-180' : ''
              }`}
            />
          </button>
          {expanded === 'industries' && (
            <div className="space-y-2 mt-2 pl-2 border-l">
              {industries.map((industry) => (
                <label key={industry} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={localCriteria.industries.includes(industry)}
                    onChange={() => toggleIndustry(industry)}
                    className="rounded"
                    aria-label={`Filter by ${industry} industry`}
                  />
                  <span>{industry}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Hidden Gems */}
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={localCriteria.includeHiddenGems}
            onChange={(e) =>
              setLocalCriteria((prev) => ({
                ...prev,
                includeHiddenGems: e.target.checked,
              }))
            }
            className="rounded"
            aria-label="Include hidden gem opportunities"
          />
          <span>Include Hidden Gems</span>
        </label>

        {/* Sort Options */}
        <div>
          <label className="block text-sm font-medium mb-2">Sort By</label>
          <select
            value={localCriteria.sortBy}
            onChange={(e) =>
              setLocalCriteria((prev) => ({
                ...prev,
                sortBy: e.target.value as typeof prev.sortBy,
              }))
            }
            className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            aria-label="Sort jobs by"
          >
            <option value="match">Best Match</option>
            <option value="salary">Highest Salary</option>
            <option value="recency">Most Recent</option>
            <option value="company">Company Name</option>
          </select>
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-4 border-t">
          <Button
            onClick={handleApplyFilters}
            className="flex-1"
            size="sm"
          >
            Apply
          </Button>
          {activeFilterCount > 0 && (
            <Button
              onClick={handleClearFilters}
              variant="outline"
              size="sm"
              className="flex-1"
            >
              Clear
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
