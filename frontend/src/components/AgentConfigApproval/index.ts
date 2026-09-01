/**
 * Agent Configuration Approval UI Components
 *
 * Complete admin dashboard for reviewing and approving agent configurations
 * before they go live.
 *
 * Usage:
 * ```tsx
 * import { ApprovalDashboard } from '@/components/AgentConfigApproval'
 *
 * export default function AdminPage() {
 *   return <ApprovalDashboard />
 * }
 * ```
 */

export { ApprovalDashboard } from "./ApprovalDashboard";
export { ApprovalDetailPage } from "./ApprovalDetailPage";
export { ValidationChecklist } from "./ValidationChecklist";
export { ConfigComparison } from "./ConfigComparison";
export { AuditTimeline } from "./AuditTimeline";
export { ExportButtons } from "./ExportButtons";
export { DashboardWithBatchFeatures } from "./DashboardWithBatch";

// Types
export type {
  AgentConfig,
  AgentConfigVersion,
  ValidationCheckItem,
  AgentConfigValidation,
  ApprovalChecklist,
  AgentConfigAudit,
  ApprovalRequest,
  PendingApprovalItem,
} from "./types";
