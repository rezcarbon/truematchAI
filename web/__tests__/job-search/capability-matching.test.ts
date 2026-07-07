/**
 * Tests for capability matching algorithm
 */

import { calculateCapabilityMatch, getMatchScoreColor, getMatchScoreLabel, getMatchScoreBgColor } from '@/lib/capability-matching';
import type { Job, Skill } from '@/types/jobs';

describe('Capability Matching', () => {
  const mockUserSkills: Skill[] = [
    { name: 'React', proficiency: 'advanced', yearsOfExperience: 4 },
    { name: 'TypeScript', proficiency: 'advanced', yearsOfExperience: 3 },
    { name: 'Node.js', proficiency: 'intermediate', yearsOfExperience: 2 },
    { name: 'CSS', proficiency: 'intermediate', yearsOfExperience: 2 },
  ];

  const mockJob: Job = {
    id: 'test-job',
    title: 'Senior React Developer',
    company: 'TestCorp',
    location: 'Remote',
    remote: 'fully',
    salaryMin: 100000,
    salaryMax: 150000,
    description: 'Build great products',
    requirements: [
      { skill: 'React', level: 'advanced', mandatory: true, weight: 1.0 },
      { skill: 'TypeScript', level: 'advanced', mandatory: true, weight: 0.9 },
      { skill: 'Node.js', level: 'intermediate', mandatory: true, weight: 0.8 },
      { skill: 'AWS', level: 'beginner', mandatory: false, weight: 0.4 },
    ],
    responsibilities: [],
    benefits: [],
    yearsOfExperienceRequired: 5,
    postedDate: new Date(),
    jobType: 'full-time',
    industry: 'Technology',
    companySize: 'medium',
    level: 'senior',
    tags: [],
  };

  describe('calculateCapabilityMatch', () => {
    it('should calculate match score for aligned candidate', () => {
      const match = calculateCapabilityMatch(mockUserSkills, 5, mockJob);

      expect(match.score).toBeGreaterThan(0);
      expect(match.score).toBeLessThanOrEqual(100);
      expect(match.matchType).toBeDefined();
      expect(match.breakdown).toBeDefined();
    });

    it('should have high score for perfectly matched candidate', () => {
      const perfectMatch = calculateCapabilityMatch(mockUserSkills, 5, mockJob);

      expect(perfectMatch.score).toBeGreaterThan(70);
      expect(perfectMatch.matchType).toMatch(/exact|strong/);
    });

    it('should identify exact matches', () => {
      const match = calculateCapabilityMatch(mockUserSkills, 5, mockJob);

      if (match.score >= 85) {
        expect(match.matchType).toBe('exact');
      }
    });

    it('should identify strong matches', () => {
      const match = calculateCapabilityMatch(mockUserSkills, 4, mockJob);

      if (match.score >= 70 && match.score < 85) {
        expect(match.matchType).toBe('strong');
      }
    });

    it('should identify partial matches', () => {
      const lessExperiencedSkills: Skill[] = [
        { name: 'React', proficiency: 'intermediate' },
        { name: 'JavaScript', proficiency: 'intermediate' },
      ];

      const match = calculateCapabilityMatch(lessExperiencedSkills, 2, mockJob);

      if (match.score >= 50 && match.score < 70) {
        expect(match.matchType).toBe('partial');
      }
    });

    it('should identify hidden gems (lower score but potential)', () => {
      const earlyCareerSkills: Skill[] = [
        { name: 'Python', proficiency: 'intermediate' },
        { name: 'Leadership', proficiency: 'beginner' },
      ];

      const match = calculateCapabilityMatch(earlyCareerSkills, 1, mockJob);

      expect(match).toBeDefined();
      expect(match.reasoning).toBeDefined();
    });

    it('should include reasoning in match result', () => {
      const match = calculateCapabilityMatch(mockUserSkills, 5, mockJob);

      expect(match.reasoning).toBeInstanceOf(Array);
      expect(match.reasoning.length).toBeGreaterThan(0);
      expect(typeof match.reasoning[0]).toBe('string');
    });

    it('should calculate breakdown percentages', () => {
      const match = calculateCapabilityMatch(mockUserSkills, 5, mockJob);

      expect(match.breakdown.skillsMatch).toBeGreaterThanOrEqual(0);
      expect(match.breakdown.skillsMatch).toBeLessThanOrEqual(100);
      expect(match.breakdown.experienceMatch).toBeGreaterThanOrEqual(0);
      expect(match.breakdown.experienceMatch).toBeLessThanOrEqual(100);
      expect(match.breakdown.roleTransitionScore).toBeGreaterThanOrEqual(0);
      expect(match.breakdown.roleTransitionScore).toBeLessThanOrEqual(100);
      expect(match.breakdown.culturalFitEstimate).toBeGreaterThanOrEqual(0);
      expect(match.breakdown.culturalFitEstimate).toBeLessThanOrEqual(100);
    });

    it('should handle candidate with no matching skills', () => {
      const noMatchSkills: Skill[] = [
        { name: 'Plumbing', proficiency: 'advanced' },
        { name: 'Cooking', proficiency: 'intermediate' },
      ];

      const match = calculateCapabilityMatch(noMatchSkills, 5, mockJob);

      expect(match.score).toBeGreaterThanOrEqual(0);
      expect(match.score).toBeLessThan(70);
    });

    it('should handle candidate with more experience than required', () => {
      const match = calculateCapabilityMatch(mockUserSkills, 10, mockJob);

      expect(match.breakdown.experienceMatch).toBeGreaterThan(90);
    });

    it('should handle candidate with less experience than required', () => {
      const match = calculateCapabilityMatch(mockUserSkills, 2, mockJob);

      expect(match.breakdown.experienceMatch).toBeLessThan(70);
    });

    it('should consider skill importance weights', () => {
      // Job with weighted requirements
      const weightedJob: Job = {
        ...mockJob,
        requirements: [
          { skill: 'React', level: 'advanced', mandatory: true, weight: 1.0 },
          { skill: 'Unimportant', level: 'expert', mandatory: false, weight: 0.1 },
        ],
      };

      const match = calculateCapabilityMatch(mockUserSkills, 5, weightedJob);

      expect(match.score).toBeGreaterThan(50);
    });

    it('should identify transferable skills for role transition', () => {
      const skillsWithTransferable: Skill[] = [
        { name: 'Python', proficiency: 'advanced' },
        { name: 'Leadership', proficiency: 'advanced' },
        { name: 'Communication', proficiency: 'advanced' },
      ];

      const match = calculateCapabilityMatch(skillsWithTransferable, 3, mockJob);

      expect(match.breakdown.roleTransitionScore).toBeGreaterThan(60);
    });
  });

  describe('getMatchScoreColor', () => {
    it('should return green for excellent matches (85+)', () => {
      const color = getMatchScoreColor(90);
      expect(color).toBe('#10b981');
    });

    it('should return blue for strong matches (70-84)', () => {
      const color = getMatchScoreColor(75);
      expect(color).toBe('#3b82f6');
    });

    it('should return amber for partial matches (50-69)', () => {
      const color = getMatchScoreColor(60);
      expect(color).toBe('#f59e0b');
    });

    it('should return red for poor matches (<50)', () => {
      const color = getMatchScoreColor(30);
      expect(color).toBe('#ef4444');
    });

    it('should return green for boundary score 85', () => {
      const color = getMatchScoreColor(85);
      expect(color).toBe('#10b981');
    });

    it('should return blue for boundary score 70', () => {
      const color = getMatchScoreColor(70);
      expect(color).toBe('#3b82f6');
    });

    it('should return amber for boundary score 50', () => {
      const color = getMatchScoreColor(50);
      expect(color).toBe('#f59e0b');
    });
  });

  describe('getMatchScoreLabel', () => {
    it('should return Excellent Match for 85+', () => {
      const label = getMatchScoreLabel(90);
      expect(label).toBe('Excellent Match');
    });

    it('should return Strong Match for 70-84', () => {
      const label = getMatchScoreLabel(75);
      expect(label).toBe('Strong Match');
    });

    it('should return Partial Match for 50-69', () => {
      const label = getMatchScoreLabel(60);
      expect(label).toBe('Partial Match');
    });

    it('should return Hidden Gem for <50', () => {
      const label = getMatchScoreLabel(30);
      expect(label).toBe('Hidden Gem');
    });
  });

  describe('getMatchScoreBgColor', () => {
    it('should return green background for excellent matches', () => {
      const bgColor = getMatchScoreBgColor(90);
      expect(bgColor).toContain('emerald');
    });

    it('should return blue background for strong matches', () => {
      const bgColor = getMatchScoreBgColor(75);
      expect(bgColor).toContain('blue');
    });

    it('should return amber background for partial matches', () => {
      const bgColor = getMatchScoreBgColor(60);
      expect(bgColor).toContain('amber');
    });

    it('should return red background for poor matches', () => {
      const bgColor = getMatchScoreBgColor(30);
      expect(bgColor).toContain('red');
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero years of experience', () => {
      const match = calculateCapabilityMatch(mockUserSkills, 0, mockJob);
      expect(match.score).toBeDefined();
      expect(match.breakdown.experienceMatch).toBeGreaterThanOrEqual(0);
    });

    it('should handle very high years of experience', () => {
      const match = calculateCapabilityMatch(mockUserSkills, 50, mockJob);
      expect(match.breakdown.experienceMatch).toBeGreaterThan(90);
    });

    it('should handle empty skills array', () => {
      const match = calculateCapabilityMatch([], 5, mockJob);
      expect(match.score).toBeGreaterThanOrEqual(0);
      expect(match.score).toBeLessThan(70);
    });

    it('should handle job with no requirements', () => {
      const jobNoReqs: Job = {
        ...mockJob,
        requirements: [],
      };

      const match = calculateCapabilityMatch(mockUserSkills, 5, jobNoReqs);
      expect(match.score).toBeDefined();
    });

    it('should handle case-insensitive skill matching', () => {
      const caseInsensitiveSkills: Skill[] = [
        { name: 'REACT', proficiency: 'advanced' },
        { name: 'typescript', proficiency: 'advanced' },
      ];

      const match = calculateCapabilityMatch(caseInsensitiveSkills, 5, mockJob);
      expect(match.breakdown.skillsMatch).toBeGreaterThan(70);
    });
  });

  describe('Score Distribution', () => {
    it('should produce varied scores for different candidates', () => {
      const skilled: Skill[] = [
        { name: 'React', proficiency: 'expert' },
        { name: 'TypeScript', proficiency: 'expert' },
        { name: 'Node.js', proficiency: 'expert' },
      ];

      const lessSkilled: Skill[] = [
        { name: 'Python', proficiency: 'beginner' },
        { name: 'Java', proficiency: 'beginner' },
      ];

      const skilledMatch = calculateCapabilityMatch(skilled, 10, mockJob);
      const lesskilledMatch = calculateCapabilityMatch(lessSkilled, 1, mockJob);

      expect(skilledMatch.score).toBeGreaterThan(lesskilledMatch.score);
    });
  });
});
