/**
 * Enhanced approval dashboard with batch operations and export
 */

import React, { useState } from "react";
import { ApprovalDashboard } from "./ApprovalDashboard";

interface BatchSelection {
  [configId: string]: boolean;
}

export const DashboardWithBatchFeatures: React.FC = () => {
  const [batchMode, setBatchMode] = useState(false);
  const [selectedConfigs, setSelectedConfigs] = useState<BatchSelection>({});
  const [showBatchConfirm, setShowBatchConfirm] = useState(false);
  const [batchAction, setBatchAction] = useState<"approve" | "reject" | null>(null);
  const [batchFeedback, setBatchFeedback] = useState("");

  const selectedCount = Object.values(selectedConfigs).filter(Boolean).length;

  const handleToggleAll = (allConfigs: string[]) => {
    if (selectedCount === allConfigs.length) {
      setSelectedConfigs({});
    } else {
      const newSelection: BatchSelection = {};
      allConfigs.forEach((id) => {
        newSelection[id] = true;
      });
      setSelectedConfigs(newSelection);
    }
  };

  const handleBatchApprove = async () => {
    const configIds = Object.keys(selectedConfigs).filter((id) => selectedConfigs[id]);

    try {
      const response = await fetch("/api/v1/agent-configs/batch/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          config_ids: configIds,
          feedback: batchFeedback,
        }),
      });

      if (!response.ok) throw new Error("Batch approval failed");

      // Success - clear selections
      setSelectedConfigs({});
      setShowBatchConfirm(false);
      setBatchMode(false);
      setBatchFeedback("");

      // Refresh list (would refetch in real app)
      window.location.reload();
    } catch (error) {
      alert(`Error: ${error}`);
    }
  };

  const handleBatchReject = async () => {
    const configIds = Object.keys(selectedConfigs).filter((id) => selectedConfigs[id]);

    if (!batchFeedback.trim()) {
      alert("Please provide feedback for rejection");
      return;
    }

    try {
      const response = await fetch("/api/v1/agent-configs/batch/reject", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          config_ids: configIds,
          feedback: batchFeedback,
        }),
      });

      if (!response.ok) throw new Error("Batch rejection failed");

      // Success - clear selections
      setSelectedConfigs({});
      setShowBatchConfirm(false);
      setBatchMode(false);
      setBatchFeedback("");

      // Refresh list
      window.location.reload();
    } catch (error) {
      alert(`Error: ${error}`);
    }
  };

  return (
    <div className="space-y-4">
      {/* Batch Mode Toolbar */}
      {batchMode && selectedCount > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-blue-900">
                {selectedCount} configuration{selectedCount !== 1 ? "s" : ""} selected
              </h3>
              <p className="text-sm text-blue-700 mt-1">
                Choose to approve all or reject all with the same feedback
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setBatchAction("approve");
                  setShowBatchConfirm(true);
                }}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                Approve All
              </button>
              <button
                onClick={() => {
                  setBatchAction("reject");
                  setShowBatchConfirm(true);
                }}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Reject All
              </button>
              <button
                onClick={() => setBatchMode(false)}
                className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toggle Batch Mode */}
      {!batchMode && (
        <button
          onClick={() => setBatchMode(true)}
          className="px-3 py-1 text-sm text-blue-600 hover:text-blue-800 border border-blue-200 rounded"
        >
          ☑ Enable Batch Mode
        </button>
      )}

      {/* Main Dashboard */}
      {/* In production, would pass batchMode and handlers to ApprovalDashboard */}
      <ApprovalDashboard />

      {/* Batch Confirmation Modal */}
      {showBatchConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm mx-4">
            <h2 className="text-lg font-semibold mb-4">
              {batchAction === "approve"
                ? "Approve All Configurations?"
                : "Reject All Configurations?"}
            </h2>

            {batchAction === "reject" && (
              <>
                <label className="block text-sm font-medium mb-2">Feedback</label>
                <textarea
                  value={batchFeedback}
                  onChange={(e) => setBatchFeedback(e.target.value)}
                  placeholder="Provide feedback for all configurations..."
                  className="w-full px-3 py-2 border border-gray-300 rounded mb-4 resize-none"
                  rows={3}
                />
              </>
            )}

            {batchAction === "approve" && (
              <>
                <label className="block text-sm font-medium mb-2">Optional Feedback</label>
                <textarea
                  value={batchFeedback}
                  onChange={(e) => setBatchFeedback(e.target.value)}
                  placeholder="Add feedback (optional)..."
                  className="w-full px-3 py-2 border border-gray-300 rounded mb-4 resize-none"
                  rows={2}
                />
              </>
            )}

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowBatchConfirm(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded"
              >
                Cancel
              </button>
              <button
                onClick={
                  batchAction === "approve" ? handleBatchApprove : handleBatchReject
                }
                className={`px-4 py-2 rounded text-white font-medium ${
                  batchAction === "approve"
                    ? "bg-green-600 hover:bg-green-700"
                    : "bg-red-600 hover:bg-red-700"
                }`}
              >
                {batchAction === "approve" ? "Approve All" : "Reject All"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
