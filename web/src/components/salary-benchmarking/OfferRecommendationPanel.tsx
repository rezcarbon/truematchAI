'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, AlertCircle, CheckCircle, Target } from 'lucide-react';

interface OfferRecommendationPanelProps {
  candidateName: string;
  positionTitle: string;
  recommendedSalary: number;
  minAcceptable: number;
  maxAcceptable: number;
  winLikelihood: number;
  negotiationBuffer: number;
  justification: string;
  candidates?: string[];
  onMakeOffer?: () => void;
}

export function OfferRecommendationPanel({
  candidateName,
  positionTitle,
  recommendedSalary,
  minAcceptable,
  maxAcceptable,
  winLikelihood,
  negotiationBuffer,
  justification,
  candidates,
  onMakeOffer,
}: OfferRecommendationPanelProps) {
  const percentageOfMax = Math.round(((recommendedSalary - minAcceptable) / (maxAcceptable - minAcceptable)) * 100);
  const successChance = Math.round(winLikelihood * 100);
  const confidenceLevel = successChance > 80 ? 'Very High' : successChance > 60 ? 'High' : successChance > 40 ? 'Moderate' : 'Low';

  return (
    <Card className="w-full border-2 border-blue-200">
      <CardHeader className="bg-blue-50 pb-3">
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-lg text-gray-900">{candidateName}</CardTitle>
            <div className="text-sm text-gray-600 mt-1">{positionTitle}</div>
          </div>
          <Badge className={`${
            successChance > 75 ? 'bg-green-100 text-green-800' :
            successChance > 50 ? 'bg-blue-100 text-blue-800' :
            'bg-orange-100 text-orange-800'
          }`}>
            {successChance}% Win Likelihood
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Recommended Offer */}
        <div className="space-y-2">
          <div className="text-sm font-semibold text-gray-700">Recommended Offer</div>
          <div className="text-4xl font-bold text-blue-600">
            ${(recommendedSalary / 1000).toFixed(0)}K
          </div>
          <div className="text-xs text-gray-600">
            Base annual salary
          </div>
        </div>

        {/* Range Context */}
        <div className="space-y-2">
          <div className="text-sm font-semibold text-gray-700">Negotiation Range</div>
          <div className="space-y-1">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Minimum Acceptable:</span>
              <span className="font-semibold text-gray-900">${(minAcceptable / 1000).toFixed(1)}K</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Maximum Acceptable:</span>
              <span className="font-semibold text-gray-900">${(maxAcceptable / 1000).toFixed(1)}K</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Buffer:</span>
              <span className="font-semibold text-green-600">${(negotiationBuffer / 1000).toFixed(1)}K</span>
            </div>
          </div>

          {/* Range Bar */}
          <div className="mt-3 relative h-8 bg-gray-100 rounded-lg overflow-hidden">
            {/* Acceptable range */}
            <div
              className="absolute top-0 bottom-0 bg-green-100"
              style={{
                left: '0%',
                right: '0%',
              }}
            />

            {/* Recommended point */}
            <div
              className="absolute top-0 bottom-0 w-1 bg-blue-600"
              style={{ left: `${percentageOfMax}%` }}
            />
          </div>
        </div>

        {/* Success Confidence */}
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start gap-2">
            <Target size={18} className="text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-blue-900">Acceptance Confidence: {confidenceLevel}</div>
              <div className="text-sm text-blue-800 mt-1">{successChance}% likelihood of offer acceptance at recommended salary</div>
            </div>
          </div>
        </div>

        {/* Justification */}
        <div className="space-y-2">
          <div className="text-sm font-semibold text-gray-700">Recommendation Justification</div>
          <p className="text-sm text-gray-700 leading-relaxed">{justification}</p>
        </div>

        {/* Comparable Candidates */}
        {candidates && candidates.length > 0 && (
          <div className="space-y-2 border-t pt-3">
            <div className="text-sm font-semibold text-gray-700">Comparable Candidates</div>
            <div className="space-y-1">
              {candidates.map((candidate, idx) => (
                <div key={idx} className="text-sm text-gray-600 flex items-center gap-2">
                  <CheckCircle size={14} className="text-gray-400" />
                  {candidate}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Risk Alert */}
        {successChance < 60 && (
          <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg flex items-start gap-2">
            <AlertCircle size={18} className="text-orange-600 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-orange-900 text-sm">Below Ideal Confidence</div>
              <div className="text-sm text-orange-800 mt-1">Consider adding signing bonus or additional benefits to increase acceptance likelihood.</div>
            </div>
          </div>
        )}

        {/* Action Button */}
        <button
          onClick={onMakeOffer}
          className="w-full mt-4 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold transition-colors flex items-center justify-center gap-2"
        >
          <CheckCircle size={18} />
          Generate Offer Letter
        </button>
      </CardContent>
    </Card>
  );
}
