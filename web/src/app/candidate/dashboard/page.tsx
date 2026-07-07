'use client';

import { useState, useEffect } from 'react';
import Link from "next/link";
import { PageHeader } from "@/components/shared/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EnhancedDashboard } from "@/components/candidate/EnhancedDashboard";
import { CVAnalysisWidget } from "@/components/candidate/CVAnalysisWidget";
import { mockAssessment } from "@/lib/mock";
import { AlertCircle, X } from "lucide-react";
import { useProfileCompletion } from "@/hooks/useProfileCompletion";

export default function CandidateDashboard() {
  const a = mockAssessment;
  const [showProfileBanner, setShowProfileBanner] = useState(false);
  const [profileIncomplete, setProfileIncomplete] = useState(false);

  // Check profile completion on mount
  useProfileCompletion('candidate');

  useEffect(() => {
    const checkProfile = async () => {
      try {
        const response = await fetch('/api/proxy/profile/user/me');
        if (response.ok) {
          const profile = await response.json();
          const isIncomplete = !profile.display_name || profile.display_name.trim() === '';
          setProfileIncomplete(isIncomplete);
          setShowProfileBanner(isIncomplete);
        }
      } catch (error) {
        console.error('Failed to check profile:', error);
      }
    };

    checkProfile();
  }, []);

  return (
    <div>
      <PageHeader title="Your dashboard" subtitle="A capability-first view of how you match open roles." />

      {/* Profile Completion Banner */}
      {showProfileBanner && profileIncomplete && (
        <div className="mb-6 flex items-start gap-3 rounded-lg bg-amber-50/60 border border-amber-200/60 p-4">
          <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-medium text-amber-900">Complete your profile</p>
            <p className="text-xs text-amber-700 mt-1">Add your name and professional details to unlock all features and appear more credible to recruiters.</p>
            <div className="mt-3 flex gap-2">
              <Link href="/candidate/profile">
                <Button size="sm" variant="default" className="h-8">
                  Complete now
                </Button>
              </Link>
              <Button
                size="sm"
                variant="ghost"
                className="h-8"
                onClick={() => setShowProfileBanner(false)}
              >
                Dismiss
              </Button>
            </div>
          </div>
          <button
            onClick={() => setShowProfileBanner(false)}
            className="text-amber-600 hover:text-amber-700 flex-shrink-0"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Enhanced Dashboard */}
      <EnhancedDashboard
        assessment={a}
        assessmentCount={3}
        averageScore={84}
        activeApplications={2}
        recentActivity={[
          {
            id: '1',
            type: 'assessment',
            title: 'Assessment completed',
            description: `You completed the assessment for ${a.positionTitle}`,
            timestamp: a.createdAt,
          },
          {
            id: '2',
            type: 'message',
            title: 'New message from recruiter',
            description: 'Jocelyn Tan sent you a message about your application',
            timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          },
        ]}
      />

      {/* Optional: Additional Analysis Widget */}
      <div className="mt-8">
        <CVAnalysisWidget
          recentAnalysisCount={0}
          avgScore={0}
          lastAnalysisTitle={undefined}
          lastAnalysisScore={undefined}
        />
      </div>
    </div>
  );
}
