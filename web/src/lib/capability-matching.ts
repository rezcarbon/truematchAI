/**
 * Capability matching algorithm for job-candidate alignment
 */

import type { Job, Skill, CapabilityMatch, SkillsAlignment, JobRequirement } from '@/types/jobs';

const PROFICIENCY_LEVELS = {
  beginner: 1,
  intermediate: 2,
  advanced: 3,
  expert: 4,
};

type ProficiencyLevel = keyof typeof PROFICIENCY_LEVELS;

function getProficiencyScore(level: ProficiencyLevel): number {
  return PROFICIENCY_LEVELS[level];
}

function calculateSkillMatch(userLevel: ProficiencyLevel, requiredLevel: ProficiencyLevel): number {
  const userScore = getProficiencyScore(userLevel);
  const requiredScore = getProficiencyScore(requiredLevel);

  if (userScore >= requiredScore) {
    return 100; // Meets or exceeds requirement
  }

  // Partial credit for being close
  const gap = requiredScore - userScore;
  return Math.max(50, 100 - gap * 20);
}

export function calculateCapabilityMatch(
  userSkills: Skill[],
  yearsOfExperience: number,
  job: Job
): CapabilityMatch {
  // Calculate skills alignment
  const skillsAlignment = calculateSkillsAlignment(userSkills, job.requirements);

  // Build match components
  const skillsMatchScore = calculateSkillsMatchScore(skillsAlignment);
  const experienceMatch = calculateExperienceMatch(yearsOfExperience, job.yearsOfExperienceRequired);
  const roleTransitionScore = calculateRoleTransitionScore(userSkills, job);
  const culturalFitEstimate = calculateCulturalFit(userSkills, job);

  // Weighted average
  const weights = {
    skillsMatch: 0.45,
    experienceMatch: 0.25,
    roleTransition: 0.15,
    culturalFit: 0.15,
  };

  const finalScore = Math.round(
    skillsMatchScore * weights.skillsMatch +
      experienceMatch * weights.experienceMatch +
      roleTransitionScore * weights.roleTransition +
      culturalFitEstimate * weights.culturalFit
  );

  // Determine match type
  let matchType: CapabilityMatch['matchType'] = 'exact';
  if (finalScore >= 85) matchType = 'exact';
  else if (finalScore >= 70) matchType = 'strong';
  else if (finalScore >= 50) matchType = 'partial';
  else matchType = 'hidden_gem';

  // Build reasoning
  const reasoning = buildReasoning(
    finalScore,
    skillsAlignment,
    experienceMatch,
    roleTransitionScore
  );

  return {
    score: finalScore,
    matchType,
    breakdown: {
      skillsMatch: Math.round(skillsMatchScore),
      experienceMatch: Math.round(experienceMatch),
      roleTransitionScore: Math.round(roleTransitionScore),
      culturalFitEstimate: Math.round(culturalFitEstimate),
    },
    reasoning,
  };
}

function calculateSkillsAlignment(
  userSkills: Skill[],
  requirements: JobRequirement[]
): SkillsAlignment {
  const userSkillMap = new Map(userSkills.map((s) => [s.name.toLowerCase(), s]));

  const matchedSkills = [];
  const missingSkills = [];
  const overqualifiedSkills = [];

  for (const req of requirements) {
    const userSkill = userSkillMap.get(req.skill.toLowerCase());

    if (userSkill) {
      const match = calculateSkillMatch(userSkill.proficiency, req.level);
      matchedSkills.push({
        name: req.skill,
        userLevel: userSkill.proficiency,
        requiredLevel: req.level,
        match,
      });

      // Check if overqualified
      if (
        getProficiencyScore(userSkill.proficiency) >
        getProficiencyScore(req.level) + 1
      ) {
        overqualifiedSkills.push({
          name: req.skill,
          userLevel: userSkill.proficiency,
        });
      }
    } else if (req.mandatory) {
      missingSkills.push({
        name: req.skill,
        requiredLevel: req.level,
        importance: req.weight,
      });
    }
  }

  return {
    matchedSkills,
    missingSkills,
    overqualifiedSkills,
  };
}

