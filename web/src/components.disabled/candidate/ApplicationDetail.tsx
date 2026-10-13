'use client';

import React, { useMemo, useCallback } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Building2,
  MapPin,
  DollarSign,
  Briefcase,
  Calendar,
  FileText,
  MessageSquare,
  Gift,
  BookOpen,
  ExternalLink,
  X,
} from 'lucide-react';
import { TimelineView, type TimelineEvent } from './TimelineView';
import type { ApplicationStage } from './ApplicationPipeline';

export interface ApplicationDetailProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  applicationId: string;
  jobTitle: string;
  company: string;
  stage: ApplicationStage;
  appliedDate: string;
  jobDescription?: string;
  salary?: {
    min: number;
    max: number;
    currency: string;
  };
  location?: string;
  companyWebsite?: string;
  applicationUrl?: string;
  feedback?: {
    message: string;
    from: string;
    date: string;
  };
  offer?: {
    details: string;
    salary: string;
    benefits: string[];
    deadline: string;
  };
  timelineEvents: TimelineEvent[];
  onInterviewPrepClick?: (applicationId: string) => void;
  className?: string;
}

export const ApplicationDetail: React.FC<ApplicationDetailProps> = React.memo(
  ({
    open,
    onOpenChange,
    applicationId,
    jobTitle,
    company,
    stage,
    appliedDate,
    jobDescription,
    salary,
    location,
    companyWebsite,
    applicationUrl,
    feedback,
    offer,
    timelineEvents,
    onInterviewPrepClick,
    className = '',
  }) => {
    const handleClose = useCallback(() => {
      onOpenChange(false);
    }, [onOpenChange]);

    const handleInterviewPrepClick = useCallback(() => {
      onInterviewPrepClick?.(applicationId);
    }, [applicationId, onInterviewPrepClick]);

    const stageColor = useMemo(() => {
      const colors: Record<ApplicationStage, string> = {
        applied: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
        screened: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
        interviewed: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
        offer: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
        closed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      };
      return colors[stage];
    }, [stage]);

    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className={`max-w-3xl max-h-[90vh] overflow-y-auto ${className}`}>
          <DialogHeader>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <DialogTitle className="text-2xl">{jobTitle}</DialogTitle>
                <DialogDescription className="text-base mt-1 flex items-center gap-2">
                  <Building2 className="w-4 h-4" />
                  {company}
                </DialogDescription>
              </div>
              <Badge variant="secondary" className={`whitespace-nowrap ${stageColor}`}>
                {stage.charAt(0).toUpperCase() + stage.slice(1)}
              </Badge>
            </div>
          </DialogHeader>

          <div className="space-y-6">
            {/* Job Summary Card */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Job Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  {location && (
                    <div className="flex items-start gap-3">
                      <MapPin className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-muted-foreground">Location</p>
                        <p className="text-sm font-medium">{location}</p>
                      </div>
                    </div>
                  )}

                  {salary && (
                    <div className="flex items-start gap-3">
                      <DollarSign className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-muted-foreground">Salary Range</p>
                        <p className="text-sm font-medium">
                          {salary.currency} {salary.min.toLocaleString()} -{' '}
                          {salary.max.toLocaleString()}
                        </p>
                      </div>
                    </div>
                  )}

                  <div className="flex items-start gap-3">
                    <Calendar className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-muted-foreground">Applied</p>
                      <p className="text-sm font-medium">
                        {new Date(appliedDate).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                        })}
                      </p>
                    </div>
                  </div>

                  {companyWebsite && (
                    <div className="flex items-start gap-3">
                      <ExternalLink className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-muted-foreground">Company</p>
                        <Button
                          variant="link"
                          size="sm"
                          className="px-0 h-auto text-sm font-medium"
                          asChild
                        >
                          <a
                            href={companyWebsite}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            Visit Website
                          </a>
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Tabs for detailed content */}
            <Tabs defaultValue="overview" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="timeline">Timeline</TabsTrigger>
                {feedback && <TabsTrigger value="feedback">Feedback</TabsTrigger>}
                {offer && <TabsTrigger value="offer">Offer</TabsTrigger>}
              </TabsList>

              {/* Overview Tab */}
              <TabsContent value="overview" className="space-y-4">
                {jobDescription && (
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        Job Description
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        <p className="whitespace-pre-wrap text-sm text-muted-foreground">
                          {jobDescription}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Action buttons */}
                <div className="flex gap-2 pt-4">
                  {stage === 'interviewed' && (
                    <Button onClick={handleInterviewPrepClick} className="flex-1">
                      <BookOpen className="w-4 h-4 mr-2" />
                      Interview Preparation
                    </Button>
                  )}
                  {applicationUrl && (
                    <Button variant="outline" className="flex-1" asChild>
                      <a href={applicationUrl} target="_blank" rel="noopener noreferrer">
                        View on Portal
                        <ExternalLink className="w-4 h-4 ml-2" />
                      </a>
                    </Button>
                  )}
                </div>
              </TabsContent>

              {/* Timeline Tab */}
              <TabsContent value="timeline" className="space-y-4">
                {timelineEvents.length > 0 ? (
                  <TimelineView
                    events={timelineEvents}
                    title="Event History"
                  />
                ) : (
                  <Card>
                    <CardContent className="py-8 text-center">
                      <p className="text-sm text-muted-foreground">
                        No events recorded yet
                      </p>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              {/* Feedback Tab */}
              {feedback && (
                <TabsContent value="feedback" className="space-y-4">
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <MessageSquare className="w-4 h-4" />
                        Feedback
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="p-3 bg-secondary/50 rounded-lg">
                        <p className="text-sm whitespace-pre-wrap">
                          {feedback.message}
                        </p>
                      </div>
                      <div className="flex items-center justify-between text-xs text-muted-foreground pt-2">
                        <span>From: {feedback.from}</span>
                        <span>
                          {new Date(feedback.date).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                          })}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              )}

              {/* Offer Tab */}
              {offer && (
                <TabsContent value="offer" className="space-y-4">
                  <Card className="border-green-200 dark:border-green-800">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2 text-green-700 dark:text-green-200">
                        <Gift className="w-4 h-4" />
                        Offer Details
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="p-3 bg-green-50 dark:bg-green-950 rounded-lg">
                        <p className="text-sm whitespace-pre-wrap text-green-900 dark:text-green-200">
                          {offer.details}
                        </p>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs text-muted-foreground">Salary</p>
                          <p className="text-lg font-semibold text-green-700 dark:text-green-200">
                            {offer.salary}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Response Deadline</p>
                          <p className="text-sm font-medium">
                            {new Date(offer.deadline).toLocaleDateString('en-US', {
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric',
                            })}
                          </p>
                        </div>
                      </div>

                      {offer.benefits.length > 0 && (
                        <div>
                          <p className="text-sm font-semibold mb-2">Benefits</p>
                          <ul className="space-y-1">
                            {offer.benefits.map((benefit, index) => (
                              <li
                                key={index}
                                className="text-sm text-muted-foreground flex items-start gap-2"
                              >
                                <span className="text-green-600 dark:text-green-400 mt-1">
                                  •
                                </span>
                                {benefit}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              )}
            </Tabs>
          </div>
        </DialogContent>
      </Dialog>
    );
  }
);

ApplicationDetail.displayName = 'ApplicationDetail';
