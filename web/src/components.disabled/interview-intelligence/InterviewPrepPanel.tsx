'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';

interface TalkingPoint {
  topic: string;
  key_message: string;
  supporting_details: string;
  estimated_duration_minutes: number;
}

interface InterviewQuestion {
  question: string;
  category: string;
  required_skill: string;
  difficulty: string;
  suggested_follow_ups: string[];
}

interface InterviewPrepPanelProps {
  candidateName: string;
  positionTitle: string;
  talkingPoints: TalkingPoint[];
  questions: InterviewQuestion[];
  estimatedDurationMinutes: number;
  isLoading?: boolean;
  onGenerate?: () => void;
}

export function InterviewPrepPanel({
  candidateName,
  positionTitle,
  talkingPoints,
  questions,
  estimatedDurationMinutes,
  isLoading = false,
  onGenerate,
}: InterviewPrepPanelProps) {
  const [activeTab, setActiveTab] = useState<'talking-points' | 'questions'>('talking-points');

  if (isLoading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Loader2 className="animate-spin" size={20} />
            Generating Interview Prep...
          </CardTitle>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-lg text-gray-900">Interview Preparation</CardTitle>
            <div className="text-sm text-gray-600 mt-1">
              Candidate: <span className="font-semibold">{candidateName}</span> | Position: <span className="font-semibold">{positionTitle}</span>
            </div>
          </div>
          <Badge variant="outline">
            {estimatedDurationMinutes} min interview
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Tabs */}
        <div className="flex gap-2 border-b">
          <button
            onClick={() => setActiveTab('talking-points')}
            className={`px-4 py-2 font-semibold border-b-2 transition-colors ${
              activeTab === 'talking-points'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            Talking Points ({talkingPoints.length})
          </button>
          <button
            onClick={() => setActiveTab('questions')}
            className={`px-4 py-2 font-semibold border-b-2 transition-colors ${
              activeTab === 'questions'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            Questions ({questions.length})
          </button>
        </div>

        {/* Talking Points Tab */}
        {activeTab === 'talking-points' && (
          <div className="space-y-3">
            {talkingPoints.map((point, idx) => (
              <div key={idx} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex justify-between items-start gap-2">
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900">{point.topic}</div>
                    <div className="text-sm text-gray-700 mt-1 font-medium">{point.key_message}</div>
                    <div className="text-sm text-gray-600 mt-2">{point.supporting_details}</div>
                  </div>
                  <Badge variant="secondary" className="whitespace-nowrap">
                    {point.estimated_duration_minutes} min
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Questions Tab */}
        {activeTab === 'questions' && (
          <div className="space-y-3">
            {questions.map((q, idx) => (
              <div key={idx} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex justify-between items-start gap-2 mb-2">
                  <div className="font-semibold text-gray-900">{q.question}</div>
                  <div className="flex gap-1">
                    <Badge variant="outline" className="text-xs">{q.category}</Badge>
                    <Badge
                      className={`text-xs ${
                        q.difficulty === 'hard' ? 'bg-red-100 text-red-800' :
                        q.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}
                    >
                      {q.difficulty}
                    </Badge>
                  </div>
                </div>
                <div className="text-xs text-gray-600 mb-2">
                  <span className="font-semibold">Skill:</span> {q.required_skill}
                </div>
                {q.suggested_follow_ups.length > 0 && (
                  <div className="mt-2 pl-3 border-l-2 border-blue-200">
                    <div className="text-xs font-semibold text-gray-700 mb-1">Follow-ups:</div>
                    <ul className="space-y-1">
                      {q.suggested_follow_ups.map((fu, fidx) => (
                        <li key={fidx} className="text-xs text-gray-600">• {fu}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 pt-4 border-t">
          <button
            onClick={onGenerate}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold transition-colors"
          >
            Regenerate Prep
          </button>
          <button className="flex-1 px-4 py-2 border border-gray-300 text-gray-900 rounded-lg hover:bg-gray-50 font-semibold transition-colors">
            Export PDF
          </button>
        </div>
      </CardContent>
    </Card>
  );
}
