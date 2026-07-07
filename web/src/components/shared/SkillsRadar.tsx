'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts';

interface SkillRadarData {
  skill: string;
  candidate: number; // 0-100
  required: number; // 0-100
}

interface SkillsRadarProps {
  data: SkillRadarData[];
  loading?: boolean;
  title?: string;
  subtitle?: string;
}

export function SkillsRadar({
  data,
  loading = false,
  title = 'Skills Alignment',
  subtitle = 'Your skills vs. job requirements',
}: SkillsRadarProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{title}</CardTitle>
          {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <p className="text-sm text-muted-foreground">Loading visualization...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{title}</CardTitle>
          {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <p className="text-sm text-muted-foreground">No skill data available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Prepare data for radar chart - limit to top 8 skills for readability
  const chartData = data.slice(0, 8).map((item) => ({
    skill: item.skill.length > 15 ? item.skill.substring(0, 12) + '...' : item.skill,
    fullSkill: item.skill,
    candidate: Math.round(item.candidate),
    required: Math.round(item.required),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
        {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
      </CardHeader>
      <CardContent>
        <div className="w-full h-96">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={chartData} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
              <PolarGrid stroke="hsl(var(--muted-foreground))" opacity={0.2} />
              <PolarAngleAxis
                dataKey="skill"
                tick={{ fontSize: 12 }}
                tick={{ fill: 'hsl(var(--muted-foreground))' }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 100]}
                tick={{ fontSize: 12 }}
                tick={{ fill: 'hsl(var(--muted-foreground))' }}
              />
              <Radar
                name="Your Level"
                dataKey="candidate"
                stroke="hsl(var(--primary))"
                fill="hsl(var(--primary))"
                fillOpacity={0.5}
              />
              <Radar
                name="Required Level"
                dataKey="required"
                stroke="hsl(var(--muted-foreground))"
                fill="hsl(var(--muted-foreground))"
                fillOpacity={0.2}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Legend and Summary */}
        <div className="mt-6 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-primary" />
              <span className="text-sm text-muted-foreground">Your Skills</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-muted" />
              <span className="text-sm text-muted-foreground">Required</span>
            </div>
          </div>

          {/* Skill Details */}
          <div className="mt-4 space-y-2 max-h-40 overflow-y-auto">
            {data.map((item, idx) => {
              const gap = Math.max(0, item.required - item.candidate);
              const aligned = item.candidate >= item.required;

              return (
                <div
                  key={idx}
                  className="text-xs border rounded p-2 flex items-center justify-between"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{item.skill}</p>
                    <div className="flex gap-2 text-muted-foreground text-xs mt-1">
                      <span>You: {Math.round(item.candidate)}</span>
                      <span>•</span>
                      <span>Need: {Math.round(item.required)}</span>
                    </div>
                  </div>
                  <div className="flex-shrink-0 ml-2">
                    {aligned ? (
                      <span className="text-green-600 font-semibold text-xs">✓</span>
                    ) : (
                      <span className="text-amber-600 font-semibold text-xs">+{Math.round(gap)}</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
