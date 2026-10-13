import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Zap, ArrowRight, BarChart3 } from 'lucide-react';

interface JDSimulationWidgetProps {
  recentSimulationCount?: number;
  avgQualityScore?: number;
  lastSimulationTitle?: string;
  lastSimulationScore?: number;
}

export function JDSimulationWidget({
  recentSimulationCount = 0,
  avgQualityScore = 0,
  lastSimulationTitle,
  lastSimulationScore,
}: JDSimulationWidgetProps) {
  return (
    <Card className="overflow-hidden border-l-4 border-l-amber-600">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-amber-600" />
            JD Simulation
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Stats */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-lg bg-amber-50/60 p-3">
            <p className="text-xs font-semibold text-muted-foreground uppercase">
              Simulations Run
            </p>
            <p className="text-2xl font-bold text-amber-600">{recentSimulationCount}</p>
          </div>
          <div className="rounded-lg bg-emerald-50/60 p-3">
            <p className="text-xs font-semibold text-muted-foreground uppercase">
              Avg Quality
            </p>
            <p className="text-2xl font-bold text-emerald-600">
              {avgQualityScore > 0 ? `${avgQualityScore}` : '—'}
            </p>
          </div>
        </div>

        {/* Recent Simulation Preview */}
        {lastSimulationTitle && (
          <div className="space-y-2 rounded-lg border border-amber-200/40 bg-amber-50/30 p-3">
            <p className="text-xs font-semibold text-muted-foreground">Latest Simulation</p>
            <p className="text-sm font-medium text-foreground truncate">{lastSimulationTitle}</p>
            {lastSimulationScore && (
              <div className="flex items-center gap-2">
                <BarChart3 className="h-3 w-3 text-amber-600" />
                <p className="text-xs text-muted-foreground">
                  Quality: <span className="font-semibold text-foreground">{lastSimulationScore}/100</span>
                </p>
              </div>
            )}
          </div>
        )}

        {/* CTA Button */}
        <Link href="/recruiter/jd-simulation" className="block">
          <Button variant="default" className="w-full" size="sm">
            {recentSimulationCount > 0 ? 'New Simulation' : 'Start Simulation'}
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </Link>

        {/* Helper Text */}
        <p className="text-xs text-muted-foreground text-center">
          Test your job descriptions for quality and candidate fit
        </p>
      </CardContent>
    </Card>
  );
}
