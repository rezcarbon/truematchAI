'use client';

import React, { useState, useRef } from 'react';
import { Upload, FileText, Loader2 } from 'lucide-react';

interface JDUploadInputProps {
  onSubmit: (jdText: string) => void;
  loading?: boolean;
}

export default function JDUploadInput({
  onSubmit,
  loading = false,
}: JDUploadInputProps) {
  const [jdText, setJdText] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setJdText(e.target.value);
  };

  const handleFileUpload = (file: File) => {
    if (!file.type.startsWith('text/') && file.type !== 'application/pdf') {
      alert('Please upload a text file (.txt, .md, .docx, etc.)');
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setJdText(content);
    };
    reader.readAsText(file);
  };

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer?.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0]);
    }
  };

  const handleSubmit = () => {
    if (!jdText.trim()) {
      alert('Please enter or upload a job description');
      return;
    }
    onSubmit(jdText);
  };

  const handleClear = () => {
    setJdText('');
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Upload or Paste Your Job Description
        </h2>
        <p className="text-gray-600">
          Provide your job description and we'll analyze it for optimization
          opportunities.
        </p>
      </div>

      {/* Upload Area */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 bg-gray-50 hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.md,.doc,.docx,.pdf"
          onChange={handleFileInputChange}
          className="hidden"
          aria-label="Upload job description file"
        />

        <Upload
          className={`w-12 h-12 mx-auto mb-3 ${
            dragActive ? 'text-blue-600' : 'text-gray-400'
          }`}
        />
        <p className="font-semibold text-gray-900 mb-1">
          Drag and drop your file here
        </p>
        <p className="text-gray-600 text-sm">
          or click to select a file (TXT, MD, DOCX, PDF)
        </p>
      </div>

      {/* Or Divider */}
      <div className="flex items-center gap-4">
        <div className="flex-1 border-t border-gray-300" />
        <span className="text-gray-500 font-medium">Or paste below</span>
        <div className="flex-1 border-t border-gray-300" />
      </div>

      {/* Paste Area */}
      <div>
        <label
          htmlFor="jd-textarea"
          className="block text-sm font-medium text-gray-700 mb-2"
        >
          Job Description
        </label>
        <textarea
          id="jd-textarea"
          value={jdText}
          onChange={handleTextChange}
          placeholder="Paste your job description here..."
          rows={12}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono text-sm"
        />
        <p className="text-gray-500 text-xs mt-2">
          {jdText.length} characters
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 justify-end">
        <button
          onClick={handleClear}
          disabled={!jdText.trim() || loading}
          className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          Clear
        </button>
        <button
          onClick={handleSubmit}
          disabled={!jdText.trim() || loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center gap-2"
        >
          {loading && <Loader2 className="w-4 h-4 animate-spin" />}
          {loading ? 'Analyzing...' : 'Analyze JD'}
        </button>
      </div>
    </div>
  );
}
