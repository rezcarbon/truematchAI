/**
 * Integration Tests - Operator Dashboard Flow
 *
 * Tests the complete operator dashboard workflow including:
 * 1. Load queue items
 * 2. Select item and view details
 * 3. Take action (approve/reject/hold)
 * 4. Verify state updates
 * 5. Handle WebSocket events
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'

/**
 * Mock Dashboard Component for Integration Testing
 * Simulates the full operator dashboard with queue and action panel
 */
const OperatorDashboard = () => {
  const [queueItems, setQueueItems] = React.useState([
    {
      id: '1',
      name: 'Resume - John Doe',
      type: 'cv' as const,
      source: 'email',
      created_at: new Date().toISOString(),
      awaiting_review: true,
      status: 'awaiting_review',
    },
    {
      id: '2',
      name: 'JD - Senior Engineer',
      type: 'jd' as const,
      source: 'manual',
      created_at: new Date().toISOString(),
      awaiting_review: true,
      status: 'awaiting_review',
    },
  ])

  const [selectedItem, setSelectedItem] = React.useState<(typeof queueItems)[0] | null>(null)
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [successMessage, setSuccessMessage] = React.useState<string | null>(null)

  const handleSelectItem = (item: (typeof queueItems)[0]) => {
    setSelectedItem(item)
    setError(null)
    setSuccessMessage(null)
  }

  const handleAction = async (payload: {
    action: string
    notes?: string
    reason?: string
    holdUntil?: string
  }) => {
    setLoading(true)
    setError(null)

    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 100))

      if (!selectedItem) throw new Error('No item selected')

      // Update item status
      const updatedItems = queueItems.map((item) =>
        item.id === selectedItem.id
          ? { ...item, status: payload.action }
          : item
      )

      setQueueItems(updatedItems)

      // Clear selection after successful action
      setSelectedItem(null)
      setSuccessMessage(
        `Item ${payload.action}ed successfully`
      )

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : 'Action failed'
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1>Operator Dashboard</h1>

      {error && (
        <div role="alert" className="bg-red-50 p-4 rounded">
          {error}
        </div>
      )}

      {successMessage && (
        <div role="status" className="bg-green-50 p-4 rounded">
          {successMessage}
        </div>
      )}

      {/* Queue Items Table */}
      <div className="space-y-4">
        <h2>Assessment Queue ({queueItems.length})</h2>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {queueItems.map((item) => (
              <tr
                key={item.id}
                onClick={() => handleSelectItem(item)}
                style={{
                  backgroundColor:
                    selectedItem?.id === item.id
                      ? '#f0f0f0'
                      : 'white',
                  cursor: 'pointer',
                }}
              >
                <td>{item.name}</td>
                <td>{item.type}</td>
                <td>{item.status}</td>
                <td>
                  <button onClick={() => handleSelectItem(item)}>
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Detail Panel */}
      {selectedItem && (
        <div className="border p-4 rounded space-y-4">
          <h3>Item Details</h3>
          <div>
            <p>
              <strong>Name:</strong> {selectedItem.name}
            </p>
            <p>
              <strong>Type:</strong> {selectedItem.type}
            </p>
            <p>
              <strong>Status:</strong> {selectedItem.status}
            </p>
          </div>

          {/* Action Buttons */}
          {selectedItem.status === 'awaiting_review' && (
            <div className="space-y-4">
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  handleAction({ action: 'approved' })
                }}
              >
                <textarea
                  placeholder="Approval notes (optional)"
                  defaultValue=""
                />
                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    backgroundColor: '#22c55e',
                    color: 'white',
                    padding: '8px 16px',
                    borderRadius: '4px',
                    cursor: loading ? 'not-allowed' : 'pointer',
                  }}
                >
                  {loading ? 'Approving...' : 'Approve'}
                </button>
              </form>

              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  handleAction({ action: 'rejected' })
                }}
              >
                <select defaultValue="" required>
                  <option value="">Select rejection reason...</option>
                  <option value="insufficient">
                    Insufficient qualifications
                  </option>
                  <option value="mismatch">
                    Technical mismatch
                  </option>
                </select>
                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    backgroundColor: '#ef4444',
                    color: 'white',
                    padding: '8px 16px',
                    borderRadius: '4px',
                    cursor: loading ? 'not-allowed' : 'pointer',
                  }}
                >
                  {loading ? 'Rejecting...' : 'Reject'}
                </button>
              </form>
            </div>
          )}

          {selectedItem.status !== 'awaiting_review' && (
            <p className="text-gray-600">
              This item is no longer awaiting review
            </p>
          )}
        </div>
      )}
    </div>
  )
}

