'use client';

import React, { useState, useEffect } from 'react';
import { Save, X } from 'lucide-react';

interface InlineEditorProps {
  value: string;
  onChange: (value: string) => void;
  onSave: () => void;
  onCancel: () => void;
}

export default function InlineEditor({
  value,
  onChange,
  onSave,
  onCancel,
}: InlineEditorProps) {
  const [hasChanges, setHasChanges] = useState(false);
  const [originalValue] = useState(value);

  useEffect(() => {
    setHasChanges(value !== originalValue);
  }, [value, originalValue]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  const handleSave = () => {
    onSave();
    setHasChanges(false);
  };

  const handleCancel = () => {
    onChange(originalValue);
    onCancel();
  };

  return (
    <div className="space-y-4">
      <div>
        <label
          htmlFor="editor-textarea"
          className="block text-sm font-medium text-gray-700 mb-2"
        >
          Edit Job Description
        </label>
        <textarea
          id="editor-textarea"
          value={value}
          onChange={handleChange}
          rows={16}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono text-sm"
          placeholder="Edit your job description here..."
        />

        <div className="flex justify-between items-center mt-3">
          <div className="text-xs text-gray-500">
            {value.split(/\s+/).filter(Boolean).length} words •{' '}
            {value.length} characters
          </div>
          {hasChanges && (
            <div className="text-xs text-yellow-600 font-medium">
              You have unsaved changes
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 justify-end">
        <button
          onClick={handleCancel}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium flex items-center gap-2"
        >
          <X className="w-4 h-4" />
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={!hasChanges}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          Save Changes
        </button>
      </div>
    </div>
  );
}
