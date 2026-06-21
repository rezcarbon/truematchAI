import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type TransitionResult, type TransitionOption } from "@/lib/api";
import { ArrowUpRight, ArrowRight, ShieldCheck, GraduationCap, Clock, Check } from "lucide-react";

const OUTCOME_OPTIONS = [
  { value: "pursuing", label: "Pursuing" },
  { value: "achieved", label: "Achieved" },
  { value: "not_pursued", label: "Not pursued" },
];

function OutcomeRecorder({ analysisId, role }: { analysisId: string; role: string }) {
  const [saved, setSaved] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function record(status: string) {
    setBusy(true);
    try {
      await api.recordTransitionOutcome({ analysisId, predictedRole: role, status });
      setSaved(status);
    } catch {
      /* non-blocking */
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-3 flex flex-wrap items-center gap-1.5 border-t pt-3">
      <span className="text-[11px] font-medium uppercase text-muted-foreground">Record outcome</span>
      {OUTCOME_OPTIONS.map((o) => (
        <button
          key={o.value}
          type="button"
          disabled={busy}
          onClick={() => record(o.value)}
          className={`rounded-full border px-2 py-0.5 text-xs transition ${
            saved === o.value
              ? "border-emerald-300 bg-emerald-50 text-emerald-700"
              : "border-border hover:bg-muted"
          }`}
        >
          {saved === o.value && <Check className="mr-0.5 inline h-3 w-3" />}
          {o.label}
        </button>
      ))}
    </div>
  );
}

const FEASIBILITY: Record<string, { variant: "success" | "warning" | "secondary"; label: string }> = {
  READY: { variant: "success", label: "Ready now" },
  STRETCH: { variant: "warning", label: "Stretch" },
  ASPIRATIONAL: { variant: "secondary", label: "Aspirational" },
};
const STRENGTH: Record<string, "success" | "secondary" | "warning"> = {
  HIGH: "success", MEDIUM: "secondary", WEAK: "warning",
};

function OptionCard({ o, analysisId }: { o: TransitionOption; analysisId?: string }) {
  const feas = FEASIBILITY[o.feasibility] ?? FEASIBILITY.STRETCH;
  const tl = o.timeline;
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle className="flex items-center gap-1.5 text-base">
            {o.direction === "upward" ? (
              <ArrowUpRight className="h-4 w-4 text-primary" />
            ) : (
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
            )}
            {o.role}
          </CardTitle>
          <div className="flex items-center gap-1.5">
            <Badge variant={feas.variant}>{feas.label}</Badge>
            <Badge variant={STRENGTH[o.evidenceStrength] ?? "secondary"}>
              {o.evidenceStrength} evidence
            </Badge>
          </div>
        </div>
        <p className="pt-1 text-sm text-muted-foreground">{o.rationale}</p>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {tl && (
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Clock className="h-3.5 w-3.5" />
            <span>
              Estimated <strong className="text-foreground">{tl.monthsMin}–{tl.monthsMax} months</strong>{" "}
              ({tl.confidence} confidence){tl.basis ? ` — ${tl.basis}` : ""}
            </span>
          </div>
        )}

        {o.transferableStrengths && o.transferableStrengths.length > 0 && (
          <div>
            <div className="mb-1.5 text-xs font-medium uppercase text-muted-foreground">
              What carries over
            </div>
            <div className="flex flex-wrap gap-1.5">
              {o.transferableStrengths.map((s) => (
                <Badge key={s} variant="outline">{s}</Badge>
              ))}
            </div>
          </div>
        )}

        {o.upskillingGap && o.upskillingGap.length > 0 && (
          <div>
            <div className="mb-2 text-xs font-medium uppercase text-muted-foreground">
              What to build
            </div>
            <ul className="space-y-3">
              {o.upskillingGap.map((g, i) => (
                <li key={i} className="rounded-md border bg-muted/30 p-3">
                  <p className="font-medium">{g.capability}</p>
                  {g.why && <p className="mt-0.5 text-xs text-muted-foreground">{g.why}</p>}
                  {g.how && <p className="mt-0.5 text-xs">{g.how}</p>}
                  {g.recommendedTraining && g.recommendedTraining.length > 0 && (
                    <div className="mt-2 space-y-1">
                      <div className="flex items-center gap-1 text-[11px] font-medium uppercase text-muted-foreground">
                        <GraduationCap className="h-3 w-3" /> Recommended courses
                      </div>
                      {g.recommendedTraining.map((c, ci) => (
                        <div key={ci} className="flex flex-wrap items-center gap-1.5 text-xs">
                          {c.url ? (
                            <a href={c.url} target="_blank" rel="noopener noreferrer"
                               className="font-medium text-primary hover:underline">{c.title}</a>
                          ) : (
                            <span className="font-medium">{c.title}</span>
                          )}
                          <Badge variant="outline" className="text-[10px]">{c.provider}</Badge>
                          {c.format && <span className="text-muted-foreground">{c.format}</span>}
                          {typeof c.durationWeeks === "number" && (
                            <span className="text-muted-foreground">· {c.durationWeeks}w</span>
                          )}
                          {c.level && <span className="text-muted-foreground">· {c.level}</span>}
                        </div>
                      ))}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {analysisId && <OutcomeRecorder analysisId={analysisId} role={o.role} />}
      </CardContent>
    </Card>
  );
}

/** Shared renderer for a completed TransitionResult — used by the candidate
 *  result page and the recruiter internal-mobility view. Pass `analysisId` to
 *  enable per-pathway outcome recording (recruiter / admin). */
export function TransitionPathways({ result, analysisId }: { result: TransitionResult; analysisId?: string }) {
  return (
    <div className="space-y-6">
      {result.readinessSummary && (
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="p-4 text-sm">{result.readinessSummary}</CardContent>
        </Card>
      )}

      {result.transitionOptions.length === 0 ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            No transition pathway could be grounded in the current evidence. More résumé detail
            (scope, outcomes, tools) surfaces more options — we don&apos;t invent them.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {result.transitionOptions.map((o, i) => (
            <OptionCard key={i} o={o} analysisId={analysisId} />
          ))}
        </div>
      )}

      {result.honestyNotes && (
        <Card className="border-amber-200 bg-amber-50/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5 text-base">
              <ShieldCheck className="h-4 w-4" /> Honest read
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm">{result.honestyNotes}</CardContent>
        </Card>
      )}
    </div>
  );
}
