'use client';

import { useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { JDSimulationForm } from '@/components/recruiter/JDSimulationForm';

export default function JDSimulationPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: {
    jdText: string;
    positionTitle?: string;
  }) => {
    setLoading(true);
    setError(null);

    try {
      // Call API to create JD simulation
      const response = await fetch('/api/proxy/recruiters/jd-simulation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jd_text: data.jdText,
          simulation_type: 'requirement_fit',
          position_id: null,
          target_candidate_profile: null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start simulation');
      }

      const result = await response.json();

      // Redirect to results page
      window.location.href = `/recruiter/jd-simulation/${result.simulation_id}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Test Your Job Description"
        subtitle="Analyze your job posting to identify capability gaps, requirement creep, and optimization opportunities"
        icon="Zap"
      />

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        <JDSimulationForm
          onSubmit={handleSubmit}
          loading={loading}
          error={error}
        />
      </div>
    </div>
  );
}
