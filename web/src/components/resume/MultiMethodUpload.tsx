"use client";

import React, { useState, useRef, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { UploadCloud, FileText, X, Link as LinkIcon, Copy } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ResumeUploadMethod } from "@/types/resume";

interface MultiMethodUploadProps {
  onUpload: (file: File | string, method: ResumeUploadMethod) => Promise<void>;
  loading?: boolean;
  disabled?: boolean;
  accept?: string;
}

export function MultiMethodUpload({
  onUpload,
  loading = false,
  disabled = false,
  accept = ".pdf,.doc,.docx,.txt",
}: MultiMethodUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [activeTab, setActiveTab] = useState<ResumeUploadMethod>("drag-drop");
  const [pastedContent, setPastedContent] = useState("");
  const [linkedInUrl, setLinkedInUrl] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (f: File | null) => {
      setFile(f);
    },
    []
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      if (!disabled) {
        e.preventDefault();
        setDragging(true);
      }
    },
    [disabled]
  );

  const handleDragLeave = useCallback(() => {
    setDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      if (!disabled) {
        e.preventDefault();
        setDragging(false);
        const droppedFile = e.dataTransfer.files?.[0];
        if (droppedFile) {
          handleFile(droppedFile);
        }
      }
    },
    [disabled, handleFile]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (selectedFile) {
        handleFile(selectedFile);
      }
    },
    [handleFile]
  );

  const handleUploadClick = useCallback(async () => {
    try {
      if (activeTab === "drag-drop" || activeTab === "file-click") {
        if (!file) return;
        setUploadProgress(50);
        await onUpload(file, activeTab);
        setUploadProgress(100);
        setFile(null);
      } else if (activeTab === "paste") {
        if (!pastedContent.trim()) return;
        setUploadProgress(50);
        await onUpload(pastedContent, "paste");
        setUploadProgress(100);
        setPastedContent("");
      } else if (activeTab === "linkedin") {
        if (!linkedInUrl.trim()) return;
        setUploadProgress(50);
        await onUpload(linkedInUrl, "linkedin");
        setUploadProgress(100);
        setLinkedInUrl("");
      }
      setUploadProgress(0);
    } catch (error) {
      console.error("Upload error:", error);
      setUploadProgress(0);
    }
  }, [activeTab, file, pastedContent, linkedInUrl, onUpload]);

  const canUpload = useCallback(() => {
    if (activeTab === "drag-drop" || activeTab === "file-click") {
      return !!file && !loading;
    } else if (activeTab === "paste") {
      return pastedContent.trim().length > 0 && !loading;
    } else if (activeTab === "linkedin") {
      return linkedInUrl.trim().length > 0 && !loading;
    }
    return false;
  }, [activeTab, file, pastedContent, linkedInUrl, loading]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Your Resume</CardTitle>
        <p className="text-sm text-muted-foreground">Choose your preferred upload method</p>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Tab Navigation */}
        <div className="flex gap-2 border-b">
          {(["drag-drop", "paste", "linkedin"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                "flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors",
                activeTab === tab
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground hover:text-foreground"
              )}
              disabled={disabled || loading}
            >
              {tab === "drag-drop" && <UploadCloud className="h-4 w-4" />}
              {tab === "paste" && <Copy className="h-4 w-4" />}
              {tab === "linkedin" && <LinkIcon className="h-4 w-4" />}
              {tab === "drag-drop" && "Upload"}
              {tab === "paste" && "Paste"}
              {tab === "linkedin" && "LinkedIn"}
            </button>
          ))}
        </div>

        {/* Upload Tab */}
        {(activeTab === "drag-drop" || activeTab === "file-click") && (
          <div className="space-y-4">
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => !disabled && inputRef.current?.click()}
              className={cn(
                "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-10 text-center transition-colors",
                disabled || loading
                  ? "cursor-not-allowed opacity-50 border-border"
                  : dragging
                    ? "border-primary bg-accent"
                    : "border-border hover:border-primary/50"
              )}
            >
              <UploadCloud className="mb-3 h-10 w-10 text-muted-foreground" />
              <p className="font-medium">Drag & drop your resume</p>
              <p className="text-sm text-muted-foreground">or click to browse</p>
              <p className="text-xs text-muted-foreground mt-2">{accept}</p>
              <input
                ref={inputRef}
                type="file"
                accept={accept}
                disabled={disabled || loading}
                className="hidden"
                onChange={handleFileSelect}
              />
            </div>

            {file && (
              <div className="flex items-center justify-between rounded-md border bg-card px-4 py-3">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-primary" />
                  <div>
                    <p className="text-sm font-medium">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => handleFile(null)}
                  disabled={loading}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Paste Tab */}
        {activeTab === "paste" && (
          <div className="space-y-4">
            <textarea
              value={pastedContent}
              onChange={(e) => setPastedContent(e.target.value)}
              placeholder="Paste your resume content here..."
              className="min-h-[200px] w-full rounded-md border bg-background p-3 text-sm font-mono"
              disabled={disabled || loading}
            />
            <p className="text-xs text-muted-foreground">
              Paste your entire resume text content. We'll extract skills and experience from it.
            </p>
          </div>
        )}

        {/* LinkedIn Tab */}
        {activeTab === "linkedin" && (
          <div className="space-y-4">
            <input
              type="url"
              value={linkedInUrl}
              onChange={(e) => setLinkedInUrl(e.target.value)}
              placeholder="https://www.linkedin.com/in/yourprofile"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              disabled={disabled || loading}
            />
            <p className="text-xs text-muted-foreground">
              Share your LinkedIn profile URL. We'll fetch and analyze your profile data.
            </p>
          </div>
        )}

        {/* Upload Progress */}
        {uploadProgress > 0 && uploadProgress < 100 && (
          <div className="space-y-2">
            <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground text-center">{uploadProgress}%</p>
          </div>
        )}

        {/* Upload Button */}
        <Button
          onClick={handleUploadClick}
          disabled={!canUpload()}
          className="w-full"
          size="lg"
        >
          {loading || uploadProgress > 0
            ? `${activeTab === "drag-drop" || activeTab === "file-click" ? "Uploading" : "Processing"}...`
            : `${activeTab === "drag-drop" || activeTab === "file-click" ? "Upload" : "Process"} Resume`}
        </Button>
      </CardContent>
    </Card>
  );
}
