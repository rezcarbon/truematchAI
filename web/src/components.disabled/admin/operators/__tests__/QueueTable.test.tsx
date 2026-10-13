import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueueTable } from '../QueueTable'

const mockQueueItems = [
  {
    id: '1',
    name: 'Resume - John Doe',
    type: 'cv' as const,
    source: 'email',
    created_at: new Date('2024-01-15').toISOString(),
    awaiting_review: true,
    status: 'awaiting_review',
  },
  {
    id: '2',
    name: 'JD - Senior Engineer',
    type: 'jd' as const,
    source: 'manual',
    created_at: new Date('2024-01-14').toISOString(),
    awaiting_review: false,
    status: 'approved',
  },
  {
    id: '3',
    name: 'Assessment - Tech Round',
    type: 'assessment' as const,
    source: 'system',
    created_at: new Date('2024-01-13').toISOString(),
    awaiting_review: true,
    status: 'awaiting_review',
  },
]

describe('QueueTable Component', () => {
  it('renders table with queue items', () => {
    const mockCallback = jest.fn()
    render(
      <QueueTable
        items={mockQueueItems}
        onSelectRow={mockCallback}
        isLoading={false}
        filterAwaitingReview={false}
      />
    )

    expect(screen.getByText('Resume - John Doe')).toBeInTheDocument()
    expect(screen.getByText('JD - Senior Engineer')).toBeInTheDocument()
    expect(screen.getByText('Assessment - Tech Round')).toBeInTheDocument()
  })

  it('displays table headers', () => {
    const mockCallback = jest.fn()
    render(
      <QueueTable
        items={mockQueueItems}
        onSelectRow={mockCallback}
        isLoading={false}
      />
    )

    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Type')).toBeInTheDocument()
    expect(screen.getByText('Source')).toBeInTheDocument()
    expect(screen.getByText('Created')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    const mockCallback = jest.fn()
    render(
      <QueueTable
        items={[]}
        onSelectRow={mockCallback}
        isLoading={true}
      />
    )

    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('displays error message when error prop is provided', () => {
    const mockCallback = jest.fn()
    const errorMessage = 'Failed to load queue items'
    render(
      <QueueTable
        items={[]}
        onSelectRow={mockCallback}
        isLoading={false}
        error={errorMessage}
      />
    )

    expect(screen.getByText(errorMessage)).toBeInTheDocument()
  })

  it('shows empty state when no items', () => {
    const mockCallback = jest.fn()
    render(
      <QueueTable
        items={[]}
        onSelectRow={mockCallback}
        isLoading={false}
        filterAwaitingReview={true}
      />
    )

    expect(
      screen.getByText(/No items awaiting review/i)
    ).toBeInTheDocument()
  })

  it('calls onSelectRow when a row is clicked', async () => {
    const user = userEvent.setup()
    const mockCallback = jest.fn()

    render(
      <QueueTable
        items={mockQueueItems}
        onSelectRow={mockCallback}
        isLoading={false}
      />
    )

    const firstRow = screen.getByText('Resume - John Doe')
    await user.click(firstRow)

    expect(mockCallback).toHaveBeenCalledWith(mockQueueItems[0])
  })

  it('filters to show only awaiting_review items when filter is enabled', () => {
    const mockCallback = jest.fn()
    render(
      <QueueTable
        items={mockQueueItems}
        onSelectRow={mockCallback}
        isLoading={false}
        filterAwaitingReview={true}
      />
    )

    // Should show items 1 and 3 (awaiting_review = true)
    expect(screen.getByText('Resume - John Doe')).toBeInTheDocument()
    expect(screen.getByText('Assessment - Tech Round')).toBeInTheDocument()

    // Should not show item 2 (awaiting_review = false)
    expect(screen.queryByText('JD - Senior Engineer')).not.toBeInTheDocument()
  })

  it('shows all items when filter is disabled', () => {
    const mockCallback = jest.fn()
    render(
      <QueueTable
        items={mockQueueItems}
        onSelectRow={mockCallback}
        isLoading={false}
        filterAwaitingReview={false}
      />
    )

    expect(screen.getByText('Resume - John Doe')).toBeInTheDocument()
    expect(screen.getByText('JD - Senior Engineer')).toBeInTheDocument()
    expect(screen.getByText('Assessment - Tech Round')).toBeInTheDocument()
  })

  it('toggles filter when filter button is clicked', async () => {
    const user = userEvent.setup()
    const mockOnFilterChange = jest.fn()
    const mockOnSelectRow = jest.fn()

    render(
      <QueueTable
        items={mockQueueItems}
        onSelectRow={mockOnSelectRow}
        onFilterChange={mockOnFilterChange}
        isLoading={false}
        filterAwaitingReview={true}
      />
    )

    const filterButton = screen.getByRole('button', {
      name: /showing.*awaiting review/i,
    })
    await user.click(filterButton)

    expect(mockOnFilterChange).toHaveBeenCalledWith(false)
  })

  it('highlights selected row', () => {
    const mockCallback = jest.fn()
    render(
      <QueueTable
        items={mockQueueItems}
        onSelectRow={mockCallback}
        selectedId="1"
        isLoading={false}
      />
    )

    const rows = screen.getAllByRole('row')
    // First row should have bg-primary/5 class when selected
    expect(rows[1]).toHaveClass('bg-primary/5')
  })

  it('displays correct type badges', () => {
    const mockCallback = jest.fn()
    render(
      <QueueTable
        items={mockQueueItems}
        onSelectRow={mockCallback}
        isLoading={false}
        filterAwaitingReview={false}
      />
    )

    expect(screen.getByText('cv')).toBeInTheDocument()
    expect(screen.getByText('jd')).toBeInTheDocument()
    expect(screen.getByText('assessment')).toBeInTheDocument()
  })

  it('displays status badges with correct styling', () => {
    const mockCallback = jest.fn()
    render(
      <QueueTable
        items={mockQueueItems}
        onSelectRow={mockCallback}
        isLoading={false}
        filterAwaitingReview={false}
      />
    )

    // Check for status badge labels (filter off so the approved row is shown).
    // Two mock items are awaiting_review, so use getAllByText for that label.
    expect(screen.getAllByText('Awaiting Review').length).toBeGreaterThan(0)
    expect(screen.getByText('Approved')).toBeInTheDocument()
  })

  it('formats created_at dates correctly', () => {
    const mockCallback = jest.fn()
    render(
      <QueueTable
        items={mockQueueItems}
        onSelectRow={mockCallback}
        isLoading={false}
      />
    )

    // Dates should be formatted in locale format
    const dateStrings = screen.getAllByText(/Jan/)
    expect(dateStrings.length).toBeGreaterThan(0)
  })

  it('displays item count in footer', () => {
    const mockCallback = jest.fn()
    render(
      <QueueTable
        items={mockQueueItems}
        onSelectRow={mockCallback}
        isLoading={false}
        filterAwaitingReview={false}
      />
    )

    expect(screen.getByText(/Showing 3 of 3 items/i)).toBeInTheDocument()
  })

  it('handles empty items array gracefully', () => {
    const mockCallback = jest.fn()
    const { container } = render(
      <QueueTable
        items={[]}
        onSelectRow={mockCallback}
        isLoading={false}
        filterAwaitingReview={false}
      />
    )

    expect(container).toBeInTheDocument()
    expect(screen.getByText(/No queue items found/i)).toBeInTheDocument()
  })
})
