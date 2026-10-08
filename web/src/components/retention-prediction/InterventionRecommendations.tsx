'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, AlertCircle, Heart, Briefcase, DollarSign, Users } from 'lucide-react';

interface Intervention {
  intervention_type: string;
  priority: 'high' | 'medium' | 'low';
  target_audience: string;
  description: string;
  action_steps: string[];
  expected_impact: string;
  success_indicators: string[];
}

interface InterventionRecommendationsProps {
  candidateName: string;
  interventions: Intervention[];
  onMarkComplete?: (type: string) => void;
  onSchedule?: (type: string) => void;
}

const INTERVENTION_ICONS = {
  performance_coaching: <Briefcase size={20} />,
  role_discussion: <Users size={20} />,
  compensation_review: <DollarSign size={20} />,
  team_integration: <Users size={20} />,
  mentoring: <Heart size={20} />,
  regular_check_in: <CheckCircle size={20} />,
};

export function InterventionRecommendations({
  candidateName,
  interventions,
  onMarkComplete,
  onSchedule,
}: InterventionRecommendationsProps) {
  const [expandedIndex, setExpandedIndex] = useState<number>(0);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-lg text-gray-900">
          Manager Coaching Recommendations for {candidateName}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-3">
        {interventions.map((intervention, idx) => (
          <div
            key={idx}
            className="border rounded-lg overflow-hidden"
          >
            {/* Header */}
            <div
              onClick={() => setExpandedIndex(expandedIndex === idx ? -1 : idx)}
              className="p-4 bg-gray-50 cursor-pointer hover:bg-gray-100 flex items-center justify-between transition-colors"
            >
              <div className="flex items-center gap-3 flex-1">
                <div className="text-blue-600">
                  {INTERVENTION_ICONS[intervention.intervention_type as keyof typeof INTERVENTION_ICONS] || <CheckCircle />}
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-900 capitalize">
                    {intervention.intervention_type.replace(/_/g, ' ')}
                  </div>
                  <div className="text-sm text-gray-600">
                    Target: <span className="font-medium">{intervention.target_audience}</span>
                  </div>
                </div>
              </div>
              <Badge className={getPriorityColor(intervention.priority)}>
                {intervention.priority.toUpperCase()}
              </Badge>
            </div>

            {/* Expandable Content */}
            {expandedIndex === idx && (
              <div className="p-4 border-t bg-white space-y-4">
                {/* Description */}
                <div>
                  <div className="text-sm font-semibold text-gray-700 mb-2">Description</div>
                  <p className="text-sm text-gray-600">{intervention.description}</p>
                </div>

                {/* Action Steps */}
                <div>
                  <div className="text-sm font-semibold text-gray-700 mb-2">Action Steps</div>
                  <ol className="space-y-2">
                    {intervention.action_steps.map((step, stepIdx) => (
                      <li key={stepIdx} className="text-sm text-gray-600 flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-semibold text-xs">
                          {stepIdx + 1}
                        </span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ol>
                </div>

                {/* Expected Impact */}
                <div>
                  <div className="text-sm font-semibold text-gray-700 mb-2">Expected Impact</div>
                  <div className="p-3 bg-green-50 border border-green-200 rounded text-sm text-green-800">
                    {intervention.expected_impact}
                  </div>
                </div>

                {/* Success Indicators */}
                <div>
                  <div className="text-sm font-semibold text-gray-700 mb-2">Success Indicators</div>
                  <ul className="space-y-1">
                    {intervention.success_indicators.map((indicator, indIdx) => (
                      <li key={indIdx} className="text-sm text-gray-600 flex items-center gap-2">
                        <CheckCircle size={14} className="text-green-600" />
                        {indicator}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 pt-2 border-t">
                  <button
                    onClick={() => onSchedule?.(intervention.intervention_type)}
                    className="flex-1 px-3 py-2 bg-blue-600 text-white rounded text-sm font-semibold hover:bg-blue-700 transition-colors"
                  >
                    Schedule
                  </button>
                  <button
                    onClick={() => onMarkComplete?.(intervention.intervention_type)}
                    className="flex-1 px-3 py-2 border border-gray-300 text-gray-900 rounded text-sm font-semibold hover:bg-gray-50 transition-colors"
                  >
                    Mark Complete
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
