"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/shared/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { FileUpload } from "@/components/shared/FileUpload";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [jd, setJd] = useState("");
  const [title, setTitle] = useState("");
  const [status, setStatus] = useState<"idle" | "uploading" | "uploaded" | "assessing" | "error">(
    "idle"
  );
  const [message, setMessage] = useState<string>("");

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

  async function assess() {
    if (!resumeId || jd.trim().length < 20) {
      setMessage("Paste the full job description (at least a couple of sentences).");
      return;
    }
    setStatus("assessing");
    setMessage("");
    try {
      const res = await api.createSelfAssessment(resumeId, jd, title || undefined);
      router.push(`/candidate/assessment/${res.id}`);
    } catch (e) {
      setStatus("error");
      setMessage(e instanceof Error ? e.message : "Could not start assessment.");
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader
        title="Assess your resume"
        subtitle="See how a traditional ATS scores you vs. what your experience actually demonstrates."
      />

      <Card>
        <CardHeader>
          <CardTitle>1. Your resume</CardTitle>
          <CardDescription>PDF or Word. Your document is processed securely.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <FileUpload onFile={setFile} />
          {status !== "uploaded" && status !== "assessing" && (
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
            Paste the job description you want to be assessed against.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
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
            className="w-full"
            disabled={!resumeId || status === "assessing"}
            onClick={assess}
          >
            {status === "assessing" ? "Starting assessment…" : "Run assessment"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
