'use client';

import { useState } from 'react';
import { Plus, Globe, AlertTriangle, CheckCircle, Trash2, TestTubes } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

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

interface ScraperConfigurationProps {
  scrapers: Scraper[];
  onEnable: (id: string) => Promise<void>;
  onDisable: (id: string) => Promise<void>;
  onTest: (id: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onApprove: (id: string) => Promise<void>;
  onCreate: () => void;
}

const SCRAPER_INFO = {
  usajobs: { name: 'USAJOBS', description: 'Official US federal government jobs API', riskLevel: 'low' },
  ziprecruiter: { name: 'ZipRecruiter', description: 'ZipRecruiter official API', riskLevel: 'low' },
  theirstack: { name: 'TheirStack', description: 'Aggregator with legal partnerships', riskLevel: 'low' },
  linkedin: { name: 'LinkedIn', description: 'LinkedIn job scraper', riskLevel: 'high' },
  indeed: { name: 'Indeed', description: 'Indeed.com job scraper', riskLevel: 'high' },
  glassdoor: { name: 'Glassdoor', description: 'Glassdoor job scraper', riskLevel: 'critical' },
};

function RiskBadge({ level }: { level: 'low' | 'high' | 'critical' }) {
  if (level === 'low') {
    return <Badge className="bg-green-100 text-green-800">✓ Safe</Badge>;
  }
  if (level === 'high') {
    return <Badge variant="destructive" className="bg-amber-100 text-amber-800">⚠️ High Risk</Badge>;
  }
  return <Badge variant="destructive">🚫 Critical Risk</Badge>;
}

function ApprovalStatus({ approved, riskLevel }: { approved: boolean; riskLevel: string }) {
  if (riskLevel === 'low') return null;

  return (
    <div className="flex items-center gap-2 rounded-md bg-amber-50 p-2 text-xs">
      {approved ? (
        <>
          <CheckCircle className="h-3.5 w-3.5 text-green-600" />
          <span className="text-green-700">Legal approval: ✓ Approved</span>
        </>
      ) : (
        <>
          <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
          <span className="text-amber-700">Legal approval: ⚠️ Requires review</span>
        </>
      )}
    </div>
  );
}

export function ScraperConfiguration({
  scrapers,
  onEnable,
  onDisable,
  onTest,
  onDelete,
  onApprove,
  onCreate,
}: ScraperConfigurationProps) {
  const [loading, setLoading] = useState<{ [key: string]: boolean }>({});

  const handleAction = async (id: string, action: () => Promise<void>) => {
    setLoading(prev => ({ ...prev, [id]: true }));
    try {
      await action();
    } finally {
      setLoading(prev => ({ ...prev, [id]: false }));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Job Scrapers</h2>
          <p className="text-sm text-muted-foreground">Configure and manage automated job data sources</p>
        </div>
        <Button onClick={onCreate} size="sm">
          <Plus className="mr-2 h-4 w-4" /> Add scraper
        </Button>
      </div>

      {/* Scrapers List */}
      <div className="space-y-3">
        {scrapers.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-8">
              <Globe className="mb-2 h-8 w-8 text-muted-foreground" />
              <p className="text-muted-foreground">No scrapers configured yet</p>
              <Button onClick={onCreate} variant="link" size="sm" className="mt-2">
                Add your first scraper
              </Button>
            </CardContent>
          </Card>
        ) : (
          scrapers.map((scraper) => {
            const info = SCRAPER_INFO[scraper.sourceType];
            const isLoading = loading[scraper.id];

            return (
              <Card key={scraper.id} className={scraper.riskLevel === 'critical' ? 'border-red-200' : ''}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    {/* Left: Scraper Info */}
                    <div className="flex-1 space-y-3">
                      {/* Title & Status */}
                      <div className="flex items-center gap-3">
                        <Globe className="h-5 w-5 text-muted-foreground shrink-0" />
                        <div>
                          <h3 className="font-semibold">{info.name}</h3>
                          <p className="text-xs text-muted-foreground">{info.description}</p>
                        </div>
                        <div className="ml-auto flex items-center gap-2">
                          <RiskBadge level={scraper.riskLevel} />
                          {scraper.enabled ? (
                            <Badge className="bg-green-100 text-green-800">● Active</Badge>
                          ) : (
                            <Badge variant="secondary">○ Inactive</Badge>
                          )}
                        </div>
                      </div>

                      {/* Stats Grid */}
                      <div className="grid grid-cols-3 gap-4 rounded-lg bg-muted/30 p-3">
                        <div className="text-xs">
                          <p className="font-medium text-muted-foreground">Schedule</p>
                          <p className="font-bold">Every {scraper.pollHours}h</p>
                        </div>
                        <div className="text-xs">
                          <p className="font-medium text-muted-foreground">Last run</p>
                          <p className="font-mono text-[11px] font-bold">{scraper.lastRun || '—'}</p>
                        </div>
                        <div className="text-xs">
                          <p className="font-medium text-muted-foreground">Next run</p>
                          <p className="font-mono text-[11px] font-bold">{scraper.nextRun || '—'}</p>
                        </div>
                      </div>

                      {/* Approval Status */}
                      {scraper.riskLevel !== 'low' && (
                        <ApprovalStatus approved={scraper.legalApproved} riskLevel={scraper.riskLevel} />
                      )}

                      {/* API Key Status */}
                      <div className="text-xs">
                        {scraper.hasApiKey ? (
                          <p className="text-green-700">✓ API key configured</p>
                        ) : (
                          <p className="text-amber-700">⚠️ API key required</p>
                        )}
                      </div>
                    </div>

                    {/* Right: Actions */}
                    <div className="flex flex-col gap-2">
                      {scraper.riskLevel !== 'low' && !scraper.legalApproved && (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={isLoading}
                          onClick={() => handleAction(scraper.id, () => onApprove(scraper.id))}
                        >
                          {isLoading ? '...' : 'Approve'}
                        </Button>
                      )}

                      <Button
                        size="sm"
                        variant="outline"
                        disabled={isLoading}
                        onClick={() => handleAction(scraper.id, () => onTest(scraper.id))}
                      >
                        <TestTubes className="mr-1 h-3.5 w-3.5" />
                        {isLoading ? 'Testing...' : 'Test'}
                      </Button>

                      {scraper.enabled ? (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={isLoading}
                          onClick={() => handleAction(scraper.id, () => onDisable(scraper.id))}
                        >
                          {isLoading ? '...' : 'Disable'}
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          disabled={isLoading}
                          onClick={() => handleAction(scraper.id, () => onEnable(scraper.id))}
                        >
                          {isLoading ? '...' : 'Enable'}
                        </Button>
                      )}

                      <Button
                        size="sm"
                        variant="ghost"
                        disabled={isLoading}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        onClick={() => handleAction(scraper.id, () => onDelete(scraper.id))}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}
