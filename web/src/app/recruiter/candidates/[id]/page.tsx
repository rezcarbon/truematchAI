import { api } from "@/lib/api";
import { PageHeader } from "@/components/shared/AppShell";
import { ScoreTrio } from "@/components/shared/ScoreTrio";
import { CounterRecCard } from "@/components/shared/CounterRecCard";
import { GovernanceBadge } from "@/components/shared/GovernanceBadge";
import { SubstitutionPanel } from "@/components/recruiter/SubstitutionPanel";
import { SignalProgression } from "@/components/assessment/SignalProgression";
import { CapabilityNarrative } from "@/components/assessment/CapabilityNarrative";
import { TrajectoryChart } from "@/components/assessment/TrajectoryChart";
import { GapAnalysis } from "@/components/assessment/GapAnalysis";
import { GovernanceBadges } from "@/components/assessment/GovernanceBadges";
import { DecisionPanel } from "@/components/recruiter/DecisionPanel";
import { JDQualityCard } from "@/components/recruiter/JDQualityCard";
import { mockAssessment } from "@/lib/mock";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  CheckCircle2, XCircle, ExternalLink, Calendar,
  Shield, FileText, Clock, ArrowLeft
} from "lucide-react";
import Link from "next/link";

/* ── Audit trail row ────────────────────────────────────────────────────── */
function AuditRow({ event, time, detail }: { event: string; time: string; detail?: string }) {
  const icon =
    event.includes("completed") ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> :
    event.includes("failed")    ? <XCircle className="h-3.5 w-3.5 text-red-500" /> :
    event.includes("provenance") ? <Shield className="h-3.5 w-3.5 text-blue-500" /> :
    <Clock className="h-3.5 w-3.5 text-muted-foreground" />;
  return (
    <div className="flex items-start gap-3 py-2 border-b last:border-0">
      <span className="mt-0.5 shrink-0">{icon}</span>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium">{event}</p>
        {detail && <p className="text-[11px] text-muted-foreground truncate">{detail}</p>}
      </div>
      <span className="text-[10px] tabular-nums text-muted-foreground shrink-0">{time}</span>
    </div>
  );
}

