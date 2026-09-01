import React from 'react';
import { render, screen } from '@testing-library/react';
import { VersionComparison } from '@/components/resume/VersionComparison';
import type { ResumeVersion, VersionComparison as VersionComparisonType } from '@/types/resume';

describe('VersionComparison', () => {
  const versionA: ResumeVersion = {
    id: 'v1',
    resumeId: 'resume1',
    version: 1,
    fileName: 'resume_v1.pdf',
    format: 'pdf',
    fileSize: 1024,
    uploadMethod: 'drag-drop',
    status: 'completed',
    extractedText: 'John Doe Senior Developer React TypeScript',
    skills: ['React', 'TypeScript', 'CSS'],
    experience_years: 5,
    summary: 'Experienced React developer with 5 years experience',
    uploadedAt: '2024-01-01T10:00:00Z',
  };

  const versionB: ResumeVersion = {
    id: 'v2',
    resumeId: 'resume1',
    version: 2,
    fileName: 'resume_v2.pdf',
    format: 'pdf',
    fileSize: 1124,
    uploadMethod: 'drag-drop',
    status: 'completed',
    extractedText:
      'John Doe Senior Full Stack Developer React TypeScript Node.js MongoDB',
    skills: ['React', 'TypeScript', 'Node.js', 'MongoDB'],
    experience_years: 6,
    summary:
      'Experienced full stack developer with 6 years experience in modern web technologies',
    uploadedAt: '2024-01-15T10:00:00Z',
  };

  const comparison: VersionComparisonType = {
    versionA,
    versionB,
    skillsAdded: ['Node.js', 'MongoDB'],
    skillsRemoved: ['CSS'],
    experienceYearsDifference: 1,
    summaryDifference: 'Gained full stack skills',
    extractedTextDifference: 'Added Node.js and MongoDB to tech stack',
  };

  it('renders comparison header', () => {
    render(
      <VersionComparison
        versionA={versionA}
        versionB={versionB}
        comparison={comparison}
      />
    );

    expect(screen.getByText('Comparing versions')).toBeInTheDocument();
    expect(screen.getByText('v1')).toBeInTheDocument();
    expect(screen.getByText('v2')).toBeInTheDocument();
  });

  it('displays skills added', () => {
    render(
      <VersionComparison
        versionA={versionA}
        versionB={versionB}
        comparison={comparison}
      />
    );

    expect(screen.getByText('Skills Added')).toBeInTheDocument();
    expect(screen.getByText('Node.js')).toBeInTheDocument();
    expect(screen.getByText('MongoDB')).toBeInTheDocument();
  });

  it('displays skills removed', () => {
    render(
      <VersionComparison
        versionA={versionA}
        versionB={versionB}
        comparison={comparison}
      />
    );

    expect(screen.getByText('Skills Removed')).toBeInTheDocument();
    expect(screen.getByText('CSS')).toBeInTheDocument();
  });

  it('displays experience years difference', () => {
    render(
      <VersionComparison
        versionA={versionA}
        versionB={versionB}
        comparison={comparison}
      />
    );

    expect(screen.getByText('Experience Changes')).toBeInTheDocument();
    expect(screen.getByText('+1 years added')).toBeInTheDocument();
  });

  it('displays experience years for both versions', () => {
    render(
      <VersionComparison
        versionA={versionA}
        versionB={versionB}
        comparison={comparison}
      />
    );

    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('6')).toBeInTheDocument();
  });

  it('displays summary changes', () => {
    render(
      <VersionComparison
        versionA={versionA}
        versionB={versionB}
        comparison={comparison}
      />
    );

    expect(screen.getByText('Summary Changes')).toBeInTheDocument();
    expect(screen.getByText(versionA.summary)).toBeInTheDocument();
    expect(screen.getByText(versionB.summary)).toBeInTheDocument();
  });

  it('displays detailed text diff', () => {
    render(
      <VersionComparison
        versionA={versionA}
        versionB={versionB}
        comparison={comparison}
      />
    );

    expect(screen.getByText('Detailed Changes')).toBeInTheDocument();
    expect(screen.getByText(comparison.extractedTextDifference)).toBeInTheDocument();
  });

  it('handles no skills changes', () => {
    const noSkillChangesComparison: VersionComparisonType = {
      ...comparison,
      skillsAdded: [],
      skillsRemoved: [],
    };

    render(
      <VersionComparison
        versionA={versionA}
        versionB={versionB}
        comparison={noSkillChangesComparison}
      />
    );

    expect(screen.getByText('No skill changes detected.')).toBeInTheDocument();
  });

  it('handles negative experience difference', () => {
    const negativeExperienceDiff: VersionComparisonType = {
      ...comparison,
      experienceYearsDifference: -1,
    };

    render(
      <VersionComparison
        versionA={versionA}
        versionB={versionB}
        comparison={negativeExperienceDiff}
      />
    );

    expect(screen.getByText('-1 years removed')).toBeInTheDocument();
  });

  it('hides experience section when no difference', () => {
    const noExperienceDiff: VersionComparisonType = {
      ...comparison,
      experienceYearsDifference: 0,
    };

    render(
      <VersionComparison
        versionA={versionA}
        versionB={versionB}
        comparison={noExperienceDiff}
      />
    );

    expect(screen.queryByText('Experience Changes')).not.toBeInTheDocument();
  });

  it('displays summary for both versions', () => {
    render(
      <VersionComparison
        versionA={versionA}
        versionB={versionB}
        comparison={comparison}
      />
    );

    const summaryHeaders = screen.getAllByText(/v[12]/);
    expect(summaryHeaders.length).toBeGreaterThanOrEqual(2);
  });

  it('handles missing optional fields', () => {
    const minimalComparison: VersionComparisonType = {
      versionA: { ...versionA, summary: '' },
      versionB: { ...versionB, summary: '' },
      skillsAdded: [],
      skillsRemoved: [],
      experienceYearsDifference: 0,
      summaryDifference: '',
      extractedTextDifference: '',
    };

    render(
      <VersionComparison
        versionA={minimalComparison.versionA}
        versionB={minimalComparison.versionB}
        comparison={minimalComparison}
      />
    );

    expect(screen.getByText('Summary Changes')).toBeInTheDocument();
  });

  it('shows "No summary available" when summary is empty', () => {
    const noSummaryComparison: VersionComparisonType = {
      ...comparison,
      versionA: { ...versionA, summary: '' },
    };

    render(
      <VersionComparison
        versionA={noSummaryComparison.versionA}
        versionB={versionB}
        comparison={noSummaryComparison}
      />
    );

    expect(screen.getByText('No summary available')).toBeInTheDocument();
  });

  it('renders skill badges with correct styling', () => {
    const { container } = render(
      <VersionComparison
        versionA={versionA}
        versionB={versionB}
        comparison={comparison}
      />
    );

    const badges = container.querySelectorAll('[class*="badge"]');
    expect(badges.length).toBeGreaterThan(0);
  });

  it('displays multiple skills in added/removed sections', () => {
    const multiSkillComparison: VersionComparisonType = {
      ...comparison,
      skillsAdded: ['Golang', 'Docker', 'Kubernetes'],
      skillsRemoved: ['PHP', 'jQuery'],
    };

    render(
      <VersionComparison
        versionA={versionA}
        versionB={versionB}
        comparison={multiSkillComparison}
      />
    );

    expect(screen.getByText('Golang')).toBeInTheDocument();
    expect(screen.getByText('Docker')).toBeInTheDocument();
    expect(screen.getByText('Kubernetes')).toBeInTheDocument();
    expect(screen.getByText('PHP')).toBeInTheDocument();
    expect(screen.getByText('jQuery')).toBeInTheDocument();
  });

  it('shows count of added and removed skills', () => {
    render(
      <VersionComparison
        versionA={versionA}
        versionB={versionB}
        comparison={comparison}
      />
    );

    expect(screen.getByText('Skills Added (2)')).toBeInTheDocument();
    expect(screen.getByText('Skills Removed (1)')).toBeInTheDocument();
  });

  it('displays years experience text correctly', () => {
    render(
      <VersionComparison
        versionA={versionA}
        versionB={versionB}
        comparison={comparison}
      />
    );

    const experienceText = screen.getAllByText('years experience');
    expect(experienceText.length).toBeGreaterThanOrEqual(2);
  });

  it('properly handles comparison with only added skills', () => {
    const onlyAddedComparison: VersionComparisonType = {
      ...comparison,
      skillsRemoved: [],
    };

    render(
      <VersionComparison
        versionA={versionA}
        versionB={versionB}
        comparison={onlyAddedComparison}
      />
    );

    expect(screen.getByText('Skills Added')).toBeInTheDocument();
    expect(screen.queryByText('Skills Removed')).not.toBeInTheDocument();
  });

  it('properly handles comparison with only removed skills', () => {
    const onlyRemovedComparison: VersionComparisonType = {
      ...comparison,
      skillsAdded: [],
    };

    render(
      <VersionComparison
        versionA={versionA}
        versionB={versionB}
        comparison={onlyRemovedComparison}
      />
    );

    expect(screen.queryByText('Skills Added')).not.toBeInTheDocument();
    expect(screen.getByText('Skills Removed')).toBeInTheDocument();
  });
});
