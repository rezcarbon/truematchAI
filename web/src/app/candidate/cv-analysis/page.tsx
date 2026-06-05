'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';

interface Resume {
  id: string;
  filename: string;
  created_at: string;
}

interface FormState {
  resumeId: string;
  targetRole: string;
  targetSeniority: 'junior' | 'mid' | 'senior' | 'lead' | '';
  careerFocusAreas: string[];
}

export default function CVAnalysisPage() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loadingResumes, setLoadingResumes] = useState(true);
  const [form, setForm] = useState<FormState>({
    resumeId: '',
    targetRole: '',
    targetSeniority: '',
    careerFocusAreas: [],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Fetch user's resumes on mount
  useEffect(() => {
    const fetchResumes = async () => {
      try {
        setLoadingResumes(true);
        const response = await fetch('/api/proxy/files/resumes');
        if (!response.ok) {
          throw new Error('Failed to fetch resumes');
        }
        const data = await response.json();
        setResumes(data.items || []);
        // Auto-select the first resume if available
        if (data.items && data.items.length > 0) {
          setForm(prev => ({ ...prev, resumeId: data.items[0].id }));
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load resumes');
      } finally {
        setLoadingResumes(false);
      }
    };

    fetchResumes();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    // Validation
    if (!form.resumeId) {
      setError('Please select a resume');
      return;
    }
    if (!form.targetRole.trim()) {
      setError('Please enter your target role');
      return;
    }
    if (!form.targetSeniority) {
      setError('Please select your target seniority level');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/proxy/candidates/cv-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resume_id: form.resumeId,
          target_role: form.targetRole.trim(),
          target_seniority: form.targetSeniority,
          career_focus_areas: form.careerFocusAreas,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start analysis');
      }

      const result = await response.json();
      setSuccess(true);

      // Redirect to results page after a short delay
      setTimeout(() => {
        window.location.href = `/candidate/cv-analysis/${result.analysis_id}`;
      }, 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setLoading(false);
    }
  };

  const seniorityLevels = [
    { value: 'junior', label: 'Junior (0-2 years)' },
    { value: 'mid', label: 'Mid-level (2-5 years)' },
    { value: 'senior', label: 'Senior (5-10 years)' },
    { value: 'lead', label: 'Lead/Principal (10+ years)' },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Analyze Your CV"
        subtitle="Get personalized recommendations to improve your CV and find your best career fit"
        icon="Sparkles"
      />

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle>CV Analysis</CardTitle>
            <p className="mt-2 text-sm text-muted-foreground">
              We'll analyze your CV against job descriptions to identify skill gaps, career opportunities, and suggest improvements.
            </p>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Resume Selection */}
              <div className="space-y-2">
                <label htmlFor="resume-id" className="block text-sm font-medium">Select Resume *</label>
                {loadingResumes ? (
                  <div className="flex items-center justify-center h-10">
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  </div>
                ) : resumes.length === 0 ? (
                  <div className="rounded-lg border border-dashed p-4 text-center">
                    <p className="text-sm text-muted-foreground">
                      No resumes found. Please <a href="/candidate/upload" className="text-primary hover:underline">upload a resume</a> first.
                    </p>
                  </div>
                ) : (
                  <select
                    id="resume-id"
                    value={form.resumeId}
                    onChange={(e) => setForm({ ...form, resumeId: e.target.value })}
                    disabled={loading}
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <option value="">Select a resume</option>
                    {resumes.map((resume) => (
                      <option key={resume.id} value={resume.id}>
                        {resume.filename} ({new Date(resume.created_at).toLocaleDateString()})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Target Role */}
              <div className="space-y-2">
                <label htmlFor="target-role" className="block text-sm font-medium">Target Role *</label>
                <input
                  id="target-role"
                  type="text"
                  value={form.targetRole}
                  onChange={(e) => setForm({ ...form, targetRole: e.target.value })}
                  placeholder="e.g., Senior Backend Engineer"
                  disabled={loading || resumes.length === 0}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <p className="text-xs text-muted-foreground">
                  The role you're targeting for your next move
                </p>
              </div>

              {/* Target Seniority */}
              <div className="space-y-2">
                <label htmlFor="target-seniority" className="block text-sm font-medium">Target Seniority Level *</label>
                <select
                  id="target-seniority"
                  value={form.targetSeniority}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      targetSeniority: e.target.value as typeof form.targetSeniority,
                    })
                  }
                  disabled={loading || resumes.length === 0}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <option value="">Select a seniority level</option>
                  {seniorityLevels.map((level) => (
                    <option key={level.value} value={level.value}>
                      {level.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Career Focus Areas */}
              <div className="space-y-2">
                <label htmlFor="focus-areas" className="block text-sm font-medium">
                  Career Focus Areas (Optional)
                </label>
                <input
                  id="focus-areas"
                  type="text"
                  placeholder="e.g., System Design, Distributed Systems, Kubernetes"
                  disabled={loading || resumes.length === 0}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50 disabled:cursor-not-allowed"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      const value = (e.target as HTMLInputElement).value.trim();
                      if (value) {
                        setForm({
                          ...form,
                          careerFocusAreas: [...form.careerFocusAreas, value],
                        });
                        (e.target as HTMLInputElement).value = '';
                      }
                    }
                  }}
                />
                <p className="text-xs text-muted-foreground">
                  Enter skills and press Enter to add them
                </p>
                {form.careerFocusAreas.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {form.careerFocusAreas.map((area, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() =>
                          setForm({
                            ...form,
                            careerFocusAreas: form.careerFocusAreas.filter(
                              (_, i) => i !== idx
                            ),
                          })
                        }
                        className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium"
                      >
                        {area} ×
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Error Message */}
              {error && (
                <div className="flex items-start gap-3 rounded-lg bg-red-50/60 border border-red-200/60 p-4">
                  <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}

              {/* Success Message */}
              {success && (
                <div className="flex items-start gap-3 rounded-lg bg-green-50/60 border border-green-200/60 p-4">
                  <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-green-600">Analysis started successfully! Redirecting...</p>
                </div>
              )}

              {/* Submit Button */}
              <Button
                type="submit"
                disabled={loading || !form.resumeId || resumes.length === 0}
                className="w-full"
                size="lg"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Starting Analysis...
                  </>
                ) : (
                  'Start CV Analysis'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
