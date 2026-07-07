'use client';

import React, { useState, useCallback } from 'react';
import { Loader2, AlertCircle } from 'lucide-react';
import clsx from 'clsx';

interface JDSimulationFormProps {
  onSubmit: (jdText: string) => Promise<void>;
  loading?: boolean;
  placeholder?: string;
  minLength?: number;
  maxLength?: number;
}

interface FormErrors {
  general?: string;
  jdText?: string;
}

export default function JDSimulationForm({
  onSubmit,
  loading = false,
  placeholder = 'Paste your job description here...',
  minLength = 50,
  maxLength = 10000,
}: JDSimulationFormProps) {
  const [jdText, setJdText] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});
  const [successMessage, setSuccessMessage] = useState('');

  const validateForm = useCallback((): boolean => {
    const newErrors: FormErrors = {};

    if (!jdText.trim()) {
      newErrors.jdText = 'Job description is required';
    } else if (jdText.trim().length < minLength) {
      newErrors.jdText = `Job description must be at least ${minLength} characters (currently ${jdText.trim().length})`;
    } else if (jdText.length > maxLength) {
      newErrors.jdText = `Job description cannot exceed ${maxLength} characters`;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [jdText, minLength, maxLength]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      setSuccessMessage('');

      if (!validateForm()) {
        return;
      }

      try {
        await onSubmit(jdText);
        setSuccessMessage('Job description submitted successfully!');
        setJdText('');
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'An error occurred while processing your request';
        setErrors({ general: errorMessage });
      }
    },
    [jdText, validateForm, onSubmit]
  );

  const handleClear = useCallback(() => {
    setJdText('');
    setErrors({});
    setSuccessMessage('');
  }, []);

  const textLengthPercent = (jdText.length / maxLength) * 100;
  const isLengthWarning = jdText.length > maxLength * 0.9;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Analyze Job Description
        </h2>
        <p className="text-gray-600">
          Enter or paste a job description to analyze and optimize its quality
        </p>
      </div>

      {/* Error Alert */}
      {errors.general && (
        <div className="flex gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-red-900">{errors.general}</p>
          </div>
        </div>
      )}

      {/* Success Message */}
      {successMessage && (
        <div className="flex gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5">
            <svg
              className="w-5 h-5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <p className="font-medium text-green-900">{successMessage}</p>
        </div>
      )}

      {/* Textarea */}
      <div>
        <label
          htmlFor="jd-input"
          className="block text-sm font-medium text-gray-700 mb-2"
        >
          Job Description
          <span className="text-red-500 ml-1">*</span>
        </label>
        <textarea
          id="jd-input"
          value={jdText}
          onChange={(e) => setJdText(e.target.value)}
          placeholder={placeholder}
          disabled={loading}
          rows={10}
          className={clsx(
            'w-full px-4 py-3 border rounded-lg font-mono text-sm resize-none transition-colors',
            'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            errors.jdText
              ? 'border-red-300 bg-red-50 text-gray-900'
              : 'border-gray-300 bg-white hover:border-gray-400',
            loading && 'opacity-50 cursor-not-allowed'
          )}
          aria-invalid={!!errors.jdText}
          aria-describedby={errors.jdText ? 'jd-error' : undefined}
        />

        {/* Character counter and error */}
        <div className="mt-2 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            {jdText.length} / {maxLength} characters
          </div>
          {errors.jdText && (
            <div
              id="jd-error"
              className="text-sm text-red-600 font-medium flex items-center gap-1"
            >
              <AlertCircle className="w-4 h-4" />
              {errors.jdText}
            </div>
          )}
        </div>

        {/* Progress bar */}
        <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={clsx(
              'h-full transition-all',
              isLengthWarning ? 'bg-yellow-500' : 'bg-blue-500'
            )}
            style={{ width: `${Math.min(textLengthPercent, 100)}%` }}
            role="progressbar"
            aria-valuenow={Math.min(jdText.length, maxLength)}
            aria-valuemin={0}
            aria-valuemax={maxLength}
          />
        </div>
      </div>

      {/* Minimum length indicator */}
      {jdText.length < minLength && (
        <div className="text-sm text-yellow-700 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          Minimum {minLength} characters required. You have {jdText.length} character{jdText.length !== 1 ? 's' : ''}.
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3 justify-end pt-4">
        <button
          type="button"
          onClick={handleClear}
          disabled={!jdText.trim() || loading}
          className={clsx(
            'px-6 py-2 border rounded-lg font-medium transition-colors',
            loading || !jdText.trim()
              ? 'opacity-50 cursor-not-allowed border-gray-300 text-gray-500 bg-gray-50'
              : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50'
          )}
        >
          Clear
        </button>
        <button
          type="submit"
          disabled={loading || !jdText.trim() || !!errors.jdText}
          className={clsx(
            'px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2',
            loading || !jdText.trim() || errors.jdText
              ? 'opacity-50 cursor-not-allowed bg-blue-400 text-white'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          )}
        >
          {loading && <Loader2 className="w-4 h-4 animate-spin" />}
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>
    </form>
  );
}
