import { useState } from "react";
import { useRouter } from "next/navigation";
"use client";
function cn(...inputs: any[]) {
  return twMerge(clsx(inputs));
}

// import { FileUpload } from "@/components/shared/FileUpload"; (needs manual conversion)
// api removed - use fetch directly;
import { Compass } from "lucide-react";
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

export default function TransitionStartPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [currentRole, setCurrentRole] = useState("");
  const [target, setTarget] = useState("");
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

  async function start() {
    if (!resumeId) return;
    setStatus("starting");
    setMessage("");
    try {
      const res = await api.createTransition(resumeId, currentRole || undefined, target || undefined);
      router.push(`/candidate/transition-intelligence/${res.analysisId}`);
    } catch (e) {
      setStatus("error");
      setMessage(e instanceof Error ? e.message : "Could not start the analysis.");
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader
        title="Transition Pathways"
        subtitle="See the adjacent and higher-complexity roles your evidenced capability could move you into — with the specific upskilling that closes the gap, recommended courses, and an honest timeline. Grounded in what your résumé actually proves; nothing inflated."
      />

      <Card>
        <CardHeader>
          <CardTitle>1. Your résumé</CardTitle>
          <CardDescription>PDF or Word, in any language. Processed securely.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <FileUpload onFile={setFile} />
          {status !== "uploaded" && status !== "starting" && (
            <Button className="w-full" disabled={!file || status === "uploading"} onClick={upload}>
              {status === "uploading" ? "Uploading…" : "Upload résumé"}
            </Button>
          )}
          {resumeId && <p className="text-sm text-success">Résumé uploaded </p>}
        </CardContent>
      </Card>

      <Card className={resumeId ? "" : "pointer-events-none opacity-50"}>
        <CardHeader>
          <CardTitle>2. Where you are (and optionally, where you want to go)</CardTitle>
          <CardDescription>
            Your current/most-recent role anchors the prediction. A target direction is optional.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium uppercase text-muted-foreground">
              Current role
            </label>
            <input
              value={currentRole}
              onChange={(e) => setCurrentRole(e.target.value)}
              placeholder="e.g. Senior Software Engineer"
              className="w-full rounded-md border bg-background p-2.5 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium uppercase text-muted-foreground">
              Target direction (optional)
            </label>
            <input
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="e.g. move into engineering management, or an AI-platform role"
              className="w-full rounded-md border bg-background p-2.5 text-sm"
            />
          </div>
          <Button className="w-full gap-1.5" disabled={!resumeId || status === "starting"} onClick={start}>
            <Compass className="h-4 w-4" />
            {status === "starting" ? "Analyzing…" : "Map my pathways"}
          </Button>
          {message && <p className="text-sm text-destructive">{message}</p>}
        </CardContent>
      </Card>
    </div>
  );
}


