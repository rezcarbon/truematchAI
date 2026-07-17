/**
 * Main approval detail page - reviews config and allows approve/reject
 */

import React, { useState, useEffect } from "react";
import { useGetApprovalChecklist, useApproveConfig, useRejectConfig } from "../../hooks/useAgentConfigApi";
import { ValidationChecklist } from "./ValidationChecklist";
import { ConfigComparison } from "./ConfigComparison";
import { AuditTimeline } from "./AuditTimeline";
import { ExportButtons } from "./ExportButtons";

interface ApprovalDetailPageProps {
  configId: string;
  onApprovalComplete?: () => void;
}

type TabType = "checklist" | "comparison" | "audit";

export const ApprovalDetailPage: React.FC<ApprovalDetailPageProps> = ({
  configId,
  onApprovalComplete,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>("checklist");
  const [feedback, setFeedback] = useState("");
  const [showApproveConfirm, setShowApproveConfirm] = useState(false);
  const [showRejectConfirm, setShowRejectConfirm] = useState(false);

  // Fetch approval checklist
  const { data: checklist, loading: checklistLoading, error: checklistError, fetch } =
    useGetApprovalChecklist(configId);

  // Approval mutations
  const { approve, loading: approveLoading, error: approveError } = useApproveConfig();
  const { reject, loading: rejectLoading, error: rejectError } = useRejectConfig();

  useEffect(() => {
    fetch();
  }, [configId, fetch]);

  const handleApprove = async () => {
    try {
      await approve(configId, feedback);
      setShowApproveConfirm(false);
      onApprovalComplete?.();
    } catch (error) {
      // Error is handled in hook state
    }
  };

  const handleReject = async () => {
    try {
      await reject(configId, feedback);
      setShowRejectConfirm(false);
      onApprovalComplete?.();
    } catch (error) {
      // Error is handled in hook state
    }
  };

  if (checklistLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading approval checklist...</p>
        </div>
      </div>
    );
  }

  if (checklistError || !checklist) {
    return (
      <div className="border border-red-200 rounded-lg p-4 bg-red-50">
        <h3 className="font-semibold text-red-900">Error Loading Configuration</h3>
        <p className="text-sm text-red-800 mt-1">
          {checklistError?.message || "Unable to load approval checklist"}
        </p>
        <button
          onClick={() => fetch()}
          className="mt-3 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  const isApprovalDisabled = checklist.recommendation === "review_required";

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            {checklist.agent_type.charAt(0).toUpperCase() + checklist.agent_type.slice(1)} Agent
            Config
          </h1>
          <p className="text-gray-600 mt-1">Version {checklist.version_number}</p>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-600">Submitted</div>
          <div className="font-medium">
            {checklist.submitted_at
              ? new Date(checklist.submitted_at).toLocaleDateString()
              : "Unknown"}
          </div>
        </div>
      </div>

      {/* Status Banner */}
      {isApprovalDisabled && (
        <div className="border border-yellow-200 rounded-lg p-4 bg-yellow-50">
          <div className="flex items-start gap-2">
            <span className="text-yellow-600 text-xl mt-0.5">⚠</span>
            <div>
              <h3 className="font-semibold text-yellow-900">Review Required</h3>
              <p className="text-sm text-yellow-800 mt-1">
                This configuration requires additional review before approval. See validation
                results below.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 flex gap-4">
        <button
          onClick={() => setActiveTab("checklist")}
          className={`px-4 py-2 font-medium border-b-2 -mb-px transition ${
            activeTab === "checklist"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-600 hover:text-gray-900"
          }`}
        >
          Validation
        </button>
        <button
          onClick={() => setActiveTab("comparison")}
          className={`px-4 py-2 font-medium border-b-2 -mb-px transition ${
            activeTab === "comparison"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-600 hover:text-gray-900"
          }`}
        >
          Comparison
        </button>
        <button
          onClick={() => setActiveTab("audit")}
          className={`px-4 py-2 font-medium border-b-2 -mb-px transition ${
            activeTab === "audit"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-600 hover:text-gray-900"
          }`}
        >
          History
        </button>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg">
        {activeTab === "checklist" && (
          <ValidationChecklist validation={checklist} />
        )}
        {activeTab === "comparison" && (
          <ConfigComparison proposedVersion={{} as any} activeVersion={undefined} />
        )}
        {activeTab === "audit" && (
          <AuditTimeline configId={configId} />
        )}
      </div>

      {/* Feedback Form */}
      <div className="border border-gray-200 rounded-lg p-4">
        <label className="block font-semibold mb-2">Feedback (Optional)</label>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="Add feedback for the recruiter..."
          className="w-full px-3 py-2 border border-gray-300 rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={3}
        />
      </div>

      {/* Export Options */}
      <div className="border border-gray-200 rounded-lg p-4">
        <label className="block font-semibold mb-3">Export Configuration</label>
        <ExportButtons configId={configId} configName={checklist.name} />
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={() => setShowApproveConfirm(true)}
          disabled={isApprovalDisabled || approveLoading}
          className={`px-4 py-2 rounded font-medium transition ${
            isApprovalDisabled || approveLoading
              ? "bg-gray-300 text-gray-600 cursor-not-allowed"
              : "bg-green-600 text-white hover:bg-green-700"
          }`}
        >
          {approveLoading ? "Approving..." : "Approve"}
        </button>
        <button
          onClick={() => setShowRejectConfirm(true)}
          disabled={rejectLoading}
          className={`px-4 py-2 rounded font-medium transition ${
            rejectLoading
              ? "bg-gray-300 text-gray-600 cursor-not-allowed"
              : "bg-red-600 text-white hover:bg-red-700"
          }`}
        >
          {rejectLoading ? "Rejecting..." : "Reject"}
        </button>
      </div>

      {/* Error Messages */}
      {approveError && (
        <div className="border border-red-200 rounded-lg p-3 bg-red-50 text-sm text-red-800">
          {approveError.message}
        </div>
      )}
      {rejectError && (
        <div className="border border-red-200 rounded-lg p-3 bg-red-50 text-sm text-red-800">
          {rejectError.message}
        </div>
      )}

      {/* Confirmation Modals */}
      {showApproveConfirm && (
        <ConfirmationModal
          title="Approve Configuration?"
          message="This will activate the new configuration for all new chat sessions."
          confirmLabel="Approve"
          onConfirm={handleApprove}
          onCancel={() => setShowApproveConfirm(false)}
        />
      )}
      {showRejectConfirm && (
        <ConfirmationModal
          title="Reject Configuration?"
          message="The recruiter will need to make changes and resubmit."
          confirmLabel="Reject"
          isDanger
          onConfirm={handleReject}
          onCancel={() => setShowRejectConfirm(false)}
        />
      )}
    </div>
  );
};

interface ConfirmationModalProps {
  title: string;
  message: string;
  confirmLabel: string;
  isDanger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  title,
  message,
  confirmLabel,
  isDanger,
  onConfirm,
  onCancel,
}) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-sm mx-4">
        <h2 className="text-lg font-semibold mb-2">{title}</h2>
        <p className="text-gray-600 mb-6">{message}</p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2 rounded text-white font-medium ${
              isDanger
                ? "bg-red-600 hover:bg-red-700"
                : "bg-green-600 hover:bg-green-700"
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
