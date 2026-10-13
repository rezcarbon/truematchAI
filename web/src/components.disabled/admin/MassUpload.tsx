'use client';

import { useState, useRef } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle2, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface FieldMapping {
  id: string;
  name: string;
  description: string;
  isSystem: boolean;
}

interface MassUploadProps {
  fieldMappings: FieldMapping[];
  onUpload: (file: File, mappingId: string) => Promise<{ batchId: string }>;
}

export function MassUpload({ fieldMappings, onUpload }: MassUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [selectedMapping, setSelectedMapping] = useState<string>(fieldMappings[0]?.id || '');
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadComplete, setUploadComplete] = useState<{ batchId: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles[0]) {
      validateAndSetFile(droppedFiles[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    // Validate file type
    const validTypes = ['text/csv', 'application/vnd.ms-excel', 'application/json', 'text/plain'];
    if (!validTypes.includes(selectedFile.type) && !selectedFile.name.endsWith('.csv') && !selectedFile.name.endsWith('.json')) {
      setError('Please upload a CSV or JSON file');
      return;
    }

    // Validate file size (max 50MB)
    if (selectedFile.size > 50 * 1024 * 1024) {
      setError('File size must be less than 50MB');
      return;
    }

    setFile(selectedFile);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file || !selectedMapping) {
      setError('Please select a file and field mapping');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const result = await onUpload(file, selectedMapping);
      setUploadComplete(result);
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const isCSV = file?.name.endsWith('.csv');
  const fileSize = file?.size ? `${(file.size / 1024).toFixed(1)} KB` : '';

  return (
    <div className="space-y-6">
      {/* Success Message */}
      {uploadComplete && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="flex items-start gap-3 p-4">
            <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-green-900">Upload queued for processing</h3>
              <p className="text-sm text-green-700 mt-1">
                Batch ID: <code className="bg-green-900/10 px-2 py-1 rounded">{uploadComplete.batchId}</code>
              </p>
              <p className="text-xs text-green-700 mt-2">
                You can track the progress of this batch on the Upload History page.
              </p>
              <Button
                size="sm"
                variant="outline"
                className="mt-3 text-green-700 border-green-300 hover:bg-green-100"
                onClick={() => {
                  setUploadComplete(null);
                  setFile(null);
                }}
              >
                Upload another file
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Upload Area */}
      {!uploadComplete && (
        <Card>
          <CardHeader>
            <CardTitle>Upload job data</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Error Message */}
            {error && (
              <div className="flex items-start gap-3 rounded-lg bg-red-50 p-3">
                <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* Drag and Drop Area */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
                isDragging
                  ? 'border-primary bg-primary/5'
                  : 'border-muted-foreground/25 hover:border-primary/50'
              }`}
            >
              <Upload className="mx-auto h-8 w-8 text-muted-foreground mb-2" />
              <p className="text-sm font-medium">Drag and drop your CSV or JSON file here</p>
              <p className="text-xs text-muted-foreground mt-1">or</p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                className="mt-3"
              >
                Browse files
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.json"
                onChange={handleFileSelect}
                className="hidden"
              />
              <p className="text-xs text-muted-foreground mt-3">Max file size: 50MB</p>
            </div>

            {/* Selected File */}
            {file && (
              <div className="flex items-center justify-between rounded-lg border bg-muted/30 p-3">
                <div className="flex items-center gap-3 min-w-0">
                  <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="font-medium truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">{fileSize}</p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setFile(null);
                    if (fileInputRef.current) fileInputRef.current.value = '';
                  }}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}

            {/* Field Mapping Selection */}
            {file && isCSV && (
              <div className="space-y-2">
                <label className="text-sm font-medium">Field Mapping</label>
                <div className="grid grid-cols-1 gap-2">
                  {fieldMappings.map((mapping) => (
                    <button
                      key={mapping.id}
                      onClick={() => setSelectedMapping(mapping.id)}
                      className={`rounded-lg border p-3 text-left transition-colors ${
                        selectedMapping === mapping.id
                          ? 'border-primary bg-primary/5'
                          : 'border-muted hover:border-primary/50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-sm">{mapping.name}</p>
                          <p className="text-xs text-muted-foreground">{mapping.description}</p>
                        </div>
                        {mapping.isSystem && (
                          <Badge variant="secondary" className="shrink-0">System</Badge>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Upload Button */}
            {file && (
              <Button
                onClick={handleUpload}
                disabled={isUploading || !selectedMapping}
                className="w-full"
              >
                {isUploading ? (
                  <>
                    <span className="mr-2">Uploading...</span>
                    <span className="animate-spin">⏳</span>
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload {isCSV ? 'CSV' : 'JSON'} ({file.name})
                  </>
                )}
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Format Help */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Supported formats</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-xs">
          <div>
            <p className="font-medium mb-1">CSV Format</p>
            <p className="text-muted-foreground">Comma-separated values with headers. Required fields: Job Title, Description, Company</p>
            <code className="block bg-muted p-2 rounded mt-1 text-[10px] overflow-x-auto">
              Job Title,Description,Company,Location,Salary
            </code>
          </div>
          <div>
            <p className="font-medium mb-1">JSON Format</p>
            <p className="text-muted-foreground">Array of job objects or single object. Required fields: title, description, company</p>
            <code className="block bg-muted p-2 rounded mt-1 text-[10px] overflow-x-auto">
              {`[{"title":"...", "description":"...", "company":"..."}]`}
            </code>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
