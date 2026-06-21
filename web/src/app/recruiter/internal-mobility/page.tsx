"use client";

import { useState } from "react";
import { PageHeader } from "@/components/shared/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { FileUpload } from "@/components/shared/FileUpload";
import { Button } from "@/components/ui/button";
import { LanguageBadge, languageName } from "@/components/shared/LanguageBadge";
import { TransitionPathways } from "@/components/shared/TransitionPathways";
import { api, type TransitionResult } from "@/lib/api";
import { Loader2, Users } from "lucide-react";

export default function InternalMobilityPage() {
  const [file, setFile] = useState<File | null>(null);
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [currentRole, setCurrentRole] = useState("");
  const [target, setTarget] = useState("");
  const [status, setStatus] = useState<"idle" | "uploading" | "uploaded" | "running" | "done" | "error">("idle");
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<TransitionResult | null>(null);
  const [analysisId, setAnalysisId] = useState<string | null>(null);

  async function upload() {
    if (!file) return;
    setStatus("uploading");
    setMessage("");
    try {
      const res = await api.uploadResume(file);
      setResumeId(res.resume_id);
      setStatus("uploaded");
    } catch (e) {
      setStatus("error");
      setMessage(e instanceof Error ? e.message : "Upload failed.");
    }
  }

  async function run() {
    if (!resumeId) return;
    setStatus("running");
    setResult(null);
    setMessage("");
    try {
      const start = await api.createTransition(resumeId, currentRole || undefined, target || undefined);
      setAnalysisId(start.analysisId);
      // poll
      for (let i = 0; i < 60; i++) {
        const r = await api.getTransition(start.analysisId);
        if (r.status === "completed") { setResult(r); setStatus("done"); return; }
        if (r.status === "failed") { setStatus("error"); setMessage(r.error || "Analysis failed."); return; }
        await new Promise((res) => setTimeout(res, 4000));
      }
      setStatus("error");
      setMessage("Timed out waiting for the analysis.");
    } catch (e) {
      setStatus("error");
      setMessage(e instanceof Error ? e.message : "Could not run the analysis.");
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        title="Internal Mobility"
        subtitle="From an employee's or candidate's evidenced capability, see the adjacent and higher-complexity roles they could move into, the upskilling that closes each gap (with recommended courses), and an honest timeline — grounded in evidence, never inflated."
      />

      <Card>
        <CardHeader>
          <CardTitle>1. The person's CV</CardTitle>
          <CardDescription>PDF or Word, in any language. Used only for this analysis.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <FileUpload onFile={setFile} />
          {status !== "uploaded" && status !== "running" && status !== "done" && (
            <Button className="w-full" disabled={!file || status === "uploading"} onClick={upload}>
              {status === "uploading" ? "Uploading…" : "Upload CV"}
            </Button>
          )}
          {resumeId && <p className="text-sm text-success">CV uploaded ✓</p>}
        </CardContent>
      </Card>

      <Card className={resumeId ? "" : "pointer-events-none opacity-50"}>
        <CardHeader>
          <CardTitle>2. Their current role (and optional target)</CardTitle>
          <CardDescription>The current role anchors the prediction.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <input
            value={currentRole}
            onChange={(e) => setCurrentRole(e.target.value)}
            placeholder="Current role, e.g. Operations Analyst"
            className="w-full rounded-md border bg-background p-2.5 text-sm"
          />
          <input
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="Target direction (optional), e.g. data / AI roles"
            className="w-full rounded-md border bg-background p-2.5 text-sm"
          />
          <Button className="w-full gap-1.5" disabled={!resumeId || status === "running"} onClick={run}>
            <Users className="h-4 w-4" />
            {status === "running" ? "Analyzing…" : "Map internal pathways"}
          </Button>
          {message && <p className="text-sm text-destructive">{message}</p>}
        </CardContent>
      </Card>

      {status === "running" && (
        <div className="flex flex-col items-center gap-3 py-10 text-center">
          <Loader2 className="h-7 w-7 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Mapping pathways from evidenced capability…</p>
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground">
            {typeof result.capabilityScore === "number" ? `Capability verdict ${result.capabilityScore}/100. ` : ""}
            {languageName(result.sourceLanguage) && <LanguageBadge language={result.sourceLanguage} label="CV translated from" />}
          </div>
          <TransitionPathways result={result} analysisId={analysisId ?? undefined} />
        </div>
      )}
    </div>
  );
}
