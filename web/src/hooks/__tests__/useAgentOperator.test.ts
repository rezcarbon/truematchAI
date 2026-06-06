import { renderHook, waitFor } from '@testing-library/react'
import { useAgentOperator } from '../useAgentOperator'

// Mock next-auth/react
jest.mock('next-auth/react', () => ({
  useSession() {
    return {
      data: {
        user: {
          id: 'test-user-id',
          email: 'test@example.com',
          name: 'Test User',
        },
        accessToken: 'test-access-token',
      },
      status: 'authenticated',
    }
  },
}))

describe('useAgentOperator Hook', () => {
  let mockWebSocket: any

  beforeEach(() => {
    jest.clearAllMocks()

    // Create a mock WebSocket that we can control
    mockWebSocket = {
      onopen: null,
      onmessage: null,
      onerror: null,
      onclose: null,
      readyState: 1, // OPEN
      send: jest.fn(),
      close: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    }

    global.WebSocket = jest.fn().mockImplementation(() => {
      // Simulate connection after a microtask
      setImmediate(() => {
        if (mockWebSocket.onopen) {
          mockWebSocket.onopen()
        }
      })
      return mockWebSocket
    }) as any
  })

  it('initializes with empty state', () => {
    const { result } = renderHook(() => useAgentOperator())

    expect(result.current.queueItems).toEqual([])
    expect(result.current.events).toEqual([])
    expect(result.current.error).toBeNull()
  })

  it('connects to WebSocket on mount', async () => {
    const { result } = renderHook(() => useAgentOperator())

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    expect(global.WebSocket).toHaveBeenCalled()
  })

  it('handles queue_item_action events', async () => {
    const { result } = renderHook(() => useAgentOperator())

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    const mockEvent = {
      type: 'queue_item_action',
      timestamp: new Date().toISOString(),
      data: {
        item_id: '1',
        action: 'approved',
        user_id: 'user-1',
        status: 'completed',
        notes: 'Test approval',
      },
    }

    // Simulate WebSocket message
    if (mockWebSocket.onmessage) {
      mockWebSocket.onmessage({
        data: JSON.stringify(mockEvent),
      })
    }

    await waitFor(() => {
      expect(result.current.events.length).toBeGreaterThan(0)
      expect(result.current.events[0].type).toBe('queue_item_action')
    })
  })

  it('handles agent_status_change events', async () => {
    const { result } = renderHook(() => useAgentOperator())

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    const mockEvent = {
      type: 'agent_status_change',
      timestamp: new Date().toISOString(),
      data: {
        agent_type: 'cv',
        running: true,
        queue_size: 5,
      },
    }

    if (mockWebSocket.onmessage) {
      mockWebSocket.onmessage({
        data: JSON.stringify(mockEvent),
      })
    }

    await waitFor(() => {
      expect(result.current.agentStatuses.has('cv')).toBe(true)
      const cvStatus = result.current.agentStatuses.get('cv')
      expect(cvStatus?.running).toBe(true)
      expect(cvStatus?.queue_size).toBe(5)
    })
  })

  it('handles processing_alert events', async () => {
    const { result } = renderHook(() => useAgentOperator())

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    const mockEvent = {
      type: 'processing_alert',
      timestamp: new Date().toISOString(),
      data: {
        agent_type: 'jd',
        level: 'error',
        message: 'Processing failed',
      },
    }

    if (mockWebSocket.onmessage) {
      mockWebSocket.onmessage({
        data: JSON.stringify(mockEvent),
      })
    }

    await waitFor(() => {
      expect(result.current.events.length).toBeGreaterThan(0)
      expect(result.current.events[0].type).toBe('processing_alert')
    })
  })

  it('updates queue items from queue_item_action events', async () => {
    const { result } = renderHook(() => useAgentOperator())

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    // First, add a queue item
    const addEvent = {
      type: 'queue_item_action',
      timestamp: new Date().toISOString(),
      data: {
        item_id: '1',
        action: 'approved',
        user_id: 'user-1',
        status: 'approved',
      },
    }

    if (mockWebSocket.onmessage) {
      mockWebSocket.onmessage({
        data: JSON.stringify(addEvent),
      })
    }

    // Queue items state might be updated based on implementation
    // This test verifies the event is captured
    await waitFor(() => {
      expect(result.current.events.length).toBeGreaterThan(0)
    })
  })

  it('clears events with clearEvents function', async () => {
    const { result } = renderHook(() => useAgentOperator())

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    const mockEvent = {
      type: 'queue_item_action',
      timestamp: new Date().toISOString(),
      data: {
        item_id: '1',
        action: 'approved',
        user_id: 'user-1',
        status: 'completed',
      },
    }

    if (mockWebSocket.onmessage) {
      mockWebSocket.onmessage({
        data: JSON.stringify(mockEvent),
      })
    }

    await waitFor(() => {
      expect(result.current.events.length).toBeGreaterThan(0)
    })

    result.current.clearEvents()

    expect(result.current.events).toEqual([])
  })

  it('registers and calls status change callbacks', async () => {
    const { result } = renderHook(() => useAgentOperator())

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    const mockCallback = jest.fn()

    const unsubscribe = result.current.onAgentStatusChange(mockCallback)

    const mockEvent = {
      type: 'agent_status_change',
      timestamp: new Date().toISOString(),
      data: {
        agent_type: 'cv',
        running: true,
        queue_size: 5,
      },
    }

    if (mockWebSocket.onmessage) {
      mockWebSocket.onmessage({
        data: JSON.stringify(mockEvent),
      })
    }

    await waitFor(() => {
      expect(mockCallback).toHaveBeenCalledWith(mockEvent)
    })

    unsubscribe()
  })

  it('registers and calls processing alert callbacks', async () => {
    const { result } = renderHook(() => useAgentOperator())

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    const mockCallback = jest.fn()

    const unsubscribe = result.current.onProcessingAlert(mockCallback)

    const mockEvent = {
      type: 'processing_alert',
      timestamp: new Date().toISOString(),
      data: {
        agent_type: 'email',
        level: 'warning',
        message: 'High queue size',
      },
    }

    if (mockWebSocket.onmessage) {
      mockWebSocket.onmessage({
        data: JSON.stringify(mockEvent),
      })
    }

    await waitFor(() => {
      expect(mockCallback).toHaveBeenCalledWith(mockEvent)
    })

    unsubscribe()
  })

  it('handles WebSocket errors', async () => {
    const { result } = renderHook(() => useAgentOperator())

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    const errorEvent = new Event('error')
    if (mockWebSocket.onerror) {
      mockWebSocket.onerror(errorEvent)
    }

    await waitFor(() => {
      expect(result.current.error).not.toBeNull()
    })
  })

  it('handles malformed JSON messages', async () => {
    const { result } = renderHook(() => useAgentOperator())

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    if (mockWebSocket.onmessage) {
      mockWebSocket.onmessage({
        data: 'invalid json',
      })
    }

    await waitFor(() => {
      expect(result.current.error).not.toBeNull()
    })
  })

  it('keeps last 100 events only', async () => {
    const { result } = renderHook(() => useAgentOperator())

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    // Send 110 events
    for (let i = 0; i < 110; i++) {
      const mockEvent = {
        type: 'processing_alert',
        timestamp: new Date().toISOString(),
        data: {
          agent_type: 'cv',
          level: 'info',
          message: `Event ${i}`,
        },
      }

      if (mockWebSocket.onmessage) {
        mockWebSocket.onmessage({
          data: JSON.stringify(mockEvent),
        })
      }
    }

    await waitFor(() => {
      expect(result.current.events.length).toBeLessThanOrEqual(100)
    })
  })

  it('calls onQueueItemAction with correct parameters', () => {
    const { result } = renderHook(() => useAgentOperator())

    const consoleSpy = jest.spyOn(console, 'log').mockImplementation()

    result.current.onQueueItemAction('item-1', 'approved', 'Good fit')

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('item-1'),
      expect.stringContaining('approved')
    )

    consoleSpy.mockRestore()
  })

  it('closes WebSocket on unmount', async () => {
    const { unmount } = renderHook(() => useAgentOperator())

    await waitFor(() => {
      // Wait for connection
    })

    unmount()

    await waitFor(() => {
      expect(mockWebSocket.close).toHaveBeenCalled()
    })
  })

  it('handles disconnection and sets isConnected to false', async () => {
    const { result } = renderHook(() => useAgentOperator())

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    mockWebSocket.readyState = 3 // CLOSED
    if (mockWebSocket.onclose) {
      mockWebSocket.onclose()
    }

    await waitFor(() => {
      expect(result.current.isConnected).toBe(false)
    })
  })

  it('maintains agent statuses in a Map', async () => {
    const { result } = renderHook(() => useAgentOperator())

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    const events = [
      {
        type: 'agent_status_change',
        timestamp: new Date().toISOString(),
        data: {
          agent_type: 'cv',
          running: true,
          queue_size: 5,
        },
      },
      {
        type: 'agent_status_change',
        timestamp: new Date().toISOString(),
        data: {
          agent_type: 'jd',
          running: false,
          queue_size: 0,
        },
      },
    ]

    events.forEach((event) => {
      if (mockWebSocket.onmessage) {
        mockWebSocket.onmessage({
          data: JSON.stringify(event),
        })
      }
    })

    await waitFor(() => {
      expect(result.current.agentStatuses.size).toBe(2)
      expect(result.current.agentStatuses.has('cv')).toBe(true)
      expect(result.current.agentStatuses.has('jd')).toBe(true)
    })
  })
})
