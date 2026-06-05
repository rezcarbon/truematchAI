'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { X, ChevronDown, Filter } from 'lucide-react';
import type { PipelineFilters } from '@/hooks/useFilteredPipeline';

interface FilterPanelProps {
  onFiltersChange: (filters: PipelineFilters) => Promise<void>;
  onClearFilters: () => Promise<void>;
  filteredCount: number;
  totalCount: number;
  sources?: string[];
}

const STAGES = [
  { id: 'applied', label: 'Applied' },
  { id: 'phone_screen', label: 'Phone Screen' },
  { id: 'technical', label: 'Technical' },
  { id: 'onsite', label: 'On-site' },
  { id: 'offer', label: 'Offer' },
  { id: 'hired', label: 'Hired' },
  { id: 'rejected', label: 'Rejected' },
];

const SOURCE_OPTIONS = [
  { id: 'linkedin', label: '💼 LinkedIn' },
  { id: 'referral', label: '👥 Referral' },
  { id: 'indeed', label: '📌 Indeed' },
  { id: 'glassdoor', label: '⭐ Glassdoor' },
  { id: 'company_website', label: '🌐 Company Website' },
  { id: 'recruiter_outreach', label: '📧 Recruiter Outreach' },
  { id: 'university', label: '🎓 University' },
];

