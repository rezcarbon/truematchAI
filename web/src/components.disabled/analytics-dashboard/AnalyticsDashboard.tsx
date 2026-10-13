'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Download, Calendar, TrendingUp, Users, Clock, Target } from 'lucide-react';

interface DashboardMetrics {
  totalPositions: number;
  activeApplications: number;
  avgTimeToFill: number;
  offerAcceptanceRate: number;
  retentionRate: number;
  avgSalaryOfferDeviation: number;
  hiringVelocityTrend: Array<{ month: string; positions: number }>;
  retentionByTenure: Array<{ tenureMonths: number; retentionRate: number }>;
  interviewQualityScores: Array<{ week: string; score: number }>;
  salaryAcceptanceCorrelation: Array<{ percentile: number; acceptanceRate: number }>;
}

interface AnalyticsDashboardProps {
  metrics: DashboardMetrics;
  dateRange?: { start: string; end: string };
  isLoading?: boolean;
  onExport?: () => void;
  onDateRangeChange?: (start: string, end: string) => void;
}

export function AnalyticsDashboard({
  metrics,
  dateRange,
  isLoading = false,
  onExport,
  onDateRangeChange,
}: AnalyticsDashboardProps) {
  const [exportFormat, setExportFormat] = useState<'pdf' | 'csv'>('pdf');

  if (isLoading) {
    return <div className="grid grid-cols-4 gap-4">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="h-32 bg-gray-200 rounded animate-pulse" />
      ))}
    </div>;
  }

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">
            {dateRange && `${dateRange.start} to ${dateRange.end}`}
          </p>
        </div>
        <div className="flex gap-2">
          <select
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value as 'pdf' | 'csv')}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          >
            <option value="pdf">PDF</option>
            <option value="csv">CSV</option>
          </select>
          <button
            onClick={onExport}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold"
          >
            <Download size={18} />
            Export
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Card>
          <CardContent className="pt-6 text-center">
            <Target size={24} className="mx-auto text-blue-600 mb-2" />
            <div className="text-3xl font-bold text-gray-900">{metrics.totalPositions}</div>
            <div className="text-xs text-gray-600 mt-1">Open Positions</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6 text-center">
            <Users size={24} className="mx-auto text-green-600 mb-2" />
            <div className="text-3xl font-bold text-gray-900">{metrics.activeApplications}</div>
            <div className="text-xs text-gray-600 mt-1">Active Apps</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6 text-center">
            <Clock size={24} className="mx-auto text-orange-600 mb-2" />
            <div className="text-3xl font-bold text-gray-900">{metrics.avgTimeToFill}</div>
            <div className="text-xs text-gray-600 mt-1">Avg Days to Fill</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6 text-center">
            <TrendingUp size={24} className="mx-auto text-purple-600 mb-2" />
            <div className="text-3xl font-bold text-gray-900">{Math.round(metrics.offerAcceptanceRate * 100)}%</div>
            <div className="text-xs text-gray-600 mt-1">Offer Accept Rate</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6 text-center">
            <Users size={24} className="mx-auto text-red-600 mb-2" />
            <div className="text-3xl font-bold text-gray-900">{Math.round(metrics.retentionRate * 100)}%</div>
            <div className="text-xs text-gray-600 mt-1">Retention Rate</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6 text-center">
            <TrendingUp size={24} className="mx-auto text-indigo-600 mb-2" />
            <div className="text-3xl font-bold text-gray-900">{Math.round(metrics.avgSalaryOfferDeviation)}%</div>
            <div className="text-xs text-gray-600 mt-1">Salary Deviation</div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hiring Velocity */}
        <Card>
          <CardHeader>
            <CardTitle>Hiring Velocity Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={metrics.hiringVelocityTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="positions" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Interview Quality */}
        <Card>
          <CardHeader>
            <CardTitle>Interview Quality Scores</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={metrics.interviewQualityScores}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="week" />
                <YAxis domain={[0, 5]} />
                <Tooltip />
                <Bar dataKey="score" fill="#10b981" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Retention by Tenure */}
        <Card>
          <CardHeader>
            <CardTitle>Retention by Tenure</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={metrics.retentionByTenure}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="tenureMonths" />
                <YAxis />
                <Tooltip formatter={(v) => `${Math.round(v as number * 100)}%`} />
                <Line type="monotone" dataKey="retentionRate" stroke="#f59e0b" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Salary vs Acceptance */}
        <Card>
          <CardHeader>
            <CardTitle>Salary Percentile vs Acceptance</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={metrics.salaryAcceptanceCorrelation}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="percentile" />
                <YAxis />
                <Tooltip formatter={(v) => `${Math.round(v as number * 100)}%`} />
                <Line type="monotone" dataKey="acceptanceRate" stroke="#8b5cf6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Insights */}
      <Card>
        <CardHeader>
          <CardTitle>Key Insights</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="text-sm font-semibold text-blue-900">📊 Hiring Performance</div>
            <p className="text-sm text-blue-800 mt-1">Average time to fill decreased by 15% this month, indicating improved recruiter efficiency.</p>
          </div>
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="text-sm font-semibold text-green-900">✅ Offer Acceptance</div>
            <p className="text-sm text-green-800 mt-1">Offers at the 75th percentile have a 68% acceptance rate, up from 55% last month.</p>
          </div>
          <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
            <div className="text-sm font-semibold text-orange-900">⚠️ Retention Alert</div>
            <p className="text-sm text-orange-800 mt-1">New hires (0-3 months) show 12% higher attrition. Consider enhanced onboarding.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
