'use client';

import React, { useState, useRef, useCallback } from 'react';
import {
  Upload,
  Copy,
  Link as LinkIcon,
  FileText,
  X,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';
import clsx from 'clsx';

interface UploadZoneProps {
  onUpload: (file: File | string, method: UploadMethod) => Promise<void>;
  onFileSelect?: (file: File) => void;
  loading?: boolean;
  disabled?: boolean;
  maxFileSize?: number; // in bytes
  acceptedFormats?: string[];
  multiple?: boolean;
  showNotifications?: boolean;
}

export type UploadMethod = 'file' | 'paste' | 'linkedin' | 'links';

interface UploadNotification {
  id: string;
  type: 'success' | 'error';
  message: string;
}

export default function UploadZone({
  onUpload,
  onFileSelect,
  loading = false,
  disabled = false,
  maxFileSize = 10 * 1024 * 1024, // 10MB
  acceptedFormats = ['.pdf', '.doc', '.docx', '.txt'],
  multiple = false,
  showNotifications = true,
}: UploadZoneProps) {
  const [activeTab, setActiveTab] = useState<UploadMethod>('file');
  const [dragging, setDragging] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [pastedContent, setPastedContent] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [links, setLinks] = useState('');
  const [notifications, setNotifications] = useState<UploadNotification[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addNotification = useCallback(
    (type: 'success' | 'error', message: string) => {
      if (!showNotifications) return;

      const id = Date.now().toString();
      setNotifications((prev) => [...prev, { id, type, message }]);

      setTimeout(() => {
        setNotifications((prev) => prev.filter((n) => n.id !== id));
      }, 4000);
    },
    [showNotifications]
  );

  const validateFile = useCallback(
    (file: File): string | null => {
      if (file.size > maxFileSize) {
        return `File size exceeds ${(maxFileSize / 1024 / 1024).toFixed(1)}MB limit`;
      }

      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!acceptedFormats.includes(fileExtension)) {
        return `File type not supported. Accepted formats: ${acceptedFormats.join(', ')}`;
      }

      return null;
    },
    [maxFileSize, acceptedFormats]
  );

  const handleFileSelect = useCallback(
    (files: FileList | null) => {
      if (!files) return;

      const fileArray = Array.from(files);

      if (!multiple && fileArray.length > 1) {
        addNotification('error', 'Only one file can be uploaded at a time');
        return;
      }

      const validFiles: File[] = [];

      for (const file of fileArray) {
        const error = validateFile(file);
        if (error) {
          addNotification('error', error);
        } else {
          validFiles.push(file);
          onFileSelect?.(file);
        }
      }

      setSelectedFiles((prev) => (multiple ? [...prev, ...validFiles] : validFiles));
    },
    [validateFile, onFileSelect, addNotification, multiple]
  );

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled && !loading) {
      setDragging(true);
    }
  }, [disabled, loading]);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setDragging(false);

      if (!disabled && !loading) {
        handleFileSelect(e.dataTransfer.files);
      }
    },
    [disabled, loading, handleFileSelect]
  );

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      handleFileSelect(e.target.files);
    },
    [handleFileSelect]
  );

  const handleRemoveFile = useCallback((index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handlePasteUpload = useCallback(async () => {
    if (!pastedContent.trim()) {
      addNotification('error', 'Please paste some content');
      return;
    }

    try {
      await onUpload(pastedContent, 'paste');
      addNotification('success', 'Content uploaded successfully');
      setPastedContent('');
    } catch (error) {
      addNotification(
        'error',
        error instanceof Error ? error.message : 'Upload failed'
      );
    }
  }, [pastedContent, onUpload, addNotification]);

  const handleFileUpload = useCallback(async () => {
    if (selectedFiles.length === 0) {
      addNotification('error', 'Please select a file');
      return;
    }

    for (const file of selectedFiles) {
      try {
        await onUpload(file, 'file');
        addNotification('success', `${file.name} uploaded successfully`);
      } catch (error) {
        addNotification(
          'error',
          `Failed to upload ${file.name}: ${error instanceof Error ? error.message : 'Unknown error'}`
        );
      }
    }

    setSelectedFiles([]);
  }, [selectedFiles, onUpload, addNotification]);

  const handleLinkedInUpload = useCallback(async () => {
    if (!linkedinUrl.trim()) {
      addNotification('error', 'Please enter a LinkedIn URL');
      return;
    }

    try {
      await onUpload(linkedinUrl, 'linkedin');
      addNotification('success', 'LinkedIn profile processed successfully');
      setLinkedinUrl('');
    } catch (error) {
      addNotification(
        'error',
        error instanceof Error ? error.message : 'Processing failed'
      );
    }
  }, [linkedinUrl, onUpload, addNotification]);

  const handleLinksUpload = useCallback(async () => {
    if (!links.trim()) {
      addNotification('error', 'Please enter at least one URL');
      return;
    }

    try {
      await onUpload(links, 'links');
      addNotification('success', 'Links processed successfully');
      setLinks('');
    } catch (error) {
      addNotification(
        'error',
        error instanceof Error ? error.message : 'Processing failed'
      );
    }
  }, [links, onUpload, addNotification]);

  const acceptAttribute = acceptedFormats.join(',');

  return (
    <div className="space-y-4">
      {/* Tab Navigation */}
      <div className="flex gap-0 border-b border-gray-200">
        {(['file', 'paste', 'linkedin', 'links'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            disabled={disabled || loading}
            className={clsx(
              'flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2',
              activeTab === tab
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900',
              (disabled || loading) && 'opacity-50 cursor-not-allowed'
            )}
          >
            {tab === 'file' && <Upload className="w-4 h-4" />}
            {tab === 'paste' && <Copy className="w-4 h-4" />}
            {tab === 'linkedin' && <LinkIcon className="w-4 h-4" />}
            {tab === 'links' && <LinkIcon className="w-4 h-4" />}
            <span className="capitalize">{tab}</span>
          </button>
        ))}
      </div>

      {/* File Upload Tab */}
      {activeTab === 'file' && (
        <div className="space-y-4">
          {/* Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => !disabled && !loading && fileInputRef.current?.click()}
            className={clsx(
              'relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
              dragging
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50',
              (disabled || loading) && 'opacity-50 cursor-not-allowed'
            )}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept={acceptAttribute}
              multiple={multiple}
              onChange={handleFileInputChange}
              disabled={disabled || loading}
              className="hidden"
              aria-label="Upload files"
            />

            <Upload
              className={clsx(
                'w-12 h-12 mx-auto mb-3',
                dragging ? 'text-blue-600' : 'text-gray-400'
              )}
            />
            <p className="font-semibold text-gray-900 mb-1">
              Drag & drop files here
            </p>
            <p className="text-gray-600 text-sm mb-2">or click to browse</p>
            <p className="text-xs text-gray-500">
              Max {(maxFileSize / 1024 / 1024).toFixed(1)}MB • {acceptedFormats.join(', ')}
            </p>
          </div>

          {/* Selected Files */}
          {selectedFiles.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-900">
                Selected Files ({selectedFiles.length})
              </p>
              {selectedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded-lg"
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <FileText className="w-5 h-5 text-gray-400 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-600">
                        {(file.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleRemoveFile(index)}
                    disabled={loading}
                    className="p-1 text-gray-400 hover:text-red-600 transition-colors flex-shrink-0"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Upload Button */}
          <button
            onClick={handleFileUpload}
            disabled={selectedFiles.length === 0 || loading}
            className={clsx(
              'w-full px-4 py-2 rounded-lg font-medium transition-colors',
              selectedFiles.length === 0 || loading
                ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            )}
          >
            {loading ? 'Uploading...' : 'Upload'}
          </button>
        </div>
      )}

      {/* Paste Tab */}
      {activeTab === 'paste' && (
        <div className="space-y-4">
          <textarea
            value={pastedContent}
            onChange={(e) => setPastedContent(e.target.value)}
            placeholder="Paste your content here..."
            disabled={disabled || loading}
            rows={8}
            className={clsx(
              'w-full px-4 py-3 border rounded-lg font-mono text-sm resize-none transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              (disabled || loading)
                ? 'bg-gray-50 border-gray-200 cursor-not-allowed'
                : 'bg-white border-gray-300'
            )}
          />
          <p className="text-xs text-gray-600">
            {pastedContent.length} characters
          </p>
          <button
            onClick={handlePasteUpload}
            disabled={!pastedContent.trim() || loading}
            className={clsx(
              'w-full px-4 py-2 rounded-lg font-medium transition-colors',
              !pastedContent.trim() || loading
                ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            )}
          >
            {loading ? 'Processing...' : 'Process Content'}
          </button>
        </div>
      )}

      {/* LinkedIn Tab */}
      {activeTab === 'linkedin' && (
        <div className="space-y-4">
          <input
            type="url"
            value={linkedinUrl}
            onChange={(e) => setLinkedinUrl(e.target.value)}
            placeholder="https://www.linkedin.com/in/yourprofile"
            disabled={disabled || loading}
            className={clsx(
              'w-full px-4 py-2 border rounded-lg text-sm transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              (disabled || loading)
                ? 'bg-gray-50 border-gray-200 cursor-not-allowed'
                : 'bg-white border-gray-300'
            )}
          />
          <p className="text-xs text-gray-600">
            Share your public LinkedIn profile URL. We'll fetch and analyze your profile.
          </p>
          <button
            onClick={handleLinkedInUpload}
            disabled={!linkedinUrl.trim() || loading}
            className={clsx(
              'w-full px-4 py-2 rounded-lg font-medium transition-colors',
              !linkedinUrl.trim() || loading
                ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            )}
          >
            {loading ? 'Processing...' : 'Process LinkedIn Profile'}
          </button>
        </div>
      )}

      {/* Links Tab */}
      {activeTab === 'links' && (
        <div className="space-y-4">
          <textarea
            value={links}
            onChange={(e) => setLinks(e.target.value)}
            placeholder="Enter URLs (one per line):&#10;https://example.com/resume&#10;https://example.com/portfolio"
            disabled={disabled || loading}
            rows={6}
            className={clsx(
              'w-full px-4 py-3 border rounded-lg font-mono text-sm resize-none transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              (disabled || loading)
                ? 'bg-gray-50 border-gray-200 cursor-not-allowed'
                : 'bg-white border-gray-300'
            )}
          />
          <p className="text-xs text-gray-600">
            Enter one URL per line. We'll fetch and process the content from these links.
          </p>
          <button
            onClick={handleLinksUpload}
            disabled={!links.trim() || loading}
            className={clsx(
              'w-full px-4 py-2 rounded-lg font-medium transition-colors',
              !links.trim() || loading
                ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            )}
          >
            {loading ? 'Processing...' : 'Process Links'}
          </button>
        </div>
      )}

      {/* Notifications */}
      <div className="fixed bottom-4 right-4 space-y-2 z-50">
        {notifications.map((notification) => (
          <div
            key={notification.id}
            className={clsx(
              'flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-sm font-medium animate-in slide-in-from-right',
              notification.type === 'success'
                ? 'bg-green-500 text-white'
                : 'bg-red-500 text-white'
            )}
          >
            {notification.type === 'success' ? (
              <CheckCircle className="w-5 h-5" />
            ) : (
              <AlertCircle className="w-5 h-5" />
            )}
            {notification.message}
          </div>
        ))}
      </div>
    </div>
  );
}