export function FilterPanel({
  onFiltersChange,
  onClearFilters,
  filteredCount,
  totalCount,
  sources,
}: FilterPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  // Filter states
  const [selectedStages, setSelectedStages] = useState<string[]>([]);
  const [searchText, setSearchText] = useState('');
  const [keywordMin, setKeywordMin] = useState(0);
  const [keywordMax, setKeywordMax] = useState(100);
  const [semanticMin, setSemanticMin] = useState(0);
  const [semanticMax, setSemanticMax] = useState(100);
  const [capabilityMin, setCapabilityMin] = useState(0);
  const [capabilityMax, setCapabilityMax] = useState(100);
  const [overallMin, setOverallMin] = useState(0);
  const [overallMax, setOverallMax] = useState(100);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [dateStart, setDateStart] = useState<string>('');
  const [dateEnd, setDateEnd] = useState<string>('');

  const activeFilterCount =
    selectedStages.length +
    (searchText ? 1 : 0) +
    (keywordMin > 0 || keywordMax < 100 ? 1 : 0) +
    (semanticMin > 0 || semanticMax < 100 ? 1 : 0) +
    (capabilityMin > 0 || capabilityMax < 100 ? 1 : 0) +
    (overallMin > 0 || overallMax < 100 ? 1 : 0) +
    selectedSources.length +
    (dateStart || dateEnd ? 1 : 0);

  const handleApplyFilters = async () => {
    const filters: PipelineFilters = {};

    if (selectedStages.length > 0) {
      filters.stages = selectedStages;
    }

    if (searchText.trim()) {
      filters.searchText = searchText;
    }

    if (keywordMin > 0 || keywordMax < 100) {
      filters.scoreRange = { ...filters.scoreRange, keyword: { min: keywordMin, max: keywordMax } };
    }

    if (semanticMin > 0 || semanticMax < 100) {
      filters.scoreRange = { ...filters.scoreRange, semantic: { min: semanticMin, max: semanticMax } };
    }

    if (capabilityMin > 0 || capabilityMax < 100) {
      filters.scoreRange = { ...filters.scoreRange, capability: { min: capabilityMin, max: capabilityMax } };
    }

    if (overallMin > 0 || overallMax < 100) {
      filters.scoreRange = { ...filters.scoreRange, overall: { min: overallMin, max: overallMax } };
    }

    if (selectedSources.length > 0) {
      filters.sources = selectedSources;
    }

    if (dateStart || dateEnd) {
      filters.dateRange = {};
      if (dateStart) filters.dateRange.start = new Date(dateStart);
      if (dateEnd) filters.dateRange.end = new Date(dateEnd);
    }

    await onFiltersChange(filters);
  };

  const handleClearAll = async () => {
    setSelectedStages([]);
    setSearchText('');
    setKeywordMin(0);
    setKeywordMax(100);
    setSemanticMin(0);
    setSemanticMax(100);
    setCapabilityMin(0);
    setCapabilityMax(100);
    setOverallMin(0);
    setOverallMax(100);
    setSelectedSources([]);
    setDateStart('');
    setDateEnd('');
    await onClearFilters();
  };

  return (
    <div className="space-y-4">
      {/* Filter Summary */}
      <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-center gap-3">
          <Filter className="h-5 w-5 text-blue-600" />
          <div>
            <p className="font-medium text-sm">
              {filteredCount} of {totalCount} candidates
              {activeFilterCount > 0 && (
                <span className="text-xs text-muted-foreground ml-2">({activeFilterCount} filters active)</span>
              )}
            </p>
            {activeFilterCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearAll}
                className="h-6 px-2 text-xs mt-1"
              >
                Clear all filters
              </Button>
            )}
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowFilters(!showFilters)}
          className="gap-2"
        >
          <ChevronDown className={`h-4 w-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          {showFilters ? 'Hide' : 'Show'} Filters
        </Button>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Filter Candidates</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Search */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Search by name</label>
              <input
                type="text"
                value={searchText}
                onChange={e => setSearchText(e.target.value)}
                placeholder="Search candidate name..."
                className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>

            {/* Stages */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Pipeline Stages</label>
              <div className="grid grid-cols-2 gap-2">
                {STAGES.map(stage => (
                  <label key={stage.id} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedStages.includes(stage.id)}
                      onChange={e => {
                        if (e.target.checked) {
                          setSelectedStages([...selectedStages, stage.id]);
                        } else {
                          setSelectedStages(selectedStages.filter(s => s !== stage.id));
                        }
                      }}
                      className="rounded"
                    />
                    <span className="text-sm">{stage.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Score Ranges */}
            <div className="space-y-4">
              <h3 className="font-medium text-sm">Score Ranges</h3>

              {/* Keyword Score */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-sm">Keyword Match</label>
                  <Badge variant="outline">{keywordMin}% - {keywordMax}%</Badge>
                </div>
                <div className="flex gap-4">
                  <div className="flex-1">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={keywordMin}
                      onChange={e => setKeywordMin(Math.min(parseInt(e.target.value), keywordMax))}
                      className="w-full"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Min: {keywordMin}%</p>
                  </div>
                  <div className="flex-1">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={keywordMax}
                      onChange={e => setKeywordMax(Math.max(parseInt(e.target.value), keywordMin))}
                      className="w-full"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Max: {keywordMax}%</p>
                  </div>
                </div>
              </div>

              {/* Semantic Score */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-sm">Semantic Match</label>
                  <Badge variant="outline">{semanticMin}% - {semanticMax}%</Badge>
                </div>
                <div className="flex gap-4">
                  <div className="flex-1">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={semanticMin}
                      onChange={e => setSemanticMin(Math.min(parseInt(e.target.value), semanticMax))}
                      className="w-full"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Min: {semanticMin}%</p>
                  </div>
                  <div className="flex-1">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={semanticMax}
                      onChange={e => setSemanticMax(Math.max(parseInt(e.target.value), semanticMin))}
                      className="w-full"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Max: {semanticMax}%</p>
                  </div>
                </div>
              </div>

              {/* Capability Score */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-sm">Capability Assessment</label>
                  <Badge variant="outline">{capabilityMin}% - {capabilityMax}%</Badge>
                </div>
                <div className="flex gap-4">
                  <div className="flex-1">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={capabilityMin}
                      onChange={e => setCapabilityMin(Math.min(parseInt(e.target.value), capabilityMax))}
                      className="w-full"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Min: {capabilityMin}%</p>
                  </div>
                  <div className="flex-1">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={capabilityMax}
                      onChange={e => setCapabilityMax(Math.max(parseInt(e.target.value), capabilityMin))}
                      className="w-full"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Max: {capabilityMax}%</p>
                  </div>
                </div>
              </div>

              {/* Overall Score */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-sm">Overall Fit Score</label>
                  <Badge variant="outline">{overallMin}% - {overallMax}%</Badge>
                </div>
                <div className="flex gap-4">
                  <div className="flex-1">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={overallMin}
                      onChange={e => setOverallMin(Math.min(parseInt(e.target.value), overallMax))}
                      className="w-full"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Min: {overallMin}%</p>
                  </div>
                  <div className="flex-1">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={overallMax}
                      onChange={e => setOverallMax(Math.max(parseInt(e.target.value), overallMin))}
                      className="w-full"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Max: {overallMax}%</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Sources */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Application Source</label>
              <div className="grid grid-cols-2 gap-2">
                {SOURCE_OPTIONS.map(source => (
                  <label key={source.id} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedSources.includes(source.id)}
                      onChange={e => {
                        if (e.target.checked) {
                          setSelectedSources([...selectedSources, source.id]);
                        } else {
                          setSelectedSources(selectedSources.filter(s => s !== source.id));
                        }
                      }}
                      className="rounded"
                    />
                    <span className="text-sm">{source.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Date Range */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Applied Date Range</label>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-muted-foreground">From</label>
                  <input
                    type="date"
                    value={dateStart}
                    onChange={e => setDateStart(e.target.value)}
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                  />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground">To</label>
                  <input
                    type="date"
                    value={dateEnd}
                    onChange={e => setDateEnd(e.target.value)}
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                  />
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4 border-t">
              <Button onClick={handleApplyFilters} className="flex-1">
                Apply Filters
              </Button>
              {activeFilterCount > 0 && (
                <Button onClick={handleClearAll} variant="outline" className="flex-1">
                  <X className="h-4 w-4 mr-2" />
                  Clear All
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
