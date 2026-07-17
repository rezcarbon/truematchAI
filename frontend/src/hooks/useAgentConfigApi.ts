/**
 * React hooks for agent configuration API interactions
 */

import { useState, useCallback } from "react";
import {
  AgentConfig,
  ApprovalChecklist,
  AgentConfigValidation,
  AgentConfigAudit,
  ApprovalRequest,
} from "../components/AgentConfigApproval/types";

const API_BASE = "/api/v1/agent-configs";

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Fetch single config
 */
export function useGetConfig(configId: string | null) {
  const [state, setState] = useState<UseApiState<AgentConfig>>({
    data: null,
    loading: false,
    error: null,
  });

  const fetch = useCallback(async () => {
    if (!configId) return;
    setState({ data: null, loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/${configId}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
    }
  }, [configId]);

  return { ...state, fetch };
}

/**
 * Fetch approval checklist
 */
export function useGetApprovalChecklist(configId: string | null) {
  const [state, setState] = useState<UseApiState<ApprovalChecklist>>({
    data: null,
    loading: false,
    error: null,
  });

  const fetch = useCallback(async () => {
    if (!configId) return;
    setState({ data: null, loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/${configId}/approval-checklist`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
    }
  }, [configId]);

  return { ...state, fetch };
}

/**
 * Fetch validation results
 */
export function useValidateConfig(configId: string | null) {
  const [state, setState] = useState<UseApiState<AgentConfigValidation>>({
    data: null,
    loading: false,
    error: null,
  });

  const fetch = useCallback(async () => {
    if (!configId) return;
    setState({ data: null, loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/${configId}/validate`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
    }
  }, [configId]);

  return { ...state, fetch };
}

/**
 * Fetch audit logs
 */
export function useGetAuditLogs(configId: string | null) {
  const [state, setState] = useState<UseApiState<AgentConfigAudit[]>>({
    data: null,
    loading: false,
    error: null,
  });

  const fetch = useCallback(async () => {
    if (!configId) return;
    setState({ data: null, loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/${configId}/audit`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
    }
  }, [configId]);

  return { ...state, fetch };
}

/**
 * Approve config
 */
export function useApproveConfig() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const approve = useCallback(
    async (configId: string, feedback?: string) => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE}/${configId}/approve`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ feedback }),
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        const data = await response.json();
        setLoading(false);
        return data;
      } catch (err) {
        const error = err as Error;
        setError(error);
        setLoading(false);
        throw error;
      }
    },
    []
  );

  return { approve, loading, error };
}

/**
 * Reject config
 */
export function useRejectConfig() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const reject = useCallback(
    async (configId: string, feedback: string) => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE}/${configId}/reject`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ feedback }),
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        const data = await response.json();
        setLoading(false);
        return data;
      } catch (err) {
        const error = err as Error;
        setError(error);
        setLoading(false);
        throw error;
      }
    },
    []
  );

  return { reject, loading, error };
}

/**
 * Activate config
 */
export function useActivateConfig() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const activate = useCallback(async (configId: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/${configId}/activate`, {
        method: "POST",
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
      const data = await response.json();
      setLoading(false);
      return data;
    } catch (err) {
      const error = err as Error;
      setError(error);
      setLoading(false);
      throw error;
    }
  }, []);

  return { activate, loading, error };
}
