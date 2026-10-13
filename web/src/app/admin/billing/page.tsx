'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/AppShell';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, Download, CreditCard } from 'lucide-react';
import { adminApi } from '@/lib/api-admin';
import { Subscription, Invoice, SubscriptionStatus } from '@/types/admin';
import { formatDate } from '@/lib/utils';
import { StatusBadge } from '@/components/shared/StatusBadge';

const subscriptionStatusMap: Record<SubscriptionStatus, 'success' | 'warning' | 'error' | 'default'> = {
  active: 'success',
  canceled: 'default',
  past_due: 'error',
  expired: 'error',
};

export default function BillingPage() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [selectedSubscription, setSelectedSubscription] = useState<Subscription | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isDownloading, setIsDownloading] = useState<string | null>(null);

  useEffect(() => {
    fetchSubscriptions();
  }, [page]);

  const fetchSubscriptions = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await adminApi.getSubscriptions({
        page,
        limit: 10,
      });
      setSubscriptions(response.data);
      setTotalPages(response.pages);
      if (response.data.length > 0) {
        setSelectedSubscription(response.data[0]);
        fetchInvoices(response.data[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load subscriptions');
    } finally {
      setLoading(false);
    }
  };

  const fetchInvoices = async (subscriptionId: string) => {
    try {
      const response = await adminApi.getInvoices(subscriptionId);
      setInvoices(response.data);
    } catch (err) {
      console.error('Failed to load invoices:', err);
    }
  };

  const handleSubscriptionSelect = (subscription: Subscription) => {
    setSelectedSubscription(subscription);
    fetchInvoices(subscription.id);
  };

  const handleDownloadInvoice = async (invoiceId: string) => {
    try {
      setIsDownloading(invoiceId);
      const blob = await adminApi.getInvoicePdf(invoiceId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `invoice-${invoiceId}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download invoice');
    } finally {
      setIsDownloading(null);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Billing & Subscriptions"
        subtitle="Manage customer subscriptions and invoices"
      />

      {/* Error Display */}
      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-200">
          {error}
          <button onClick={() => setError(null)} className="ml-2 underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center p-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Empty State */}
      {!loading && subscriptions.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center text-muted-foreground">
            No subscriptions found
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      {!loading && subscriptions.length > 0 && (
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Subscriptions List */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle>Subscriptions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {subscriptions.map((subscription) => (
                <button
                  key={subscription.id}
                  onClick={() => handleSubscriptionSelect(subscription)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    selectedSubscription?.id === subscription.id
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted border border-transparent'
                  }`}
                >
                  <p className="font-medium text-sm">{subscription.organizationName}</p>
                  <p className="text-xs text-muted-foreground">{subscription.plan} Plan</p>
                  <StatusBadge
                    status={subscriptionStatusMap[subscription.status]}
                    text={subscription.status}
                  />
                </button>
              ))}
            </CardContent>
          </Card>

          {/* Subscription Details */}
          <div className="lg:col-span-2 space-y-6">
            {selectedSubscription && (
              <>
                {/* Summary Cards */}
                <div className="grid gap-4 md:grid-cols-2">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="space-y-2">
                        <p className="text-sm text-muted-foreground">Monthly Rate</p>
                        <p className="text-3xl font-bold">
                          ${(selectedSubscription.monthlyRate / 100).toLocaleString()}
                        </p>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="space-y-2">
                        <p className="text-sm text-muted-foreground">This Month Usage</p>
                        <p className="text-3xl font-bold">
                          ${(selectedSubscription.totalThisMonth / 100).toLocaleString()}
                        </p>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="space-y-2">
                        <p className="text-sm text-muted-foreground">Estimated Next Month</p>
                        <p className="text-3xl font-bold">
                          ${(selectedSubscription.estimatedNextMonth / 100).toLocaleString()}
                        </p>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="space-y-2">
                        <p className="text-sm text-muted-foreground">Auto Renew</p>
                        <p className="text-xl font-bold">
                          {selectedSubscription.autoRenew ? 'Enabled' : 'Disabled'}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Billing Cycle */}
                <Card>
                  <CardHeader>
                    <CardTitle>Billing Cycle</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Cycle Start</span>
                      <span className="font-medium">{formatDate(selectedSubscription.billingCycleStart)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Cycle End</span>
                      <span className="font-medium">{formatDate(selectedSubscription.billingCycleEnd)}</span>
                    </div>
                  </CardContent>
                </Card>

                {/* Usage Metrics */}
                <Card>
                  <CardHeader>
                    <CardTitle>Usage Metrics</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {selectedSubscription.usageThisMonth?.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No usage data available</p>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="border-b bg-muted/50">
                            <tr>
                              <th className="px-4 py-2 text-left font-semibold">Date</th>
                              <th className="px-4 py-2 text-left font-semibold">Assessments</th>
                              <th className="px-4 py-2 text-left font-semibold">Active Recruiters</th>
                              <th className="px-4 py-2 text-left font-semibold">Cost</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedSubscription.usageThisMonth?.map((usage) => (
                              <tr key={usage.date} className="border-b hover:bg-muted/30">
                                <td className="px-4 py-2">{formatDate(usage.date)}</td>
                                <td className="px-4 py-2">{usage.assessmentsCreated}</td>
                                <td className="px-4 py-2">{usage.activeRecruiters}</td>
                                <td className="px-4 py-2">
                                  ${(usage.costEstimate / 100).toLocaleString()}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Invoices */}
                <Card>
                  <CardHeader>
                    <CardTitle>Invoices</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {invoices.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No invoices</p>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="border-b bg-muted/50">
                            <tr>
                              <th className="px-4 py-2 text-left font-semibold">Invoice</th>
                              <th className="px-4 py-2 text-left font-semibold">Period</th>
                              <th className="px-4 py-2 text-left font-semibold">Amount</th>
                              <th className="px-4 py-2 text-left font-semibold">Status</th>
                              <th className="px-4 py-2 text-left font-semibold">Due Date</th>
                              <th className="px-4 py-2 text-right font-semibold">Action</th>
                            </tr>
                          </thead>
                          <tbody>
                            {invoices.map((invoice) => (
                              <tr key={invoice.id} className="border-b hover:bg-muted/30">
                                <td className="px-4 py-2 font-mono text-xs">{invoice.id}</td>
                                <td className="px-4 py-2">{invoice.period}</td>
                                <td className="px-4 py-2">
                                  ${(invoice.amount / 100).toLocaleString()}
                                </td>
                                <td className="px-4 py-2">
                                  <Badge
                                    variant={
                                      invoice.status === 'paid' ? 'default' : 'secondary'
                                    }
                                  >
                                    {invoice.status}
                                  </Badge>
                                </td>
                                <td className="px-4 py-2">{formatDate(invoice.dueDate)}</td>
                                <td className="px-4 py-2 text-right">
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => handleDownloadInvoice(invoice.id)}
                                    disabled={isDownloading === invoice.id}
                                  >
                                    {isDownloading === invoice.id ? (
                                      <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                      <Download className="h-4 w-4" />
                                    )}
                                  </Button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </div>
      )}

      {/* Pagination */}
      {!loading && totalPages > 1 && (
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
