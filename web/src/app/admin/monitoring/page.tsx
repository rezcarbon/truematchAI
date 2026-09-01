'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/AppShell';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { adminApi } from '@/lib/api-admin';
import { SystemHealthResponse, ServiceHealth } from '@/types/admin';
import { StatusBadge } from '@/components/shared/StatusBadge';

export default function MonitoringPage() {
  const [health, setHealth] = useState<SystemHealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchSystemHealth();

    if (autoRefresh) {
      const interval = setInterval(fetchSystemHealth, 30000); // Refresh every 30s
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const fetchSystemHealth = async () => {
    try {
      setError(null);
      const response = await adminApi.getSystemHealth();
      setHealth(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load system health');
    } finally {
      setLoading(false);
    }
  };

  const getServiceStatusColor = (status: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (status) {
      case 'operational':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'down':
        return 'error';
      default:
        return 'default';
    }
  };

  const getHealthStatusColor = (status: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (status) {
      case 'operational':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'down':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="System Monitoring"
          subtitle="Real-time system health and service status"
        />
        <div className="flex gap-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-4 py-2 rounded border text-sm font-medium ${
              autoRefresh
                ? 'bg-primary text-primary-foreground border-primary'
                : 'border-muted-foreground text-muted-foreground'
            }`}
          >
            {autoRefresh ? 'Auto Refresh: ON' : 'Auto Refresh: OFF'}
          </button>
          <button
            onClick={fetchSystemHealth}
            className="px-4 py-2 rounded border border-muted-foreground text-sm font-medium hover:bg-muted"
          >
            Refresh
          </button>
        </div>
      </div>

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
      {!loading && !health && (
        <Card>
          <CardContent className="p-8 text-center text-muted-foreground">
            No system health data available
          </CardContent>
        </Card>
      )}

      {/* Health Status */}
      {!loading && health && (
        <>
          {/* Overall Status Card */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Overall System Status</p>
                  <p className="text-2xl font-bold">
                    {health.status === 'operational' ? 'Healthy' : health.status === 'degraded' ? 'Degraded' : 'Down'}
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    Uptime: {formatUptime(health.uptime)}
                  </p>
                </div>
                <StatusBadge status={getHealthStatusColor(health.status)} text={health.status} />
              </div>
            </CardContent>
          </Card>

          {/* Metrics Grid */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">CPU Usage</p>
                  <p className="text-3xl font-bold">{health.metrics.cpuUsage}%</p>
                  <div className="w-full bg-muted rounded-full h-2 mt-2">
                    <div
                      className={`h-2 rounded-full ${
                        health.metrics.cpuUsage > 80
                          ? 'bg-red-500'
                          : health.metrics.cpuUsage > 60
                            ? 'bg-yellow-500'
                            : 'bg-green-500'
                      }`}
                      style={{ width: `${health.metrics.cpuUsage}%` }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Memory Usage</p>
                  <p className="text-3xl font-bold">{health.metrics.memoryUsage}%</p>
                  <div className="w-full bg-muted rounded-full h-2 mt-2">
                    <div
                      className={`h-2 rounded-full ${
                        health.metrics.memoryUsage > 80
                          ? 'bg-red-500'
                          : health.metrics.memoryUsage > 60
                            ? 'bg-yellow-500'
                            : 'bg-green-500'
                      }`}
                      style={{ width: `${health.metrics.memoryUsage}%` }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Disk Usage</p>
                  <p className="text-3xl font-bold">{health.metrics.diskUsage}%</p>
                  <div className="w-full bg-muted rounded-full h-2 mt-2">
                    <div
                      className={`h-2 rounded-full ${
                        health.metrics.diskUsage > 80
                          ? 'bg-red-500'
                          : health.metrics.diskUsage > 60
                            ? 'bg-yellow-500'
                            : 'bg-green-500'
                      }`}
                      style={{ width: `${health.metrics.diskUsage}%` }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Additional Metrics */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">DB Connections</p>
                  <p className="text-3xl font-bold">{health.metrics.databaseConnections}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Queued Jobs</p>
                  <p className="text-3xl font-bold">{health.metrics.queuedJobs}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Error Rate</p>
                  <p className="text-3xl font-bold">{health.metrics.errorRate}%</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Requests/sec</p>
                  <p className="text-3xl font-bold">{health.metrics.requestsPerSecond}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Service Status */}
          <Card>
            <CardHeader>
              <CardTitle>Service Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b bg-muted/50">
                    <tr>
                      <th className="px-6 py-3 text-left font-semibold">Service</th>
                      <th className="px-6 py-3 text-left font-semibold">Status</th>
                      <th className="px-6 py-3 text-left font-semibold">Response Time</th>
                      <th className="px-6 py-3 text-left font-semibold">Last Check</th>
                      <th className="px-6 py-3 text-left font-semibold">Message</th>
                    </tr>
                  </thead>
                  <tbody>
                    {health.services?.map((service: ServiceHealth) => (
                      <tr key={service.name} className="border-b hover:bg-muted/30">
                        <td className="px-6 py-3 font-medium">{service.name}</td>
                        <td className="px-6 py-3">
                          <StatusBadge
                            status={getServiceStatusColor(service.status)}
                            text={service.status}
                          />
                        </td>
                        <td className="px-6 py-3 text-muted-foreground">
                          {service.responseTime ? `${service.responseTime}ms` : '—'}
                        </td>
                        <td className="px-6 py-3 text-xs text-muted-foreground">
                          {new Date(service.lastCheck).toLocaleString()}
                        </td>
                        <td className="px-6 py-3 text-sm">{service.message || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Last Updated */}
          <div className="text-xs text-right text-muted-foreground">
            Last updated: {new Date(health.metrics.timestamp).toLocaleString()}
          </div>
        </>
      )}
    </div>
  );
}
