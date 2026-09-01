"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

interface AnnotationModalProps {
  open: boolean;
  versionNumber?: number;
  onSave: (annotation: string) => Promise<void>;
  onClose: () => void;
  initialAnnotation?: string;
  loading?: boolean;
}

export function AnnotationModal({
  open,
  versionNumber,
  onSave,
  onClose,
  initialAnnotation = "",
  loading = false,
}: AnnotationModalProps) {
  const [annotation, setAnnotation] = useState(initialAnnotation);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    if (!annotation.trim()) {
      setError("Please enter an annotation");
      return;
    }

    try {
      await onSave(annotation);
      setAnnotation("");
      setError(null);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save annotation");
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>
            {versionNumber ? `Add Note to Version ${versionNumber}` : "Add Note"}
          </CardTitle>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            disabled={loading}
          >
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <textarea
            value={annotation}
            onChange={(e) => {
              setAnnotation(e.target.value);
              setError(null);
            }}
            placeholder="Add a note about this version (e.g., 'Added new skills', 'Updated contact info')"
            className="w-full rounded-md border bg-background p-3 text-sm min-h-[120px]"
            disabled={loading}
          />

          {error && <p className="text-sm text-destructive">{error}</p>}

          <div className="flex gap-2 justify-end">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={loading || !annotation.trim()}
            >
              {loading ? "Saving..." : "Save Note"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