function calculateSkillsMatchScore(alignment: SkillsAlignment): number {
  if (alignment.matchedSkills.length === 0) {
    return 0;
  }

  const totalMatch = alignment.matchedSkills.reduce((sum, skill) => sum + skill.match, 0);
  return totalMatch / alignment.matchedSkills.length;
}

function calculateExperienceMatch(userExperience: number, requiredExperience: number): number {
  if (userExperience >= requiredExperience) {
    return Math.min(100, 100 + (userExperience - requiredExperience) * 2);
  }

  const yearsShort = requiredExperience - userExperience;
  return Math.max(40, 100 - yearsShort * 15);
}

function calculateRoleTransitionScore(userSkills: Skill[], job: Job): number {
  // If transitioning to a different type of role, evaluate transferable skills
  const relevantSkills = userSkills.filter((s) =>
    s.name.toLowerCase().includes('python') ||
    s.name.toLowerCase().includes('communication') ||
    s.name.toLowerCase().includes('leadership') ||
    s.name.toLowerCase().includes('analysis')
  );

  return Math.min(100, 60 + relevantSkills.length * 10);
}

function calculateCulturalFit(userSkills: Skill[], job: Job): number {
  // Basic estimation based on job characteristics
  let score = 70; // Base score

  // Add points for relevant soft skills
  const softSkills = userSkills.filter((s) =>
    s.name.toLowerCase().match(/(leadership|communication|collaboration|mentoring)/i)
  );

  score += softSkills.length * 5;

  // Consider job seniority
  if (job.level === 'lead' || job.level === 'executive') {
    if (userSkills.some((s) => s.name.toLowerCase().includes('leadership'))) {
      score += 10;
    }
  }

  return Math.min(100, score);
}

function buildReasoning(
  score: number,
  alignment: SkillsAlignment,
  experienceMatch: number,
  roleTransition: number
): string[] {
  const reasoning: string[] = [];

  if (alignment.matchedSkills.length > 0) {
    const highMatches = alignment.matchedSkills.filter((s) => s.match >= 90);
    if (highMatches.length > 0) {
      reasoning.push(
        `Strong match in ${highMatches.length} key skill(s): ${highMatches
          .map((s) => s.name)
          .join(', ')}`
      );
    }
  }

  if (alignment.missingSkills.length > 0) {
    const mandatoryMissing = alignment.missingSkills.filter((s) => s.importance > 0.7);
    if (mandatoryMissing.length > 0) {
      reasoning.push(
        `Missing some required skills: ${mandatoryMissing.map((s) => s.name).join(', ')}`
      );
    }
  }

  if (experienceMatch >= 90) {
    reasoning.push('Excellent experience level for this role');
  } else if (experienceMatch >= 70) {
    reasoning.push('Adequate experience for this role');
  } else if (experienceMatch >= 50) {
    reasoning.push('Slightly below required experience but learnable');
  }

  if (roleTransition > 75) {
    reasoning.push('Strong transferable skills for career progression');
  }

  if (alignment.overqualifiedSkills.length > 2) {
    reasoning.push('Overqualified in several areas - room for growth possible');
  }

  if (score >= 85) {
    reasoning.push('Highly recommended candidate');
  } else if (score >= 70) {
    reasoning.push('Good fit with minor gaps');
  } else if (score >= 50) {
    reasoning.push('Hidden gem - potential beyond traditional qualification matching');
  }

  return reasoning;
}

// Color coding for match scores
export function getMatchScoreColor(score: number): string {
  if (score >= 85) return '#10b981'; // emerald-500
  if (score >= 70) return '#3b82f6'; // blue-500
  if (score >= 50) return '#f59e0b'; // amber-500
  return '#ef4444'; // red-500
}

export function getMatchScoreBgColor(score: number): string {
  if (score >= 85) return 'bg-emerald-50 border-emerald-200';
  if (score >= 70) return 'bg-blue-50 border-blue-200';
  if (score >= 50) return 'bg-amber-50 border-amber-200';
  return 'bg-red-50 border-red-200';
}

export function getMatchScoreLabel(score: number): string {
  if (score >= 85) return 'Excellent Match';
  if (score >= 70) return 'Strong Match';
  if (score >= 50) return 'Partial Match';
  return 'Hidden Gem';
}
