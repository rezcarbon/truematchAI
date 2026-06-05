'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/providers/ToastProvider';
import { AlertCircle, Loader2, X, Calendar, Users } from 'lucide-react';

interface Interviewer {
  id: string;
  name: string;
  email: string;
}

interface InterviewSchedulerProps {
  candidateName: string;
  candidateEmail?: string;
  candidateId: string;
  positionId: string;
  interviewers: Interviewer[];
  onSchedule: (data: {
    scheduledAt: Date;
    interviewerIds: string[];
    meetingPlatform: string;
  }) => Promise<void>;
  onClose: () => void;
}

export function InterviewScheduler({
  candidateName,
  candidateEmail,
  candidateId,
  positionId,
  interviewers,
  onSchedule,
  onClose,
}: InterviewSchedulerProps) {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    date: '',
    time: '',
    interviewerIds: [] as string[],
    meetingPlatform: 'google_meet',
  });

  const handleInterviewerToggle = (interviewerId: string) => {
    setFormData(prev => ({
      ...prev,
      interviewerIds: prev.interviewerIds.includes(interviewerId)
        ? prev.interviewerIds.filter(id => id !== interviewerId)
        : [...prev.interviewerIds, interviewerId],
    }));
  };

  const handleSchedule = async () => {
    setError(null);

    // Validation
    if (!formData.date) {
      setError('Please select a date');
      addToast('Please select a date', 'warning');
      return;
    }
    if (!formData.time) {
      setError('Please select a time');
      addToast('Please select a time', 'warning');
      return;
    }
    if (formData.interviewerIds.length === 0) {
      setError('Please select at least one interviewer');
      addToast('Please select at least one interviewer', 'warning');
      return;
    }

    setLoading(true);

    try {
      const scheduledAt = new Date(`${formData.date}T${formData.time}`);
      await onSchedule({
        scheduledAt,
        interviewerIds: formData.interviewerIds,
        meetingPlatform: formData.meetingPlatform,
      });

      addToast(`Interview scheduled for ${candidateName}! 🎉`, 'success');
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to schedule interview';
      setError(message);
      addToast(message, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Schedule Interview</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">{candidateName}</p>
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </CardHeader>

        <CardContent className="space-y-6">
          {error && (
            <div className="flex items-start gap-3 rounded-lg bg-red-50/60 border border-red-200/60 p-4">
              <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Date & Time Selection */}
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Date</label>
              <input
                type="date"
                value={formData.date}
                onChange={e => setFormData(prev => ({ ...prev, date: e.target.value }))}
                className="w-full mt-1 rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Time</label>
              <input
                type="time"
                value={formData.time}
                onChange={e => setFormData(prev => ({ ...prev, time: e.target.value }))}
                className="w-full mt-1 rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Meeting Platform</label>
              <select
                value={formData.meetingPlatform}
                onChange={e => setFormData(prev => ({ ...prev, meetingPlatform: e.target.value }))}
                className="w-full mt-1 rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              >
                <option value="google_meet">Google Meet</option>
                <option value="zoom">Zoom</option>
                <option value="teams">Microsoft Teams</option>
                <option value="in_person">In Person</option>
              </select>
            </div>
          </div>

          {/* Interviewer Selection */}
          <div>
            <label className="text-sm font-medium block mb-3">Interviewers</label>
            <div className="space-y-2">
              {interviewers.length === 0 ? (
                <p className="text-sm text-muted-foreground">No interviewers available</p>
              ) : (
                interviewers.map(interviewer => (
                  <label
                    key={interviewer.id}
                    className="flex items-center gap-3 p-3 border rounded-lg hover:bg-accent cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={formData.interviewerIds.includes(interviewer.id)}
                      onChange={() => handleInterviewerToggle(interviewer.id)}
                      className="rounded"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm">{interviewer.name}</p>
                      <p className="text-xs text-muted-foreground">{interviewer.email}</p>
                    </div>
                  </label>
                ))
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {formData.interviewerIds.length} selected
            </p>
          </div>

          {/* Summary */}
          {formData.date && formData.time && (
            <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 space-y-2">
              <p className="text-sm">
                <span className="font-medium">📅 Interview Scheduled For:</span>
              </p>
              <p className="text-sm">
                {new Date(`${formData.date}T${formData.time}`).toLocaleString('en-US', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
              {candidateEmail && (
                <p className="text-sm text-muted-foreground">
                  Calendar invitation will be sent to {candidateEmail}
                </p>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={loading}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSchedule}
              disabled={loading}
              className="flex-1"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Scheduling...
                </>
              ) : (
                <>
                  <Calendar className="h-4 w-4 mr-2" />
                  Schedule Interview
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
