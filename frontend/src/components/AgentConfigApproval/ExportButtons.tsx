/**
 * Export buttons component - PDF, JSON, CSV exports
 */

import React, { useState } from "react";

interface ExportButtonsProps {
  configId: string;
  configName: string;
}

export const ExportButtons: React.FC<ExportButtonsProps> = ({
  configId,
  configName,
}) => {
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExportPDF = async () => {
    setExporting(true);
    setError(null);
    try {
      const response = await fetch(`/api/v1/agent-configs/${configId}/export/pdf`);
      if (!response.ok) throw new Error(`Export failed: ${response.status}`);

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${configName}_approval_checklist.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setExporting(false);
    }
  };

  const handleExportJSON = async () => {
    setExporting(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/v1/agent-configs/${configId}/export/details?format=json`
      );
      if (!response.ok) throw new Error(`Export failed: ${response.status}`);

      const data = await response.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${configName}_config.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setExporting(false);
    }
  };

  const handleExportCSV = async () => {
    setExporting(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/v1/agent-configs/${configId}/export/details?format=csv`
      );
      if (!response.ok) throw new Error(`Export failed: ${response.status}`);

      const data = await response.json();
      const blob = new Blob([data.data], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${configName}_config.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <button
          onClick={handleExportPDF}
          disabled={exporting}
          className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
          title="Export approval checklist as PDF"
        >
          {exporting ? "Exporting..." : "📄 Export PDF"}
        </button>
        <button
          onClick={handleExportJSON}
          disabled={exporting}
          className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
          title="Export configuration as JSON"
        >
          {exporting ? "Exporting..." : "{ } JSON"}
        </button>
        <button
          onClick={handleExportCSV}
          disabled={exporting}
          className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200 disabled:opacity-50"
          title="Export as CSV"
        >
          {exporting ? "Exporting..." : "📊 CSV"}
        </button>
      </div>

      {error && (
        <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
          Export error: {error}
        </div>
      )}
    </div>
  );
};