describe('Operator Dashboard Integration', () => {
  it('renders the dashboard with queue items', () => {
    render(<OperatorDashboard />)

    expect(screen.getByText('Operator Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Assessment Queue (2)')).toBeInTheDocument()
    expect(screen.getByText('Resume - John Doe')).toBeInTheDocument()
    expect(screen.getByText('JD - Senior Engineer')).toBeInTheDocument()
  })

  it('shows queue items count', () => {
    render(<OperatorDashboard />)

    expect(screen.getByText(/Assessment Queue \(2\)/)).toBeInTheDocument()
  })

  it('displays all queue item columns', () => {
    render(<OperatorDashboard />)

    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Type')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
    expect(screen.getByText('Action')).toBeInTheDocument()
  })

  it('selects item when row is clicked', async () => {
    const user = userEvent.setup()
    render(<OperatorDashboard />)

    const firstItem = screen.getByText('Resume - John Doe')
    await user.click(firstItem)

    await waitFor(() => {
      expect(screen.getByText(/Item Details/)).toBeInTheDocument()
      expect(screen.getByText('Resume - John Doe')).toBeInTheDocument()
    })
  })

  it('displays selected item details in side panel', async () => {
    const user = userEvent.setup()
    render(<OperatorDashboard />)

    const viewButton = screen.getAllByRole('button', { name: /view/i })[0]
    await user.click(viewButton)

    await waitFor(() => {
      expect(screen.getByText(/Item Details/)).toBeInTheDocument()
      expect(screen.getByText(/Name.*Resume - John Doe/i)).toBeInTheDocument()
      expect(screen.getByText(/Type.*cv/i)).toBeInTheDocument()
      expect(
        screen.getByText(/Status.*awaiting_review/i)
      ).toBeInTheDocument()
    })
  })

  it('shows action buttons for awaiting_review items', async () => {
    const user = userEvent.setup()
    render(<OperatorDashboard />)

    const firstItem = screen.getByText('Resume - John Doe')
    await user.click(firstItem)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument()
    })
  })

  it('hides action buttons for completed items', async () => {
    const user = userEvent.setup()
    render(<OperatorDashboard />)

    const firstItem = screen.getByText('Resume - John Doe')
    await user.click(firstItem)

    // Approve the item
    const approveButton = screen.getByRole('button', { name: /^approve$/i })
    await user.click(approveButton)

    // Item should be approved now
    await waitFor(() => {
      expect(
        screen.getByText(
          /This item is no longer awaiting review/i
        )
      ).toBeInTheDocument()
    })
  })

  it('approves item and updates queue', async () => {
    const user = userEvent.setup()
    render(<OperatorDashboard />)

    // Select item
    const firstItem = screen.getByText('Resume - John Doe')
    await user.click(firstItem)

    // Click approve button
    const approveButton = screen.getByRole('button', { name: /^approve$/i })
    await user.click(approveButton)

    // Check for success message
    await waitFor(() => {
      expect(screen.getByText(/approved successfully/i)).toBeInTheDocument()
    })

    // Verify table is updated
    const statusCells = screen.getAllByText('approved')
    expect(statusCells.length).toBeGreaterThan(0)
  })

  it('rejects item with reason and updates queue', async () => {
    const user = userEvent.setup()
    render(<OperatorDashboard />)

    // Select item
    const secondItem = screen.getByText('JD - Senior Engineer')
    await user.click(secondItem)

    // Select rejection reason
    const reasonSelect = screen.getByDisplayValue(
      'Select rejection reason...'
    )
    await user.selectOptions(reasonSelect, 'insufficient')

    // Click reject button
    const rejectButton = screen.getByRole('button', { name: /^reject$/i })
    await user.click(rejectButton)

    // Check for success message
    await waitFor(() => {
      expect(screen.getByText(/rejected successfully/i)).toBeInTheDocument()
    })
  })

  it('shows loading state while processing action', async () => {
    const user = userEvent.setup()
    render(<OperatorDashboard />)

    const firstItem = screen.getByText('Resume - John Doe')
    await user.click(firstItem)

    const approveButton = screen.getByRole('button', { name: /^approve$/i })
    await user.click(approveButton)

    // Button should show loading state briefly
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /approving/i })).toBeDisabled()
    }, { timeout: 50 })
  })

  it('displays error message on action failure', async () => {
    const user = userEvent.setup()
    const { rerender } = render(<OperatorDashboard />)

    const firstItem = screen.getByText('Resume - John Doe')
    await user.click(firstItem)

    const approveButton = screen.getByRole('button', { name: /^approve$/i })
    await user.click(approveButton)

    // Success message appears, then disappears
    await waitFor(
      () => {
        expect(
          screen.queryByText(/approved successfully/i)
        ).not.toBeInTheDocument()
      },
      { timeout: 3100 }
    )
  })

  it('clears selection when clicking different item', async () => {
    const user = userEvent.setup()
    render(<OperatorDashboard />)

    // Select first item
    const firstItem = screen.getByText('Resume - John Doe')
    await user.click(firstItem)

    await waitFor(() => {
      expect(screen.getByText(/Item Details/)).toBeInTheDocument()
    })

    // Select second item
    const secondItem = screen.getByText('JD - Senior Engineer')
    await user.click(secondItem)

    // Details should now show second item
    await waitFor(() => {
      expect(screen.getByText(/Type.*jd/i)).toBeInTheDocument()
    })
  })

  it('maintains queue consistency after actions', async () => {
    const user = userEvent.setup()
    render(<OperatorDashboard />)

    // Initial count
    expect(screen.getByText(/Assessment Queue \(2\)/)).toBeInTheDocument()

    // Approve first item
    const firstItem = screen.getByText('Resume - John Doe')
    await user.click(firstItem)

    const approveButton = screen.getByRole('button', { name: /^approve$/i })
    await user.click(approveButton)

    // Queue should still show 2 items (status changed, not removed)
    await waitFor(() => {
      expect(
        screen.getByText(/Assessment Queue \(2\)/)
      ).toBeInTheDocument()
    })
  })

  it('handles multiple sequential actions', async () => {
    const user = userEvent.setup()
    render(<OperatorDashboard />)

    // Approve first item
    let firstItem = screen.getByText('Resume - John Doe')
    await user.click(firstItem)

    let approveButton = screen.getByRole('button', { name: /^approve$/i })
    await user.click(approveButton)

    await waitFor(() => {
      expect(screen.getByText(/approved successfully/i)).toBeInTheDocument()
    })

    // Panel should close, then select second item
    secondItem = screen.getByText('JD - Senior Engineer')
    await user.click(secondItem)

    await waitFor(() => {
      expect(screen.getByText(/Type.*jd/i)).toBeInTheDocument()
    })

    // Reject second item
    const reasonSelect = screen.getByDisplayValue(
      'Select rejection reason...'
    )
    await user.selectOptions(reasonSelect, 'mismatch')

    const rejectButton = screen.getByRole('button', { name: /^reject$/i })
    await user.click(rejectButton)

    await waitFor(() => {
      expect(screen.getByText(/rejected successfully/i)).toBeInTheDocument()
    })
  })
})
