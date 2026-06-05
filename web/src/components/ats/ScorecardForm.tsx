'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/providers/ToastProvider';
import { AlertCircle, Loader2, Save, X } from 'lucide-react';
import { useSubmitScorecard } from '@/hooks/useATSInterviews';

interface ScorecardFormProps {
  interviewId: string;
  candidateName: string;
  positionTitle?: string;
  onSuccess?: () => void;
  onClose: () => void;
}

const COMPETENCIES = [
  {
    id: 'problem_solving',
    label: 'Problem Solving',
    description: 'Ability to break down complex problems and design solutions',
  },
  {
    id: 'communication',
    label: 'Communication',
    description: 'Ability to articulate ideas clearly and listen effectively',
  },
  {
    id: 'technical_depth',
    label: 'Technical Depth',
    description: 'Deep expertise and knowledge in relevant technical areas',
  },
  {
    id: 'teamwork',
    label: 'Teamwork',
    description: 'Ability to collaborate with others and contribute to team goals',
  },
  {
    id: 'leadership',
    label: 'Leadership',
    description: 'Ability to guide, influence, and inspire others',
  },
];

const SCORE_LEVELS = [
  { value: 1, label: '1 - Needs Improvement', color: 'bg-red-100 text-red-700' },
  { value: 2, label: '2 - Below Expectations', color: 'bg-orange-100 text-orange-700' },
  { value: 3, label: '3 - Meets Expectations', color: 'bg-yellow-100 text-yellow-700' },
  { value: 4, label: '4 - Exceeds Expectations', color: 'bg-blue-100 text-blue-700' },
  { value: 5, label: '5 - Outstanding', color: 'bg-green-100 text-green-700' },
];

export function ScorecardForm({
  interviewId,
  candidateName,
  positionTitle,
  onSuccess,
  onClose,
}: ScorecardFormProps) {
  const { addToast } = useToast();
  const { submitScorecard, loading } = useSubmitScorecard();
  const [error, setError] = useState<string | null>(null);
  const [competencyScores, setCompetencyScores] = useState<Record<string, number>>({});
  const [feedback, setFeedback] = useState('');
  const [recommendation, setRecommendation] = useState<string>('');

  const handleScoreChange = (competencyId: string, score: number) => {
    setCompetencyScores(prev => ({ ...prev, [competencyId]: score }));
  };

  const handleSubmit = async () => {
    setError(null);

    // Validation
    if (Object.keys(competencyScores).length < COMPETENCIES.length) {
      setError('Please rate all competencies');
      addToast('Please rate all competencies', 'warning');
      return;
    }

    if (!recommendation) {
      setError('Please select an overall recommendation');
      addToast('Please select an overall recommendation', 'warning');
      return;
    }

    try {
      await submitScorecard(interviewId, competencyScores, feedback, recommendation);
      onSuccess?.();
      onClose();
    } catch (err) {
      // Error already shown as toast
    }
  };

  const allCompetenciesRated = Object.keys(competencyScores).length === COMPETENCIES.length;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between sticky top-0 bg-card border-b">
          <div>
            <CardTitle>Interview Scorecard</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">{candidateName}</p>
            {positionTitle && (
              <p className="text-xs text-muted-foreground">{positionTitle}</p>
            )}
          </div>
          <button
            onClick={onClose}
            disabled={loading}
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </CardHeader>

        <CardContent className="space-y-6 p-6">
          {error && (
            <div className="flex items-start gap-3 rounded-lg bg-red-50/60 border border-red-200/60 p-4">
              <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Competency Ratings */}
          <div className="space-y-6">
            <p className="text-sm font-medium text-muted-foreground">Rate the candidate on each competency</p>

            {COMPETENCIES.map(competency => (
              <div key={competency.id} className="space-y-3">
                <div>
                  <p className="font-medium text-sm">{competency.label}</p>
                  <p className="text-xs text-muted-foreground">{competency.description}</p>
                </div>

                {/* Score Buttons */}
                <div className="flex gap-2 flex-wrap">
                  {SCORE_LEVELS.map(level => (
                    <button
                      key={level.value}
                      onClick={() => handleScoreChange(competency.id, level.value)}
                      disabled={loading}
                      className={`px-3 py-2 rounded text-sm font-medium transition-all ${
                        competencyScores[competency.id] === level.value
                          ? level.color + ' ring-2 ring-offset-2 ring-primary'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {level.value}
                    </button>
                  ))}
                </div>

                {/* Selected score display */}
                {competencyScores[competency.id] && (
                  <p className="text-xs text-muted-foreground">
                    Selected: {SCORE_LEVELS.find(l => l.value === competencyScores[competency.id])?.label}
                  </p>
                )}
              </div>
            ))}
          </div>

          {/* Feedback */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Interview Feedback (Optional)</label>
            <textarea
              value={feedback}
              onChange={e => setFeedback(e.target.value)}
              disabled={loading}
              placeholder="Share your observations, strengths, areas for improvement, or notable moments from the interview..."
              className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
              rows={5}
            />
            <p className="text-xs text-muted-foreground">{feedback.length}/500</p>
          </div>

          {/* Overall Recommendation */}
          <div className="space-y-3">
            <p className="text-sm font-medium">Overall Recommendation</p>
            <div className="grid grid-cols-2 gap-3">
              {['strong_yes', 'yes', 'no', 'strong_no'].map(rec => (
                <button
                  key={rec}
                  onClick={() => setRecommendation(rec)}
                  disabled={loading}
                  className={`p-3 rounded-lg border-2 transition-all text-sm font-medium ${
                    recommendation === rec
                      ? 'border-primary bg-primary/5'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {rec === 'strong_yes' && '👍 Strong Yes'}
                  {rec === 'yes' && '✅ Yes'}
                  {rec === 'no' && '❌ No'}
                  {rec === 'strong_no' && '👎 Strong No'}
                </button>
              ))}
            </div>
          </div>

          {/* Summary */}
          {allCompetenciesRated && (
            <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 space-y-2">
              <p className="text-sm font-medium">Scorecard Summary</p>
              <p className="text-xs text-muted-foreground">
                Ratings: {COMPETENCIES.map(c => `${competencyScores[c.id] || '?'}`).join(', ')}
              </p>
              <p className="text-xs text-muted-foreground">
                Recommendation: {recommendation ? (
                  { strong_yes: 'Strong Yes', yes: 'Yes', no: 'No', strong_no: 'Strong No' }[recommendation]
                ) : 'Not selected'}
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={loading}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={loading || !allCompetenciesRated}
              className="flex-1"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Submit Scorecard
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
