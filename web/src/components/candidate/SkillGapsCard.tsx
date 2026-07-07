'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, BookOpen } from 'lucide-react';

interface SkillGap {
  name: string;
  importance: 'Critical' | 'Important' | 'Nice-to-have';
  weeksToLearn: number;
  learningResources: {
    title: string;
    url: string;
    type: 'Course' | 'Tutorial' | 'Documentation' | 'Book';
  }[];
  description?: string;
}

interface SkillGapsCardProps {
  gaps: SkillGap[];
  loading?: boolean;
}

export function SkillGapsCard({ gaps, loading = false }: SkillGapsCardProps) {
  const getImportanceBadgeVariant = (importance: string) => {
    switch (importance) {
      case 'Critical':
        return 'destructive';
      case 'Important':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case 'Critical':
        return 'border-l-red-500';
      case 'Important':
        return 'border-l-amber-500';
      default:
        return 'border-l-blue-500';
    }
  };

  const resourceIcons = {
    Course: '🎓',
    Tutorial: '📺',
    Documentation: '📚',
    Book: '📖',
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Skill Gaps</CardTitle>
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

  if (gaps.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Skill Gaps</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No significant skill gaps identified!</p>
        </CardContent>
      </Card>
    );
  }

  // Sort by importance
  const sortedGaps = [...gaps].sort((a, b) => {
    const importanceOrder = { Critical: 0, Important: 1, 'Nice-to-have': 2 };
    return importanceOrder[a.importance] - importanceOrder[b.importance];
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Skill Gaps</CardTitle>
        <p className="text-xs text-muted-foreground mt-1">
          Skills to develop for your target role
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {sortedGaps.map((gap, idx) => (
          <div
            key={idx}
            className={`border-l-4 pl-4 py-3 ${getImportanceColor(gap.importance)} bg-muted/30 rounded`}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <h4 className="font-medium text-sm">{gap.name}</h4>
                {gap.description && (
                  <p className="text-xs text-muted-foreground mt-1">{gap.description}</p>
                )}
              </div>
              <Badge variant={getImportanceBadgeVariant(gap.importance)} className="ml-2 flex-shrink-0">
                {gap.importance}
              </Badge>
            </div>

            <div className="flex items-center gap-2 text-xs text-muted-foreground mt-2 mb-3">
              <span className="font-medium">
                ⏱️ {gap.weeksToLearn} week{gap.weeksToLearn !== 1 ? 's' : ''}
              </span>
            </div>

            {gap.learningResources.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                  <BookOpen className="h-3 w-3" />
                  Learning Resources:
                </p>
                <div className="flex flex-wrap gap-2">
                  {gap.learningResources.map((resource, resIdx) => (
                    <a
                      key={resIdx}
                      href={resource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-background border border-border text-xs hover:bg-accent transition-colors"
                      aria-label={`Open ${resource.type}: ${resource.title}`}
                    >
                      <span>{resourceIcons[resource.type]}</span>
                      <span className="truncate max-w-[150px]">{resource.title}</span>
                      <ExternalLink className="h-3 w-3 flex-shrink-0" />
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
