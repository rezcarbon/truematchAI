'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Mail,
  Phone,
  Briefcase,
  Calendar,
  MapPin,
  FileText,
  ExternalLink,
  X,
  MessageSquare,
} from 'lucide-react';
import { HorizontalPipeline } from './HorizontalPipeline';
import { TimelineView } from './TimelineView';
import { FeedbackSection } from './FeedbackSection';
import { InterviewPrepWidget } from './InterviewPrepWidget';
import { OfferDetailsCard } from './OfferDetailsCard';
import { cn } from '@/lib/utils';
import type { HorizontalPipeline as Pipeline } from './types';

interface ApplicationDetailModalProps {
  application: Pipeline.Application;
  onClose: () => void;
  onStatusChange?: (newStatus: Pipeline.ApplicationStatus) => void;
  onScheduleInterview?: () => void;
  onAddFeedback?: (feedback: Omit<Pipeline.Feedback, 'id' | 'date'>) => void;
  onGeneratePrepGuide?: (
    positionTitle: string,
    candidateName: string
  ) => Promise<Pipeline.InterviewPrepGuide>;
  isOpen: boolean;
}

const getStatusColor = (status: Pipeline.ApplicationStatus) => {
  const colors = {
    applied: 'bg-blue-100 text-blue-800',
    screened: 'bg-purple-100 text-purple-800',
    interviewed: 'bg-indigo-100 text-indigo-800',
    offer: 'bg-yellow-100 text-yellow-800',
    closed: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
  };
  return colors[status] || colors.applied;
};

