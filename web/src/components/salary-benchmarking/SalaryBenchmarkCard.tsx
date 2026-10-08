'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, DollarSign, MapPin } from 'lucide-react';

interface SalaryBenchmarkCardProps {
  roleTitle: string;
  level: string;
  location: string;
  minSalary: number;
  midpointSalary: number;
  maxSalary: number;
  percentile: number;
  lastUpdated: string;
}

export function SalaryBenchmarkCard({
  roleTitle,
  level,
  location,
  minSalary,
  midpointSalary,
  maxSalary,
  percentile,
  lastUpdated,
}: SalaryBenchmarkCardProps) {
  const percentileColor = percentile >= 75 ? 'bg-green-100 text-green-800' : percentile >= 50 ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800';

  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-lg text-gray-900">{roleTitle}</CardTitle>
            <div className="flex gap-2 mt-2">
              <Badge variant="outline">{level}</Badge>
              <Badge variant="secondary" className="flex gap-1">
                <MapPin size={12} />
                {location}
              </Badge>
            </div>
          </div>
          <Badge className={percentileColor}>
            {percentile}th percentile
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Salary Range Visualization */}
        <div className="space-y-2">
          <div className="text-xs font-semibold text-gray-700 uppercase">Market Salary Range</div>

          {/* Range Bar */}
          <div className="relative h-8 bg-gray-100 rounded-lg overflow-hidden">
            {/* Min to Max background */}
            <div className="absolute inset-0 flex">
              <div className="flex-1 bg-gradient-to-r from-blue-100 to-blue-200" />
            </div>

            {/* Midpoint indicator */}
            <div
              className="absolute top-0 bottom-0 w-1 bg-blue-600"
              style={{ left: `${((midpointSalary - minSalary) / (maxSalary - minSalary)) * 100}%` }}
            />
          </div>

          {/* Salary labels */}
          <div className="flex justify-between text-sm font-semibold text-gray-700">
            <span>${(minSalary / 1000).toFixed(0)}K</span>
            <span className="text-blue-600">${(midpointSalary / 1000).toFixed(0)}K (Midpoint)</span>
            <span>${(maxSalary / 1000).toFixed(0)}K</span>
          </div>
        </div>

        {/* Salary Breakdown */}
        <div className="grid grid-cols-3 gap-3 border-t pt-3">
          <div>
            <div className="text-xs text-gray-600">Min Salary</div>
            <div className="text-lg font-bold text-green-600">${(minSalary / 1000).toFixed(1)}K</div>
          </div>
          <div>
            <div className="text-xs text-gray-600">Mid Salary</div>
            <div className="text-lg font-bold text-blue-600">${(midpointSalary / 1000).toFixed(1)}K</div>
          </div>
          <div>
            <div className="text-xs text-gray-600">Max Salary</div>
            <div className="text-lg font-bold text-orange-600">${(maxSalary / 1000).toFixed(1)}K</div>
          </div>
        </div>

        {/* Last Updated */}
        <div className="text-xs text-gray-500 text-right">
          Last updated: {new Date(lastUpdated).toLocaleDateString()}
        </div>
      </CardContent>
    </Card>
  );
}
