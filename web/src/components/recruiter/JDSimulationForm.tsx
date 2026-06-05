'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, Loader2 } from 'lucide-react';

interface JDSimulationFormProps {
  onSubmit: (data: { jdText: string; positionTitle?: string }) => Promise<void>;
  loading?: boolean;
  error?: string;
}

export function JDSimulationForm({ onSubmit, loading = false, error }: JDSimulationFormProps) {
  const [jdText, setJdText] = useState('');
  const [positionTitle, setPositionTitle] = useState('');
  const [localError, setLocalError] = useState<string | null>(error || null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    // Validation
    if (!jdText.trim()) {
      setLocalError('Job description is required');
      return;
    }
    if (jdText.trim().length < 50) {
      setLocalError('Job description must be at least 50 characters');
      return;
    }

    try {
      await onSubmit({
        jdText: jdText.trim(),
        positionTitle: positionTitle.trim() || undefined,
      });
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Failed to submit simulation');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Simulate a Job Description</CardTitle>
        <p className="mt-2 text-sm text-muted-foreground">
          Test how well a job description attracts qualified candidates. Identify capability gaps,
          requirement creep, and optimization opportunities.
        </p>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Job Description Input */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">Job Description *</label>
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste the complete job description here. Include all requirements, responsibilities, and qualifications."
              disabled={loading}
              className="w-full min-h-[200px] border rounded-lg p-3 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <p className="text-xs text-muted-foreground">
              Include full job description for accurate analysis ({jdText.length} characters)
            </p>
          </div>

          {/* Position Title Input */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">Position Title (Optional)</label>
            <input
              type="text"
              value={positionTitle}
              onChange={(e) => setPositionTitle(e.target.value)}
              placeholder="e.g., Senior Backend Engineer"
              disabled={loading}
              className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <p className="text-xs text-muted-foreground">
              Helps identify role-specific patterns
            </p>
          </div>

          {/* Error Message */}
          {(localError || error) && (
            <div className="flex items-start gap-3 rounded-lg bg-red-50/60 border border-red-200/60 p-4">
              <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-red-600">{localError || error}</p>
            </div>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={loading || !jdText.trim()}
            className="w-full"
            size="lg"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Analyzing...
              </>
            ) : (
              'Run Simulation'
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
