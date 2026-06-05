'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Loader2, X, Download, MessageCircle, Calendar } from 'lucide-react';
import { useToast } from '@/components/providers/ToastProvider';
import { useApplicationInterviews } from '@/hooks/useATSInterviews';

interface CandidateDetailModalProps {
  applicationId: string;
  candidateName: string;
  candidateEmail?: string;
  positionTitle?: string;
  keywordScore?: number;
  semanticScore?: number;
  capabilityScore?: number;
  resumeText?: string;
  appliedAt?: string;
  source?: string;
  stage?: string;
  onClose: () => void;
  onScheduleInterview?: () => void;
}

const STAGE_COLORS: Record<string, string> = {
  applied: 'bg-blue-100 text-blue-700',
  phone_screen: 'bg-purple-100 text-purple-700',
  technical: 'bg-orange-100 text-orange-700',
  onsite: 'bg-green-100 text-green-700',
  offer: 'bg-emerald-100 text-emerald-700',
  hired: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
};

const SOURCE_ICONS: Record<string, string> = {
  linkedin: '💼',
  referral: '👥',
  indeed: '📌',
  glassdoor: '⭐',
  company_website: '🌐',
  recruiter_outreach: '📧',
  university: '🎓',
  unknown: '❓',
};

export function CandidateDetailModal({
  applicationId,
  candidateName,
  candidateEmail,
  positionTitle,
  keywordScore,
  semanticScore,
  capabilityScore,
  resumeText,
  appliedAt,
  source,
  stage,
  onClose,
  onScheduleInterview,
}: CandidateDetailModalProps) {
  const { addToast } = useToast();
  const { interviews, loading: loadingInterviews, fetchInterviews } = useApplicationInterviews(applicationId);
  const [activeTab, setActiveTab] = useState<'overview' | 'resume' | 'interviews'>('overview');
  const [selectedTab, setSelectedTab] = useState<'overview' | 'resume' | 'interviews'>('overview');

  useEffect(() => {
    if (activeTab === 'interviews') {
      fetchInterviews();
    }
  }, [activeTab, fetchInterviews]);

  const averageScore = keywordScore && semanticScore && capabilityScore
    ? Math.round((keywordScore + semanticScore + capabilityScore) / 3)
    : undefined;

  const handleDownloadResume = () => {
    if (!resumeText) {
      addToast('Resume text not available', 'warning');
      return;
    }

    const element = document.createElement('a');
    element.setAttribute('href', `data:text/plain;charset=utf-8,${encodeURIComponent(resumeText)}`);
    element.setAttribute('download', `${candidateName.replace(/\s+/g, '_')}_resume.txt`);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    addToast('Resume downloaded', 'success');
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <CardHeader className="flex flex-row items-start justify-between flex-shrink-0 border-b">
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold">{candidateName}</h2>
              {stage && (
                <Badge className={`${STAGE_COLORS[stage] || 'bg-gray-100 text-gray-700'}`}>
                  {stage.replace(/_/g, ' ')}
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
              {source && <span>{SOURCE_ICONS[source] || '?'} {source}</span>}
              {appliedAt && <span>• Applied {new Date(appliedAt).toLocaleDateString()}</span>}
              {positionTitle && <span>• {positionTitle}</span>}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </CardHeader>

        {/* Tab Navigation */}
        <div className="flex border-b bg-gray-50 flex-shrink-0">
          {(['overview', 'resume', 'interviews'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-3 px-4 text-sm font-medium border-b-2 transition-all ${
                activeTab === tab
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {tab === 'overview' && '📊 Overview'}
              {tab === 'resume' && '📄 Resume'}
              {tab === 'interviews' && '🎤 Interviews'}
            </button>
          ))}
        </div>

        {/* Content */}
        <CardContent className="flex-1 overflow-y-auto p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Contact Info */}
              <div className="space-y-3">
                <h3 className="font-semibold text-sm">Contact Information</h3>
                {candidateEmail && (
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">Email:</span>
                    <a href={`mailto:${candidateEmail}`} className="text-primary hover:underline">
                      {candidateEmail}
                    </a>
                  </div>
                )}
              </div>

              {/* Three-Signal Scores */}
              <div className="grid grid-cols-3 gap-4">
                {[
                  { label: 'Keyword Match', score: keywordScore, color: 'bg-blue-100 text-blue-700' },
                  { label: 'Semantic Match', score: semanticScore, color: 'bg-purple-100 text-purple-700' },
                  { label: 'Capability Assessment', score: capabilityScore, color: 'bg-green-100 text-green-700' },
                ].map(({ label, score, color }) => (
                  <div key={label} className={`rounded-lg p-4 ${color}`}>
                    <p className="text-xs font-medium opacity-75">{label}</p>
                    <p className="text-2xl font-bold mt-1">{score ? Math.round(score) : '—'}%</p>
                    {score && score >= 80 && <p className="text-xs mt-1">✅ Strong</p>}
                    {score && score >= 60 && score < 80 && <p className="text-xs mt-1">⚠️ Moderate</p>}
                    {score && score < 60 && <p className="text-xs mt-1">❌ Weak</p>}
                  </div>
                ))}
              </div>

              {/* Overall Score */}
              {averageScore && (
                <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">Overall Fit Score</p>
                      <p className="text-2xl font-bold text-primary mt-1">{averageScore}%</p>
                    </div>
                    <div className="w-16 h-16 relative">
                      <svg className="w-full h-full" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="45" fill="none" stroke="#e5e7eb" strokeWidth="3" />
                        <circle
                          cx="50"
                          cy="50"
                          r="45"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="3"
                          strokeDasharray={`${(averageScore / 100) * 283} 283`}
                          className={averageScore >= 80 ? 'text-green-500' : averageScore >= 60 ? 'text-yellow-500' : 'text-red-500'}
                          style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center text-xs font-bold">
                        {averageScore}%
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Summary */}
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <h3 className="font-semibold text-sm">Summary</h3>
                <p className="text-sm text-muted-foreground">
                  {averageScore && averageScore >= 80
                    ? '🟢 Strong candidate - excellent alignment with position requirements'
                    : averageScore && averageScore >= 60
                    ? '🟡 Moderate candidate - meets core requirements, gaps in some areas'
                    : '🔴 Weak candidate - significant gaps against position requirements'}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4">
                <Button variant="outline" onClick={handleDownloadResume} className="flex-1">
                  <Download className="h-4 w-4 mr-2" />
                  Download Resume
                </Button>
                <Button onClick={onScheduleInterview} className="flex-1">
                  <Calendar className="h-4 w-4 mr-2" />
                  Schedule Interview
                </Button>
              </div>
            </div>
          )}

          {/* Resume Tab */}
          {activeTab === 'resume' && (
            <div className="space-y-4">
              {resumeText ? (
                <div className="bg-gray-50 rounded-lg p-4 font-mono text-sm whitespace-pre-wrap break-words max-h-[500px] overflow-y-auto">
                  {resumeText}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Resume content not available
                </div>
              )}
              <Button onClick={handleDownloadResume} className="w-full">
                <Download className="h-4 w-4 mr-2" />
                Download Resume
              </Button>
            </div>
          )}

          {/* Interviews Tab */}
          {activeTab === 'interviews' && (
            <div className="space-y-4">
              {loadingInterviews ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              ) : interviews.length === 0 ? (
                <div className="text-center py-8">
                  <MessageCircle className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-muted-foreground">No interviews scheduled yet</p>
                  <Button onClick={onScheduleInterview} className="mt-4">
                    <Calendar className="h-4 w-4 mr-2" />
                    Schedule First Interview
                  </Button>
                </div>
              ) : (
                interviews.map(interview => (
                  <Card key={interview.id}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">
                          {interview.meeting_platform ? `${interview.meeting_platform.toUpperCase()}` : 'Interview'}
                        </CardTitle>
                        <Badge variant="outline">{interview.status}</Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm">
                      {interview.scheduled_at && (
                        <div>
                          <p className="text-muted-foreground">Scheduled</p>
                          <p className="font-medium">
                            {new Date(interview.scheduled_at).toLocaleString()}
                          </p>
                        </div>
                      )}
                      {interview.interviewer_ids.length > 0 && (
                        <div>
                          <p className="text-muted-foreground">Interviewers</p>
                          <p className="font-medium">{interview.interviewer_ids.length} assigned</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
