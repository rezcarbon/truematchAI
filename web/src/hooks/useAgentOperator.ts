/**
 * useAgentOperator Hook
 *
 * WebSocket-based hook for real-time agent operator dashboard updates.
 * Handles connection management, message parsing, and state synchronization.
 *
 * Usage:
 *   const {
 *     queueItems,
 *     events,
 *     isConnected,
 *     onQueueItemAction,
 *     onAgentStatusChange,
 *     onProcessingAlert,
 *   } = useAgentOperator();
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useSession } from 'next-auth/react';

/**
 * Queue item action event payload
 */
interface QueueItemActionEvent {
  type: 'queue_item_action';
  timestamp: string;
  data: {
    item_id: string;
    action: 'approved' | 'rejected' | 'reassigned' | 'held';
    user_id: string;
    status: string;
    notes?: string;
    assessment_id?: string;
  };
}

/**
 * Agent status change event payload
 */
interface AgentStatusChangeEvent {
  type: 'agent_status_change';
  timestamp: string;
  data: {
    agent_type: 'cv' | 'jd' | 'email';
    running: boolean;
    queue_size: number;
    last_error?: string;
  };
}

/**
 * Processing alert event payload
 */
interface ProcessingAlertEvent {
  type: 'processing_alert';
  timestamp: string;
  data: {
    agent_type: 'cv' | 'jd' | 'email';
    level: 'error' | 'warning' | 'info';
    message: string;
    context?: Record<string, unknown>;
  };
}

type OperatorMessage =
  | QueueItemActionEvent
  | AgentStatusChangeEvent
  | ProcessingAlertEvent;

/**
 * Queue item state for dashboard display
 */
interface QueueItem {
  id: string;
  name: string;
  type: 'cv' | 'jd' | 'assessment';
  source: string;
  created_at: string;
  awaiting_review: boolean;
  status: string;
  notes?: string;
}

/**
 * Agent status state
 */
interface AgentStatus {
  agent_type: 'cv' | 'jd' | 'email';
  running: boolean;
  queue_size: number;
  last_error?: string;
}

/**
 * Hook state interface
 */
interface UseAgentOperatorReturn {
  queueItems: QueueItem[];
  agentStatuses: Map<string, AgentStatus>;
  events: OperatorMessage[];
  isConnected: boolean;
  error: string | null;
  onQueueItemAction: (
    itemId: string,
    action: 'approved' | 'rejected' | 'reassigned' | 'held',
    notes?: string
  ) => void;
  onAgentStatusChange: (callback: (event: AgentStatusChangeEvent) => void) => () => void;
  onProcessingAlert: (callback: (event: ProcessingAlertEvent) => void) => () => void;
  clearEvents: () => void;
}

