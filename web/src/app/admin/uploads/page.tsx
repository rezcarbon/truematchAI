'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/AppShell';
import { MassUpload } from '@/components/admin/MassUpload';
import { UploadBatchTracker } from '@/components/admin/UploadBatchTracker';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';

interface FieldMapping {
  id: string;
  name: string;
  description: string;
  isSystem: boolean;
}

interface Batch {
  batchId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  filename: string;
  totalRows: number;
  processedRows: number;
  failedRows: number;
  duplicateRows: number;
  createdAt: string;
  completedAt?: string;
  errors?: { [key: string]: string[] };
}

export default function UploadsPage() {
  const [fieldMappings, setFieldMappings] = useState<FieldMapping[]>([]);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
    // Poll for batch updates every 5 seconds
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [mappingsRes, batchesRes] = await Promise.all([
        api.getFieldMappings(),
        api.getUploadBatches(),
      ]);
      setFieldMappings((mappingsRes.mappings || []) as unknown as FieldMapping[]);
      setBatches((batchesRes.batches || []) as unknown as Batch[]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
      console.error('Error loading data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpload = async (file: File, mappingId: string) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('field_mapping_id', mappingId);

      const response = await api.uploadCSV(formData);
      await loadData();
      return { batchId: (response as { batch_id?: string }).batch_id ?? "" };
    } catch (err) {
      throw err;
    }
  };

  const handleDownloadErrors = async (batchId: string) => {
    try {
      // Get batch details
      const batch = batches.find(b => b.batchId === batchId);
      if (!batch || !batch.errors) {
        alert('No errors to download');
        return;
      }

      // Create CSV content
      let csvContent = 'Row,Error\n';
      Object.entries(batch.errors).forEach(([rowNum, errors]) => {
        const errorText = errors.join('; ');
        csvContent += `${rowNum},"${errorText}"\n`;
      });

      // Download
      const element = document.createElement('a');
      element.setAttribute('href', `data:text/csv;charset=utf-8,${encodeURIComponent(csvContent)}`);
      element.setAttribute('download', `errors-${batchId.substring(0, 8)}.csv`);
      element.style.display = 'none';
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    } catch (err) {
      console.error('Error downloading errors:', err);
      alert('Failed to download errors');
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Bulk Job Import"
        subtitle="Upload job data from CSV or JSON files. Jobs are deduplicated and fed into the assessment pipeline."
      />

      {/* Error Banner */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="flex items-start gap-3 p-4">
            <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-red-900">Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
              <Button
                size="sm"
                variant="outline"
                className="mt-3 text-red-700 border-red-300 hover:bg-red-100"
                onClick={() => setError(null)}
              >
                Dismiss
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {isLoading ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-8 w-8 text-muted-foreground animate-spin mb-2" />
            <p className="text-muted-foreground">Loading upload interface...</p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Upload Component */}
          <MassUpload
            fieldMappings={fieldMappings}
            onUpload={handleUpload}
          />

          {/* Batch Tracker */}
          <UploadBatchTracker
            batches={batches}
            onRefresh={loadData}
            onDownloadErrors={handleDownloadErrors}
          />

          {/* Help Section */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Need help?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs text-muted-foreground">
              <p>
                <strong>CSV Format:</strong> Use headers like "Job Title", "Description", "Company".
                See Field Mappings section for common sources (LinkedIn, Indeed, ZipRecruiter).
              </p>
              <p>
                <strong>JSON Format:</strong> Array of objects with fields: title, description, company.
                Optional: location, job_type, salary_min, salary_max, posted_date, external_url, external_id.
              </p>
              <p>
                <strong>Deduplication:</strong> Jobs are fingerprinted (title + company + description)
                to prevent duplicates. Multiple uploads of the same job will link to one position.
              </p>
              <p>
                <strong>Processing:</strong> Large uploads are processed asynchronously. Check batch status
                to track progress. Errors are detailed per row for easy correction.
              </p>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
