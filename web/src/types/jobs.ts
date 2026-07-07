/**
 * Job search and capability matching types
 */

export interface Skill {
  name: string;
  proficiency: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  yearsOfExperience?: number;
}

export interface JobRequirement {
  skill: string;
  level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  mandatory: boolean;
  weight: number; // 0-1, importance multiplier
}

export interface SkillsAlignment {
  matchedSkills: {
    name: string;
    userLevel: 'beginner' | 'intermediate' | 'advanced' | 'expert';
    requiredLevel: 'beginner' | 'intermediate' | 'advanced' | 'expert';
    match: number; // 0-100
  }[];
  missingSkills: {
    name: string;
    requiredLevel: 'beginner' | 'intermediate' | 'advanced' | 'expert';
    importance: number; // 0-1
  }[];
  overqualifiedSkills: {
    name: string;
    userLevel: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  }[];
}

export interface CapabilityMatch {
  score: number; // 0-100
  matchType: 'exact' | 'strong' | 'partial' | 'hidden_gem';
  breakdown: {
    skillsMatch: number; // 0-100
    experienceMatch: number; // 0-100
    roleTransitionScore: number; // 0-100 for career pivots
    culturalFitEstimate: number; // 0-100
  };
  reasoning: string[];
}

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  remote: 'fully' | 'hybrid' | 'onsite' | 'flexible';
  salaryMin: number;
  salaryMax: number;
  salary_currency?: string;
  description: string;
  requirements: JobRequirement[];
  responsibilities: string[];
  benefits: string[];
  yearsOfExperienceRequired: number;
  postedDate: Date;
  applicationDeadline?: Date;
  jobType: 'full-time' | 'contract' | 'part-time' | 'temporary';
  industry: string;
  companySize: 'startup' | 'small' | 'medium' | 'large' | 'enterprise';
  department?: string;
  level: 'entry' | 'mid' | 'senior' | 'lead' | 'executive';
  tags: string[];
  isHiddenGem?: boolean;
  hiddenGemReason?: string;
}

export interface JobWithCapabilityMatch extends Job {
  capabilityMatch: CapabilityMatch;
  skillsAlignment: SkillsAlignment;
}

export interface JobFilterCriteria {
  searchQuery?: string;
  locations: string[];
  salaryMin?: number;
  salaryMax?: number;
  matchScoreMin?: number;
  matchScoreMax?: number;
  remote?: 'fully' | 'hybrid' | 'onsite' | 'flexible' | 'all';
  roles: string[];
  jobTypes: Array<'full-time' | 'contract' | 'part-time' | 'temporary'>;
  levels: Array<'entry' | 'mid' | 'senior' | 'lead' | 'executive'>;
  industries: string[];
  includeHiddenGems: boolean;
  sortBy: 'match' | 'salary' | 'recency' | 'company';
  sortOrder: 'asc' | 'desc';
}

export interface SavedJob {
  jobId: string;
  userId: string;
  savedAt: Date;
  appliedAt?: Date;
  status: 'saved' | 'applied' | 'rejected' | 'archived';
  notes?: string;
}

export interface JobApplication {
  id: string;
  jobId: string;
  userId: string;
  appliedAt: Date;
  status: 'applied' | 'under_review' | 'rejected' | 'interview' | 'offer';
  resumeUsed?: string;
  coverLetterText?: string;
  notes?: string;
}
