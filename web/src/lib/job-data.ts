/**
 * Sample job data for demonstration
 */

import type { Job } from '@/types/jobs';

export const sampleJobs: Job[] = [
  {
    id: 'job-1',
    title: 'Senior React Developer',
    company: 'TechCorp',
    location: 'San Francisco, CA',
    remote: 'hybrid',
    salaryMin: 150000,
    salaryMax: 200000,
    salary_currency: 'USD',
    description:
      'We are looking for an experienced React developer to lead our frontend initiatives. You will work on high-impact features and mentor junior developers.',
    requirements: [
      { skill: 'React', level: 'advanced', mandatory: true, weight: 1.0 },
      { skill: 'TypeScript', level: 'advanced', mandatory: true, weight: 0.9 },
      { skill: 'Node.js', level: 'intermediate', mandatory: false, weight: 0.5 },
      { skill: 'CSS/Tailwind', level: 'intermediate', mandatory: true, weight: 0.7 },
      { skill: 'Leadership', level: 'intermediate', mandatory: false, weight: 0.6 },
    ],
    responsibilities: [
      'Lead frontend development for new features',
      'Mentor junior developers',
      'Code review and architecture decisions',
      'Collaborate with product and design teams',
    ],
    benefits: ['Health insurance', 'Remote flexibility', '401(k)', 'Learning budget'],
    yearsOfExperienceRequired: 5,
    postedDate: new Date('2024-12-01'),
    jobType: 'full-time',
    industry: 'Technology',
    companySize: 'large',
    level: 'senior',
    tags: ['react', 'frontend', 'typescript', 'leadership'],
  },
  {
    id: 'job-2',
    title: 'Full Stack Engineer',
    company: 'StartupXYZ',
    location: 'New York, NY',
    remote: 'fully',
    salaryMin: 120000,
    salaryMax: 160000,
    description:
      'Join our fast-growing startup as a Full Stack Engineer. Work across the entire tech stack and have direct impact on our product.',
    requirements: [
      { skill: 'React', level: 'intermediate', mandatory: true, weight: 0.8 },
      { skill: 'Node.js', level: 'intermediate', mandatory: true, weight: 0.8 },
      { skill: 'MongoDB', level: 'intermediate', mandatory: false, weight: 0.6 },
      { skill: 'AWS', level: 'beginner', mandatory: false, weight: 0.4 },
    ],
    responsibilities: [
      'Build full stack features end-to-end',
      'Optimize database queries',
      'Deploy and monitor applications',
      'Contribute to infrastructure improvements',
    ],
    benefits: ['Equity', 'Health insurance', 'Flexible hours', 'Home office setup'],
    yearsOfExperienceRequired: 2,
    postedDate: new Date('2024-12-05'),
    jobType: 'full-time',
    industry: 'Technology',
    companySize: 'startup',
    level: 'mid',
    tags: ['fullstack', 'react', 'node', 'startup'],
  },
  {
    id: 'job-3',
    title: 'Data Engineer',
    company: 'DataInc',
    location: 'Remote',
    remote: 'fully',
    salaryMin: 140000,
    salaryMax: 190000,
    description:
      'Build scalable data pipelines and infrastructure. Work with petabyte-scale datasets and cutting-edge technologies.',
    requirements: [
      { skill: 'Python', level: 'advanced', mandatory: true, weight: 1.0 },
      { skill: 'SQL', level: 'advanced', mandatory: true, weight: 0.95 },
      { skill: 'Apache Spark', level: 'intermediate', mandatory: true, weight: 0.8 },
      { skill: 'AWS', level: 'intermediate', mandatory: true, weight: 0.75 },
      { skill: 'Data Warehouse', level: 'intermediate', mandatory: false, weight: 0.6 },
    ],
    responsibilities: [
      'Design and implement data pipelines',
      'Optimize query performance',
      'Mentor data engineers',
      'Collaborate with data science team',
    ],
    benefits: [
      'Competitive salary',
      'Remote work',
      'Professional development',
      'Stock options',
    ],
    yearsOfExperienceRequired: 4,
    postedDate: new Date('2024-11-28'),
    jobType: 'full-time',
    industry: 'Data & Analytics',
    companySize: 'large',
    level: 'senior',
    tags: ['data-engineering', 'python', 'spark', 'aws'],
  },
  {
    id: 'job-4',
    title: 'Product Manager',
    company: 'SaaS Corp',
    location: 'Boston, MA',
    remote: 'hybrid',
    salaryMin: 130000,
    salaryMax: 180000,
    description:
      'Lead product strategy and roadmap. Work closely with engineering and design to deliver customer value.',
    requirements: [
      { skill: 'Product Strategy', level: 'advanced', mandatory: true, weight: 1.0 },
      { skill: 'Analytics', level: 'intermediate', mandatory: true, weight: 0.8 },
      { skill: 'Technical Background', level: 'intermediate', mandatory: false, weight: 0.6 },
      { skill: 'Communication', level: 'advanced', mandatory: true, weight: 0.9 },
    ],
    responsibilities: [
      'Define product vision and strategy',
      'Manage product roadmap',
      'Conduct user research',
      'Drive cross-functional collaboration',
    ],
    benefits: [
      'Health coverage',
      'Flexible work',
      'Training budget',
      'Equity compensation',
    ],
    yearsOfExperienceRequired: 3,
    postedDate: new Date('2024-12-03'),
    jobType: 'full-time',
    industry: 'Software',
    companySize: 'medium',
    level: 'senior',
    tags: ['product-management', 'strategy', 'leadership'],
  },
  {
    id: 'job-5',
    title: 'Junior DevOps Engineer',
    company: 'CloudTech',
    location: 'Seattle, WA',
    remote: 'hybrid',
    salaryMin: 90000,
    salaryMax: 120000,
    description:
      'Start your DevOps career! We value learning and will mentor you in infrastructure and CI/CD practices.',
    requirements: [
      { skill: 'Docker', level: 'intermediate', mandatory: true, weight: 0.9 },
      { skill: 'Kubernetes', level: 'beginner', mandatory: true, weight: 0.7 },
      { skill: 'AWS', level: 'beginner', mandatory: true, weight: 0.7 },
      { skill: 'Linux', level: 'intermediate', mandatory: true, weight: 0.8 },
      { skill: 'CI/CD', level: 'beginner', mandatory: false, weight: 0.6 },
    ],
    responsibilities: [
      'Maintain and improve CI/CD pipelines',
      'Deploy and monitor applications',
      'Infrastructure automation',
      'Learn from senior DevOps team',
    ],
    benefits: ['Learning stipend', 'Health insurance', 'Certification support'],
    yearsOfExperienceRequired: 1,
    postedDate: new Date('2024-12-04'),
    jobType: 'full-time',
    industry: 'Technology',
    companySize: 'medium',
    level: 'entry',
    tags: ['devops', 'docker', 'kubernetes', 'junior'],
    isHiddenGem: true,
    hiddenGemReason: 'Great learning opportunity with mentorship despite junior level',
  },
  {
    id: 'job-6',
    title: 'ML Engineer',
    company: 'AI Labs',
    location: 'Mountain View, CA',
    remote: 'onsite',
    salaryMin: 170000,
    salaryMax: 230000,
    description: 'Work on cutting-edge machine learning models and production systems.',
    requirements: [
      { skill: 'Python', level: 'advanced', mandatory: true, weight: 1.0 },
      { skill: 'TensorFlow', level: 'advanced', mandatory: true, weight: 0.9 },
      { skill: 'Machine Learning', level: 'advanced', mandatory: true, weight: 1.0 },
      { skill: 'Statistics', level: 'advanced', mandatory: true, weight: 0.85 },
      { skill: 'Apache Spark', level: 'intermediate', mandatory: false, weight: 0.5 },
    ],
    responsibilities: [
      'Develop and train ML models',
      'Deploy models to production',
      'Research new techniques',
      'Collaborate with data scientists',
    ],
    benefits: [
      'Competitive salary',
      'Research opportunities',
      'Conference attendance',
      'Stock options',
    ],
    yearsOfExperienceRequired: 5,
    postedDate: new Date('2024-11-30'),
    jobType: 'full-time',
    industry: 'AI & Machine Learning',
    companySize: 'large',
    level: 'senior',
    tags: ['ml', 'python', 'tensorflow', 'ai'],
  },
  {
    id: 'job-7',
    title: 'QA Automation Engineer',
    company: 'QualityFirst',
    location: 'Austin, TX',
    remote: 'hybrid',
    salaryMin: 95000,
    salaryMax: 135000,
    description:
      'Build automation frameworks and ensure product quality. Work with a talented QA team.',
    requirements: [
      { skill: 'Python', level: 'intermediate', mandatory: true, weight: 0.8 },
      { skill: 'Selenium', level: 'intermediate', mandatory: true, weight: 0.85 },
      { skill: 'Testing', level: 'intermediate', mandatory: true, weight: 0.9 },
      { skill: 'CI/CD', level: 'beginner', mandatory: false, weight: 0.5 },
    ],
    responsibilities: [
      'Write and maintain automation tests',
      'Design test frameworks',
      'Execute test plans',
      'Report bugs and issues',
    ],
    benefits: ['Health insurance', 'Home office budget', 'Training programs'],
    yearsOfExperienceRequired: 2,
    postedDate: new Date('2024-12-02'),
    jobType: 'full-time',
    industry: 'Technology',
    companySize: 'medium',
    level: 'mid',
    tags: ['qa', 'automation', 'testing'],
    isHiddenGem: true,
    hiddenGemReason: 'Growing QA team with clear advancement opportunities',
  },
  {
    id: 'job-8',
    title: 'Solutions Architect',
    company: 'EnterpriseTech',
    location: 'Chicago, IL',
    remote: 'hybrid',
    salaryMin: 160000,
    salaryMax: 220000,
    description:
      'Design technical solutions for enterprise clients. Lead complex system implementations.',
    requirements: [
      { skill: 'System Design', level: 'advanced', mandatory: true, weight: 1.0 },
      { skill: 'AWS', level: 'advanced', mandatory: true, weight: 0.9 },
      { skill: 'Communication', level: 'advanced', mandatory: true, weight: 0.9 },
      { skill: 'Enterprise Architecture', level: 'intermediate', mandatory: true, weight: 0.8 },
    ],
    responsibilities: [
      'Design cloud solutions',
      'Lead technical discussions with clients',
      'Mentor engineers',
      'Manage complex projects',
    ],
    benefits: [
      'High salary',
      'Stock options',
      'Executive benefits',
      'Flexible schedule',
    ],
    yearsOfExperienceRequired: 8,
    postedDate: new Date('2024-11-29'),
    jobType: 'full-time',
    industry: 'Technology',
    companySize: 'large',
    level: 'lead',
    tags: ['architecture', 'aws', 'leadership', 'enterprise'],
  },
];

