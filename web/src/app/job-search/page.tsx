/**
 * Job search page
 */

'use client';

export const dynamic = 'force-dynamic';

import React from 'react';
import nextDynamic from 'next/dynamic';
import type { Skill } from '@/types/jobs';

// The job browser is a fully client-side, stateful widget with no server data.
// Render it client-only so the production build doesn't try to prerender it.
const JobBrowser = nextDynamic(
  () => import('@/components/job-search/JobBrowser').then((m) => m.JobBrowser),
  { ssr: false },
);

export default function JobSearchPage() {
  // Mock user skills - in production, these would come from user profile
  const userSkills: Skill[] = [
    { name: 'React', proficiency: 'advanced', yearsOfExperience: 4 },
    { name: 'TypeScript', proficiency: 'advanced', yearsOfExperience: 3 },
    { name: 'Node.js', proficiency: 'intermediate', yearsOfExperience: 2 },
    { name: 'Python', proficiency: 'intermediate', yearsOfExperience: 2 },
    { name: 'AWS', proficiency: 'beginner', yearsOfExperience: 1 },
    { name: 'Leadership', proficiency: 'intermediate', yearsOfExperience: 2 },
    { name: 'Communication', proficiency: 'advanced', yearsOfExperience: 5 },
  ];

  return (
    <main className="min-h-screen bg-gray-50">
      <JobBrowser userSkills={userSkills} yearsOfExperience={5} />
    </main>
  );
}