export function ApplicationDetailModal({
  application,
  onClose,
  onStatusChange,
  onScheduleInterview,
  onAddFeedback,
  onGeneratePrepGuide,
  isOpen,
}: ApplicationDetailModalProps) {
  const [selectedTab, setSelectedTab] = useState('overview');

  const applicationStatus: Pipeline.ApplicationStatus = application.status;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <DialogTitle className="text-2xl">
                {application.candidateName}
              </DialogTitle>
              <p className="text-sm text-muted-foreground mt-2">
                {application.positionTitle}
              </p>
            </div>
            <DialogClose className="rounded-md opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground">
              <X className="h-4 w-4" />
              <span className="sr-only">Close</span>
            </DialogClose>
          </div>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Pipeline Progress */}
          <div>
            <h3 className="text-sm font-semibold mb-3">Application Progress</h3>
            <HorizontalPipeline
              applicationStatus={{
                applicationId: application.id,
                currentStage: application.status,
                completedStages: [], // Calculate from timeline
                timestamp: new Date(),
              }}
            />
          </div>

          {/* Quick Info Grid */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-xs text-muted-foreground">Email</p>
                    <p className="text-xs font-medium truncate">
                      {application.candidateEmail}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-xs text-muted-foreground">Applied</p>
                    <p className="text-xs font-medium">
                      {new Date(application.appliedAt).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {application.location && (
              <Card>
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-xs text-muted-foreground">Location</p>
                      <p className="text-xs font-medium truncate">
                        {application.location}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-xs text-muted-foreground">Status</p>
                    <Badge
                      variant="outline"
                      className={cn('text-xs', getStatusColor(applicationStatus))}
                    >
                      {applicationStatus.replace('_', ' ')}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Tabs */}
          <Tabs value={selectedTab} onValueChange={setSelectedTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="timeline">Timeline</TabsTrigger>
              <TabsTrigger value="interviews">Interviews</TabsTrigger>
              <TabsTrigger value="feedback">Feedback</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-4">
              {/* Scores */}
              {(application.scores.keyword ||
                application.scores.semantic ||
                application.scores.capability) && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Evaluation Scores</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-3">
                      {application.scores.keyword && (
                        <div className="p-3 rounded-lg bg-blue-50">
                          <p className="text-xs text-muted-foreground">Keyword Match</p>
                          <p className="text-2xl font-bold text-blue-600 mt-1">
                            {application.scores.keyword}%
                          </p>
                        </div>
                      )}
                      {application.scores.semantic && (
                        <div className="p-3 rounded-lg bg-purple-50">
                          <p className="text-xs text-muted-foreground">Semantic Match</p>
                          <p className="text-2xl font-bold text-purple-600 mt-1">
                            {application.scores.semantic}%
                          </p>
                        </div>
                      )}
                      {application.scores.capability && (
                        <div className="p-3 rounded-lg bg-green-50">
                          <p className="text-xs text-muted-foreground">Capability</p>
                          <p className="text-2xl font-bold text-green-600 mt-1">
                            {application.scores.capability}%
                          </p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Tags and metadata */}
              {application.tags && application.tags.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Tags</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {application.tags.map(tag => (
                        <Badge key={tag} variant="secondary">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Links */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Profile Links</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {application.resumeUrl && (
                    <a
                      href={application.resumeUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-blue-600 hover:underline text-sm"
                    >
                      <FileText className="w-4 h-4" />
                      View Resume
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                  {application.linkedinUrl && (
                    <a
                      href={application.linkedinUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-blue-600 hover:underline text-sm"
                    >
                      <ExternalLink className="w-4 h-4" />
                      LinkedIn Profile
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </CardContent>
              </Card>

              {/* Interview Prep Widget */}
              {(applicationStatus === 'screened' ||
                applicationStatus === 'interviewed') && (
                <InterviewPrepWidget
                  positionTitle={application.positionTitle}
                  candidateName={application.candidateName}
                  onGeneratePrepGuide={onGeneratePrepGuide}
                />
              )}

              {/* Offer Details */}
              {application.offer && applicationStatus === 'offer' && (
                <OfferDetailsCard
                  offer={application.offer}
                  editable={true}
                />
              )}
            </TabsContent>

            {/* Timeline Tab */}
            <TabsContent value="timeline">
              <Card>
                <CardContent className="pt-4">
                  <TimelineView events={application.timeline} />
                </CardContent>
              </Card>
            </TabsContent>

            {/* Interviews Tab */}
            <TabsContent value="interviews" className="space-y-4">
              {application.interviews.length === 0 ? (
                <Card>
                  <CardContent className="pt-8 text-center">
                    <MessageSquare className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                    <p className="text-muted-foreground text-sm">No interviews scheduled yet</p>
                    {onScheduleInterview && (
                      <Button
                        size="sm"
                        className="mt-4"
                        onClick={onScheduleInterview}
                      >
                        Schedule Interview
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ) : (
                application.interviews.map(interview => (
                  <Card key={interview.id}>
                    <CardContent className="pt-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <p className="font-medium text-sm">
                          {interview.type.charAt(0).toUpperCase() + interview.type.slice(1)} Interview
                        </p>
                        <Badge variant="outline" className="text-xs">
                          {new Date(interview.date).toLocaleDateString()}
                        </Badge>
                      </div>
                      {interview.interviewer && (
                        <p className="text-sm text-muted-foreground">
                          Interviewer: {interview.interviewer}
                        </p>
                      )}
                      {interview.notes && (
                        <p className="text-sm text-foreground mt-2">{interview.notes}</p>
                      )}
                      {interview.feedback && (
                        <div className="p-2 bg-blue-50 rounded text-sm">
                          <p className="font-medium text-xs text-blue-900 mb-1">Feedback:</p>
                          <p className="text-blue-800">{interview.feedback}</p>
                        </div>
                      )}
                      {interview.score && (
                        <p className="text-sm">
                          Score: <span className="font-bold text-lg">{interview.score}/10</span>
                        </p>
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </TabsContent>

            {/* Feedback Tab */}
            <TabsContent value="feedback">
              <Card>
                <CardContent className="pt-4">
                  <FeedbackSection
                    feedback={application.feedback}
                    onAddFeedback={onAddFeedback}
                    editable={true}
                  />
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Action Buttons */}
          <div className="flex gap-2 pt-4 border-t">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
            {onScheduleInterview && (
              <Button
                onClick={onScheduleInterview}
                className="flex-1"
              >
                <Calendar className="w-4 h-4 mr-2" />
                Schedule Interview
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
