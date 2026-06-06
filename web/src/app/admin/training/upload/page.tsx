'use client';

export const dynamic = 'force-dynamic';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { PageHeader } from '@/components/shared/AppShell';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Upload, CheckCircle, Clock, AlertTriangle } from 'lucide-react';

interface UploadItem {
  id: string;
  filename?: string;
  fileName?: string;
  status: 'processing' | 'completed' | 'failed';
  createdAt?: string;
  row_count?: number;
  format?: string;
}

export default function TrainingUploadPage() {
  const { data: session } = useSession();
  const [isDragging, setIsDragging] = useState(false);
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const [loading, setLoading] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || !session) return;

    const file = files[0];
    if (!file.name.endsWith('.csv') && !file.name.endsWith('.json')) {
      alert('Please upload a CSV or JSON file');
      return;
    }

    setLoading(true);
    try {
      const token = (session as Record<string, unknown>)?.accessToken || (session?.user as Record<string, unknown>)?.accessToken;
      if (!token || typeof token !== 'string') throw new Error('No access token');
      const typedToken = token as string;

      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/training/data/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${typedToken}` },
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');
      const data = await response.json();

      setUploads([data, ...uploads]);
      alert(`Upload started! File: ${file.name}`);
    } catch (err) {
      alert(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'processing':
        return <Clock className="h-5 w-5 text-blue-600" />;
      case 'failed':
        return <AlertTriangle className="h-5 w-5 text-red-600" />;
      default:
        return <Clock className="h-5 w-5 text-gray-600" />;
    }
  };

  return (
    <div>
      <PageHeader
        title="Training Data Upload"
        subtitle="Upload CSV or JSON files with candidate feedback to train the virtual brain"
      />

      {/* Upload Area */}
      <Card
        className={`mb-8 border-2 border-dashed transition-colors ${
          isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFileUpload(e.dataTransfer.files);
        }}
      >
        <CardContent className="p-12 text-center">
          <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-semibold mb-2">Drag and drop your file here</h3>
          <p className="text-muted-foreground mb-4">or click to browse</p>
          <input
            type="file"
            accept=".csv,.json"
            onChange={(e) => handleFileUpload(e.target.files)}
            disabled={loading}
            className="hidden"
            id="file-input"
          />
          <label
            htmlFor="file-input"
            className="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Uploading...' : 'Select File'}
          </label>
          <p className="text-xs text-muted-foreground mt-4">Supported formats: CSV, JSON</p>
        </CardContent>
      </Card>

      {/* Format Guide */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="text-base">File Format Guide</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-semibold text-sm mb-2">CSV Format</h4>
            <p className="text-sm text-muted-foreground mb-2">Required columns:</p>
            <ul className="text-sm space-y-1 ml-4">
              <li>• <code className="bg-gray-100 px-2 py-1 rounded">candidate_name</code> - Full name</li>
              <li>• <code className="bg-gray-100 px-2 py-1 rounded">candidate_email</code> - Email address</li>
              <li>• <code className="bg-gray-100 px-2 py-1 rounded">decision</code> - hire, reject, applied, interested, not_interested</li>
              <li>• <code className="bg-gray-100 px-2 py-1 rounded">reasoning</code> - Why this decision (text)</li>
              <li>• <code className="bg-gray-100 px-2 py-1 rounded">rating</code> - 1-5 (optional)</li>
              <li>• <code className="bg-gray-100 px-2 py-1 rounded">skills</code> - Comma-separated (optional)</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-sm mb-2">JSON Format</h4>
            <p className="text-sm text-muted-foreground">Array of objects with the same fields as CSV</p>
          </div>
        </CardContent>
      </Card>

      {/* Recent Uploads */}
      {uploads.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Recent Uploads</h3>
          <div className="space-y-3">
            {uploads.map((upload) => (
              <Card key={upload.id}>
                <CardContent className="p-5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(upload.status)}
                      <div>
                        <p className="font-medium">{upload.filename}</p>
                        <p className="text-sm text-muted-foreground">
                          {upload.row_count} rows • {upload.format.toUpperCase()}
                        </p>
                      </div>
                    </div>
                    <Badge variant={upload.status === 'completed' ? 'default' : 'secondary'}>
                      {upload.status}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {uploads.length === 0 && !loading && (
        <Card>
          <CardContent className="p-12 text-center">
            <AlertCircle className="h-8 w-8 mx-auto mb-4 text-muted-foreground opacity-50" />
            <p className="text-muted-foreground">No uploads yet. Upload your first training data file!</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
