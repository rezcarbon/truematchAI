'use client';

import Link from 'next/link';
import { Globe, AlertCircle, Activity, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface Scraper {
  name: string;
  status: 'active' | 'inactive' | 'error';
  lastRun?: string;
  jobsFound?: number;
}

interface ScraperHealthCardProps {
  scrapers?: Scraper[];
  totalScrapers?: number;
  activeScrapers?: number;
  errorCount?: number;
}

export function ScraperHealthCard({
  scrapers = [],
  totalScrapers = 0,
  activeScrapers = 0,
  errorCount = 0,
}: ScraperHealthCardProps) {
  const hasErrors = errorCount > 0;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Globe className="h-4 w-4" />
            Scraper Health
          </CardTitle>
          <Link href="/admin/scrapers">
            <Button variant="ghost" size="sm" className="h-6 px-2 text-[11px]">
              Manage
            </Button>
          </Link>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 pb-4">
        {/* Status overview */}
        {totalScrapers > 0 && (
          <div className={`flex items-center justify-between rounded-lg p-3 ${hasErrors ? 'bg-red-50' : 'bg-green-50'}`}>
            <div>
              <p className={`text-xs font-medium ${hasErrors ? 'text-red-600' : 'text-green-600'}`}>
                {activeScrapers}/{totalScrapers} scrapers active
              </p>
              {hasErrors && (
                <p className="text-[10px] text-red-700 mt-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {errorCount} error{errorCount > 1 ? 's' : ''}
                </p>
              )}
            </div>
            <span className={`inline-block h-3 w-3 rounded-full ${hasErrors ? 'bg-red-500' : 'bg-green-500'} animate-pulse`} />
          </div>
        )}

        {/* Scrapers list */}
        {scrapers.length > 0 ? (
          <div className="space-y-1.5">
            {scrapers.slice(0, 3).map((scraper) => (
              <div key={scraper.name} className="flex items-center gap-2 text-xs rounded-md p-2 hover:bg-muted transition-colors">
                <div
                  className={`inline-block h-2 w-2 rounded-full shrink-0 ${
                    scraper.status === 'active'
                      ? 'bg-green-500'
                      : scraper.status === 'error'
                        ? 'bg-red-500'
                        : 'bg-gray-400'
                  }`}
                />
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{scraper.name}</p>
                  {scraper.lastRun && (
                    <p className="text-[10px] text-muted-foreground">Last: {scraper.lastRun}</p>
                  )}
                </div>
                {scraper.jobsFound !== undefined && scraper.status === 'active' && (
                  <p className="text-[10px] font-bold text-blue-600 shrink-0">{scraper.jobsFound}</p>
                )}
              </div>
            ))}
            {scrapers.length > 3 && (
              <p className="text-[10px] text-muted-foreground text-center pt-1">
                +{scrapers.length - 3} more
              </p>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-4 text-muted-foreground">
            <Globe className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-xs">No scrapers configured</p>
          </div>
        )}

        {/* Quick stats */}
        {totalScrapers > 0 && (
          <div className="flex gap-2 text-xs pt-1">
            <div className="flex-1 rounded-lg bg-muted/50 p-2 text-center">
              <Activity className="h-3 w-3 inline-block mr-1 text-blue-600" />
              <span className="text-muted-foreground">Running</span>
            </div>
            <div className="flex-1 rounded-lg bg-muted/50 p-2 text-center">
              <Clock className="h-3 w-3 inline-block mr-1 text-amber-600" />
              <span className="text-muted-foreground">Scheduled</span>
            </div>
          </div>
        )}

        {/* Action button */}
        {totalScrapers === 0 && (
          <Link href="/admin/scrapers" className="block">
            <Button variant="outline" size="sm" className="w-full text-xs">
              <Globe className="mr-1 h-3 w-3" /> Configure scrapers
            </Button>
          </Link>
        )}
      </CardContent>
    </Card>
  );
}
