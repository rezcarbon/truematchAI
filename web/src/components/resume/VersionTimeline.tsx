"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Download,
  Trash2,
  RotateCcw,
  FileText,
  CheckCircle,
  AlertCircle,
  Clock,
} from "lucide-react";
import type { ResumeVersion } from "@/types/resume";
import { cn } from "@/lib/utils";

interface VersionTimelineProps {
  versions: ResumeVersion[];
  currentVersionId: string;
  onRevert?: (versionId: string) => Promise<void>;
  onDelete?: (versionId: string) => Promise<void>;
  onCompare?: (versionAId: string, versionBId: string) => void;
  onAnnotate?: (versionId: string) => void;
  loading?: boolean;
}

export function VersionTimeline({
  versions,
  currentVersionId,
  onRevert,
  onDelete,
  onCompare,
  onAnnotate,
  loading = false,
}: VersionTimelineProps) {
  const sortedVersions = [...versions].sort(
    (a, b) => new Date(b.uploadedAt).getTime() - new Date(a.uploadedAt).getTime()
  );

  const getStatusIcon = (status: ResumeVersion["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case "processing":
        return <Clock className="h-5 w-5 text-blue-600 animate-spin" />;
      case "failed":
        return <AlertCircle className="h-5 w-5 text-red-600" />;
    }
  };

  const getUploadMethodLabel = (method: ResumeVersion["uploadMethod"]) => {
    const labels: Record<ResumeVersion["uploadMethod"], string> = {
      "drag-drop": "Drag & Drop",
      "file-click": "File Click",
      paste: "Pasted Content",
      linkedin: "LinkedIn",
    };
    return labels[method];
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Version History</span>
          <Badge variant="secondary">{versions.length} versions</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {sortedVersions.length === 0 ? (
          <p className="text-center text-sm text-muted-foreground py-8">
            No resume versions yet. Upload your first resume to get started.
          </p>
        ) : (
          <div className="space-y-3">
            {sortedVersions.map((version, index) => (
              <div
                key={version.id}
                className={cn(
                  "relative border rounded-lg p-4 transition-colors",
                  currentVersionId === version.id
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50"
                )}
              >
                {/* Timeline line */}
                {index < sortedVersions.length - 1 && (
                  <div className="absolute left-6 top-16 h-8 w-0.5 bg-border" />
                )}

                <div className="flex gap-4">
                  {/* Timeline dot */}
                  <div className="flex flex-col items-center gap-2">
                    {getStatusIcon(version.status)}
                  </div>

                  {/* Version info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                          <p className="font-medium truncate">{version.fileName}</p>
                          {currentVersionId === version.id && (
                            <Badge variant="default" className="ml-auto flex-shrink-0">
                              Current
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          v{version.version} • {getUploadMethodLabel(version.uploadMethod)}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {formatDate(version.uploadedAt)}
                        </p>
                      </div>
                    </div>

                    {/* Version details */}
                    <div className="grid grid-cols-3 gap-2 mb-3 text-xs">
                      <div className="bg-muted rounded p-2">
                        <p className="text-muted-foreground">Skills</p>
                        <p className="font-semibold">{version.skills.length}</p>
                      </div>
                      <div className="bg-muted rounded p-2">
                        <p className="text-muted-foreground">Experience</p>
                        <p className="font-semibold">{version.experience_years}y</p>
                      </div>
                      <div className="bg-muted rounded p-2">
                        <p className="text-muted-foreground">Size</p>
                        <p className="font-semibold">
                          {(version.fileSize / 1024).toFixed(1)}KB
                        </p>
                      </div>
                    </div>

                    {/* Annotation */}
                    {version.annotation && (
                      <div className="mb-3 p-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded text-xs">
                        <p className="text-muted-foreground font-medium mb-1">Annotation:</p>
                        <p>{version.annotation}</p>
                      </div>
                    )}

                    {/* Error message */}
                    {version.status === "failed" && version.errorMessage && (
                      <div className="mb-3 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-xs">
                        <p className="text-destructive font-medium mb-1">Error:</p>
                        <p>{version.errorMessage}</p>
                      </div>
                    )}

                    {/* Action buttons */}
                    <div className="flex gap-2 flex-wrap">
                      {currentVersionId !== version.id && version.status === "completed" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onRevert?.(version.id)}
                          disabled={loading}
                          className="text-xs"
                        >
                          <RotateCcw className="h-3 w-3 mr-1" />
                          Revert
                        </Button>
                      )}
                      {version.status === "completed" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onAnnotate?.(version.id)}
                          disabled={loading}
                          className="text-xs"
                        >
                          Add Note
                        </Button>
                      )}
                      {version.status === "completed" &&
                        sortedVersions.length > 1 &&
                        index < sortedVersions.length - 1 && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                              onCompare?.(version.id, sortedVersions[index + 1].id)
                            }
                            disabled={loading}
                            className="text-xs"
                          >
                            Compare
                          </Button>
                        )}
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onDelete?.(version.id)}
                        disabled={loading || currentVersionId === version.id}
                        className="text-xs text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-3 w-3 mr-1" />
                        Delete
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
