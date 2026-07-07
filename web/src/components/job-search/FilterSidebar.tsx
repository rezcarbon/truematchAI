'use client';

/**
 * Job filter sidebar
 */

import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import type { JobFilterCriteria } from '@/types/jobs';

interface FilterSidebarProps {
  onFilterChange: (filters: Partial<JobFilterCriteria>) => void;
  locations: string[];
  roles: string[];
  levels: string[];
  industries: string[];
}

interface FilterSectionProps {
  title: string;
  options: string[];
  selected: string[];
  onChange: (selected: string[]) => void;
  collapsible?: boolean;
}

function FilterSection({ title, options, selected, onChange, collapsible = true }: FilterSectionProps) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="border-b border-gray-200 py-4">
      <button
        onClick={() => collapsible && setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full"
      >
        <h3 className="font-semibold text-gray-900 text-sm">{title}</h3>
        {collapsible && (
          <ChevronDown
            className="w-4 h-4 text-gray-500 transition-transform"
            style={{ transform: isOpen ? 'rotate(0deg)' : 'rotate(-90deg)' }}
          />
        )}
      </button>

      {isOpen && (
        <div className="mt-3 space-y-2">
          {options.map((option) => (
            <label key={option} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selected.includes(option)}
                onChange={(e) => {
                  if (e.target.checked) {
                    onChange([...selected, option]);
                  } else {
                    onChange(selected.filter((s) => s !== option));
                  }
                }}
                className="rounded border-gray-300"
              />
              <span className="text-sm text-gray-700">{option}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

export function FilterSidebar({
  onFilterChange,
  locations,
  roles,
  levels,
  industries,
}: FilterSidebarProps) {
  const [selectedLocations, setSelectedLocations] = useState<string[]>([]);
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);
  const [selectedLevels, setSelectedLevels] = useState<string[]>([]);
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>([]);
  const [salaryMin, setSalaryMin] = useState<string>('');
  const [salaryMax, setSalaryMax] = useState<string>('');
  const [matchMin, setMatchMin] = useState<string>('');
  const [remote, setRemote] = useState<string>('all');

  const handleLocationChange = (locs: string[]) => {
    setSelectedLocations(locs);
    onFilterChange({ locations: locs });
  };

  const handleRoleChange = (roles: string[]) => {
    setSelectedRoles(roles);
    onFilterChange({ roles });
  };

  const handleLevelChange = (lvls: string[]) => {
    setSelectedLevels(lvls);
    onFilterChange({ levels: lvls as any });
  };

  const handleIndustryChange = (inds: string[]) => {
    setSelectedIndustries(inds);
    onFilterChange({ industries: inds });
  };

  const handleSalaryChange = () => {
    onFilterChange({
      salaryMin: salaryMin ? parseInt(salaryMin) : undefined,
      salaryMax: salaryMax ? parseInt(salaryMax) : undefined,
    });
  };

  const handleMatchChange = () => {
    onFilterChange({ matchScoreMin: matchMin ? parseInt(matchMin) : undefined });
  };

  const handleRemoteChange = (value: string) => {
    setRemote(value);
    onFilterChange({ remote: value as any });
  };

  const handleReset = () => {
    setSelectedLocations([]);
    setSelectedRoles([]);
    setSelectedLevels([]);
    setSelectedIndustries([]);
    setSalaryMin('');
    setSalaryMax('');
    setMatchMin('');
    setRemote('all');
    onFilterChange({
      locations: [],
      roles: [],
      levels: [],
      industries: [],
      salaryMin: undefined,
      salaryMax: undefined,
      matchScoreMin: undefined,
      remote: 'all',
    });
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 h-fit max-h-[calc(100vh-120px)] overflow-y-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-bold text-gray-900">Filters</h2>
        <button
          onClick={handleReset}
          className="text-xs text-blue-600 hover:text-blue-700 font-medium"
        >
          Reset
        </button>
      </div>

      {/* Salary Range */}
      <div className="border-b border-gray-200 py-4">
        <h3 className="font-semibold text-gray-900 text-sm mb-3">Salary Range</h3>
        <div className="space-y-2">
          <div>
            <label className="text-xs text-gray-600">Min</label>
            <div className="flex items-center gap-2">
              <span className="text-xs">$</span>
              <input
                type="number"
                value={salaryMin}
                onChange={(e) => setSalaryMin(e.target.value)}
                onBlur={handleSalaryChange}
                placeholder="50000"
                className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-600">Max</label>
            <div className="flex items-center gap-2">
              <span className="text-xs">$</span>
              <input
                type="number"
                value={salaryMax}
                onChange={(e) => setSalaryMax(e.target.value)}
                onBlur={handleSalaryChange}
                placeholder="250000"
                className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Match Score */}
      <div className="border-b border-gray-200 py-4">
        <h3 className="font-semibold text-gray-900 text-sm mb-3">Match Score</h3>
        <div className="flex items-center gap-2">
          <input
            type="number"
            min="0"
            max="100"
            value={matchMin}
            onChange={(e) => setMatchMin(e.target.value)}
            onBlur={handleMatchChange}
            placeholder="0"
            className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
          />
          <span className="text-xs text-gray-600">+</span>
        </div>
      </div>

      {/* Remote */}
      <div className="border-b border-gray-200 py-4">
        <h3 className="font-semibold text-gray-900 text-sm mb-3">Work Mode</h3>
        <select
          value={remote}
          onChange={(e) => handleRemoteChange(e.target.value)}
          className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
        >
          <option value="all">All Work Modes</option>
          <option value="fully">Fully Remote</option>
          <option value="hybrid">Hybrid</option>
          <option value="onsite">On-site</option>
          <option value="flexible">Flexible</option>
        </select>
      </div>

      {/* Locations */}
      <FilterSection
        title="Location"
        options={locations.slice(0, 8)}
        selected={selectedLocations}
        onChange={handleLocationChange}
      />

      {/* Roles */}
      <FilterSection
        title="Role"
        options={roles}
        selected={selectedRoles}
        onChange={handleRoleChange}
      />

      {/* Levels */}
      <FilterSection
        title="Level"
        options={levels}
        selected={selectedLevels}
        onChange={handleLevelChange}
      />

      {/* Industries */}
      <FilterSection
        title="Industry"
        options={industries}
        selected={selectedIndustries}
        onChange={handleIndustryChange}
      />
    </div>
  );
}
