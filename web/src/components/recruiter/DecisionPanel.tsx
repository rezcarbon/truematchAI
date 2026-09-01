"use client";
import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Check, X, Pause, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";

// Decision panel. The "overriding recommendation" warning is shown when the
// recruiter's choice diverges from the backend-suggested direction. Submitting
// POSTs the decision (with override reasoning) to the backend.
export function DecisionPanel({
  recommendedAdvance,
  assessmentId,
  positionId,
}: {
  recommendedAdvance: boolean;
  assessmentId?: string;
  positionId?: string;
}) {
  const [decision, setDecision] = React.useState<"advance" | "reject" | "hold" | null>(null);
  const [rationale, setRationale] = React.useState("");
  const [status, setStatus] = React.useState<"idle" | "saving" | "saved" | "error">("idle");
  const [error, setError] = React.useState<string | null>(null);

  const overriding =
    (decision === "reject" && recommendedAdvance) ||
    (decision === "advance" && !recommendedAdvance);

  const canSubmit = decision !== null && Boolean(assessmentId && positionId);

  async function submit() {
    if (!decision || !assessmentId || !positionId) return;
    setStatus("saving");
    setError(null);
    try {
      await api.recordDecision({
        assessment_id: assessmentId,
        position_id: positionId,
        decision,
        ai_recommendation_followed: !overriding,
        override_reasoning: overriding ? rationale || "(no reason given)" : null,
      });
      setStatus("saved");
    } catch (e) {
      setStatus("error");
      setError(e instanceof Error ? e.message : "Failed to record decision.");
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Decision</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-3 gap-2">
          <Button
            variant={decision === "advance" ? "default" : "outline"}
            onClick={() => setDecision("advance")}
          >
            <Check className="h-4 w-4" /> Advance
          </Button>
          <Button
            variant={decision === "hold" ? "secondary" : "outline"}
            onClick={() => setDecision("hold")}
          >
            <Pause className="h-4 w-4" /> Hold
          </Button>
          <Button
            variant={decision === "reject" ? "destructive" : "outline"}
            onClick={() => setDecision("reject")}
          >
            <X className="h-4 w-4" /> Reject
          </Button>
        </div>

        {overriding && (
          <div className="flex items-start gap-2 rounded-md border border-warning/40 bg-warning/10 p-3 text-sm">
            <AlertTriangle className="mt-0.5 h-4 w-4 text-warning" />
            <p>
              This decision overrides the assessment recommendation. An override note will be
              recorded in the audit trail.
            </p>
          </div>
        )}

        <textarea
          className="min-h-[80px] w-full rounded-md border bg-background p-3 text-sm"
          placeholder="Decision rationale (recorded for compliance)…"
          value={rationale}
          onChange={(e) => setRationale(e.target.value)}
        />

        {status === "saved" && <p className="text-sm text-success">Decision recorded.</p>}
        {status === "error" && <p className="text-sm text-destructive">{error}</p>}

        <Button className="w-full" disabled={!canSubmit || status === "saving"} onClick={submit}>
          {status === "saving" ? "Saving…" : "Submit Decision"}
        </Button>
      </CardContent>
    </Card>
  );
}
