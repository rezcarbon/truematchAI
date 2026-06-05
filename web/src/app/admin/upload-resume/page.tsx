'use client';

import { useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { FileUpload } from '@/components/shared/FileUpload';
import { Button } from '@/components/ui/button';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

export default function AdminUploadResumePage() {
  const [file, setFile] = useState<File | null>(null);
  const [candidateName, setCandidateName] = useState('');
  const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState<string>('');
  const [uploadedResumeId, setUploadedResumeId] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!file) return;

    setStatus('uploading');
    setMessage('');

    try {
      const res = await api.uploadResume(file);
      setUploadedResumeId(res.resume_id);
      setStatus('success');
      setMessage(`Resume uploaded successfully! (ID: ${res.resume_id})`);
      setFile(null);
      setCandidateName('');
    } catch (err) {
      setStatus('error');
      setMessage(err instanceof Error ? err.message : 'Upload failed.');
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Upload Candidate Resume"
        subtitle="Upload candidate resumes for analysis, testing, and assessment"
        icon="Upload"
      />

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle>Upload Resume</CardTitle>
            <CardDescription>
              Upload candidate resumes in PDF or Word format for testing and analysis.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Candidate Name (Optional) */}
            <div className="space-y-2">
              <label htmlFor="candidate-name" className="block text-sm font-medium">
                Candidate Name (Optional)
              </label>
              <input
                id="candidate-name"
                type="text"
                value={candidateName}
                onChange={(e) => setCandidateName(e.target.value)}
                placeholder="e.g., John Doe"
                disabled={status === 'uploading'}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <p className="text-xs text-muted-foreground">
                For your reference only. Not stored with the resume.
              </p>
            </div>

            {/* File Upload */}
            <div className="space-y-3">
              <label className="block text-sm font-medium">Resume File *</label>
              <FileUpload onFile={setFile} disabled={status === 'uploading'} />
              <p className="text-xs text-muted-foreground">
                Supported formats: PDF, Word (.doc, .docx)
              </p>
            </div>

            {/* Error Message */}
            {status === 'error' && (
              <div className="flex items-start gap-3 rounded-lg bg-red-50/60 border border-red-200/60 p-4">
                <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-600">{message}</p>
              </div>
            )}

            {/* Success Message */}
            {status === 'success' && (
              <div className="flex items-start gap-3 rounded-lg bg-green-50/60 border border-green-200/60 p-4">
                <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-green-600">
                  <p className="font-medium mb-1">Resume uploaded successfully!</p>
                  <p className="text-xs opacity-90">{message}</p>
                </div>
              </div>
            )}

            {/* Upload Button */}
            <Button
              onClick={handleUpload}
              disabled={!file || status === 'uploading'}
              className="w-full"
              size="lg"
            >
              {status === 'uploading' ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Uploading...
                </>
              ) : (
                'Upload Resume'
              )}
            </Button>

            {/* Info Box */}
            <div className="rounded-lg bg-blue-50/50 border border-blue-200/50 p-4">
              <p className="text-sm text-blue-900">
                <span className="font-medium">💡 Tip:</span> After uploading, you can use the resume in:
              </p>
              <ul className="mt-2 ml-4 text-sm text-blue-900 space-y-1">
                <li>✓ CV Analysis - Test candidate analysis workflow</li>
                <li>✓ Assessments - Create candidate assessments</li>
                <li>✓ Job Matching - See matching recommendations</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Multiple Uploads Info */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-base">Bulk Upload</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Need to upload multiple resumes at once? Use the <a href="/admin/uploads" className="text-primary hover:underline">Bulk Upload</a> feature to import candidates in batch.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
