'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/AppShell';
import { ScraperConfiguration } from '@/components/admin/ScraperConfiguration';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, Loader2, Plus } from 'lucide-react';
import { api } from '@/lib/api';

interface Scraper {
  id: string;
  sourceType: 'usajobs' | 'linkedin' | 'indeed' | 'glassdoor' | 'ziprecruiter' | 'theirstack';
  enabled: boolean;
  pollHours: number;
  lastRun?: string;
  nextRun?: string;
  jobsFound?: number;
  legalApproved: boolean;
  hasApiKey: boolean;
  riskLevel: 'low' | 'high' | 'critical';
}

export default function ScrapersPage() {
  const [scrapers, setScrapers] = useState<Scraper[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    loadScrapers();
  }, []);

  const loadScrapers = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.getScrapers();
      setScrapers((response.scrapers || []) as unknown as Scraper[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scrapers');
      console.error('Error loading scrapers:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEnable = async (id: string) => {
    try {
      await api.updateScraper(id, { enabled: true });
      await loadScrapers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to enable scraper');
    }
  };

  const handleDisable = async (id: string) => {
    try {
      await api.updateScraper(id, { enabled: false });
      await loadScrapers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disable scraper');
    }
  };

  const handleTest = async (id: string) => {
    try {
      const result = await api.testScraper(id);
      if (result.status === 'ok') {
        alert(`✓ ${(result as { source?: string }).source} scraper is working correctly`);
      } else {
        alert(`✗ ${(result as { source?: string }).source} scraper test failed`);
      }
    } catch (err) {
      alert(`Error testing scraper: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this scraper configuration?')) return;
    try {
      await api.deleteScraper(id);
      await loadScrapers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete scraper');
    }
  };

  const handleApprove = async (id: string) => {
    if (!confirm('This will approve legal requirements for this scraper. Continue?')) return;
    try {
      await api.updateScraper(id, {
        config: { legal_approved: true }
      });
      await loadScrapers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve scraper');
    }
  };

  const handleCreate = () => {
    setIsCreating(true);
    // TODO: Open scraper creation dialog
    // For now, show a message
    alert('Scraper creation dialog coming soon. Use API to create manually for now.');
    setIsCreating(false);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Job Scrapers"
        subtitle="Configure and manage automated job data sources. All scrapers run on a schedule and feed jobs into the platform."
      />

      {/* Error Banner */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="flex items-start gap-3 p-4">
            <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-red-900">Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
              <Button
                size="sm"
                variant="outline"
                className="mt-3 text-red-700 border-red-300 hover:bg-red-100"
                onClick={() => setError(null)}
              >
                Dismiss
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {isLoading ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-8 w-8 text-muted-foreground animate-spin mb-2" />
            <p className="text-muted-foreground">Loading scrapers...</p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Info Card */}
          <Card className="border-blue-200 bg-blue-50">
            <CardContent className="p-4">
              <p className="text-sm text-blue-900">
                <strong>Safe APIs (Ready to use):</strong> USAJOBS, ZipRecruiter, TheirStack — no legal review needed.
              </p>
              <p className="text-sm text-amber-900 mt-2">
                <strong>Direct Scrapers (Legal approval required):</strong> LinkedIn, Indeed, Glassdoor — requires legal team sign-off.
              </p>
            </CardContent>
          </Card>

          {/* Scraper Configuration Component */}
          <ScraperConfiguration
            scrapers={scrapers}
            onEnable={handleEnable}
            onDisable={handleDisable}
            onTest={handleTest}
            onDelete={handleDelete}
            onApprove={handleApprove}
            onCreate={handleCreate}
          />

          {/* Run History Section */}
          {scrapers.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recent Scraper Runs</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground">
                  <p>Scraper run history coming soon. Check back after first scheduled runs.</p>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
