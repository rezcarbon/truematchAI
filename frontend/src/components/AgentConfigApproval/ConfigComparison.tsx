/**
 * Side-by-side comparison of configs (proposed vs current active)
 */

import React from "react";
import { AgentConfigVersion } from "./types";

interface ConfigComparisonProps {
  proposedVersion: AgentConfigVersion;
  activeVersion?: AgentConfigVersion;
}

const DiffHighlight: React.FC<{ text: string; changed?: boolean }> = ({
  text,
  changed,
}) => {
  if (!changed) return <>{text}</>;
  return <span className="bg-yellow-100 px-0.5">{text}</span>;
};

const ToolBadge: React.FC<{ tool: string; isNew?: boolean }> = ({ tool, isNew }) => {
  const base = "inline-block px-2 py-1 rounded text-xs font-medium mr-2 mb-2";
  if (isNew) {
    return <span className={`${base} bg-green-100 text-green-800`}>+{tool}</span>;
  }
  return <span className={`${base} bg-blue-100 text-blue-800`}>{tool}</span>;
};

const RemovedToolBadge: React.FC<{ tool: string }> = ({ tool }) => {
  return (
    <span className="inline-block px-2 py-1 rounded text-xs font-medium mr-2 mb-2 bg-red-100 text-red-800 line-through">
      -{tool}
    </span>
  );
};

export const ConfigComparison: React.FC<ConfigComparisonProps> = ({
  proposedVersion,
  activeVersion,
}) => {
  const instructionsChanged =
    activeVersion && activeVersion.instructions !== proposedVersion.instructions;
  const toolsChanged =
    activeVersion &&
    JSON.stringify(activeVersion.tools_enabled) !==
      JSON.stringify(proposedVersion.tools_enabled);

  const proposedTools = new Set(proposedVersion.tools_enabled);
  const activeTools = activeVersion ? new Set(activeVersion.tools_enabled) : new Set();

  const newTools = [...proposedTools].filter((t) => !activeTools.has(t));
  const removedTools = [...activeTools].filter((t) => !proposedTools.has(t));
  const unchangedTools = [...proposedTools].filter((t) => activeTools.has(t));

  return (
    <div className="space-y-6">
      {/* Instructions Comparison */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div className="bg-gray-100 px-4 py-2 font-semibold">Instructions</div>
        <div className="grid grid-cols-2 gap-0 divide-x divide-gray-200">
          {/* Current Active */}
          <div className="p-4">
            <h4 className="font-medium text-sm text-gray-600 mb-2">Current Active</h4>
            {activeVersion ? (
              <div className="bg-gray-50 p-3 rounded text-sm whitespace-pre-wrap font-mono text-gray-700 max-h-64 overflow-y-auto">
                {activeVersion.instructions}
              </div>
            ) : (
              <div className="text-sm text-gray-500 italic">No active config</div>
            )}
          </div>

          {/* Proposed */}
          <div className="p-4">
            <h4 className="font-medium text-sm text-gray-600 mb-2">Proposed</h4>
            <div className={`p-3 rounded text-sm whitespace-pre-wrap font-mono max-h-64 overflow-y-auto ${
              instructionsChanged
                ? "bg-yellow-50 text-gray-700 border border-yellow-200"
                : "bg-gray-50 text-gray-700"
            }`}>
              {proposedVersion.instructions}
            </div>
          </div>
        </div>
      </div>

      {/* Tools Comparison */}
      <div className="border border-gray-200 rounded-lg p-4">
        <h3 className="font-semibold mb-3">Tools Configuration</h3>
        <div className="grid grid-cols-2 gap-4">
          {/* Current Active */}
          <div>
            <h4 className="font-medium text-sm text-gray-600 mb-2">Current Active</h4>
            {activeVersion ? (
              <div className="flex flex-wrap">
                {activeVersion.tools_enabled.map((tool) => (
                  <span
                    key={tool}
                    className="inline-block px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800 mr-2 mb-2"
                  >
                    {tool}
                  </span>
                ))}
              </div>
            ) : (
              <div className="text-sm text-gray-500 italic">No active config</div>
            )}
          </div>

          {/* Proposed */}
          <div>
            <h4 className="font-medium text-sm text-gray-600 mb-2">Proposed</h4>
            <div className="flex flex-wrap">
              {newTools.length > 0 && (
                <>
                  {newTools.map((tool) => (
                    <ToolBadge key={tool} tool={tool} isNew />
                  ))}
                </>
              )}
              {unchangedTools.map((tool) => (
                <ToolBadge key={tool} tool={tool} />
              ))}
              {removedTools.length > 0 && (
                <>
                  {removedTools.map((tool) => (
                    <RemovedToolBadge key={tool} tool={tool} />
                  ))}
                </>
              )}
            </div>
          </div>
        </div>

        {/* Change Summary */}
        {toolsChanged && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-600">
              {newTools.length > 0 && (
                <span className="text-green-700">
                  +{newTools.length} new tool{newTools.length !== 1 ? "s" : ""}
                </span>
              )}
              {newTools.length > 0 && removedTools.length > 0 && <span>, </span>}
              {removedTools.length > 0 && (
                <span className="text-red-700">
                  -{removedTools.length} removed tool{removedTools.length !== 1 ? "s" : ""}
                </span>
              )}
            </p>
          </div>
        )}
      </div>

      {/* Parameters Comparison */}
      <div className="border border-gray-200 rounded-lg p-4">
        <h3 className="font-semibold mb-3">Agent Parameters</h3>
        <div className="grid grid-cols-2 gap-4">
          {/* Current */}
          <div>
            <h4 className="font-medium text-sm text-gray-600 mb-2">Current Active</h4>
            {activeVersion ? (
              <div className="text-sm space-y-1 font-mono">
                {Object.entries(activeVersion.agent_parameters).map(([key, value]) => (
                  <div key={key} className="bg-gray-50 p-2 rounded">
                    <span className="text-gray-600">{key}:</span>{" "}
                    <span className="text-gray-900 font-medium">{JSON.stringify(value)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-gray-500 italic">No active config</div>
            )}
          </div>

          {/* Proposed */}
          <div>
            <h4 className="font-medium text-sm text-gray-600 mb-2">Proposed</h4>
            <div className="text-sm space-y-1 font-mono">
              {Object.entries(proposedVersion.agent_parameters).map(([key, value]) => {
                const changed =
                  activeVersion &&
                  JSON.stringify(activeVersion.agent_parameters[key]) !==
                    JSON.stringify(value);
                return (
                  <div
                    key={key}
                    className={`p-2 rounded ${changed ? "bg-yellow-50 border border-yellow-200" : "bg-gray-50"}`}
                  >
                    <span className="text-gray-600">{key}:</span>{" "}
                    <span className="text-gray-900 font-medium">{JSON.stringify(value)}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Change Reason */}
      {proposedVersion.change_reason && (
        <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
          <h3 className="font-semibold mb-2 text-blue-900">Change Reason</h3>
          <p className="text-sm text-blue-800">{proposedVersion.change_reason}</p>
        </div>
      )}
    </div>
  );
};
