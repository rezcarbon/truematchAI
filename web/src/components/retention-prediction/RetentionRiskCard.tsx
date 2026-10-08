'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, TrendingDown, Calendar, Users } from 'lucide-react';

interface AttritionSignal {
  signal: string;
  strength: number;
}

interface RetentionRiskCardProps {
  candidateName: string;
  positionTitle: string;
  riskScore: number; // 0-1
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  detectedSignals: AttritionSignal[];
  primaryRiskFactor: string;
  daysToAttrition: number;
  confidence: number;
  hireDate: string;
  hasIntervention: boolean;
  onViewInterventions?: () => void;
}

export function RetentionRiskCard({
  candidateName,
  positionTitle,
  riskScore,
  riskLevel,
  detectedSignals,
  primaryRiskFactor,
  daysToAttrition,
  confidence,
  hireDate,
  hasIntervention,
  onViewInterventions,
}: RetentionRiskCardProps) {
  const riskColors = {
    low: { bg: 'bg-green-50', border: 'border-green-200', badge: 'bg-green-100 text-green-800', text: 'text-green-700' },
    medium: { bg: 'bg-yellow-50', border: 'border-yellow-200', badge: 'bg-yellow-100 text-yellow-800', text: 'text-yellow-700' },
    high: { bg: 'bg-orange-50', border: 'border-orange-200', badge: 'bg-orange-100 text-orange-800', text: 'text-orange-700' },
    critical: { bg: 'bg-red-50', border: 'border-red-200', badge: 'bg-red-100 text-red-800', text: 'text-red-700' },
  };

  const colors = riskColors[riskLevel];
  const riskPercentage = Math.round(riskScore * 100);

  return (
    <Card className={`w-full border-2 ${colors.border}`}>
      <CardHeader className={`pb-3 ${colors.bg}`}>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-lg text-gray-900">{candidateName}</CardTitle>
            <div className="text-sm text-gray-600 mt-1">{positionTitle}</div>
          </div>
          <Badge className={colors.badge}>
            {riskLevel.toUpperCase()}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Risk Score Visualization */}
        <div className="space-y-2">
          <div className="flex justify-between items-end">
            <div className="text-sm font-semibold text-gray-700">Attrition Risk</div>
            <div className="text-2xl font-bold" style={{ color: riskLevel === 'low' ? '#16a34a' : riskLevel === 'medium' ? '#ca8a04' : riskLevel === 'high' ? '#ea580c' : '#dc2626' }}>
              {riskPercentage}%
            </div>
          </div>

          {/* Risk Bar */}
          <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all ${
                riskLevel === 'low' ? 'bg-green-500' :
                riskLevel === 'medium' ? 'bg-yellow-500' :
                riskLevel === 'high' ? 'bg-orange-500' :
                'bg-red-500'
              }`}
              style={{ width: `${riskPercentage}%` }}
            />
          </div>

          <div className="text-xs text-gray-600 text-right">
            Confidence: {Math.round(confidence * 100)}%
          </div>
        </div>

        {/* Detected Signals */}
        {detectedSignals.length > 0 && (
          <div className="border-t pt-3">
            <div className="text-xs font-semibold text-gray-700 uppercase mb-2 flex items-center gap-1">
              <AlertTriangle size={14} />
              Detected Signals
            </div>
            <div className="space-y-2">
              {detectedSignals.slice(0, 3).map((signal, idx) => (
                <div key={idx} className="flex items-center justify-between text-sm">
                  <span className="text-gray-700">{signal.signal}</span>
                  <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-red-500"
                      style={{ width: `${signal.strength * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Key Metrics */}
        <div className="grid grid-cols-3 gap-2 border-t pt-3 text-center text-sm">
          <div>
            <div className="text-xs text-gray-600 font-semibold">Primary Risk</div>
            <div className="text-xs font-bold text-gray-900 mt-1 line-clamp-2">{primaryRiskFactor}</div>
          </div>
          <div>
            <div className="text-xs text-gray-600 font-semibold flex items-center justify-center gap-1">
              <Calendar size={12} /> Timeline
            </div>
            <div className="text-lg font-bold text-gray-900 mt-1">{daysToAttrition}</div>
            <div className="text-xs text-gray-600">days</div>
          </div>
          <div>
            <div className="text-xs text-gray-600 font-semibold">Tenure</div>
            <div className="text-xs text-gray-900 mt-1">{Math.floor((Date.now() - new Date(hireDate).getTime()) / (1000 * 60 * 60 * 24))} days</div>
          </div>
        </div>

        {/* Intervention Status */}
        {hasIntervention && (
          <div className="p-2 bg-blue-50 border border-blue-200 rounded text-sm font-semibold text-blue-800 flex items-center gap-2">
            <CheckCircle size={16} />
            Intervention in Progress
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 pt-2 border-t">
          <button
            onClick={onViewInterventions}
            className="flex-1 px-3 py-2 bg-blue-600 text-white rounded text-sm font-semibold hover:bg-blue-700 transition-colors"
          >
            View Interventions
          </button>
          <button className="flex-1 px-3 py-2 border border-gray-300 text-gray-900 rounded text-sm font-semibold hover:bg-gray-50 transition-colors">
            Details
          </button>
        </div>
      </CardContent>
    </Card>
  );
}
