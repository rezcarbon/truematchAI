/**
 * Audit timeline showing all changes to a configuration
 */

import React, { useEffect } from "react";
import { useGetAuditLogs } from "../../hooks/useAgentConfigApi";
import { AgentConfigAudit } from "./types";

interface AuditTimelineProps {
  configId: string;
}

const ActionIcon: React.FC<{ action: string }> = ({ action }) => {
  switch (action) {
    case "created":
      return <span className="text-green-600 text-xl">✓</span>;
    case "modified":
      return <span className="text-blue-600 text-xl">✎</span>;
    case "submitted":
      return <span className="text-purple-600 text-xl">➤</span>;
    case "approved":
      return <span className="text-green-600 text-xl">✓</span>;
    case "rejected":
      return <span className="text-red-600 text-xl">✗</span>;
    case "activated":
      return <span className="text-blue-600 text-xl">▶</span>;
    case "deprecated":
      return <span className="text-gray-600 text-xl">◯</span>;
    default:
      return <span className="text-gray-400 text-xl">•</span>;
  }
};

const ActionLabel: React.FC<{ action: string }> = ({ action }) => {
  const labels: Record<string, string> = {
    created: "Created",
    modified: "Modified",
    submitted: "Submitted for approval",
    approved: "Approved",
    rejected: "Rejected",
    activated: "Activated",
    deprecated: "Deprecated",
  };
  return <span className="font-medium">{labels[action] || action}</span>;
};

const ActionColor: React.FC<{ action: string }> = ({ action }) => {
  switch (action) {
    case "created":
    case "approved":
      return <div className="w-1 h-1 bg-green-600 rounded-full" />;
    case "modified":
    case "activated":
      return <div className="w-1 h-1 bg-blue-600 rounded-full" />;
    case "submitted":
      return <div className="w-1 h-1 bg-purple-600 rounded-full" />;
    case "rejected":
    case "deprecated":
      return <div className="w-1 h-1 bg-red-600 rounded-full" />;
    default:
      return <div className="w-1 h-1 bg-gray-400 rounded-full" />;
  }
};

export const AuditTimeline: React.FC<AuditTimelineProps> = ({ configId }) => {
  const { data: logs, loading, error, fetch } = useGetAuditLogs(configId);

  useEffect(() => {
    fetch();
  }, [configId, fetch]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-gray-600">Loading audit history...</div>
      </div>
    );
  }

  if (error || !logs) {
    return (
      <div className="border border-red-200 rounded-lg p-4 bg-red-50 text-sm text-red-800">
        Failed to load audit logs: {error?.message}
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">No audit logs found</div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200" />

        {/* Timeline items */}
        <div className="space-y-6">
          {logs.map((log, i) => (
            <div key={log.id} className="relative pl-16">
              {/* Timeline dot */}
              <div className="absolute left-0 top-1 w-4 h-4 bg-white border-2 border-gray-300 rounded-full flex items-center justify-center">
                <ActionColor action={log.action} />
              </div>

              {/* Content */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <ActionIcon action={log.action} />
                    <ActionLabel action={log.action} />
                  </div>
                  <time className="text-sm text-gray-600">
                    {new Date(log.created_at).toLocaleString()}
                  </time>
                </div>

                {/* Actor Info */}
                {log.actor_id && (
                  <div className="text-sm text-gray-600 mb-2">
                    by <span className="font-medium">{log.actor_role || "user"}</span>
                  </div>
                )}

                {/* Reason */}
                {log.reason && (
                  <div className="text-sm mb-3">
                    <span className="text-gray-600">Reason: </span>
                    <span className="text-gray-900">{log.reason}</span>
                  </div>
                )}

                {/* Changes */}
                {log.changes && Object.keys(log.changes).length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="text-sm font-medium text-gray-700 mb-2">Changes:</div>
                    <div className="space-y-2">
                      {Object.entries(log.changes).map(([key, value]: [string, any]) => (
                        <div key={key} className="text-sm">
                          <span className="text-gray-600">{key}:</span>
                          {value && value.before !== undefined && (
                            <>
                              <div className="ml-4 mt-1">
                                <div className="text-red-700">
                                  <span className="text-red-600">-</span> {formatValue(value.before)}
                                </div>
                                <div className="text-green-700">
                                  <span className="text-green-600">+</span> {formatValue(value.after)}
                                </div>
                              </div>
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

function formatValue(value: any): string {
  if (typeof value === "string" && value.length > 100) {
    return value.substring(0, 100) + "...";
  }
  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
}
