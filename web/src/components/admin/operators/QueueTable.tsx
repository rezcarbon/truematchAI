'use client';

/**
 * QueueTable Component
 *
 * TanStack Table-based real-time queue display with sorting, filtering,
 * and selection. Shows assessments awaiting operator review.
 *
 * Features:
 * - Real-time updates via WebSocket
 * - Filterable by awaiting_review status
 * - Sortable by created_at (newest first)
 * - Single-row selection with detail panel expansion
 * - Loading and error states
 * - Status badges with visual indicators
 */

import { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  SortingState,
  ColumnFiltersState,
  Column,
  Row,
  ColumnDef,
  VisibilityState,
} from '@tanstack/react-table';
import {
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle2,
  Clock,
  Eye,
  EyeOff,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

/**
 * Queue item type matching backend schema
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

interface QueueTableProps {
  /** Array of queue items to display */
  items: QueueItem[];

  /** Called when a row is selected */
  onSelectRow: (item: QueueItem) => void;

  /** Currently selected item ID */
  selectedId?: string;

  /** Loading state indicator */
  isLoading?: boolean;

  /** Error message if loading failed */
  error?: string | null;

  /** Callback when filtering changes */
  onFilterChange?: (awaitingReviewOnly: boolean) => void;

  /** Filter to show only awaiting_review items */
  filterAwaitingReview?: boolean;
}

/**
 * Status badge component with icon and color
 */
function StatusBadge({ status }: { status: string }) {
  const config: Record<
    string,
    { icon: React.ReactNode; className: string; label: string }
  > = {
    awaiting_review: {
      icon: <AlertCircle className="h-3 w-3" />,
      className: 'bg-amber-100 text-amber-800',
      label: 'Awaiting Review',
    },
    approved: {
      icon: <CheckCircle2 className="h-3 w-3" />,
      className: 'bg-green-100 text-green-800',
      label: 'Approved',
    },
    rejected: {
      icon: <AlertCircle className="h-3 w-3" />,
      className: 'bg-red-100 text-red-800',
      label: 'Rejected',
    },
    processing: {
      icon: <Clock className="h-3 w-3" />,
      className: 'bg-blue-100 text-blue-800',
      label: 'Processing',
    },
    held: {
      icon: <Clock className="h-3 w-3" />,
      className: 'bg-orange-100 text-orange-800',
      label: 'Held',
    },
  };

  const { icon, className, label } = config[status] || {
    icon: null,
    className: 'bg-gray-100 text-gray-800',
    label: status,
  };

  return (
    <Badge variant="outline" className={`flex items-center gap-1 ${className}`}>
      {icon}
      <span>{label}</span>
    </Badge>
  );
}

/**
 * Sortable column header
 */
function SortableHeader({
  column,
  children,
}: {
  column: Column<QueueItem, unknown>;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
      className="flex items-center gap-1 font-semibold hover:text-primary transition-colors"
    >
      {children}
      {column.getIsSorted() === 'asc' && <ChevronUp className="h-4 w-4" />}
      {column.getIsSorted() === 'desc' && <ChevronDown className="h-4 w-4" />}
      {!column.getIsSorted() && (
        <span className="text-muted-foreground opacity-0 group-hover/header:opacity-100">
          ↕
        </span>
      )}
    </button>
  );
}

export function QueueTable({
  items,
  onSelectRow,
  selectedId,
  isLoading = false,
  error = null,
  onFilterChange,
  filterAwaitingReview = true,
}: QueueTableProps) {
  // State
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'created_at', desc: true }, // Newest first by default
  ]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});

  /**
   * Apply awaiting_review filter
   */
  const filteredItems = useMemo(() => {
    if (!filterAwaitingReview) return items;
    return items.filter((item) => item.awaiting_review === true);
  }, [items, filterAwaitingReview]);

  /**
   * Table columns definition
   */
  const columns: ColumnDef<QueueItem>[] = [
    {
      id: 'select',
      size: 40,
      cell: ({ row }) => (
        <div className="flex justify-center">
          {row.getIsSelected() ? (
            <Eye className="h-4 w-4 text-primary" />
          ) : (
            <EyeOff className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      ),
    },
    {
      accessorKey: 'name',
      header: ({ column }) => (
        <SortableHeader column={column}>
          Name
        </SortableHeader>
      ),
      cell: ({ row }) => (
        <div className="truncate font-medium">{row.original.name}</div>
      ),
      size: 200,
    },
    {
      accessorKey: 'type',
      header: 'Type',
      cell: ({ row }) => (
        <Badge variant="secondary" className="capitalize">
          {row.original.type}
        </Badge>
      ),
      size: 100,
    },
    {
      accessorKey: 'source',
      header: 'Source',
      cell: ({ row }) => (
        <span className="text-sm capitalize text-muted-foreground">
          {row.original.source}
        </span>
      ),
      size: 120,
    },
    {
      accessorKey: 'created_at',
      header: ({ column }) => (
        <SortableHeader column={column}>
          Created
        </SortableHeader>
      ),
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">
          {new Date(row.original.created_at).toLocaleDateString(undefined, {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      ),
      size: 150,
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => <StatusBadge status={row.original.status} />,
      size: 140,
    },
  ];

  /**
   * Create table instance
   */
  const table = useReactTable({
    data: filteredItems,
    columns,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection: selectedId ? { [selectedId]: true } : {},
    },
    enableRowSelection: true,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  // Handle row selection
  const handleRowClick = (row: Row<QueueItem>) => {
    onSelectRow(row.original);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Assessment Queue</CardTitle>
          <div className="flex items-center gap-2">
            {isLoading && <span className="text-sm text-muted-foreground">Loading...</span>}
            {error && (
              <div className="flex items-center gap-1 text-xs text-red-600">
                <AlertCircle className="h-4 w-4" />
                <span>{error}</span>
              </div>
            )}
          </div>
        </div>
        {/* Filter toggles */}
        <div className="flex items-center gap-2 mt-4">
          <Button
            variant={filterAwaitingReview ? 'default' : 'outline'}
            size="sm"
            onClick={() => onFilterChange?.(!filterAwaitingReview)}
          >
            {filterAwaitingReview
              ? `Showing ${filteredItems.length} awaiting review`
              : 'Show All'}
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {filteredItems.length === 0 && !isLoading ? (
          <div className="py-12 text-center">
            <CheckCircle2 className="h-12 w-12 text-green-600 mx-auto mb-3 opacity-50" />
            <p className="text-muted-foreground">
              {filterAwaitingReview
                ? 'No items awaiting review. Great job!'
                : 'No queue items found'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/50">
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <th
                        key={header.id}
                        className="px-4 py-2 text-left font-medium text-muted-foreground"
                        style={{ width: header.getSize() }}
                      >
                        {header.isPlaceholder
                          ? null
                          : flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    onClick={() => handleRowClick(row)}
                    className={`border-b transition-colors cursor-pointer hover:bg-muted/50 ${
                      row.getIsSelected() ? 'bg-primary/5' : ''
                    }`}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td
                        key={cell.id}
                        className="px-4 py-3"
                        style={{ width: cell.column.getSize() }}
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Table footer with info */}
        {filteredItems.length > 0 && (
          <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground border-t pt-4">
            <span>
              Showing {table.getRowModel().rows.length} of {filteredItems.length} items
            </span>
            {selectedId && (
              <span className="text-primary font-medium">
                {filteredItems.find((item) => item.id === selectedId)?.name ||
                  'Selected'}
              </span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
