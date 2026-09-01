/**
 * Type definitions for agent configuration approval UI
 */

export interface AgentConfig {
  id: string;
  company_id: string;
  agent_type: string;
  role: string;
  name: string;
  description?: string;
  status: "draft" | "pending_approval" | "approved" | "active" | "deprecated";
  version_number: number;
  is_default: boolean;
  created_at: string;
  approved_at?: string;
}

export interface AgentConfigVersion {
  id: string;
  config_id: string;
  version_number: number;
  status: string;
  instructions: string;
  tools_enabled: string[];
  tool_parameters: Record<string, any>;
  agent_parameters: Record<string, any>;
  change_reason?: string;
  submitted_at?: string;
  approved_at?: string;
  activated_at?: string;
}

export interface ValidationCheckItem {
  item: string;
  status: "passed" | "failed" | "warning" | "missing" | "incomplete";
  details: string;
}

export interface AgentConfigValidation {
  config_id: string;
  version_number: number;
  validation: {
    safety_passed: boolean;
    fairness_score: number;
    warnings: string[];
    errors: string[];
  };
  version_checks: {
    has_instructions: boolean;
    has_tools: boolean;
    change_documented: boolean;
    submitted_properly: boolean;
  };
  approval_items: ValidationCheckItem[];
  recommendation: "approve" | "review_required";
}

export interface ApprovalChecklist {
  config_id: string;
  version_number: number;
  agent_type: string;
  role: string;
  created_by: string;
  submitted_at?: string;
  validation: {
    safety_passed: boolean;
    fairness_score: number;
    warnings: string[];
    errors: string[];
  };
  version_checks: Record<string, boolean>;
  approval_items: ValidationCheckItem[];
  recommendation: string;
}

export interface AgentConfigAudit {
  id: string;
  action: string;
  actor_id?: string;
  actor_role?: string;
  reason?: string;
  changes: Record<string, any>;
  created_at: string;
}

export interface ApprovalRequest {
  feedback?: string;
}

export interface PendingApprovalItem {
  config: AgentConfig;
  validation: AgentConfigValidation;
  submitted_at: string;
  submitted_by: string;
}