export function getJobById(jobId: string): Job | undefined {
  return sampleJobs.find((job) => job.id === jobId);
}

export function searchJobs(query: string): Job[] {
  const lowerQuery = query.toLowerCase();
  return sampleJobs.filter(
    (job) =>
      job.title.toLowerCase().includes(lowerQuery) ||
      job.company.toLowerCase().includes(lowerQuery) ||
      job.description.toLowerCase().includes(lowerQuery) ||
      job.tags.some((tag) => tag.toLowerCase().includes(lowerQuery))
  );
}

export function getUniqueLocations(): string[] {
  const locations = new Set(sampleJobs.map((job) => job.location));
  return Array.from(locations).sort();
}

export function getUniqueRoles(): string[] {
  const roles = new Set(
    sampleJobs.flatMap((job) => {
      const titleParts = job.title.split(' ').slice(0, 2);
      return titleParts.join(' ');
    })
  );
  return Array.from(roles).sort();
}

export function getUniqueLevels(): Array<'entry' | 'mid' | 'senior' | 'lead' | 'executive'> {
  const levels = new Set(sampleJobs.map((job) => job.level));
  return Array.from(levels) as Array<'entry' | 'mid' | 'senior' | 'lead' | 'executive'>;
}

export function getUniqueIndustries(): string[] {
  const industries = new Set(sampleJobs.map((job) => job.industry));
  return Array.from(industries).sort();
}
