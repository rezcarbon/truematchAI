'use client';

/**
 * Job application modal
 */

import React, { useState } from 'react';
import { X } from 'lucide-react';
import type { Job } from '@/types/jobs';

interface ApplyModalProps {
  job: Job;
  isOpen: boolean;
  onClose: () => void;
  onApply: (data: ApplyFormData) => Promise<void>;
}

export interface ApplyFormData {
  jobId: string;
  resume?: string;
  coverLetter: string;
  email?: string;
}

export function ApplyModal({ job, isOpen, onClose, onApply }: ApplyModalProps) {
  const [formData, setFormData] = useState<ApplyFormData>({
    jobId: job.id,
    coverLetter: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.coverLetter.trim()) {
      setError('Please provide a cover letter or motivation statement');
      return;
    }

    try {
      setIsSubmitting(true);
      await onApply(formData);
      setSuccess(true);
      setTimeout(() => {
        onClose();
        setFormData({ jobId: job.id, coverLetter: '' });
        setSuccess(false);
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply to job');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 sticky top-0 bg-white">
          <div>
            <h2 className="font-bold text-lg text-gray-900">{job.title}</h2>
            <p className="text-sm text-gray-600">{job.company}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6">
          {success ? (
            <div className="text-center py-8">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Application Sent!</h3>
              <p className="text-sm text-gray-600">
                Your application has been submitted successfully. Good luck!
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Job Details */}
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Location:</span>
                    <p className="font-medium text-gray-900">{job.location}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Type:</span>
                    <p className="font-medium text-gray-900 capitalize">{job.jobType}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Salary:</span>
                    <p className="font-medium text-gray-900">
                      ${job.salaryMin.toLocaleString()} - ${job.salaryMax.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-600">Level:</span>
                    <p className="font-medium text-gray-900 capitalize">{job.level}</p>
                  </div>
                </div>
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  value={formData.email || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  placeholder="your@email.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Resume Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Resume (Optional)
                </label>
                <select
                  value={formData.resume || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, resume: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select a resume to attach</option>
                  <option value="default">Default Resume</option>
                  <option value="tech">Tech-Focused Resume</option>
                  <option value="custom">Custom Resume</option>
                </select>
              </div>

              {/* Cover Letter */}
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Motivation Statement / Cover Letter
                </label>
                <textarea
                  value={formData.coverLetter}
                  onChange={(e) =>
                    setFormData({ ...formData, coverLetter: e.target.value })
                  }
                  placeholder="Tell us why you're interested in this position and what unique value you can bring..."
                  rows={6}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Error Message */}
              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              {/* Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Applying...' : 'Submit Application'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
