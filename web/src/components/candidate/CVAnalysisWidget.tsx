import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Sparkles, ArrowRight, TrendingUp } from 'lucide-react';

interface CVAnalysisWidgetProps {
  recentAnalysisCount?: number;
  avgScore?: number;
  lastAnalysisTitle?: string;
  lastAnalysisScore?: number;
}

export function CVAnalysisWidget({
  recentAnalysisCount = 0,
  avgScore = 0,
  lastAnalysisTitle,
  lastAnalysisScore,
}: CVAnalysisWidgetProps) {
  return (
    <Card className="overflow-hidden border-l-4 border-l-blue-600">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-blue-600" />
            CV Analysis
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Stats */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-lg bg-blue-50/60 p-3">
            <p className="text-xs font-semibold text-muted-foreground uppercase">
              Analyses Run
            </p>
            <p className="text-2xl font-bold text-blue-600">{recentAnalysisCount}</p>
          </div>
          <div className="rounded-lg bg-emerald-50/60 p-3">
            <p className="text-xs font-semibold text-muted-foreground uppercase">
              Avg Score
            </p>
            <p className="text-2xl font-bold text-emerald-600">
              {avgScore > 0 ? `${avgScore}` : '—'}
            </p>
          </div>
        </div>

        {/* Recent Analysis Preview */}
        {lastAnalysisTitle && (
          <div className="space-y-2 rounded-lg border border-blue-200/40 bg-blue-50/30 p-3">
            <p className="text-xs font-semibold text-muted-foreground">Latest Analysis</p>
            <p className="text-sm font-medium text-foreground truncate">{lastAnalysisTitle}</p>
            {lastAnalysisScore && (
              <div className="flex items-center gap-2">
                <TrendingUp className="h-3 w-3 text-blue-600" />
                <p className="text-xs text-muted-foreground">
                  Score: <span className="font-semibold text-foreground">{lastAnalysisScore}</span>
                </p>
              </div>
            )}
          </div>
        )}

        {/* CTA Button */}
        <Link href="/candidate/cv-analysis" className="block">
          <Button variant="default" className="w-full" size="sm">
            {recentAnalysisCount > 0 ? 'New Analysis' : 'Start Analysis'}
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </Link>

        {/* Helper Text */}
        <p className="text-xs text-muted-foreground text-center">
          Upload your CV and compare against job descriptions
        </p>
      </CardContent>
    </Card>
  );
}
