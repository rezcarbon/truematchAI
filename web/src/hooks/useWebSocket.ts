import { useEffect, useCallback, useRef } from 'react';
import { useSession } from 'next-auth/react';
import type { WebSocketMessage, WebSocketMessageHandler, UsePipelineWebSocketReturn } from '@/types';
import type { Session } from 'next-auth';

/**
 * Hook for WebSocket real-time pipeline updates
 * Handles: candidate stage changes, interview notifications, presence
 */
export function usePipelineWebSocket(
  positionId: string,
  onMessage: WebSocketMessageHandler,
  enabled: boolean = true
): UsePipelineWebSocketReturn {
  const { data: session } = useSession();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (!enabled || !positionId) return;

    const accessToken = (session as Session | null)?.accessToken;
    if (!accessToken) return;

    const connectWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const url = `${protocol}//${window.location.host}/api/proxy/ws/pipeline/${positionId}?token=${accessToken}`;

      try {
        const ws = new WebSocket(url);

        ws.onopen = () => {
          console.log('WebSocket connected to pipeline');
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            onMessage(message);
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
          console.log('WebSocket disconnected, reconnecting...');
          // Attempt reconnect after 3 seconds
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
        };

        wsRef.current = ws;
      } catch (err) {
        console.error('Failed to connect WebSocket:', err);
      }
    };

    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [enabled, (session as Session | null)?.accessToken, positionId, onMessage]);

  const send = useCallback((message: WebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  return { send, isConnected: wsRef.current?.readyState === WebSocket.OPEN };
}

/**
 * Hook for WebSocket notifications
 * Handles: interview reminders, scorecard requests, system alerts
 */
export function useNotificationWebSocket(
  onNotification: WebSocketMessageHandler,
  enabled: boolean = true
): { isConnected: boolean } {
  const { data: session } = useSession();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    const accessToken = (session as Session | null)?.accessToken;
    if (!enabled || !accessToken) return;

    const connectWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const url = `${protocol}//${window.location.host}/api/proxy/ws/notifications?token=${accessToken}`;

      try {
        const ws = new WebSocket(url);

        ws.onopen = () => {
          console.log('WebSocket connected to notifications');
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            onNotification(message);

            // Send acknowledgment
            if (message.notification_id) {
              ws.send(JSON.stringify({ type: 'ack', notification_id: message.notification_id }));
            }
          } catch (err) {
            console.error('Failed to parse notification:', err);
          }
        };

        ws.onerror = (error) => {
          console.error('Notification WebSocket error:', error);
        };

        ws.onclose = () => {
          console.log('Notification WebSocket disconnected, reconnecting...');
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
        };

        wsRef.current = ws;
      } catch (err) {
        console.error('Failed to connect notification WebSocket:', err);
      }
    };

    connectWebSocket();

    // Ping every 30 seconds to keep connection alive
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
  }, [enabled, (session as Session | null)?.accessToken, onNotification]);

  return { isConnected: wsRef.current?.readyState === WebSocket.OPEN };
}
