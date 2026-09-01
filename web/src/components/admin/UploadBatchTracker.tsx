'use client';

import { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle2, Clock, Download, RotateCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

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

interface UploadBatchTrackerProps {
  batches: Batch[];
  onRefresh: () => Promise<void>;
  onDownloadErrors: (batchId: string) => Promise<void>;
}

function StatusBadge({ status }: { status: Batch['status'] }) {
  const variants = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  const icons = {
    pending: <Clock className="h-3 w-3 mr-1" />,
    processing: <span className="h-3 w-3 mr-1 inline-block animate-spin">⏳</span>,
    completed: <CheckCircle2 className="h-3 w-3 mr-1" />,
    failed: <AlertCircle className="h-3 w-3 mr-1" />,
  };

  const labels = {
    pending: 'Queued',
    processing: 'Processing',
    completed: 'Completed',
    failed: 'Failed',
  };

  return (
    <Badge className={variants[status]}>
      {icons[status]}
      {labels[status]}
    </Badge>
  );
}

function ProgressBar({ processed, total }: { processed: number; total: number }) {
  const percentage = total > 0 ? (processed / total) * 100 : 0;
  return (
    <div className="space-y-1">
      <div className="h-2 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-blue-400 to-blue-600 transition-all"
          style={{ width: `${Math.max(percentage, 5)}%` }}
        />
      </div>
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>{processed} processed</span>
        <span>{total} total</span>
        <span>{Math.round(percentage)}%</span>
      </div>
    </div>
  );
}

export function UploadBatchTracker({ batches, onRefresh, onDownloadErrors }: UploadBatchTrackerProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [expandedBatch, setExpandedBatch] = useState<string | null>(null);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleDownloadErrors = async (batchId: string) => {
    setDownloadingId(batchId);
    try {
      await onDownloadErrors(batchId);
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header with refresh button */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Upload History</h2>
        <Button
          variant="outline"
          size="sm"
          disabled={isRefreshing}
          onClick={handleRefresh}
        >
          <RotateCw className={`h-3.5 w-3.5 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Batches List */}
      {batches.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-8">
            <Clock className="h-8 w-8 text-muted-foreground mb-2" />
            <p className="text-muted-foreground">No uploads yet</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {batches.map((batch) => (
            <Card key={batch.batchId} className={batch.status === 'failed' ? 'border-red-200' : ''}>
              <CardContent className="p-4">
                {/* Batch Header */}
                <div
                  className="flex items-start justify-between cursor-pointer"
                  onClick={() => setExpandedBatch(expandedBatch === batch.batchId ? null : batch.batchId)}
                >
                  <div className="flex-1 space-y-2 min-w-0">
                    {/* Title and Status */}
                    <div className="flex items-center gap-3">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold truncate">{batch.filename}</h3>
                        <p className="text-xs text-muted-foreground">ID: {batch.batchId.substring(0, 8)}...</p>
                      </div>
                      <StatusBadge status={batch.status} />
                    </div>

                    {/* Progress Bar (if processing) */}
                    {batch.status === 'processing' && (
                      <ProgressBar processed={batch.processedRows} total={batch.totalRows} />
                    )}

                    {/* Stats Row */}
                    <div className="grid grid-cols-4 gap-3 text-xs">
                      <div>
                        <p className="text-muted-foreground">Total</p>
                        <p className="font-bold">{batch.totalRows}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Processed</p>
                        <p className="font-bold text-green-600">{batch.processedRows}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Errors</p>
                        <p className={`font-bold ${batch.failedRows > 0 ? 'text-red-600' : 'text-green-600'}`}>
                          {batch.failedRows}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Duplicates</p>
                        <p className="font-bold text-amber-600">{batch.duplicateRows}</p>
                      </div>
                    </div>

                    {/* Timestamp */}
                    <div className="text-xs text-muted-foreground">
                      {batch.status === 'completed' ? (
                        <p>Completed {new Date(batch.completedAt || '').toLocaleString()}</p>
                      ) : batch.status === 'failed' ? (
                        <p>Failed {new Date(batch.completedAt || '').toLocaleString()}</p>
                      ) : (
                        <p>Uploaded {new Date(batch.createdAt).toLocaleString()}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                {expandedBatch === batch.batchId && batch.errors && Object.keys(batch.errors).length > 0 && (
                  <div className="mt-4 space-y-3 border-t pt-4">
                    <h4 className="font-semibold text-sm">Error Details</h4>
                    <div className="max-h-64 overflow-y-auto space-y-2">
                      {Object.entries(batch.errors).slice(0, 10).map(([rowNum, errors]) => (
                        <div key={rowNum} className="rounded-lg bg-red-50 p-2">
                          <p className="text-xs font-medium text-red-900">Row {rowNum}:</p>
                          <ul className="text-xs text-red-700 list-disc list-inside mt-1">
                            {errors.map((error, idx) => (
                              <li key={idx}>{error}</li>
                            ))}
                          </ul>
                        </div>
                      ))}
                      {batch.failedRows > 10 && (
                        <p className="text-xs text-muted-foreground">
                          ... and {batch.failedRows - 10} more errors
                        </p>
                      )}
                    </div>

                    {batch.failedRows > 0 && (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={downloadingId === batch.batchId}
                        onClick={() => handleDownloadErrors(batch.batchId)}
                      >
                        <Download className="h-3.5 w-3.5 mr-2" />
                        {downloadingId === batch.batchId ? 'Downloading...' : 'Download errors'}
                      </Button>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
