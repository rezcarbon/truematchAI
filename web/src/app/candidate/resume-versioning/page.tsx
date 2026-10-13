import React, { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
"use client";
function cn(...inputs: any[]) {
  return twMerge(clsx(inputs));
}

// import { MultiMethodUpload } from "@/components/resume/MultiMethodUpload"; (needs manual conversion)
// import { VersionTimeline } from "@/components/resume/VersionTimeline"; (needs manual conversion)
// import { VersionComparison } from "@/components/resume/VersionComparison"; (needs manual conversion)
// import { AnnotationModal } from "@/components/resume/AnnotationModal"; (needs manual conversion)
// import { useResumeVersioning } from '@/hooks/useResumeVersioning"; (needs manual conversion)
import { AlertCircle, CheckCircle } from "lucide-react";
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
// import type { ResumeUploadMethod, VersionComparison as VersionComparisonType } from '@/types/resume"; (needs manual conversion)

type ModalState = "none" | "compare" | "annotate";

export default function ResumeVersioningPage() {
  const router = useRouter();
  const { resume, loading, error, uploadResume, revertToVersion, deleteVersion, annotateVersion, compareVersions } = useResumeVersioning();

  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [modalState, setModalState] = useState<ModalState>("none");
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const [comparison, setComparison] = useState<VersionComparisonType | null>(null);
  const [annotatingVersionId, setAnnotatingVersionId] = useState<string | null>(null);

  const handleUpload = useCallback(
    async (file: File | string, method: ResumeUploadMethod) => {
      setUploadError(null);
      setUploadSuccess(false);

      try {
        await uploadResume(file, method);
        setUploadSuccess(true);
        setTimeout(() => setUploadSuccess(false), 3000);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Upload failed";
        setUploadError(message);
      }
    },
    [uploadResume]
  );

  const handleRevert = useCallback(
    async (versionId: string) => {
      try {
        await revertToVersion(versionId);
        setUploadSuccess(true);
        setTimeout(() => setUploadSuccess(false), 3000);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Revert failed";
        setUploadError(message);
      }
    },
    [revertToVersion]
  );

  const handleDelete = useCallback(
    async (versionId: string) => {
      if (!confirm("Are you sure you want to delete this version?")) return;

      try {
        await deleteVersion(versionId);
        setUploadSuccess(true);
        setTimeout(() => setUploadSuccess(false), 3000);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Delete failed";
        setUploadError(message);
      }
    },
    [deleteVersion]
  );

  const handleCompare = useCallback(
    async (versionAId: string, versionBId: string) => {
      try {
        const comp = await compareVersions(versionAId, versionBId);
        setComparison(comp);
        setModalState("compare");
      } catch (err) {
        const message = err instanceof Error ? err.message : "Comparison failed";
        setUploadError(message);
      }
    },
    [compareVersions]
  );

  const handleAnnotate = useCallback(
    (versionId: string) => {
      setAnnotatingVersionId(versionId);
      setModalState("annotate");
    },
    []
  );

  const handleSaveAnnotation = useCallback(
    async (annotation: string) => {
      if (!annotatingVersionId) return;

      try {
        await annotateVersion(annotatingVersionId, annotation);
        setModalState("none");
        setAnnotatingVersionId(null);
        setUploadSuccess(true);
        setTimeout(() => setUploadSuccess(false), 3000);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to save annotation";
        setUploadError(message);
      }
    },
    [annotatingVersionId, annotateVersion]
  );

  const currentVersion = resume?.versions.find((v) => v.id === resume.currentVersionId);
  const annotatingVersion = resume?.versions.find((v) => v.id === annotatingVersionId);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title="Resume Versioning"
        subtitle="Upload, manage, and compare multiple versions of your resume"
      />

      {/* Error Alert */}
      {(uploadError || error) && (
        <div className="rounded-lg border border-red-200 bg-red-50 dark:bg-red-900/20 p-4 flex gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-red-900 dark:text-red-200">Error</p>
            <p className="text-sm text-red-800 dark:text-red-300">{uploadError || error}</p>
          </div>
        </div>
      )}

      {/* Success Alert */}
      {uploadSuccess && (
        <div className="rounded-lg border border-green-200 bg-green-50 dark:bg-green-900/20 p-4 flex gap-3">
          <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-green-800 dark:text-green-200">
            Operation completed successfully
          </p>
        </div>
      )}

      {/* Upload Section */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2">
          <MultiMethodUpload
            onUpload={handleUpload}
            loading={loading}
            disabled={loading}
          />
        </div>

        {/* Current Version Preview */}
        {currentVersion && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Current Version</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-xs text-muted-foreground">Version</p>
                <p className="font-semibold">v{currentVersion.version}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">File</p>
                <p className="font-semibold truncate text-sm">{currentVersion.fileName}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Skills</p>
                <p className="font-semibold">{currentVersion.skills.length} detected</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Experience</p>
                <p className="font-semibold">{currentVersion.experience_years} years</p>
              </div>
              <Button
                className="w-full mt-4"
                onClick={() => router.push("/candidate/assessment")}
              >
                Run Assessment
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Version Timeline */}
      {resume && (
        <VersionTimeline
          versions={resume.versions}
          currentVersionId={resume.currentVersionId}
          onRevert={handleRevert}
          onDelete={handleDelete}
          onCompare={handleCompare}
          onAnnotate={handleAnnotate}
          loading={loading}
        />
      )}

      {/* Comparison Section */}
      {modalState === "compare" && comparison && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Version Comparison</CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setModalState("none");
                setComparison(null);
              }}
            >
              Close
            </Button>
          </CardHeader>
          <CardContent>
            <VersionComparison
              versionA={comparison.versionA}
              versionB={comparison.versionB}
              comparison={comparison}
            />
          </CardContent>
        </Card>
      )}

      {/* Annotation Modal */}
      <AnnotationModal
        open={modalState === "annotate"}
        versionNumber={annotatingVersion?.version}
        initialAnnotation={annotatingVersion?.annotation}
        onSave={handleSaveAnnotation}
        onClose={() => {
          setModalState("none");
          setAnnotatingVersionId(null);
        }}
        loading={loading}
      />
    </div>
  );
}


