import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ActionPanel } from '../ActionPanel'

describe('ActionPanel Component', () => {
  const mockOnAction = jest.fn()
  const mockOnSuccess = jest.fn()
  const mockOnError = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders action buttons for awaiting_review items', () => {
    render(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="awaiting_review"
      />
    )

    expect(
      screen.getByRole('button', { name: /approve/i })
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /reject/i })
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /hold/i })
    ).toBeInTheDocument()
  })

  it('disables action buttons for non-awaiting_review items', () => {
    render(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="approved"
      />
    )

    expect(screen.getByRole('button', { name: /approve/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /reject/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /hold/i })).toBeDisabled()
  })

  it('shows message for read-only items', () => {
    render(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="rejected"
      />
    )

    expect(
      screen.getByText(/This item is no longer awaiting review/i)
    ).toBeInTheDocument()
  })

  it('opens approve modal when approve button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="awaiting_review"
      />
    )

    await user.click(screen.getByRole('button', { name: /approve/i }))

    expect(screen.getByText(/Approve this item/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/notes/i)).toBeInTheDocument()
  })

  it('submits approval action with notes', async () => {
    const user = userEvent.setup()
    mockOnAction.mockResolvedValueOnce(undefined)

    render(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="awaiting_review"
      />
    )

    await user.click(screen.getByRole('button', { name: /^approve$/i }))
    await user.type(
      screen.getByLabelText(/notes/i),
      'Good candidate, strong fit'
    )
    await user.click(screen.getByRole('button', { name: /approve/i }))

    await waitFor(() => {
      expect(mockOnAction).toHaveBeenCalledWith({
        action: 'approve',
        notes: 'Good candidate, strong fit',
      })
    })
  })

  it('submits approval action without notes', async () => {
    const user = userEvent.setup()
    mockOnAction.mockResolvedValueOnce(undefined)

    render(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="awaiting_review"
      />
    )

    await user.click(screen.getByRole('button', { name: /^approve$/i }))
    await user.click(screen.getByRole('button', { name: /approve/i }))

    await waitFor(() => {
      expect(mockOnAction).toHaveBeenCalledWith({
        action: 'approve',
        notes: '',
      })
    })
  })

  it('opens reject modal when reject button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="awaiting_review"
      />
    )

    await user.click(screen.getByRole('button', { name: /^reject$/i }))

    expect(screen.getByText(/Reject this item/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Reason for rejection/i)).toBeInTheDocument()
  })

  it('validates rejection requires a reason', async () => {
    const user = userEvent.setup()
    render(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="awaiting_review"
      />
    )

    await user.click(screen.getByRole('button', { name: /^reject$/i }))
    await user.click(screen.getByRole('button', { name: /reject/i }))

    await waitFor(() => {
      expect(
        screen.getByText(/Please select a rejection reason/i)
      ).toBeInTheDocument()
    })

    expect(mockOnAction).not.toHaveBeenCalled()
  })

  it('submits rejection action with reason and notes', async () => {
    const user = userEvent.setup()
    mockOnAction.mockResolvedValueOnce(undefined)

    render(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="awaiting_review"
      />
    )

    await user.click(screen.getByRole('button', { name: /^reject$/i }))
    await user.selectOptions(
      screen.getByLabelText(/Reason for rejection/i),
      'insufficient_qualifications'
    )
    await user.type(
      screen.getByLabelText(/Additional notes/i),
      'Missing key skills'
    )
    await user.click(screen.getByRole('button', { name: /reject/i }))

    await waitFor(() => {
      expect(mockOnAction).toHaveBeenCalledWith({
        action: 'reject',
        reason: 'insufficient_qualifications',
        notes: 'Missing key skills',
      })
    })
  })

  it('opens hold modal when hold button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="awaiting_review"
      />
    )

    await user.click(screen.getByRole('button', { name: /^hold$/i }))

    expect(screen.getByText(/Hold this item/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Hold until/i)).toBeInTheDocument()
  })

  it('validates hold requires a date', async () => {
    const user = userEvent.setup()
    render(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="awaiting_review"
      />
    )

    await user.click(screen.getByRole('button', { name: /^hold$/i }))
    await user.click(screen.getByRole('button', { name: /hold/i }))

    await waitFor(() => {
      expect(
        screen.getByText(/Please specify when to hold until/i)
      ).toBeInTheDocument()
    })

    expect(mockOnAction).not.toHaveBeenCalled()
  })

  it('submits hold action with datetime', async () => {
    const user = userEvent.setup()
    mockOnAction.mockResolvedValueOnce(undefined)

    render(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="awaiting_review"
      />
    )

    await user.click(screen.getByRole('button', { name: /^hold$/i }))

    const holdUntilInput = screen.getByLabelText(/Hold until/i)
    // Set a future date (must be at least 1 hour from now)
    await user.type(holdUntilInput, '2025-12-31T23:59')

    await user.click(screen.getByRole('button', { name: /hold/i }))

    await waitFor(() => {
      expect(mockOnAction).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'hold',
          holdUntil: '2025-12-31T23:59',
        })
      )
    })
  })

  it('cancels modal when cancel button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="awaiting_review"
      />
    )

    await user.click(screen.getByRole('button', { name: /^approve$/i }))
    expect(screen.getByText(/Approve this item/i)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /cancel/i }))
    expect(screen.queryByText(/Approve this item/i)).not.toBeInTheDocument()

    expect(mockOnAction).not.toHaveBeenCalled()
  })

  it('displays error message on failed action', async () => {
    const user = userEvent.setup()
    mockOnAction.mockRejectedValueOnce(new Error('Network error'))

    render(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="awaiting_review"
      />
    )

    await user.click(screen.getByRole('button', { name: /^approve$/i }))
    await user.click(screen.getByRole('button', { name: /approve/i }))

    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument()
    })
  })

  it('displays success message on successful action', async () => {
    const user = userEvent.setup()
    mockOnAction.mockResolvedValueOnce(undefined)

    render(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="awaiting_review"
      />
    )

    await user.click(screen.getByRole('button', { name: /^approve$/i }))
    await user.click(screen.getByRole('button', { name: /approve/i }))

    await waitFor(() => {
      expect(screen.getByText(/approved successfully/i)).toBeInTheDocument()
    })
  })

  it('calls onSuccess callback after successful action', async () => {
    const user = userEvent.setup()
    mockOnAction.mockResolvedValueOnce(undefined)

    render(
      <ActionPanel
        onAction={mockOnAction}
        onSuccess={mockOnSuccess}
        itemId="1"
        itemStatus="awaiting_review"
      />
    )

    await user.click(screen.getByRole('button', { name: /^approve$/i }))
    await user.click(screen.getByRole('button', { name: /approve/i }))

    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalledWith('approve')
    })
  })

  it('calls onError callback after failed action', async () => {
    const user = userEvent.setup()
    mockOnAction.mockRejectedValueOnce(new Error('API error'))

    render(
      <ActionPanel
        onAction={mockOnAction}
        onError={mockOnError}
        itemId="1"
        itemStatus="awaiting_review"
      />
    )

    await user.click(screen.getByRole('button', { name: /^approve$/i }))
    await user.click(screen.getByRole('button', { name: /approve/i }))

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith('API error')
    })
  })

  it('disables buttons while action is loading', async () => {
    const user = userEvent.setup()
    mockOnAction.mockImplementationOnce(
      () =>
        new Promise((resolve) =>
          setTimeout(() => resolve(undefined), 100)
        )
    )

    const { rerender } = render(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="awaiting_review"
        isLoading={false}
      />
    )

    await user.click(screen.getByRole('button', { name: /^approve$/i }))
    await user.click(screen.getByRole('button', { name: /approve/i }))

    rerender(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="awaiting_review"
        isLoading={true}
      />
    )

    const buttons = screen.getAllByRole('button')
    buttons.forEach((button) => {
      if (button.textContent?.includes('Approving')) {
        expect(button).toBeDisabled()
      }
    })
  })

  it('displays all rejection reason options', async () => {
    const user = userEvent.setup()
    render(
      <ActionPanel
        onAction={mockOnAction}
        itemId="1"
        itemStatus="awaiting_review"
      />
    )

    await user.click(screen.getByRole('button', { name: /^reject$/i }))

    const reasonSelect = screen.getByLabelText(/Reason for rejection/i)
    await user.click(reasonSelect)

    expect(screen.getByText('Insufficient qualifications')).toBeInTheDocument()
    expect(screen.getByText('Missing key requirements')).toBeInTheDocument()
    expect(screen.getByText('Experience gap too large')).toBeInTheDocument()
    expect(screen.getByText('Technical skills mismatch')).toBeInTheDocument()
    expect(screen.getByText('Not a cultural fit')).toBeInTheDocument()
    expect(screen.getByText('Duplicate submission')).toBeInTheDocument()
    expect(screen.getByText('Other reason')).toBeInTheDocument()
  })
})
