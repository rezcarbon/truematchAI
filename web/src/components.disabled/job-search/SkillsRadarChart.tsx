'use client';

/**
 * Skills alignment radar chart
 */

import React from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend } from 'recharts';
import type { SkillsAlignment } from '@/types/jobs';

interface SkillsRadarChartProps {
  skillsAlignment: SkillsAlignment;
  height?: number;
}

export function SkillsRadarChart({ skillsAlignment, height = 300 }: SkillsRadarChartProps) {
  // Prepare data for radar chart
  const data = skillsAlignment.matchedSkills.slice(0, 8).map((skill) => ({
    name: skill.name.substring(0, 12),
    fullName: skill.name,
    user: getSkillScore(skill.userLevel),
    required: getSkillScore(skill.requiredLevel),
  }));

  if (data.length === 0) {
    return (
      <div className="h-80 flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-gray-500">No matched skills to display</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">Skills Alignment</h3>
      <ResponsiveContainer width="100%" height={height}>
        <RadarChart data={data}>
          <PolarGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <PolarAngleAxis
            dataKey="name"
            tick={{ fontSize: 12, fill: '#6b7280' }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 4]}
            tick={{ fontSize: 12, fill: '#9ca3af' }}
          />
          <Radar
            name="Your Level"
            dataKey="user"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.6}
          />
          <Radar
            name="Required"
            dataKey="required"
            stroke="#ef4444"
            fill="#ef4444"
            fillOpacity={0.3}
          />
          <Legend wrapperStyle={{ paddingTop: '20px' }} />
        </RadarChart>
      </ResponsiveContainer>

      {/* Legend for skill levels */}
      <div className="mt-6 grid grid-cols-2 gap-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#3b82f6' }}></div>
          <span className="text-gray-700">Your Level</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#ef4444' }}></div>
          <span className="text-gray-700">Required Level</span>
        </div>
      </div>

      {/* Missing skills alert */}
      {skillsAlignment.missingSkills.length > 0 && (
        <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-xs font-semibold text-amber-900 mb-2">Missing Skills:</p>
          <div className="flex flex-wrap gap-2">
            {skillsAlignment.missingSkills.map((skill) => (
              <span
                key={skill.name}
                className="inline-flex items-center px-2 py-1 bg-amber-100 text-amber-800 rounded text-xs font-medium"
              >
                {skill.name}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Overqualified skills info */}
      {skillsAlignment.overqualifiedSkills.length > 0 && (
        <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-xs font-semibold text-green-900 mb-2">Overqualified in:</p>
          <div className="flex flex-wrap gap-2">
            {skillsAlignment.overqualifiedSkills.map((skill) => (
              <span
                key={skill.name}
                className="inline-flex items-center px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium"
              >
                {skill.name}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function getSkillScore(level: 'beginner' | 'intermediate' | 'advanced' | 'expert'): number {
  const scores = {
    beginner: 1,
    intermediate: 2,
    advanced: 3,
    expert: 4,
  };
  return scores[level];
}
