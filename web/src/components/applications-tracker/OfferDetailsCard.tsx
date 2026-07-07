'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DollarSign,
  Calendar,
  Clock,
  FileText,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { HorizontalPipeline as Pipeline } from './types';

interface OfferDetailsCardProps {
  offer: Pipeline.OfferDetails;
  onAccept?: () => void;
  onReject?: () => void;
  editable?: boolean;
}

export function OfferDetailsCard({
  offer,
  onAccept,
  onReject,
  editable = false,
}: OfferDetailsCardProps) {
  const daysUntilExpiry = offer.expiresAt
    ? Math.ceil(
      (new Date(offer.expiresAt).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
    )
    : null;

  const isExpired = daysUntilExpiry !== null && daysUntilExpiry <= 0;

  return (
    <Card
      className={cn(
        'border-2',
        offer.accepted ? 'border-green-500 bg-green-50' : 'border-yellow-500 bg-yellow-50'
      )}
    >
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">Offer Details</CardTitle>
            {offer.expiresAt && (
              <p className="text-sm text-muted-foreground mt-1">
                {daysUntilExpiry && daysUntilExpiry > 0
                  ? `Expires in ${daysUntilExpiry} days`
                  : 'Offer expired'}
              </p>
            )}
          </div>
          {offer.accepted && (
            <Badge className="bg-green-600">
              <CheckCircle2 className="w-3 h-3 mr-1" />
              Accepted
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Salary Information */}
        {(offer.salary || offer.salaryRange) && (
          <div className="bg-white p-3 rounded-lg border">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-sm text-muted-foreground">Base Salary</p>
                <p className="text-2xl font-bold text-green-600 mt-1">
                  {offer.salary
                    ? `$${offer.salary.toLocaleString()}`
                    : `$${offer.salaryRange?.min.toLocaleString()}-$${offer.salaryRange?.max.toLocaleString()}`}
                </p>
              </div>
              <DollarSign className="w-5 h-5 text-green-600 mt-1" />
            </div>
          </div>
        )}

        {/* Start Date */}
        {offer.startDate && (
          <div className="flex items-center gap-3 p-3 bg-white rounded-lg border">
            <Calendar className="w-5 h-5 text-blue-600 flex-shrink-0" />
            <div>
              <p className="text-sm text-muted-foreground">Start Date</p>
              <p className="font-medium">
                {new Date(offer.startDate).toLocaleDateString('en-US', {
                  month: 'long',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </p>
            </div>
          </div>
        )}

        {/* Benefits */}
        {offer.benefits && offer.benefits.length > 0 && (
          <div className="p-3 bg-white rounded-lg border">
            <p className="text-sm font-medium mb-2">Benefits Package</p>
            <ul className="space-y-1">
              {offer.benefits.map((benefit, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-foreground">
                  <span className="text-green-600 font-bold">✓</span>
                  <span>{benefit}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Notes */}
        {offer.notes && (
          <div className="p-3 bg-white rounded-lg border">
            <div className="flex gap-2 items-start">
              <FileText className="w-4 h-4 text-gray-600 mt-1 flex-shrink-0" />
              <div>
                <p className="text-sm text-muted-foreground mb-1">Additional Notes</p>
                <p className="text-sm text-foreground">{offer.notes}</p>
              </div>
            </div>
          </div>
        )}

        {/* Expiry warning */}
        {isExpired && (
          <div className="p-3 bg-red-100 border border-red-300 rounded-lg">
            <p className="text-sm text-red-800 font-medium">
              This offer has expired. Please contact the hiring manager.
            </p>
          </div>
        )}

        {/* Action buttons */}
        {!offer.accepted && !isExpired && (onAccept || onReject) && (
          <div className="flex gap-2 pt-2 border-t">
            {onAccept && (
              <Button
                size="sm"
                className="flex-1 bg-green-600 hover:bg-green-700"
                onClick={onAccept}
              >
                <CheckCircle2 className="w-4 h-4 mr-2" />
                Accept Offer
              </Button>
            )}
            {onReject && (
              <Button
                size="sm"
                variant="outline"
                className="flex-1"
                onClick={onReject}
              >
                <XCircle className="w-4 h-4 mr-2" />
                Decline
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
