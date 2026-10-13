import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { ShieldCheck, ShieldAlert } from "lucide-react";
import type { Governance } from "@/lib/types";

// DISPLAY ONLY. Coherence / consistency / fidelity scores and statuses are
// produced entirely by the backend. This component never computes them and
// never applies any threshold — it just renders what it is handed.
export function GovernanceBadges({ governance }: { governance: Governance }) {
  const signals = [governance.coherence, governance.consistency, governance.fidelity];
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-primary" />
          Governance
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-3 gap-3">
          {signals.map((s) => (
            <div key={s.label} className="rounded-md border p-3 text-center">
              <div className="text-2xl font-bold tabular-nums">{s.score}</div>
              <div className="mb-2 text-xs text-muted-foreground">{s.label}</div>
              <StatusBadge status={s.status} />
            </div>
          ))}
        </div>

        <div>
          <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold">
            <ShieldAlert className="h-4 w-4 text-muted-foreground" />
            Bias Flags
          </h4>
          {governance.biasFlags.length === 0 ? (
            <p className="text-sm text-muted-foreground">No bias flags raised.</p>
          ) : (
            <ul className="space-y-2">
              {governance.biasFlags.map((f) => (
                <li key={f.id} className="flex items-start justify-between gap-2 rounded-md border p-2 text-sm">
                  <div>
                    <span className="font-medium">{f.category}</span>
                    <p className="text-muted-foreground">{f.description}</p>
                  </div>
                  <StatusBadge status={f.severity === "high" ? "fail" : f.severity === "medium" ? "review" : "pass"} />
                </li>
              ))}
            </ul>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          Governance signals are provided by the assessment service for transparency.
        </p>
      </CardContent>
    </Card>
  );
}
