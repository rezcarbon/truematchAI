
function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
    </div>
  );
}
// import { DualScoreCard } from "@/components/assessment/DualScoreCard"; (needs manual conversion)
// import { CapabilityNarrative } from "@/components/assessment/CapabilityNarrative"; (needs manual conversion)
// import { TrajectoryChart } from "@/components/assessment/TrajectoryChart"; (needs manual conversion)
// import { GapAnalysis } from "@/components/assessment/GapAnalysis"; (needs manual conversion)
// import { CounterRecommendation } from "@/components/assessment/CounterRecommendation"; (needs manual conversion)
// import { SignalProgression } from "@/components/assessment/SignalProgression"; (needs manual conversion)
// import { GovernanceBadges } from "@/components/assessment/GovernanceBadges"; (needs manual conversion)
// import { DeltaVisualization } from "@/components/assessment/DeltaVisualization"; (needs manual conversion)
// import { LanguageBadge, languageName } from "@/components/shared/LanguageBadge"; (needs manual conversion)
// api removed - use fetch directly;

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
