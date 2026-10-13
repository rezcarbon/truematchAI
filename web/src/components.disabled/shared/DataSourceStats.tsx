'use client';

import Link from 'next/link';
import { Globe, Upload, TrendingUp, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface DataSourceStatsProps {
  jobsUploaded?: number;
  jobsScraped?: number;
  activeScrapers?: number;
  scraperErrors?: number;
  uploadBatches?: number;
}

export function DataSourceStats({
  jobsUploaded = 0,
  jobsScraped = 0,
  activeScrapers = 0,
  scraperErrors = 0,
  uploadBatches = 0,
}: DataSourceStatsProps) {
  const totalJobs = jobsUploaded + jobsScraped;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Globe className="h-4 w-4" />
            Data Sources
          </CardTitle>
          <Link href="/admin/uploads">
            <Button variant="ghost" size="sm" className="h-6 px-2 text-[11px]">
              Manage
            </Button>
          </Link>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 pb-4">
        {/* Total jobs */}
        <div className="flex items-center justify-between rounded-lg bg-gradient-to-r from-blue-50 to-blue-100 p-3">
          <div>
            <p className="text-xs text-blue-600 font-medium">Total jobs imported</p>
            <p className="text-lg font-bold text-blue-900">{totalJobs}</p>
          </div>
          <TrendingUp className="h-5 w-5 text-blue-600" />
        </div>

        {/* Breakdown */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <Upload className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-muted-foreground">Manual uploads</span>
            </div>
            <span className="font-bold">{jobsUploaded}</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <Globe className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-muted-foreground">From scrapers</span>
            </div>
            <span className="font-bold">{jobsScraped}</span>
          </div>
        </div>

        {/* Scraper status */}
        {activeScrapers > 0 && (
          <div className="flex items-center justify-between rounded-lg bg-muted/50 p-3 text-xs">
            <div>
              <p className="text-muted-foreground font-medium">{activeScrapers} scrapers active</p>
              {scraperErrors > 0 && (
                <p className="text-red-600 text-[10px] mt-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {scraperErrors} error{scraperErrors > 1 ? 's' : ''}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Quick actions */}
        <div className="flex gap-2 pt-1">
          <Link href="/admin/uploads" className="flex-1">
            <Button variant="outline" size="sm" className="w-full text-xs">
              <Upload className="mr-1 h-3 w-3" /> Upload
            </Button>
          </Link>
          <Link href="/admin/scrapers" className="flex-1">
            <Button variant="outline" size="sm" className="w-full text-xs">
              <Globe className="mr-1 h-3 w-3" /> Scrapers
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
