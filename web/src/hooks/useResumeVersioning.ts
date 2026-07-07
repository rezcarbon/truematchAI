import { useState, useCallback } from "react";
import type {
  Resume,
  ResumeVersion,
  ResumeUploadMethod,
  ResumeStatus,
  VersionComparison,
} from "@/types/resume";

interface UseResumeVersioningReturn {
  resume: Resume | null;
  loading: boolean;
  error: string | null;
  uploadResume: (
    file: File | string,
    method: ResumeUploadMethod
  ) => Promise<ResumeVersion>;
  revertToVersion: (versionId: string) => Promise<void>;
  deleteVersion: (versionId: string) => Promise<void>;
  annotateVersion: (versionId: string, annotation: string) => Promise<void>;
  compareVersions: (versionAId: string, versionBId: string) => Promise<VersionComparison>;
}

export function useResumeVersioning(
  initialResume?: Resume
): UseResumeVersioningReturn {
  const [resume, setResume] = useState<Resume | null>(initialResume || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const uploadResume = useCallback(
    async (file: File | string, method: ResumeUploadMethod): Promise<ResumeVersion> => {
      setLoading(true);
      setError(null);

      try {
        const formData = new FormData();

        if (file instanceof File) {
          formData.append("file", file);
        } else {
          formData.append("content", file);
        }

        formData.append("uploadMethod", method);

        const response = await fetch("/api/resume/upload", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || "Failed to upload resume");
        }

        const data = await response.json();

        // Update local state
        if (!resume) {
          setResume({
            id: data.resumeId,
            userId: data.userId,
            currentVersionId: data.versionId,
            versions: [data.version],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            assessmentCount: 0,
          });
        } else {
          setResume({
            ...resume,
            currentVersionId: data.versionId,
            versions: [data.version, ...resume.versions],
            updatedAt: new Date().toISOString(),
          });
        }

        return data.version;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error occurred";
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [resume]
  );

  const revertToVersion = useCallback(
    async (versionId: string): Promise<void> => {
      if (!resume) throw new Error("No resume loaded");

      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/resume/${resume.id}/revert`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ versionId }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || "Failed to revert resume");
        }

        setResume({
          ...resume,
          currentVersionId: versionId,
          updatedAt: new Date().toISOString(),
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error occurred";
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [resume]
  );

  const deleteVersion = useCallback(
    async (versionId: string): Promise<void> => {
      if (!resume) throw new Error("No resume loaded");

      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/resume/${resume.id}/versions/${versionId}`, {
          method: "DELETE",
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || "Failed to delete version");
        }

        setResume({
          ...resume,
          versions: resume.versions.filter((v) => v.id !== versionId),
          updatedAt: new Date().toISOString(),
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error occurred";
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [resume]
  );

  const annotateVersion = useCallback(
    async (versionId: string, annotation: string): Promise<void> => {
      if (!resume) throw new Error("No resume loaded");

      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `/api/resume/${resume.id}/versions/${versionId}/annotate`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ annotation }),
          }
        );

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || "Failed to annotate version");
        }

        const updatedVersion = await response.json();

        setResume({
          ...resume,
          versions: resume.versions.map((v) =>
            v.id === versionId ? { ...v, annotation: updatedVersion.annotation } : v
          ),
          updatedAt: new Date().toISOString(),
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error occurred";
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [resume]
  );

  const compareVersions = useCallback(
    async (versionAId: string, versionBId: string): Promise<VersionComparison> => {
      if (!resume) throw new Error("No resume loaded");

      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/resume/${resume.id}/compare`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ versionAId, versionBId }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || "Failed to compare versions");
        }

        return await response.json();
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error occurred";
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [resume]
  );

  return {
    resume,
    loading,
    error,
    uploadResume,
    revertToVersion,
    deleteVersion,
    annotateVersion,
    compareVersions,
  };
}
