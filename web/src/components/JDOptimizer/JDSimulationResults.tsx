'use client';

import React, { useCallback } from 'react';
import { Download, AlertCircle, CheckCircle } from 'lucide-react';
import clsx from 'clsx';
import { OptimizationIssue, JDOptimizationResult } from '@/types/jd-optimizer';
import QualityScoreGauge from './QualityScoreGauge';
import IssueCard from './IssueCard';

interface JDSimulationResultsProps {
  result: JDOptimizationResult;
  loading?: boolean;
  onExport?: () => void;
  onApplyFix?: (issueId: string) => Promise<void>;
  fixedIssues?: Set<string>;
}

interface DimensionScore {
  name: string;
  score: number;
  category: string;
  description: string;
}

export default function JDSimulationResults({
  result,
  loading = false,
  onExport,
  onApplyFix,
  fixedIssues = new Set(),
}: JDSimulationResultsProps) {
  // Generate dimension scores from issues
  const getDimensionScores = useCallback((): DimensionScore[] => {
    const dimensions: Record<string, DimensionScore> = {
      clarity: {
        name: 'Clarity',
        score: 0,
        category: 'Clarity of job requirements and expectations',
        description: 'How clear and understandable the job description is',
      },
      tone: {
        name: 'Tone',
        score: 0,
        category: 'Professional and welcoming tone',
        description: 'Overall professional and inclusive tone of the description',
      },
      completeness: {
        name: 'Completeness',
        score: 0,
        category: 'Comprehensive job information',
        description: 'How complete and detailed the job information is',
      },
      structure: {
        name: 'Structure',
        score: 0,
        category: 'Logical organization',
        description: 'How well-organized and structured the content is',
      },
      engagement: {
        name: 'Engagement',
        score: 0,
        category: 'Candidate engagement',
        description: 'How engaging and compelling the description is',
      },
      specificity: {
        name: 'Specificity',
        score: 0,
        category: 'Specific requirements',
        description: 'How specific and measurable the requirements are',
      },
      consistency: {
        name: 'Consistency',
        score: 0,
        category: 'Content consistency',
        description: 'Consistency in terminology and formatting',
      },
      accessibility: {
        name: 'Accessibility',
        score: 0,
        category: 'Inclusive language',
        description: 'Use of inclusive and accessible language',
      },
      impact: {
        name: 'Impact',
        score: 0,
        category: 'High-impact wording',
        description: 'Impact and persuasiveness of the content',
      },
      atsScore: {
        name: 'ATS Score',
        score: 0,
        category: 'ATS optimization',
        description: 'Applicant Tracking System compatibility',
      },
    };

    // Calculate scores based on issues
    if (result.issues && result.issues.length > 0) {
      const categoryIssueCount: Record<string, number> = {};

      result.issues.forEach((issue) => {
        if (!categoryIssueCount[issue.category]) {
          categoryIssueCount[issue.category] = 0;
        }
        categoryIssueCount[issue.category]++;
      });

      // Calculate scores inversely proportional to issues
      const totalCategories = Object.keys(dimensions).length;
      const baseScore = 85;

      Object.keys(dimensions).forEach((key) => {
        const issueCount = categoryIssueCount[key] || 0;
        const issueDeduction = issueCount * 5;
        dimensions[key].score = Math.max(0, baseScore - issueDeduction);
      });
    } else {
      // No issues found - excellent score
      Object.keys(dimensions).forEach((key) => {
        dimensions[key].score = 95;
      });
    }

    return Object.values(dimensions);
  }, [result.issues]);

  const dimensionScores = getDimensionScores();
  const averageDimensionScore =
    dimensionScores.reduce((sum, dim) => sum + dim.score, 0) / dimensionScores.length;

  const highSeverityIssues = (result.issues || []).filter(
    (issue) => issue.severity === 'high'
  );
  const mediumSeverityIssues = (result.issues || []).filter(
    (issue) => issue.severity === 'medium'
  );
  const lowSeverityIssues = (result.issues || []).filter(
    (issue) => issue.severity === 'low'
  );

  const handleExport = useCallback(() => {
    if (onExport) {
      onExport();
    } else {
      // Default export as JSON
      const exportData = {
        qualityScore: result.qualityScore,
        dimensionScores,
        averageDimensionScore,
        summary: result.summary,
        issues: result.issues,
        improvements: result.improvements,
        exportedAt: new Date().toISOString(),
      };

      const element = document.createElement('a');
      element.setAttribute(
        'href',
        `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(exportData, null, 2))}`
      );
      element.setAttribute('download', `jd-analysis-${Date.now()}.json`);
      element.style.display = 'none';
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    }
  }, [result, dimensionScores, averageDimensionScore, onExport]);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Analysis Results
          </h2>
          <p className="text-gray-600">
            Detailed breakdown of your job description quality
          </p>
        </div>
        <button
          onClick={handleExport}
          disabled={loading}
          className={clsx(
            'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors',
            loading
              ? 'opacity-50 cursor-not-allowed bg-gray-100 text-gray-500'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          )}
        >
          <Download className="w-4 h-4" />
          Export Results
        </button>
      </div>

      {/* Overall Score Section */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200 p-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
          {/* Gauge */}
          <div className="flex justify-center">
            <QualityScoreGauge score={result.qualityScore} />
          </div>

          {/* Summary Stats */}
          <div className="space-y-4">
            <div>
              <p className="text-sm font-semibold text-gray-600 mb-1">
                SUMMARY
              </p>
              <p className="text-base text-gray-900">
                {result.summary ||
                  'Your job description has been analyzed for quality and optimization.'}
              </p>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="bg-white rounded-lg p-3 border border-gray-200">
                <p className="text-xs font-semibold text-gray-600 mb-1">
                  Issues Found
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {result.issues?.length || 0}
                </p>
              </div>
              <div className="bg-white rounded-lg p-3 border border-gray-200">
                <p className="text-xs font-semibold text-gray-600 mb-1">
                  Avg. Dimension
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.round(averageDimensionScore)}
                </p>
              </div>
              <div className="bg-white rounded-lg p-3 border border-gray-200">
                <p className="text-xs font-semibold text-gray-600 mb-1">
                  Fixed Issues
                </p>
                <p className="text-2xl font-bold text-green-600">
                  {fixedIssues.size}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 10 Dimension Scores */}
      <div>
        <h3 className="text-xl font-bold text-gray-900 mb-4">
          Quality Dimensions
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {dimensionScores.map((dimension) => {
            const score = dimension.score;
            const scoreColor =
              score >= 80
                ? 'text-green-600'
                : score >= 60
                  ? 'text-yellow-600'
                  : 'text-red-600';

            return (
              <div
                key={dimension.name}
                className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900">
                      {dimension.name}
                    </h4>
                    <p className="text-xs text-gray-600 mt-1">
                      {dimension.description}
                    </p>
                  </div>
                  <span
                    className={clsx(
                      'text-lg font-bold flex-shrink-0',
                      scoreColor
                    )}
                  >
                    {score}
                  </span>
                </div>

                {/* Score bar */}
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={clsx(
                      'h-full transition-all',
                      score >= 80
                        ? 'bg-green-500'
                        : score >= 60
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                    )}
                    style={{ width: `${score}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Issues by Severity */}
      {(result.issues && result.issues.length > 0) && (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-gray-900">
            Issues & Suggestions
          </h3>

          {/* High Severity */}
          {highSeverityIssues.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <h4 className="font-semibold text-gray-900">
                  Critical Issues ({highSeverityIssues.length})
                </h4>
              </div>
              <div className="space-y-3">
                {highSeverityIssues.map((issue) => (
                  <IssueCard
                    key={issue.id}
                    issue={{ ...issue, isFixed: fixedIssues.has(issue.id) }}
                    onApplyFix={() => onApplyFix?.(issue.id)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Medium Severity */}
          {mediumSeverityIssues.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-yellow-600" />
                <h4 className="font-semibold text-gray-900">
                  Recommendations ({mediumSeverityIssues.length})
                </h4>
              </div>
              <div className="space-y-3">
                {mediumSeverityIssues.map((issue) => (
                  <IssueCard
                    key={issue.id}
                    issue={{ ...issue, isFixed: fixedIssues.has(issue.id) }}
                    onApplyFix={() => onApplyFix?.(issue.id)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Low Severity */}
          {lowSeverityIssues.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-blue-600" />
                <h4 className="font-semibold text-gray-900">
                  Minor Improvements ({lowSeverityIssues.length})
                </h4>
              </div>
              <div className="space-y-3">
                {lowSeverityIssues.map((issue) => (
                  <IssueCard
                    key={issue.id}
                    issue={{ ...issue, isFixed: fixedIssues.has(issue.id) }}
                    onApplyFix={() => onApplyFix?.(issue.id)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* No Issues State */}
      {(!result.issues || result.issues.length === 0) && (
        <div className="text-center py-12 bg-green-50 border border-green-200 rounded-lg">
          <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-green-900 mb-2">
            Excellent Job Description!
          </h3>
          <p className="text-green-800">
            Your job description meets high quality standards. No issues were found.
          </p>
        </div>
      )}

      {/* Improvements List */}
      {result.improvements && result.improvements.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Key Improvements Made
          </h3>
          <ul className="space-y-2">
            {result.improvements.map((improvement, index) => (
              <li key={index} className="flex gap-3 text-gray-700">
                <span className="text-blue-600 font-bold flex-shrink-0">
                  ✓
                </span>
                <span>{improvement}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
