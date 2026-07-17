/**
 * Validation checklist component showing governance checks
 */

import React from "react";
import { ValidationCheckItem, AgentConfigValidation } from "./types";

interface ValidationChecklistProps {
  validation: AgentConfigValidation;
}

const StatusIcon: React.FC<{ status: string }> = ({ status }) => {
  switch (status) {
    case "passed":
      return <span className="text-green-600 text-xl">✓</span>;
    case "failed":
      return <span className="text-red-600 text-xl">✗</span>;
    case "warning":
      return <span className="text-yellow-600 text-xl">⚠</span>;
    case "missing":
    case "incomplete":
      return <span className="text-gray-400 text-xl">◯</span>;
    default:
      return null;
  }
};

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const baseClass = "inline-block px-2 py-1 text-xs font-semibold rounded";
  switch (status) {
    case "passed":
      return <span className={`${baseClass} bg-green-100 text-green-800`}>Passed</span>;
    case "failed":
      return <span className={`${baseClass} bg-red-100 text-red-800`}>Failed</span>;
    case "warning":
      return <span className={`${baseClass} bg-yellow-100 text-yellow-800`}>Warning</span>;
    case "missing":
    case "incomplete":
      return <span className={`${baseClass} bg-gray-100 text-gray-800`}>Incomplete</span>;
    default:
      return null;
  }
};

export const ValidationChecklist: React.FC<ValidationChecklistProps> = ({ validation }) => {
  const { validation: val, version_checks, approval_items, recommendation } = validation;

  return (
    <div className="space-y-6">
      {/* Safety Summary */}
      <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
        <h3 className="text-lg font-semibold mb-4">Governance Validation</h3>

        <div className="grid grid-cols-3 gap-4 mb-4">
          {/* Safety Status */}
          <div className="bg-white p-3 rounded border border-gray-200">
            <div className="text-sm text-gray-600 mb-1">Safety Check</div>
            <div className="flex items-center gap-2">
              <StatusIcon status={val.safety_passed ? "passed" : "failed"} />
              <span className="font-medium">
                {val.safety_passed ? "Passed" : "Failed"}
              </span>
            </div>
          </div>

          {/* Fairness Score */}
          <div className="bg-white p-3 rounded border border-gray-200">
            <div className="text-sm text-gray-600 mb-1">Fairness Score</div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{val.fairness_score}</span>
              <span className="text-sm text-gray-600">/100</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
              <div
                className={`h-2 rounded-full ${
                  val.fairness_score >= 70 ? "bg-green-600" : "bg-yellow-600"
                }`}
                style={{ width: `${val.fairness_score}%` }}
              />
            </div>
          </div>

          {/* Recommendation */}
          <div className="bg-white p-3 rounded border border-gray-200">
            <div className="text-sm text-gray-600 mb-1">Recommendation</div>
            <div className="font-medium">
              {recommendation === "approve" ? (
                <span className="text-green-600">✓ Approve</span>
              ) : (
                <span className="text-yellow-600">⚠ Review Required</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Errors */}
      {val.errors.length > 0 && (
        <div className="border border-red-200 rounded-lg p-4 bg-red-50">
          <h4 className="font-semibold text-red-900 mb-2">Errors</h4>
          <ul className="space-y-1">
            {val.errors.map((error, i) => (
              <li key={i} className="text-sm text-red-800 flex items-start gap-2">
                <span className="text-red-600 font-bold mt-0.5">•</span>
                <span>{error}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Warnings */}
      {val.warnings.length > 0 && (
        <div className="border border-yellow-200 rounded-lg p-4 bg-yellow-50">
          <h4 className="font-semibold text-yellow-900 mb-2">Warnings</h4>
          <ul className="space-y-1">
            {val.warnings.map((warning, i) => (
              <li key={i} className="text-sm text-yellow-800 flex items-start gap-2">
                <span className="text-yellow-600 font-bold mt-0.5">⚠</span>
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Approval Items Checklist */}
      <div className="border border-gray-200 rounded-lg p-4">
        <h4 className="font-semibold mb-3">Approval Checklist</h4>
        <div className="space-y-3">
          {approval_items.map((item, i) => (
            <div key={i} className="flex items-start gap-3 pb-3 border-b border-gray-100 last:border-b-0">
              <div className="mt-0.5">
                <StatusIcon status={item.status} />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium">{item.item}</span>
                  <StatusBadge status={item.status} />
                </div>
                <p className="text-sm text-gray-600">{item.details}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Version Checks */}
      <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
        <h4 className="font-semibold mb-3">Configuration Completeness</h4>
        <div className="grid grid-cols-2 gap-3">
          {Object.entries(version_checks).map(([key, value]) => (
            <div key={key} className="flex items-center gap-2">
              <span className={value ? "text-green-600 text-lg" : "text-gray-400 text-lg"}>
                {value ? "✓" : "◯"}
              </span>
              <span className="text-sm">
                {key
                  .replace(/_/g, " ")
                  .split(" ")
                  .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                  .join(" ")}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
