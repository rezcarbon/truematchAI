import { useEffect, useState } from 'react';
'use client';
function cn(...inputs: any[]) {
  return twMerge(clsx(inputs));
}

// import { Input } from '@/components/ui/input'; (needs manual conversion)
// import { Card, CardContent } from '@/components/ui/card'; (needs manual conversion)
import { Loader2, Search, Download } from 'lucide-react';
// adminApi removed - use fetch directly;
// import { AuditEvent } from '@/types/admin'; (needs manual conversion)
import {
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function Badge({ variant = "default", className, ...props }: any) {
  const variants: any = {
    default: "bg-blue-100 text-blue-800",
    secondary: "bg-gray-100 text-gray-800",
    success: "bg-green-100 text-green-800",
    danger: "bg-red-100 text-red-800",
    warning: "bg-yellow-100 text-yellow-800",
  };
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-1 text-xs font-medium", variants[variant], className)} {...props} />
  );
}

function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
    </div>
  );
}

function Button({ className, variant = "default", size = "default", ...props }: any) {
  const variants: any = { default: "bg-blue-600 text-white hover:bg-blue-700", outline: "border border-gray-300 bg-white hover:bg-gray-50", ghost: "hover:bg-gray-100" };
  const sizes: any = { default: "px-4 py-2", sm: "px-3 py-1 text-sm", lg: "px-6 py-3 text-lg" };
  return <button className={cn("inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none", variants[variant], sizes[size], className)} {...props} />;
}

function formatDate(iso: string): string {
  try { return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }); }
  catch { return iso; }
}
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export default function AuditPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [eventType, setEventType] = useState('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    fetchAuditEvents();
  }, [page, eventType]);

  const fetchAuditEvents = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await adminApi.getAuditEvents({
        eventType: eventType !== 'all' ? (eventType as any) : undefined,
        limit: 20,
        offset: (page - 1) * 20,
      });
      setEvents(response.events);
      setTotalPages(Math.ceil(response.total / 20));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit events');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      fetchAuditEvents();
      return;
    }
    try {
      setLoading(true);
      const response = await adminApi.getAuditEvents({ search: searchQuery });
      setEvents(response.events);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      setIsExporting(true);
      const blob = await adminApi.exportAuditLog('csv');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-log-${new Date().toISOString()}.csv`;
      a.click();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader title="Audit Trail" subtitle="Immutable record of all platform actions." />
        <Button onClick={handleExport} disabled={isExporting}>
          <Download className="mr-2 h-4 w-4" />
          {isExporting ? 'Exporting...' : 'Export Log'}
        </Button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-200">
          {error}
          <button onClick={() => setError(null)} className="ml-2 underline">
            Dismiss
          </button>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <div className="flex gap-2">
          <Input
            placeholder="Search by resource or action..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <Button variant="outline" size="icon" onClick={handleSearch}>
            <Search className="h-4 w-4" />
          </Button>
        </div>
        <Select value={eventType} onValueChange={setEventType}>
          <SelectTrigger>
            <SelectValue placeholder="Filter by event type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Events</SelectItem>
            <SelectItem value="assessment_created">Assessment Created</SelectItem>
            <SelectItem value="assessment_completed">Assessment Completed</SelectItem>
            <SelectItem value="assessment_overridden">Assessment Overridden</SelectItem>
            <SelectItem value="governance_gate_triggered">Gate Triggered</SelectItem>
            <SelectItem value="user_invited">User Invited</SelectItem>
            <SelectItem value="user_role_changed">Role Changed</SelectItem>
            <SelectItem value="configuration_changed">Configuration Changed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : events.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">No audit events found</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b bg-muted/50">
                  <tr>
                    <th className="px-6 py-3 text-left font-semibold">Event</th>
                    <th className="px-6 py-3 text-left font-semibold">Actor</th>
                    <th className="px-6 py-3 text-left font-semibold">Resource</th>
                    <th className="px-6 py-3 text-left font-semibold">Time</th>
                    <th className="px-6 py-3 text-left font-semibold">Details</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((event) => (
                    <tr key={event.id} className="border-b hover:bg-muted/30">
                      <td className="px-6 py-3">
                        <Badge variant="outline">{event.eventType}</Badge>
                      </td>
                      <td className="px-6 py-3">
                        <div className="text-sm">
                          <p className="font-medium">{event.actor.email}</p>
                          <p className="text-xs text-muted-foreground">{event.actor.role}</p>
                        </div>
                      </td>
                      <td className="px-6 py-3 text-sm">
                        {event.resource ? (
                          <p>
                            {event.resource.type} {event.resource.id}
                          </p>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="px-6 py-3 text-xs text-muted-foreground">
                        {formatDate(event.timestamp)}
                      </td>
                      <td className="px-6 py-3 text-xs">
                        <pre className="overflow-x-auto whitespace-pre-wrap break-words rounded bg-muted p-2 text-xs">
                          {JSON.stringify(event.details, null, 2)}
                        </pre>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={page === 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={page === totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}


