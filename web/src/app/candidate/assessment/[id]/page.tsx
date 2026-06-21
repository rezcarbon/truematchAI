import { PageHeader } from "@/components/shared/AppShell";
import { DualScoreCard } from "@/components/assessment/DualScoreCard";
import { CapabilityNarrative } from "@/components/assessment/CapabilityNarrative";
import { TrajectoryChart } from "@/components/assessment/TrajectoryChart";
import { GapAnalysis } from "@/components/assessment/GapAnalysis";
import { CounterRecommendation } from "@/components/assessment/CounterRecommendation";
import { SignalProgression } from "@/components/assessment/SignalProgression";
import { GovernanceBadges } from "@/components/assessment/GovernanceBadges";
import { DeltaVisualization } from "@/components/assessment/DeltaVisualization";
import { LanguageBadge, languageName } from "@/components/shared/LanguageBadge";
import { api } from "@/lib/api";

export default async function AssessmentPage({ params }: { params: { id: string } }) {
  const a = await api.getAssessment(params.id);
  const translated = languageName(a.sourceLanguage) || languageName(a.jdSourceLanguage);
  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader title={`Assessment — ${a.positionTitle}`} subtitle={`Candidate: ${a.candidateName}`} />
      {translated && (
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <LanguageBadge language={a.sourceLanguage} label="CV translated from" />
          <LanguageBadge language={a.jdSourceLanguage} label="JD translated from" />
          <span className="text-xs text-muted-foreground">
            Scored on a faithful English translation; the original text is retained.
          </span>
        </div>
      )}
      <div className="space-y-6">
        <SignalProgression
          traditionalScore={a.traditionalScore}
          semanticScore={a.semanticScore}
          capabilityScore={a.capabilityScore.overall}
          matchType={a.matchType}
        />
        <DualScoreCard
          traditionalScore={a.traditionalScore}
          capabilityScore={a.capabilityScore.overall}
          delta={a.delta}
        />
        <CounterRecommendation rec={a.counterRecommendation} />
        <div className="grid gap-6 lg:grid-cols-2">
          <CapabilityNarrative narrative={a.narrative} components={a.capabilityScore.components} />
          <div className="space-y-6">
            <DeltaVisualization
              traditionalScore={a.traditionalScore}
              capabilityScore={a.capabilityScore.overall}
            />
            <GovernanceBadges governance={a.governance} />
          </div>
        </div>
        <TrajectoryChart data={a.trajectory} />
        <GapAnalysis gaps={a.gaps} />
      </div>
    </div>
  );
}
