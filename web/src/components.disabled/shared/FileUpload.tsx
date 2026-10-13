"use client";
import * as React from "react";
import { UploadCloud, FileText, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export function FileUpload({
  accept = ".pdf,.doc,.docx",
  onFile,
  disabled = false,
}: {
  accept?: string;
  onFile?: (file: File) => void;
  disabled?: boolean;
}) {
  const [file, setFile] = React.useState<File | null>(null);
  const [dragging, setDragging] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  function handle(f: File | null) {
    setFile(f);
    if (f && onFile) onFile(f);
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          if (!disabled) {
            e.preventDefault();
            setDragging(true);
          }
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          if (!disabled) {
            e.preventDefault();
            setDragging(false);
            handle(e.dataTransfer.files?.[0] ?? null);
          }
        }}
        onClick={() => !disabled && inputRef.current?.click()}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-10 text-center transition-colors",
          disabled ? "cursor-not-allowed opacity-50 border-border" : dragging ? "border-primary bg-accent" : "border-border hover:border-primary/50"
        )}
      >
        <UploadCloud className="mb-3 h-10 w-10 text-muted-foreground" />
        <p className="font-medium">Drag &amp; drop your resume</p>
        <p className="text-sm text-muted-foreground">or click to browse — {accept}</p>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          disabled={disabled}
          className="hidden"
          onChange={(e) => handle(e.target.files?.[0] ?? null)}
        />
      </div>

      {file && (
        <div className="mt-4 flex items-center justify-between rounded-md border bg-card px-4 py-3">
          <div className="flex items-center gap-3">
            <FileText className="h-5 w-5 text-primary" />
            <div>
              <p className="text-sm font-medium">{file.name}</p>
              <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(0)} KB</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={() => handle(null)} aria-label="Remove file">
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