export function useAgentOperator(): UseAgentOperatorReturn {
  const { data: session } = useSession();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttemptsRef = useRef(5);

  // State management
  const [queueItems, setQueueItems] = useState<QueueItem[]>([]);
  const [agentStatuses, setAgentStatuses] = useState<Map<string, AgentStatus>>(
    new Map()
  );
  const [events, setEvents] = useState<OperatorMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Callback registries for external handlers
  const statusChangeCallbacksRef = useRef<
    Set<(event: AgentStatusChangeEvent) => void>
  >(new Set());
  const alertCallbacksRef = useRef<Set<(event: ProcessingAlertEvent) => void>>(
    new Set()
  );

  /**
   * Register a listener for agent status changes
   */
  const onAgentStatusChange = useCallback(
    (callback: (event: AgentStatusChangeEvent) => void) => {
      statusChangeCallbacksRef.current.add(callback);

      // Return unsubscribe function
      return () => {
        statusChangeCallbacksRef.current.delete(callback);
      };
    },
    []
  );

  /**
   * Register a listener for processing alerts
   */
  const onProcessingAlert = useCallback(
    (callback: (event: ProcessingAlertEvent) => void) => {
      alertCallbacksRef.current.add(callback);

      // Return unsubscribe function
      return () => {
        alertCallbacksRef.current.delete(callback);
      };
    },
    []
  );

  /**
   * Clear event history
   */
  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  /**
   * Handle incoming WebSocket messages
   */
  const handleMessage = useCallback((payload: OperatorMessage) => {
    // Add to event history
    setEvents((prev) => [payload, ...prev].slice(0, 100)); // Keep last 100 events

    switch (payload.type) {
      case 'queue_item_action': {
        const event = payload as QueueItemActionEvent;
        // Update queue item in state
        setQueueItems((prev) =>
          prev.map((item) =>
            item.id === event.data.item_id
              ? {
                  ...item,
                  status: event.data.status,
                  notes: event.data.notes,
                  awaiting_review: event.data.status === 'awaiting_review',
                }
              : item
          )
        );
        break;
      }

      case 'agent_status_change': {
        const event = payload as AgentStatusChangeEvent;
        setAgentStatuses((prev) => {
          const updated = new Map(prev);
          updated.set(event.data.agent_type, {
            agent_type: event.data.agent_type,
            running: event.data.running,
            queue_size: event.data.queue_size,
            last_error: event.data.last_error,
          });
          return updated;
        });

        // Notify subscribers
        statusChangeCallbacksRef.current.forEach((callback) => {
          callback(event);
        });
        break;
      }

      case 'processing_alert': {
        const event = payload as ProcessingAlertEvent;
        // Notify subscribers
        alertCallbacksRef.current.forEach((callback) => {
          callback(event);
        });
        break;
      }
    }
  }, []);

  /**
   * Establish WebSocket connection with exponential backoff retry
   */
  const connectWebSocket = useCallback(() => {
    if (!session?.user) return;

    const accessToken = (session as any)?.accessToken;
    if (!accessToken) {
      setError('No access token available');
      return;
    }

    try {
      const protocol = typeof window !== 'undefined' &&
        window.location.protocol === 'https:'
        ? 'wss:'
        : 'ws:';
      const url = `${protocol}//${window.location.host}/ws/operator?token=${accessToken}`;

      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('[Operator] WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as OperatorMessage;
          handleMessage(message);
        } catch (err) {
          console.error('[Operator] Failed to parse message:', err);
          setError('Failed to parse server message');
        }
      };

      ws.onerror = (event) => {
        console.error('[Operator] WebSocket error:', event);
        setError('WebSocket connection error');
      };

      ws.onclose = () => {
        console.log('[Operator] WebSocket disconnected');
        setIsConnected(false);

        // Attempt reconnect with exponential backoff
        if (reconnectAttemptsRef.current < maxReconnectAttemptsRef.current) {
          const backoffMs = Math.min(
            1000 * Math.pow(2, reconnectAttemptsRef.current),
            30000
          ); // Max 30s
          reconnectAttemptsRef.current += 1;

          console.log(
            `[Operator] Reconnecting in ${backoffMs}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttemptsRef.current})`
          );

          reconnectTimeoutRef.current = setTimeout(connectWebSocket, backoffMs);
        } else {
          setError('Max reconnection attempts reached');
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('[Operator] Failed to connect WebSocket:', err);
      setError(
        err instanceof Error ? err.message : 'Failed to connect to operator'
      );
    }
  }, [session, handleMessage]);

  /**
   * Stub handler for queue item actions (can be extended for remote triggering)
   */
  const onQueueItemAction = useCallback(
    (
      itemId: string,
      action: 'approved' | 'rejected' | 'reassigned' | 'held',
      notes?: string
    ) => {
      // This is a local state update; the actual API call is handled
      // by the component using this hook
      console.log(`[Operator] Queue item action: ${itemId} -> ${action}`, notes);
    },
    []
  );

  /**
   * Effect: Connect to WebSocket on mount
   */
  useEffect(() => {
    if (!session?.user) return;

    connectWebSocket();

    // Send ping every 30 seconds to keep connection alive
    const pingInterval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [session, connectWebSocket]);

  return {
    queueItems,
    agentStatuses,
    events,
    isConnected,
    error,
    onQueueItemAction,
    onAgentStatusChange,
    onProcessingAlert,
    clearEvents,
  };
}
