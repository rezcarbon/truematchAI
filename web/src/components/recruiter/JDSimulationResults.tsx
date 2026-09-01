import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { JDQualityCard } from '@/components/recruiter/JDQualityCard';
import {
  Plus,
  RefreshCw,
  FileSearch,
  TrendingUp,
  AlertTriangle,
  CheckCircle2
} from 'lucide-react';
import Link from 'next/link';

interface JDQuality {
  score: number;
  flags: Array<{
    type: string;
    text: string;
    severity: 'high' | 'medium' | 'low';
  }>;
}

interface JDSimulationResultsProps {
  jdQuality: JDQuality;
  positionTitle?: string;
  jdText?: string;
  simulationId?: string;
}

export function JDSimulationResults({
  jdQuality,
  positionTitle = 'Untitled Position',
  jdText,
  simulationId,
}: JDSimulationResultsProps) {
  const flagsBySeverity = [
    ...jdQuality.flags.filter((f) => f.severity === 'high'),
    ...jdQuality.flags.filter((f) => f.severity === 'medium'),
    ...jdQuality.flags.filter((f) => f.severity === 'low'),
  ];

  return (
    <>
      {/* Main Results */}
      <div className="max-w-5xl space-y-8">
        {/* JD Quality Card */}
        <Card>
          <CardHeader>
            <CardTitle>Simulation Results for {positionTitle}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">JD Quality Score</h3>
                <Badge variant="secondary">{jdQuality.score}/100</Badge>
              </div>
              {jdQuality.flags.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Issues Found</p>
                  {jdQuality.flags.map((flag, idx) => (
                    <div key={idx} className="text-sm p-2 bg-muted rounded">
                      <p className="font-medium">{flag.text}</p>
                      <p className="text-xs text-muted-foreground mt-1">{flag.type}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Detailed Findings */}
        {flagsBySeverity.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-600" />
                Issues Found ({flagsBySeverity.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {flagsBySeverity.map((flag, idx) => {
                const severityColor =
                  flag.severity === 'high'
                    ? 'bg-red-50/60 border-red-200/60'
                    : flag.severity === 'medium'
                    ? 'bg-amber-50/60 border-amber-200/60'
                    : 'bg-blue-50/60 border-blue-200/60';

                return (
                  <div
                    key={idx}
                    className={`rounded-lg border p-4 space-y-2 ${severityColor}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-medium">{flag.text}</p>
                      <Badge
                        variant={
                          flag.severity === 'high'
                            ? 'destructive'
                            : flag.severity === 'medium'
                            ? 'secondary'
                            : 'outline'
                        }
                      >
                        {flag.severity}
                      </Badge>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        )}

        {/* Key Insights */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-blue-600" />
              Key Insights
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-lg border p-4 space-y-2">
                <p className="text-xs font-semibold text-muted-foreground uppercase">
                  Overall Quality
                </p>
                <p className="text-2xl font-bold">{jdQuality.score}/100</p>
                <p className="text-sm text-muted-foreground">
                  {jdQuality.score >= 80
                    ? 'Excellent job description'
                    : jdQuality.score >= 60
                    ? 'Good job description, minor improvements needed'
                    : 'Job description needs significant improvements'}
                </p>
              </div>
              <div className="rounded-lg border p-4 space-y-2">
                <p className="text-xs font-semibold text-muted-foreground uppercase">
                  Recommendations
                </p>
                <p className="text-2xl font-bold">{flagsBySeverity.length}</p>
                <p className="text-sm text-muted-foreground">
                  {flagsBySeverity.length === 0
                    ? 'No issues found'
                    : `${flagsBySeverity.filter((f) => f.severity === 'high').length} high priority`}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Next Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Next Steps</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <Link href="/recruiter/positions/new">
                <Button
                  variant="outline"
                  className="w-full h-auto flex flex-col items-center gap-3 p-4 hover:bg-accent"
                >
                  <Plus className="h-5 w-5" />
                  <div className="text-center">
                    <p className="text-sm font-medium">Create Position</p>
                    <p className="text-xs text-muted-foreground">
                      Post this as a new role
                    </p>
                  </div>
                </Button>
              </Link>

              <Link href="/recruiter/jd-quality">
                <Button
                  variant="outline"
                  className="w-full h-auto flex flex-col items-center gap-3 p-4 hover:bg-accent"
                >
                  <FileSearch className="h-5 w-5" />
                  <div className="text-center">
                    <p className="text-sm font-medium">View All JDs</p>
                    <p className="text-xs text-muted-foreground">
                      Compare with other roles
                    </p>
                  </div>
                </Button>
              </Link>

              <Link href="/recruiter/jd-simulation">
                <Button
                  variant="outline"
                  className="w-full h-auto flex flex-col items-center gap-3 p-4 hover:bg-accent"
                >
                  <RefreshCw className="h-5 w-5" />
                  <div className="text-center">
                    <p className="text-sm font-medium">Test Another JD</p>
                    <p className="text-xs text-muted-foreground">
                      Run another simulation
                    </p>
                  </div>
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
