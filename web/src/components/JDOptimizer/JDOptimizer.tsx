'use client';

import React, { useState, useCallback } from 'react';
import clsx from 'clsx';
import { Upload, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import JDUploadInput from './JDUploadInput';
import QualityScoreGauge from './QualityScoreGauge';
import ProgressIndicator from './ProgressIndicator';
import IssueCard from './IssueCard';
import BeforeAfterComparison from './BeforeAfterComparison';
import InlineEditor from './InlineEditor';
import { JDOptimizationResult, OptimizationIssue } from '@/types/jd-optimizer';

interface JDOptimizerProps {
  apiEndpoint?: string;
}

type Step = 'input' | 'processing' | 'results';

export default function JDOptimizer({
  apiEndpoint = '/api/jd-optimizer',
}: JDOptimizerProps) {
  const [step, setStep] = useState<Step>('input');
  const [originalJD, setOriginalJD] = useState('');
  const [optimizedJD, setOptimizedJD] = useState('');
  const [qualityScore, setQualityScore] = useState(0);
  const [issues, setIssues] = useState<OptimizationIssue[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIssueId, setSelectedIssueId] = useState<string | null>(null);
  const [isEditingJD, setIsEditingJD] = useState(false);
  const [editedJD, setEditedJD] = useState('');

  const handleUploadOrPaste = useCallback(
    async (jdText: string) => {
      setOriginalJD(jdText);
      setError(null);
      setStep('processing');
      setLoading(true);

      try {
        const response = await fetch(apiEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ jobDescription: jdText }),
        });

        if (!response.ok) {
          throw new Error(`API error: ${response.statusText}`);
        }

        const result: JDOptimizationResult = await response.json();

        setOptimizedJD(result.optimizedJD);
        setQualityScore(result.qualityScore);
        setIssues(result.issues || []);
        setEditedJD(result.optimizedJD);
        setStep('results');
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Unknown error occurred';
        setError(errorMessage);
        setStep('input');
      } finally {
        setLoading(false);
      }
    },
    [apiEndpoint]
  );

  const handleIssueApply = useCallback(
    (issueId: string, fixedText: string) => {
      setEditedJD((prev) => {
        let updated = prev;
        const issue = issues.find((i) => i.id === issueId);

        if (issue && issue.problematicText) {
          updated = updated.replace(issue.problematicText, fixedText);
        }

        return updated;
      });

      setIssues((prev) =>
        prev.map((issue) =>
          issue.id === issueId ? { ...issue, isFixed: true } : issue
        )
      );
    },
    [issues]
  );

  const handleSaveOptimized = useCallback(() => {
    setOptimizedJD(editedJD);
  }, [editedJD]);

  const handleReset = useCallback(() => {
    setStep('input');
    setOriginalJD('');
    setOptimizedJD('');
    setQualityScore(0);
    setIssues([]);
    setError(null);
    setSelectedIssueId(null);
    setIsEditingJD(false);
    setEditedJD('');
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            JD Optimization Tool
          </h1>
          <p className="text-gray-600">
            Improve your job descriptions with AI-powered optimization
          </p>
        </div>

        {/* Error State */}
        {error && (
          <div
            className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3"
            role="alert"
          >
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-red-900">Error</p>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Input Step */}
        {step === 'input' && (
          <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200">
            <JDUploadInput
              onSubmit={handleUploadOrPaste}
              loading={loading}
            />
          </div>
        )}

        {/* Processing Step */}
        {step === 'processing' && (
          <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200 text-center">
            <Loader2 className="w-12 h-12 text-blue-600 mx-auto mb-4 animate-spin" />
            <p className="text-gray-600 text-lg">
              Analyzing your job description...
            </p>
          </div>
        )}

        {/* Results Step */}
        {step === 'results' && (
          <div className="space-y-6">
            {/* Top Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
                <p className="text-gray-600 text-sm mb-2">Quality Score</p>
                <QualityScoreGauge score={qualityScore} />
              </div>

              <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
                <p className="text-gray-600 text-sm mb-2">Issues Found</p>
                <p className="text-3xl font-bold text-gray-900">
                  {issues.length}
                </p>
              </div>

              <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
                <p className="text-gray-600 text-sm mb-2">Improvement</p>
                <p className="text-3xl font-bold text-green-600">
                  {Math.round(qualityScore)}%
                </p>
              </div>
            </div>

            {/* Progress Indicator */}
            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Optimization Progress
              </h2>
              <ProgressIndicator
                totalIssues={issues.length}
                fixedIssues={issues.filter((i) => i.isFixed).length}
              />
            </div>

            {/* Issues List */}
            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Issues & Recommendations
              </h2>
              <div className="space-y-4">
                {issues.length === 0 ? (
                  <div className="flex items-center justify-center py-8">
                    <CheckCircle className="w-6 h-6 text-green-600 mr-2" />
                    <p className="text-gray-600">
                      No issues found! Your JD is well-optimized.
                    </p>
                  </div>
                ) : (
                  issues.map((issue) => (
                    <div
                      key={issue.id}
                      className={clsx(
                        'transition-all cursor-pointer',
                        selectedIssueId === issue.id
                          ? 'ring-2 ring-blue-500 rounded-lg'
                          : ''
                      )}
                      onClick={() =>
                        setSelectedIssueId(
                          selectedIssueId === issue.id ? null : issue.id
                        )
                      }
                    >
                      <IssueCard
                        issue={issue}
                        isSelected={selectedIssueId === issue.id}
                        onApplyFix={() =>
                          handleIssueApply(
                            issue.id,
                            issue.suggestion || issue.problematicText
                          )
                        }
                      />
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Before/After Comparison */}
            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Before & After
              </h2>
              <BeforeAfterComparison
                before={originalJD}
                after={editedJD}
              />
            </div>

            {/* Inline Editor */}
            {isEditingJD && (
              <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Edit Optimized JD
                </h2>
                <InlineEditor
                  value={editedJD}
                  onChange={setEditedJD}
                  onSave={handleSaveOptimized}
                  onCancel={() => {
                    setIsEditingJD(false);
                    setEditedJD(optimizedJD);
                  }}
                />
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 justify-end bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <button
                onClick={() => setIsEditingJD(!isEditingJD)}
                className="px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 transition-colors font-medium"
              >
                {isEditingJD ? 'Cancel Editing' : 'Edit JD'}
              </button>

              <button
                onClick={handleReset}
                className="px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 transition-colors font-medium"
              >
                Optimize Another
              </button>

              <button
                onClick={() => {
                  const blob = new Blob([editedJD], { type: 'text/plain' });
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = 'optimized-jd.txt';
                  a.click();
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Download
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
