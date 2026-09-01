'use client';

import React, { useState, useCallback } from 'react';
import {
  Download,
  Trash2,
  RotateCcw,
  FileText,
  CheckCircle,
  AlertCircle,
  Clock,
} from 'lucide-react';
import clsx from 'clsx';
import { ResumeVersion } from '@/types/resume';

interface ResumeVersionHistoryProps {
  versions: ResumeVersion[];
  currentVersionId: string;
  onRevert?: (versionId: string) => Promise<void>;
  onDelete?: (versionId: string) => Promise<void>;
  onCompare?: (versionAId: string, versionBId: string) => void;
  onDownload?: (versionId: string) => void;
  loading?: boolean;
}

export default function ResumeVersionHistory({
  versions,
  currentVersionId,
  onRevert,
  onDelete,
  onCompare,
  onDownload,
  loading = false,
}: ResumeVersionHistoryProps) {
  const [expandedVersionId, setExpandedVersionId] = useState<string | null>(null);
  const [revertConfirmId, setRevertConfirmId] = useState<string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const sortedVersions = [...versions].sort(
    (a, b) => new Date(b.uploadedAt).getTime() - new Date(a.uploadedAt).getTime()
  );

  const getStatusIcon = (status: ResumeVersion['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'processing':
        return <Clock className="h-5 w-5 text-blue-600 animate-spin" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
    }
  };

  const getUploadMethodLabel = (method: ResumeVersion['uploadMethod']) => {
    const labels: Record<ResumeVersion['uploadMethod'], string> = {
      'drag-drop': 'Drag & Drop',
      'file-click': 'File Upload',
      paste: 'Pasted Content',
      linkedin: 'LinkedIn',
    };
    return labels[method];
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleRevertClick = useCallback((versionId: string) => {
    setRevertConfirmId(versionId);
  }, []);

  const handleConfirmRevert = useCallback(
    async (versionId: string) => {
      try {
        await onRevert?.(versionId);
        setRevertConfirmId(null);
      } catch (error) {
        console.error('Revert failed:', error);
      }
    },
    [onRevert]
  );

  const handleDeleteClick = useCallback((versionId: string) => {
    setDeleteConfirmId(versionId);
  }, []);

  const handleConfirmDelete = useCallback(
    async (versionId: string) => {
      try {
        await onDelete?.(versionId);
        setDeleteConfirmId(null);
      } catch (error) {
        console.error('Delete failed:', error);
      }
    },
    [onDelete]
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-gray-900">Version History</h3>
          <p className="text-sm text-gray-600">
            {versions.length} version{versions.length !== 1 ? 's' : ''} saved
          </p>
        </div>
      </div>

      {/* Empty State */}
      {sortedVersions.length === 0 && (
        <div className="text-center py-12 bg-gray-50 border border-gray-200 rounded-lg">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 font-medium">No resume versions yet</p>
          <p className="text-sm text-gray-500 mt-1">
            Upload your first resume to get started
          </p>
        </div>
      )}

      {/* Timeline */}
      <div className="space-y-3">
        {sortedVersions.map((version, index) => {
          const isExpanded = expandedVersionId === version.id;
          const isCurrentVersion = currentVersionId === version.id;
          const isCurrent = revertConfirmId === version.id;
          const isDeleteConfirm = deleteConfirmId === version.id;

          return (
            <div
              key={version.id}
              className={clsx(
                'relative border rounded-lg transition-all',
                isExpanded
                  ? 'bg-white border-blue-300 shadow-md'
                  : isCurrentVersion
                    ? 'bg-blue-50 border-blue-200'
                    : 'bg-white border-gray-200 hover:border-gray-300'
              )}
            >
              {/* Timeline Line */}
              {index < sortedVersions.length - 1 && (
                <div className="absolute left-7 top-16 h-8 w-0.5 bg-gray-200" />
              )}

              {/* Main Content */}
              <div className="p-4">
                <div className="flex gap-4">
                  {/* Timeline Dot */}
                  <div className="flex flex-col items-center flex-shrink-0 pt-1">
                    {getStatusIcon(version.status)}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <p className="font-semibold text-gray-900 truncate">
                            v{version.version}: {version.fileName}
                          </p>
                          {isCurrentVersion && (
                            <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                              Current
                            </span>
                          )}
                          {version.status === 'processing' && (
                            <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                              Processing
                            </span>
                          )}
                          {version.status === 'failed' && (
                            <span className="inline-block px-2 py-1 bg-red-100 text-red-800 text-xs font-medium rounded">
                              Failed
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-600 flex flex-wrap gap-3">
                          <span>{getUploadMethodLabel(version.uploadMethod)}</span>
                          <span>•</span>
                          <span>{formatDate(version.uploadedAt)}</span>
                          <span>•</span>
                          <span>{(version.fileSize / 1024).toFixed(1)} KB</span>
                        </p>
                      </div>

                      {/* Expand Button */}
                      <button
                        onClick={() =>
                          setExpandedVersionId(isExpanded ? null : version.id)
                        }
                        disabled={loading}
                        className="text-gray-400 hover:text-gray-600 p-2 transition-colors flex-shrink-0"
                      >
                        <svg
                          className={clsx(
                            'w-5 h-5 transition-transform',
                            isExpanded ? 'rotate-180' : ''
                          )}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 14l-7 7m0 0l-7-7m7 7V3"
                          />
                        </svg>
                      </button>
                    </div>

                    {/* Summary Stats (always visible) */}
                    {version.status === 'completed' && (
                      <div className="grid grid-cols-4 gap-2 mb-3 text-xs">
                        <div className="bg-gray-50 rounded px-2 py-1.5">
                          <p className="text-gray-600 font-medium">Skills</p>
                          <p className="font-semibold text-gray-900">
                            {version.skills?.length || 0}
                          </p>
                        </div>
                        <div className="bg-gray-50 rounded px-2 py-1.5">
                          <p className="text-gray-600 font-medium">Experience</p>
                          <p className="font-semibold text-gray-900">
                            {version.experience_years || 0}y
                          </p>
                        </div>
                        <div className="bg-gray-50 rounded px-2 py-1.5">
                          <p className="text-gray-600 font-medium">Format</p>
                          <p className="font-semibold text-gray-900 uppercase">
                            {version.format}
                          </p>
                        </div>
                        <div className="bg-gray-50 rounded px-2 py-1.5">
                          <p className="text-gray-600 font-medium">Quality</p>
                          <p className="font-semibold text-gray-900">
                            {Math.round((version.skills?.length || 0) * 3.5)}%
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Expanded Details */}
                    {isExpanded && version.status === 'completed' && (
                      <div className="space-y-3 mt-4 pt-4 border-t border-gray-200">
                        {/* Summary */}
                        {version.summary && (
                          <div>
                            <p className="text-xs font-semibold text-gray-600 mb-1">
                              SUMMARY
                            </p>
                            <p className="text-sm text-gray-700">
                              {version.summary}
                            </p>
                          </div>
                        )}

                        {/* Annotation */}
                        {version.annotation && (
                          <div className="bg-yellow-50 border border-yellow-200 rounded p-2">
                            <p className="text-xs font-semibold text-yellow-900 mb-1">
                              NOTE
                            </p>
                            <p className="text-sm text-yellow-800">
                              {version.annotation}
                            </p>
                          </div>
                        )}

                        {/* Skills Preview */}
                        {version.skills && version.skills.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold text-gray-600 mb-2">
                              TOP SKILLS
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {version.skills.slice(0, 5).map((skill, idx) => (
                                <span
                                  key={idx}
                                  className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                                >
                                  {skill}
                                </span>
                              ))}
                              {version.skills.length > 5 && (
                                <span className="inline-block px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                                  +{version.skills.length - 5} more
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Error Message */}
                    {version.status === 'failed' && version.errorMessage && (
                      <div className="bg-red-50 border border-red-200 rounded p-3 mt-3">
                        <p className="text-xs font-semibold text-red-900 mb-1">
                          ERROR
                        </p>
                        <p className="text-sm text-red-800">
                          {version.errorMessage}
                        </p>
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex flex-wrap gap-2 mt-4">
                      {version.status === 'completed' && !isCurrentVersion && (
                        <>
                          {isCurrent ? (
                            <div className="flex gap-2 w-full">
                              <button
                                onClick={() =>
                                  handleConfirmRevert(version.id)
                                }
                                disabled={loading}
                                className="flex-1 px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 transition-colors disabled:opacity-50"
                              >
                                Confirm Revert
                              </button>
                              <button
                                onClick={() =>
                                  setRevertConfirmId(null)
                                }
                                disabled={loading}
                                className="flex-1 px-3 py-1.5 border border-gray-300 text-gray-700 text-xs font-medium rounded hover:bg-gray-50 transition-colors disabled:opacity-50"
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() =>
                                handleRevertClick(version.id)
                              }
                              disabled={loading}
                              className="px-3 py-1.5 border border-gray-300 text-gray-700 text-xs font-medium rounded hover:bg-gray-50 transition-colors disabled:opacity-50 flex items-center gap-1"
                            >
                              <RotateCcw className="w-3 h-3" />
                              Revert
                            </button>
                          )}
                        </>
                      )}

                      {version.status === 'completed' && sortedVersions.length > 1 && index < sortedVersions.length - 1 && (
                        <button
                          onClick={() =>
                            onCompare?.(version.id, sortedVersions[index + 1].id)
                          }
                          disabled={loading}
                          className="px-3 py-1.5 border border-gray-300 text-gray-700 text-xs font-medium rounded hover:bg-gray-50 transition-colors disabled:opacity-50"
                        >
                          Compare
                        </button>
                      )}

                      {onDownload && version.status === 'completed' && (
                        <button
                          onClick={() => onDownload(version.id)}
                          disabled={loading}
                          className="px-3 py-1.5 border border-gray-300 text-gray-700 text-xs font-medium rounded hover:bg-gray-50 transition-colors disabled:opacity-50 flex items-center gap-1"
                        >
                          <Download className="w-3 h-3" />
                          Download
                        </button>
                      )}

                      {isDeleteConfirm ? (
                        <div className="flex gap-2 w-full">
                          <button
                            onClick={() =>
                              handleConfirmDelete(version.id)
                            }
                            disabled={loading}
                            className="flex-1 px-3 py-1.5 bg-red-600 text-white text-xs font-medium rounded hover:bg-red-700 transition-colors disabled:opacity-50"
                          >
                            Confirm Delete
                          </button>
                          <button
                            onClick={() =>
                              setDeleteConfirmId(null)
                            }
                            disabled={loading}
                            className="flex-1 px-3 py-1.5 border border-gray-300 text-gray-700 text-xs font-medium rounded hover:bg-gray-50 transition-colors disabled:opacity-50"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() =>
                            handleDeleteClick(version.id)
                          }
                          disabled={loading || isCurrentVersion}
                          className="px-3 py-1.5 border border-gray-300 text-red-600 text-xs font-medium rounded hover:bg-red-50 transition-colors disabled:opacity-50 disabled:text-gray-400 flex items-center gap-1 ml-auto"
                        >
                          <Trash2 className="w-3 h-3" />
                          Delete
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
