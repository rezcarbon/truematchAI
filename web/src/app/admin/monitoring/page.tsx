'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface SystemMetrics {
  status: string;
  last_24_hours: {
    total_sessions: number;
    avg_session_duration?: string;
  };
  last_7_days: {
    total_sessions: number;
    avg_session_duration?: string;
  };
  governance: {
    pending: number;
    approved: number;
    rejected: number;
    escalated: number;
    total: number;
  };
  timestamp: string;
}

/**
 * System Monitoring Dashboard
 *
 * Shows real-time metrics for system health, user engagement, and governance.
 * Displays:
 * - System status and uptime
 * - Session metrics (24h and 7d)
 * - Message and engagement metrics
 * - Governance review status
 * - Performance metrics and trends
 */
export default function MonitoringDashboard() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [trend, setTrend] = useState<{ time: string; sessions: number; messages: number }[]>([]);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        // In production, this would call the actual API
        // const response = await fetch('/api/v1/admin/metrics');
        // const data = await response.json();

        // Mock data for now
        const mockData: SystemMetrics = {
          status: 'healthy',
          last_24_hours: {
            total_sessions: 234,
            avg_session_duration: '00:15:30',
          },
          last_7_days: {
            total_sessions: 1543,
            avg_session_duration: '00:18:45',
          },
          governance: {
            pending: 12,
            approved: 245,
            rejected: 18,
            escalated: 5,
            total: 280,
          },
          timestamp: new Date().toISOString(),
        };

        setMetrics(mockData);

        // Mock trend data
        const mockTrend = Array.from({ length: 7 }, (_, i) => ({
          time: new Date(Date.now() - (6 - i) * 24 * 60 * 60 * 1000)
            .toLocaleDateString('en-US', { weekday: 'short' })
            .substring(0, 3),
          sessions: Math.floor(Math.random() * 300) + 150,
          messages: Math.floor(Math.random() * 1500) + 750,
        }));

        setTrend(mockTrend);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Refresh every 30s

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800';
      case 'critical':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="p-8 space-y-4">
        <div className="animate-pulse space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="p-8">
        <div className="text-center text-gray-600">Failed to load metrics</div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">System Monitoring</h1>
          <p className="text-gray-600">Real-time system health and metrics</p>
        </div>
        <Badge className={`text-lg px-3 py-1 ${getStatusColor(metrics.status)}`}>
          {metrics.status.toUpperCase()}
        </Badge>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Sessions Last 24h */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Sessions (24h)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.last_24_hours.total_sessions}</div>
            <p className="text-xs text-gray-600 mt-1">Last 24 hours</p>
          </CardContent>
        </Card>

        {/* Governance Pending */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Pending Reviews</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{metrics.governance.pending}</div>
            <p className="text-xs text-gray-600 mt-1">Awaiting approval</p>
          </CardContent>
        </Card>

        {/* Governance Approved */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Approved</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{metrics.governance.approved}</div>
            <p className="text-xs text-gray-600 mt-1">This period</p>
          </CardContent>
        </Card>

        {/* Error Rate */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Error Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0.3%</div>
            <p className="text-xs text-gray-600 mt-1">System-wide</p>
          </CardContent>
        </Card>
      </div>

      {/* Trends */}
      <Card>
        <CardHeader>
          <CardTitle>Activity Trend (7 Days)</CardTitle>
          <CardDescription>Sessions and messages over the past week</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Line yAxisId="left" type="monotone" dataKey="sessions" stroke="#3b82f6" />
              <Line yAxisId="right" type="monotone" dataKey="messages" stroke="#10b981" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Governance Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Governance Reviews</CardTitle>
            <CardDescription>Review status distribution</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm">Pending</span>
              <Badge variant="outline" className="bg-yellow-50">
                {metrics.governance.pending}
              </Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">Approved</span>
              <Badge variant="outline" className="bg-green-50">
                {metrics.governance.approved}
              </Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">Rejected</span>
              <Badge variant="outline" className="bg-red-50">
                {metrics.governance.rejected}
              </Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">Escalated</span>
              <Badge variant="outline" className="bg-purple-50">
                {metrics.governance.escalated}
              </Badge>
            </div>
            <div className="border-t pt-3 flex justify-between items-center font-semibold">
              <span>Total</span>
              <span>{metrics.governance.total}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Session Metrics</CardTitle>
            <CardDescription>Session duration and frequency</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <h4 className="text-sm font-semibold mb-2">Last 24 Hours</h4>
              <div className="space-y-1 text-sm">
                <p>
                  Sessions: <span className="font-bold">{metrics.last_24_hours.total_sessions}</span>
                </p>
                <p>
                  Avg Duration:{' '}
                  <span className="font-bold">{metrics.last_24_hours.avg_session_duration}</span>
                </p>
              </div>
            </div>
            <div className="border-t pt-3">
              <h4 className="text-sm font-semibold mb-2">Last 7 Days</h4>
              <div className="space-y-1 text-sm">
                <p>
                  Sessions: <span className="font-bold">{metrics.last_7_days.total_sessions}</span>
                </p>
                <p>
                  Avg Duration:{' '}
                  <span className="font-bold">{metrics.last_7_days.avg_session_duration}</span>
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Last Updated */}
      <div className="text-xs text-gray-500 text-right">
        Last updated: {new Date(metrics.timestamp).toLocaleString()}
      </div>
    </div>
  );
}
