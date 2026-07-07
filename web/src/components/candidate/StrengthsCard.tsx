'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ExternalLink } from 'lucide-react';

interface Strength {
  name: string;
  proficiency: number; // 1-10
  evidence: {
    type: 'GitHub' | 'ORCID' | 'DOI' | 'LinkedIn' | 'Patents';
    url: string;
    description?: string;
  }[];
}

interface StrengthsCardProps {
  strengths: Strength[];
  loading?: boolean;
}

export function StrengthsCard({ strengths, loading = false }: StrengthsCardProps) {
  const getProficiencyColor = (level: number) => {
    if (level >= 8) return 'bg-green-100 text-green-800';
    if (level >= 5) return 'bg-blue-100 text-blue-800';
    return 'bg-amber-100 text-amber-800';
  };

  const getProficiencyLabel = (level: number) => {
    if (level >= 9) return 'Expert';
    if (level >= 7) return 'Advanced';
    if (level >= 5) return 'Intermediate';
    return 'Beginner';
  };

  const evidenceIcons = {
    GitHub: '🐙',
    ORCID: '🔬',
    DOI: '📄',
    LinkedIn: '💼',
    Patents: '🏆',
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Strengths</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-muted rounded w-3/4 mb-2" />
                <div className="h-3 bg-muted rounded w-1/2" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (strengths.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Strengths</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No verified strengths identified yet.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Strengths</CardTitle>
        <p className="text-xs text-muted-foreground mt-1">
          Verified skills with linked evidence
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {strengths.map((strength, idx) => (
          <div key={idx} className="border-b last:border-0 pb-4 last:pb-0">
            <div className="flex items-start justify-between mb-2">
              <div>
                <h4 className="font-medium text-sm">{strength.name}</h4>
                <div className="flex items-center gap-2 mt-1">
                  <span
                    className={`text-xs px-2 py-1 rounded-full ${getProficiencyColor(
                      strength.proficiency
                    )}`}
                  >
                    {getProficiencyLabel(strength.proficiency)} ({strength.proficiency}/10)
                  </span>
                </div>
              </div>
            </div>

            {strength.evidence.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {strength.evidence.map((ev, evIdx) => (
                  <a
                    key={evIdx}
                    href={ev.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-primary/5 text-primary text-xs font-medium hover:bg-primary/10 transition-colors"
                    aria-label={`View evidence on ${ev.type}`}
                  >
                    <span>{evidenceIcons[ev.type]}</span>
                    <span>{ev.type}</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
