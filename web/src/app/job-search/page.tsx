/**
 * Job search page
 */

'use client';

import React from 'react';
import { JobBrowser } from '@/components/job-search/JobBrowser';
import type { Skill } from '@/types/jobs';

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
