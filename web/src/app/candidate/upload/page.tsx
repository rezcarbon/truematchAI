"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { UploadZone } from "@/components/UploadZone";
import { AlertCircle, Loader2, FileText } from "lucide-react";
import { api } from "@/lib/api";

interface Resume {
  id: string;
  filename: string;
  created_at: string;
  version: number;
  size: number;
}

interface ResumeVersion {
  id: string;
  version: number;
  filename: string;
  created_at: string;
}

export default function UploadPage() {
  const router = useRouter();
  const { data: session } = useSession();
  const [activeTab, setActiveTab] = useState("upload");
  const [file, setFile] = useState<File | null>(null);
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [versions, setVersions] = useState<ResumeVersion[]>([]);
  const [jd, setJd] = useState("");
  const [title, setTitle] = useState("");
  const [status, setStatus] = useState<"idle" | "uploading" | "uploaded" | "assessing" | "loading" | "error">(
    "idle"
  );
  const [message, setMessage] = useState<string>("");
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);

  // Load resumes on mount
  useEffect(() => {
    if (session?.user) {
      loadResumes();
    }
  }, [session]);

  const loadResumes = async () => {
    try {
      setStatus("loading");
      const accessToken = (session?.user as { accessToken?: string })?.accessToken;
      if (!accessToken) {
        throw new Error("Not authenticated");
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiUrl}/api/v1/files/resumes`, {
        headers: {
          "Authorization": `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to load resumes");
      }

      const data = await response.json();
      const resumeList = Array.isArray(data) ? data : data.items || [];
      setResumes(resumeList);
      if (resumeList.length > 0) {
        setSelectedResume(resumeList[0]);
        loadVersions(resumeList[0].id);
      }
      setStatus("idle");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Failed to load resumes");
      setStatus("error");
    }
  };

  const loadVersions = async (resumeId: string) => {
    try {
      const accessToken = (session?.user as { accessToken?: string })?.accessToken;
      if (!accessToken) return;

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiUrl}/api/v1/files/resumes/${resumeId}/versions`, {
        headers: {
          "Authorization": `Bearer ${accessToken}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setVersions(Array.isArray(data) ? data : data.versions || []);
      }
    } catch (err) {
      console.error("Failed to load versions:", err);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setStatus("uploading");
    setMessage("");

    try {
      const accessToken = (session?.user as { accessToken?: string })?.accessToken;
      if (!accessToken) {
        throw new Error("Not authenticated");
      }

      const formData = new FormData();
      formData.append("file", file);

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiUrl}/api/v1/files/resumes/upload`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${accessToken}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Upload failed");
      }

      const res = await response.json();
      setResumeId(res.resume_id || res.id);
      setMessage("Resume uploaded successfully!");
      setStatus("uploaded");
      setFile(null);

      // Reload resumes list
      await loadResumes();
    } catch (e) {
      setStatus("error");
      setMessage(e instanceof Error ? e.message : "Upload failed.");
    }
  };

  const handleAssess = async () => {
    if (!resumeId && !selectedResume?.id) {
      setMessage("Please select a resume");
      return;
    }
    if (jd.trim().length < 20) {
      setMessage("Paste the full job description (at least a couple of sentences).");
      return;
    }

    setStatus("assessing");
    setMessage("");

    try {
      const accessToken = (session?.user as { accessToken?: string })?.accessToken;
      if (!accessToken) {
        throw new Error("Not authenticated");
      }

      const currentResumeId = resumeId || selectedResume?.id;
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

      const response = await fetch(`${apiUrl}/api/v1/candidates/assessment`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          resume_id: currentResumeId,
          job_description: jd,
          position_title: title || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to start assessment");
      }

      const res = await response.json();
      router.push(`/candidate/assessment/${res.assessment_id || res.id}`);
    } catch (e) {
      setStatus("error");
      setMessage(e instanceof Error ? e.message : "Could not start assessment.");
    }
  };

  const handleSelectResume = (resume: Resume) => {
    setSelectedResume(resume);
    setResumeId(resume.id);
    loadVersions(resume.id);
  };

  const handleDeleteResume = async (resumeId: string) => {
    try {
      const accessToken = (session?.user as { accessToken?: string })?.accessToken;
      if (!accessToken) return;

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiUrl}/api/v1/files/resumes/${resumeId}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${accessToken}`,
        },
      });

      if (response.ok) {
        await loadResumes();
        setMessage("Resume deleted successfully");
      }
    } catch (err) {
      console.error("Failed to delete resume:", err);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        title="Resume Management"
        subtitle="Upload, manage, and compare your resume versions for targeted assessments"
        icon="FileText"
      />

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="upload">Upload</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
          <TabsTrigger value="versions">Versions</TabsTrigger>
        </TabsList>

        {/* Upload Tab */}
        <TabsContent value="upload" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Upload a Resume</CardTitle>
              <CardDescription>
                PDF or Word format. Your document is processed securely and stored encrypted.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <UploadZone onFile={setFile} acceptedFormats=".pdf,.doc,.docx" />

              {file && (
                <div className="flex items-center gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <FileText className="h-4 w-4 text-blue-600" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-blue-900 truncate">{file.name}</p>
                    <p className="text-xs text-blue-700">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
              )}

              {message && status === "error" && (
                <div className="flex items-start gap-3 rounded-lg bg-red-50/60 border border-red-200/60 p-4">
                  <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-red-600">{message}</p>
                </div>
              )}

              {message && status === "uploaded" && (
                <div className="flex items-start gap-3 rounded-lg bg-green-50/60 border border-green-200/60 p-4">
                  <AlertCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-green-600">{message}</p>
                </div>
              )}

              <Button
                className="w-full"
                disabled={!file || status === "uploading"}
                onClick={handleUpload}
                size="lg"
              >
                {status === "uploading" ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Uploading...
                  </>
                ) : (
                  "Upload Resume"
                )}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Run Assessment</CardTitle>
              <CardDescription>
                Compare your resume against a specific job description
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="block text-sm font-medium">Select Resume</label>
                <select
                  value={selectedResume?.id || ""}
                  onChange={(e) => {
                    const resume = resumes.find((r) => r.id === e.target.value);
                    if (resume) handleSelectResume(resume);
                  }}
                  disabled={resumes.length === 0 || status === "assessing"}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
                >
                  <option value="">Select a resume</option>
                  {resumes.map((resume) => (
                    <option key={resume.id} value={resume.id}>
                      {resume.filename} (v{resume.version})
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium">Job Title (Optional)</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Senior Backend Engineer"
                  disabled={!selectedResume || status === "assessing"}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
                />
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium">Job Description</label>
                <textarea
                  value={jd}
                  onChange={(e) => setJd(e.target.value)}
                  placeholder="Paste the full job description here..."
                  disabled={!selectedResume || status === "assessing"}
                  className="w-full min-h-[160px] px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50 resize-none"
                />
              </div>

              {message && status !== "uploaded" && (
                <div className="flex items-start gap-3 rounded-lg bg-red-50/60 border border-red-200/60 p-4">
                  <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-red-600">{message}</p>
                </div>
              )}

              <Button
                className="w-full"
                disabled={!selectedResume || !jd.trim() || status === "assessing"}
                onClick={handleAssess}
                size="lg"
              >
                {status === "assessing" ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Starting Assessment...
                  </>
                ) : (
                  "Run Assessment"
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Resume History</CardTitle>
              <CardDescription>
                View all your uploaded resumes and manage versions
              </CardDescription>
            </CardHeader>
            <CardContent>
              {status === "loading" ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : resumes.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">
                    No resumes uploaded yet. Go to the Upload tab to add your first resume.
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {resumes.map((resume) => (
                    <div
                      key={resume.id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{resume.filename}</p>
                        <p className="text-xs text-muted-foreground">
                          Version {resume.version} · {new Date(resume.created_at).toLocaleDateString()} · {(resume.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleSelectResume(resume)}
                        >
                          Use
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDeleteResume(resume.id)}
                        >
                          Delete
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Versions Tab */}
        <TabsContent value="versions" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Resume Versions</CardTitle>
              <CardDescription>
                Compare different versions of {selectedResume?.filename || "your resume"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!selectedResume ? (
                <div className="text-center py-8">
                  <p className="text-sm text-muted-foreground">
                    Select a resume from the History tab to view its versions.
                  </p>
                </div>
              ) : versions.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-sm text-muted-foreground">
                    No versions available for this resume.
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {versions.map((version) => (
                    <div
                      key={version.id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex-1">
                        <p className="text-sm font-medium">Version {version.version}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(version.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <Button size="sm" variant="outline">
                        Compare
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
