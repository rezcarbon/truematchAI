"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/shared/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { FileUpload } from "@/components/shared/FileUpload";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { Sparkles } from "lucide-react";

export default function CapabilityTranslationPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [jd, setJd] = useState("");
  const [role, setRole] = useState("");
  const [status, setStatus] = useState<
    "idle" | "uploading" | "uploaded" | "starting" | "error"
  >("idle");
  const [message, setMessage] = useState("");

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

  async function translate() {
    if (!resumeId || jd.trim().length < 20) {
      setMessage("Paste the full job description (at least a couple of sentences).");
      return;
    }
    setStatus("starting");
    setMessage("");
    try {
      const res = await api.createCapabilityTranslation(resumeId, jd, role || undefined);
      router.push(`/candidate/capability-translation/${res.translationId}`);
    } catch (e) {
      setStatus("error");
      setMessage(e instanceof Error ? e.message : "Could not start translation.");
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader
        title="Capability Translation"
        subtitle="Make your real capability legible to the ATS. We re-express what your resume already proves in the language the role screens for — grounded in your actual experience, never invented — and show the measured score lift."
      />

      <Card>
        <CardHeader>
          <CardTitle>1. Your resume</CardTitle>
          <CardDescription>PDF or Word. Processed securely; nothing is fabricated.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <FileUpload onFile={setFile} />
          {status !== "uploaded" && status !== "starting" && (
            <Button className="w-full" disabled={!file || status === "uploading"} onClick={upload}>
              {status === "uploading" ? "Uploading…" : "Upload resume"}
            </Button>
          )}
          {resumeId && <p className="text-sm text-success">Resume uploaded ✓</p>}
        </CardContent>
      </Card>

      <Card className={resumeId ? "" : "pointer-events-none opacity-50"}>
        <CardHeader>
          <CardTitle>2. Target role</CardTitle>
          <CardDescription>
            Paste the job description you want your resume to be legible to.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <input
            value={role}
            onChange={(e) => setRole(e.target.value)}
            placeholder="Role title (optional)"
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
          />
          <textarea
            value={jd}
            onChange={(e) => setJd(e.target.value)}
            placeholder="Paste the full job description here…"
            className="min-h-[160px] w-full rounded-md border bg-background p-3 text-sm"
          />
          {message && <p className="text-sm text-destructive">{message}</p>}
          <Button
            className="w-full gap-2"
            disabled={!resumeId || status === "starting"}
            onClick={translate}
          >
            <Sparkles className="h-4 w-4" />
            {status === "starting" ? "Translating…" : "Translate my capability"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
