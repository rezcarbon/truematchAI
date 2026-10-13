import { useState } from "react";
import { useRouter } from "next/navigation";
"use client";
function cn(...inputs: any[]) {
  return twMerge(clsx(inputs));
}

// import { FileUpload } from "@/components/shared/FileUpload"; (needs manual conversion)
// api removed - use fetch directly;
import { Sparkles } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function Card({ className, ...props }: any) {
  return (
    <div className={cn("rounded-lg border border-gray-200 bg-white shadow-sm", className)} {...props} />
  );
}
function CardHeader({ className, ...props }: any) {
  return <div className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />;
}
function CardTitle({ className, ...props }: any) {
  return <h2 className={cn("text-2xl font-semibold leading-none tracking-tight", className)} {...props} />;
}
function CardDescription({ className, ...props }: any) {
  return <p className={cn("text-sm text-gray-500", className)} {...props} />;
}
function CardContent({ className, ...props }: any) {
  return <div className={cn("p-6 pt-0", className)} {...props} />;
}

function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
    </div>
  );
}

function Button({ className, variant = "default", size = "default", ...props }: any) {
  const variants: any = { default: "bg-blue-600 text-white hover:bg-blue-700", outline: "border border-gray-300 bg-white hover:bg-gray-50", ghost: "hover:bg-gray-100" };
  const sizes: any = { default: "px-4 py-2", sm: "px-3 py-1 text-sm", lg: "px-6 py-3 text-lg" };
  return <button className={cn("inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none", variants[variant], sizes[size], className)} {...props} />;
}

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
          {resumeId && <p className="text-sm text-success">Resume uploaded </p>}
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


