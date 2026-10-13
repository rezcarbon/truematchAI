'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, TrendingUp, Calendar } from 'lucide-react';

interface PositionForecastCardProps {
  positionTitle: string;
  positionId: string;
  estimatedDaysToFill: number;
  forecastedFillDate: string;
  confidence: number;
  bottleneckStage: string;
  recommendations: string[];
  applicationCount: number;
}

export function PositionForecastCard({
  positionTitle,
  positionId,
  estimatedDaysToFill,
  forecastedFillDate,
  confidence,
  bottleneckStage,
  recommendations,
  applicationCount,
}: PositionForecastCardProps) {
  const confidenceColor = confidence > 0.8 ? 'bg-green-100 text-green-800' : confidence > 0.6 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800';
  const bottleneckColor = bottleneckStage === 'screening' ? 'bg-blue-100' : bottleneckStage === 'interview' ? 'bg-purple-100' : 'bg-orange-100';

  return (
    <Card className="w-full hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <CardTitle className="text-lg text-gray-900">{positionTitle}</CardTitle>
          <Badge className={confidenceColor}>
            {Math.round(confidence * 100)}% Confidence
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Key Metrics */}
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-xs text-gray-600 font-semibold uppercase">Days to Fill</div>
            <div className="text-2xl font-bold text-blue-600">{estimatedDaysToFill}</div>
          </div>
          <div>
            <div className="text-xs text-gray-600 font-semibold uppercase">Applications</div>
            <div className="text-2xl font-bold text-green-600">{applicationCount}</div>
          </div>
          <div>
            <div className="text-xs text-gray-600 font-semibold uppercase">Fill Date</div>
            <div className="text-sm font-semibold text-gray-900">
              {new Date(forecastedFillDate).toLocaleDateString()}
            </div>
          </div>
        </div>

        {/* Bottleneck Alert */}
        <div className={`p-3 rounded-lg ${bottleneckColor}`}>
          <div className="flex items-center gap-2">
            <AlertCircle size={16} />
            <div className="text-sm font-semibold capitalize">
              Bottleneck: {bottleneckStage} Stage
            </div>
          </div>
        </div>

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div className="border-t pt-3">
            <div className="text-xs font-semibold text-gray-700 uppercase mb-2 flex items-center gap-1">
              <TrendingUp size={14} />
              Recommendations
            </div>
            <ul className="space-y-2">
              {recommendations.slice(0, 3).map((rec, idx) => (
                <li key={idx} className="text-sm text-gray-700 flex gap-2">
                  <span className="text-blue-600 font-bold">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Action Button */}
        <button className="w-full mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-semibold transition-colors">
          View Details
        </button>
      </CardContent>
    </Card>
  );
}
