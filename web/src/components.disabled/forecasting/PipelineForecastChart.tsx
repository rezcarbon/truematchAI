'use client';

import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ForecastData {
  position_id: string;
  position_title: string;
  forecasted_fill_date: string;
  estimated_days_to_fill: number;
  confidence: number;
  bottleneck_stage: string;
  recommendations: string[];
}

interface ChartDataPoint {
  position: string;
  daysToFill: number;
  confidence: number;
  positionId: string;
}

interface PipelineForecastChartProps {
  forecasts: ForecastData[];
  isLoading?: boolean;
  onPositionClick?: (positionId: string) => void;
}

export function PipelineForecastChart({ forecasts, isLoading = false, onPositionClick }: PipelineForecastChartProps) {
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);

  useEffect(() => {
    if (forecasts && forecasts.length > 0) {
      const data = forecasts.map((f) => ({
        position: f.position_title.substring(0, 15),
        daysToFill: f.estimated_days_to_fill,
        confidence: Math.round(f.confidence * 100),
        positionId: f.position_id,
      }));
      setChartData(data);
    }
  }, [forecasts]);

  if (isLoading) {
    return <div className="animate-pulse h-80 bg-gray-200 rounded" />;
  }

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Forecast Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert>
            <AlertDescription>No forecasts available. Add open positions to generate forecasts.</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pipeline Forecast - Days to Fill</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="position" />
            <YAxis label={{ value: 'Days to Fill', angle: -90, position: 'insideLeft' }} />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload?.[0]) {
                  return (
                    <div className="bg-white p-2 border border-gray-300 rounded shadow-lg">
                      <p className="font-semibold">{payload[0].payload.position}</p>
                      <p className="text-sm">Days: {payload[0].value}</p>
                      <p className="text-sm">Confidence: {payload[0].payload.confidence}%</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />
            <Bar dataKey="daysToFill" fill="#3b82f6" onClick={(e: ChartDataPoint) => onPositionClick?.(e.positionId)} />
          </BarChart>
        </ResponsiveContainer>

        <div className="mt-6 grid grid-cols-2 gap-4">
          {forecasts.map((f) => (
            <div
              key={f.position_id}
              className="p-3 border rounded cursor-pointer hover:bg-gray-50"
              onClick={() => onPositionClick?.(f.position_id)}
            >
              <div className="text-sm font-semibold text-gray-900">{f.position_title}</div>
              <div className="text-xs text-gray-600 mt-1">
                Est. Fill: {f.estimated_days_to_fill} days
              </div>
              <div className="text-xs text-gray-600">
                Confidence: {Math.round(f.confidence * 100)}%
              </div>
              <div className="text-xs text-red-600 font-medium mt-1">
                Bottleneck: {f.bottleneck_stage}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
