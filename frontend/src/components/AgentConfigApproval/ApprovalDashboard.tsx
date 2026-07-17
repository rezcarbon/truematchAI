/**
 * Admin dashboard for reviewing pending agent configuration approvals
 */

import React, { useState, useEffect } from "react";
import { ApprovalDetailPage } from "./ApprovalDetailPage";

// Mock data - in production, fetch from API
const MOCK_PENDING_APPROVALS = [
  {
    id: "550e8400-e29b-41d4-a716-446655440000",
    config: {
      id: "550e8400-e29b-41d4-a716-446655440000",
      name: "Cultural Fit Screener",
      agent_type: "recruiter",
      role: "recruiter",
      version_number: 2,
      status: "pending_approval",
      description: "Enhanced screening focused on cultural alignment",
      is_default: false,
      created_at: "2026-07-16T10:00:00Z",
      company_id: "550e8400-e29b-41d4-a716-446655440001",
    },
    fairness_score: 85,
    recommendation: "approve",
    submitted_at: "2026-07-16T14:00:00Z",
    submitted_by: "john.recruiter@company.com",
  },
  {
    id: "550e8400-e29b-41d4-a716-446655440001",
    config: {
      id: "550e8400-e29b-41d4-a716-446655440001",
      name: "Technical Assessment Designer",
      agent_type: "recruiter",
      role: "recruiter",
      version_number: 1,
      status: "pending_approval",
      description: "Designs technical assessments for engineering roles",
      is_default: false,
      created_at: "2026-07-16T12:00:00Z",
      company_id: "550e8400-e29b-41d4-a716-446655440001",
    },
    fairness_score: 65,
    recommendation: "review_required",
    submitted_at: "2026-07-16T13:30:00Z",
    submitted_by: "jane.recruiter@company.com",
  },
];

interface PendingApproval {
  id: string;
  config: any;
  fairness_score: number;
  recommendation: string;
  submitted_at: string;
  submitted_by: string;
}

export const ApprovalDashboard: React.FC = () => {
  const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null);
  const [pendingApprovals, setPendingApprovals] = useState<PendingApproval[]>(MOCK_PENDING_APPROVALS);
  const [searchText, setSearchText] = useState("");
  const [filterStatus, setFilterStatus] = useState<"all" | "needs_review" | "ready">("all");

  // Filter approvals based on search and status
  const filteredApprovals = pendingApprovals.filter((approval) => {
    const matchesSearch =
      approval.config.name.toLowerCase().includes(searchText.toLowerCase()) ||
      approval.config.agent_type.toLowerCase().includes(searchText.toLowerCase());

    const matchesStatus =
      filterStatus === "all" ||
      (filterStatus === "needs_review" && approval.recommendation === "review_required") ||
      (filterStatus === "ready" && approval.recommendation === "approve");

    return matchesSearch && matchesStatus;
  });

  const handleApprovalComplete = () => {
    // Remove the approved config from the list
    setPendingApprovals(
      pendingApprovals.filter((a) => a.id !== selectedConfigId)
    );
    setSelectedConfigId(null);
  };

  if (selectedConfigId) {
    return (
      <div>
        <button
          onClick={() => setSelectedConfigId(null)}
          className="mb-4 px-3 py-1 text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
        >
          ← Back to Dashboard
        </button>
        <ApprovalDetailPage
          configId={selectedConfigId}
          onApprovalComplete={handleApprovalComplete}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Agent Configuration Approvals</h1>
        <p className="text-gray-600 mt-1">
          Review and approve pending agent configurations
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Total Pending</div>
          <div className="text-3xl font-bold mt-1">{pendingApprovals.length}</div>
        </div>
        <div className="border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Needs Review</div>
          <div className="text-3xl font-bold text-yellow-600 mt-1">
            {pendingApprovals.filter((a) => a.recommendation === "review_required").length}
          </div>
        </div>
        <div className="border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Ready to Approve</div>
          <div className="text-3xl font-bold text-green-600 mt-1">
            {pendingApprovals.filter((a) => a.recommendation === "approve").length}
          </div>
        </div>
      </div>

      {/* Search & Filter */}
      <div className="flex gap-3">
        <input
          type="text"
          placeholder="Search by name or agent type..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          className="flex-1 px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as any)}
          className="px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All</option>
          <option value="ready">Ready to Approve</option>
          <option value="needs_review">Needs Review</option>
        </select>
      </div>

      {/* Pending Approvals List */}
      {filteredApprovals.length === 0 ? (
        <div className="border border-gray-200 rounded-lg p-8 text-center text-gray-500">
          {pendingApprovals.length === 0
            ? "No pending approvals"
            : "No approvals match your search"}
        </div>
      ) : (
        <div className="space-y-3">
          {filteredApprovals.map((approval) => (
            <div
              key={approval.id}
              onClick={() => setSelectedConfigId(approval.id)}
              className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:bg-blue-50 cursor-pointer transition"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">
                    {approval.config.name}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {approval.config.agent_type} • v{approval.config.version_number}
                  </p>
                </div>

                {/* Status Badge */}
                <div className="flex items-center gap-2">
                  {approval.recommendation === "approve" ? (
                    <span className="inline-block px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                      ✓ Ready
                    </span>
                  ) : (
                    <span className="inline-block px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                      ⚠ Review
                    </span>
                  )}
                </div>
              </div>

              {/* Fairness Score */}
              <div className="flex items-center gap-3 mb-3">
                <div className="flex-1 max-w-xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-gray-600">
                      Fairness
                    </span>
                    <span className="text-sm font-semibold">
                      {approval.fairness_score}/100
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition ${
                        approval.fairness_score >= 70
                          ? "bg-green-600"
                          : "bg-yellow-600"
                      }`}
                      style={{ width: `${approval.fairness_score}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Description */}
              {approval.config.description && (
                <p className="text-sm text-gray-600 mb-3">
                  {approval.config.description}
                </p>
              )}

              {/* Meta */}
              <div className="flex items-center justify-between text-xs text-gray-500">
                <div>
                  Submitted by {approval.submitted_by}
                </div>
                <div>
                  {new Date(approval.submitted_at).toLocaleDateString()}{" "}
                  {new Date(approval.submitted_at).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