/* ── Verified evidence row ──────────────────────────────────────────────── */
function EvidenceRow({ type, ref, status, summary }: {
  type: string; ref: string; status: string; summary: string;
}) {
  const color = status === "verified" ? "text-emerald-600" : status === "not_found" ? "text-red-500" : "text-amber-600";
  const icon = status === "verified" ? "✅" : status === "not_found" ? "❌" : "⚠️";
  return (
    <div className="flex items-start gap-2 py-1.5 border-b last:border-0">
      <span className="text-sm shrink-0">{icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium capitalize">{type}</span>
          <span className={`text-[10px] font-medium ${color}`}>{status}</span>
        </div>
        <p className="text-[11px] text-muted-foreground truncate">{summary}</p>
      </div>
    </div>
  );
}

/* ── Page ────────────────────────────────────────────────────────────────── */
export default async function CandidateDetailPage({ params }: { params: { id: string } }) {
  const a = await api.getAssessment(params.id).catch(() => ({ ...mockAssessment, id: params.id }));
  const recommendedAdvance = a.delta >= 0 && a.counterRecommendation.triggered
    ? true : a.capabilityScore.overall >= a.traditionalScore;

  /* mock enrichment evidence for display */
  const mockEvidence = [
    { type: "orcid",   ref: "0009-0002-5057-4910", status: "verified",   summary: "ORCID profile with 8 registered works." },
    { type: "web",     ref: "mustafarai.com",       status: "verified",   summary: "URL responded 200." },
    { type: "web",     ref: "linkedin.com/in/...",  status: "not_found",  summary: "URL not reachable (bot-blocked)." },
    { type: "patent",  ref: "10202601003R",         status: "unverified", summary: "Verify on IPOS Singapore register." },
    { type: "patent",  ref: "10202601110Y",         status: "unverified", summary: "Verify on IPOS Singapore register." },
  ];

  return (
    <div className="space-y-6">
      {/* back + header */}
      <div>
        <Link href="/recruiter/positions" className="mb-3 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-3 w-3" /> Positions
        </Link>
        <div className="flex items-start justify-between gap-4">
          <PageHeader
            title={a.candidateName}
            subtitle={`Assessment for ${a.positionTitle}`}
          />
          <div className="flex gap-2 shrink-0 pt-1">
            <Button variant="outline" size="sm"><Calendar className="mr-1.5 h-4 w-4" />Schedule</Button>
            <Button variant="outline" size="sm"><FileText className="mr-1.5 h-4 w-4" />Export</Button>
          </div>
        </div>
      </div>

      {/* ── The signature signal panel ──────────────────────────────────── */}
      <Card className="border-2 border-primary/20 bg-gradient-to-r from-primary/5 to-transparent">
        <CardContent className="p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold">Three-Signal Assessment</h3>
            <GovernanceBadge
              status={
                a.governance.coherence.status === "pass" &&
                a.governance.fidelity.status === "pass"
                  ? "pass" : "review"
              }
              size="sm"
            />
          </div>
          <SignalProgression
            traditionalScore={a.traditionalScore}
            semanticScore={a.semanticScore}
            capabilityScore={a.capabilityScore.overall}
            matchType={a.matchType}
          />
        </CardContent>
      </Card>

      {/* ── Counter-recommendation ─────────────────────────────────────── */}
      {a.counterRecommendation.triggered && (
        <CounterRecCard
          headline={a.counterRecommendation.headline}
          rationale={a.counterRecommendation.rationale}
          suggestedRoles={a.counterRecommendation.suggestedRoles}
        />
      )}

      {/* ── Main 2-column layout ─────────────────────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">

        {/* LEFT — Assessment detail */}
        <div className="space-y-6">
          {/* Substitutions — credential alternates */}
          {a.substitutions && a.substitutions.length > 0 && (
            <SubstitutionPanel substitutions={a.substitutions} />
          )}

          {/* Capability narrative + radar */}
          <CapabilityNarrative narrative={a.narrative} components={a.capabilityScore.components} />

          {/* Trajectory */}
          <TrajectoryChart data={a.trajectory} />

          {/* Gap analysis */}
          <GapAnalysis gaps={a.gaps} />

          {/* JD quality */}
          <Card>
            <CardHeader><CardTitle className="text-sm">JD Quality</CardTitle></CardHeader>
            <CardContent>
              <JDQualityCard jd={a.jdQuality} />
            </CardContent>
          </Card>
        </div>

        {/* RIGHT — Decision + governance + evidence + audit */}
        <div className="space-y-4">
          {/* Decision panel */}
          <DecisionPanel
            recommendedAdvance={recommendedAdvance}
            assessmentId={a.id}
            positionId={a.positionId}
          />

          {/* Governance */}
          <Card>
            <CardHeader><CardTitle className="text-sm">Governance</CardTitle></CardHeader>
            <CardContent>
              <GovernanceBadges governance={a.governance} />
            </CardContent>
          </Card>

          {/* Verified external evidence */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Verified Evidence</CardTitle>
            </CardHeader>
            <CardContent className="pb-3">
              {mockEvidence.map((e, i) => (
                <EvidenceRow key={i} {...e} />
              ))}
            </CardContent>
          </Card>

          {/* Audit trail */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Audit Trail</CardTitle>
                <Badge variant="secondary" className="text-[10px]">2026.05.31c</Badge>
              </div>
            </CardHeader>
            <CardContent className="pb-3">
              <AuditRow event="pipeline.completed"  time="14:34" detail="status: completed · governed: true" />
              <AuditRow event="governance.completed" time="14:34" detail="coherence ✓ consistency ✓ fidelity ✓" />
              <AuditRow event="reasoning.completed"  time="14:33" detail={`capability ${a.capabilityScore.overall} · delta ${a.delta}`} />
              <AuditRow event="enrichment.completed" time="14:32" detail="9 items · 2 verified" />
              <AuditRow event="intake.completed"     time="14:32" detail={`traditional ${a.traditionalScore} · semantic ${a.semanticScore ?? "—"}`} />
              <AuditRow event="pipeline.provenance"  time="14:32" detail="inputs hashed · model claude-sonnet-4" />
              <AuditRow event="pipeline.started"     time="14:31" />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
