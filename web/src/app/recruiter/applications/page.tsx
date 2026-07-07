'use client';

import React, { useState, useEffect } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  HorizontalPipeline,
  ApplicationCard,
  ApplicationDetailModal,
  FeedbackSection,
  InterviewPrepWidget,
  TimelineView,
  OfferDetailsCard,
} from '@/components/applications-tracker';
import type { HorizontalPipeline as Pipeline } from '@/components/applications-tracker/types';
import {
  Search,
  Filter,
  Plus,
  BarChart3,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Mock data
const mockApplications: Pipeline.Application[] = [
  {
    id: 'app-1',
    positionId: 'pos-1',
    candidateName: 'John Smith',
    candidateEmail: 'john@example.com',
    positionTitle: 'Senior Backend Engineer',
    location: 'San Francisco, CA',
    status: 'interviewed',
    appliedAt: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000),
    source: 'LinkedIn',
    scores: { keyword: 85, semantic: 78, capability: 92 },
    tags: ['Backend', 'Python', 'AWS'],
    isUrgent: false,
    lastInterviewDate: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000),
    nextSteps: 'Send offer',
    resumeUrl: 'https://example.com/resume.pdf',
    linkedinUrl: 'https://linkedin.com/in/john',
    interviews: [
      {
        id: 'int-1',
        date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000),
        type: 'phone',
        interviewer: 'Jane Doe',
        notes: 'Great communication skills',
        feedback: 'Strong technical background',
        score: 9,
      },
    ],
    offer: undefined,
    timeline: [
      {
        id: 'evt-1',
        type: 'status_change',
        timestamp: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000),
        title: 'Application Submitted',
        description: 'Candidate applied via LinkedIn',
      },
      {
        id: 'evt-2',
        type: 'interview',
        timestamp: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000),
        title: 'Phone Interview Completed',
        description: 'Interview with Jane Doe',
      },
    ],
    feedback: [
      {
        id: 'fb-1',
        author: 'Jane Doe',
        date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000),
        text: 'Excellent technical knowledge and problem-solving skills',
        rating: 5,
        category: 'technical',
      },
    ],
  },
  {
    id: 'app-2',
    positionId: 'pos-1',
    candidateName: 'Sarah Johnson',
    candidateEmail: 'sarah@example.com',
    positionTitle: 'Senior Backend Engineer',
    location: 'New York, NY',
    status: 'offer',
    appliedAt: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000),
    source: 'Referral',
    scores: { keyword: 92, semantic: 88, capability: 95 },
    tags: ['Backend', 'Go', 'Kubernetes'],
    isUrgent: true,
    lastInterviewDate: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000),
    nextSteps: 'Waiting for acceptance',
    resumeUrl: 'https://example.com/resume2.pdf',
    linkedinUrl: 'https://linkedin.com/in/sarah',
    interviews: [
      {
        id: 'int-2',
        date: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000),
        type: 'phone',
        interviewer: 'John Doe',
        notes: 'Phone screen went well',
        feedback: 'Moved to technical round',
        score: 8,
      },
      {
        id: 'int-3',
        date: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000),
        type: 'technical',
        interviewer: 'Alice Johnson',
        notes: 'System design interview',
        feedback: 'Excellent system design skills',
        score: 10,
      },
    ],
    offer: {
      id: 'off-1',
      salary: 220000,
      benefits: ['Health Insurance', '401k', 'Remote Work', 'Stock Options', 'PTO'],
      startDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
      notes: 'Standard offer letter with sign-on bonus',
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
      accepted: false,
    },
    timeline: [
      {
        id: 'evt-3',
        type: 'status_change',
        timestamp: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000),
        title: 'Application Submitted',
      },
      {
        id: 'evt-4',
        type: 'interview',
        timestamp: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000),
        title: 'Phone Interview Scheduled',
      },
      {
        id: 'evt-5',
        type: 'interview',
        timestamp: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000),
        title: 'Technical Interview Completed',
      },
      {
        id: 'evt-6',
        type: 'offer',
        timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
        title: 'Offer Extended',
      },
    ],
    feedback: [
      {
        id: 'fb-2',
        author: 'John Doe',
        date: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000),
        text: 'Strong fundamentals, good communicator',
        rating: 4,
        category: 'technical',
      },
      {
        id: 'fb-3',
        author: 'Alice Johnson',
        date: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000),
        text: 'Excellent system design and architecture knowledge',
        rating: 5,
        category: 'technical',
      },
    ],
  },
  {
    id: 'app-3',
    positionId: 'pos-1',
    candidateName: 'Mike Chen',
    candidateEmail: 'mike@example.com',
    positionTitle: 'Senior Backend Engineer',
    location: 'Remote',
    status: 'screened',
    appliedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
    source: 'Job Board',
    scores: { keyword: 72, semantic: 68, capability: 75 },
    tags: ['Backend', 'Java', 'Spring Boot'],
    isUrgent: false,
    resumeUrl: 'https://example.com/resume3.pdf',
    linkedinUrl: 'https://linkedin.com/in/mike',
    interviews: [],
    offer: undefined,
    timeline: [
      {
        id: 'evt-7',
        type: 'status_change',
        timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
        title: 'Application Submitted',
      },
      {
        id: 'evt-8',
        type: 'status_change',
        timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
        title: 'Screening Completed',
      },
    ],
    feedback: [],
  },
];

interface PipelineStats {
  total: number;
  applied: number;
  screened: number;
  interviewed: number;
  offer: number;
  closed: number;
}

export default function ApplicationsPage() {
  const [selectedApplication, setSelectedApplication] =
    useState<Pipeline.Application | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [applications, setApplications] = useState<Pipeline.Application[]>(mockApplications);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<Pipeline.ApplicationStatus | 'all'>('all');
  const [activeTab, setActiveTab] = useState('gallery');

  // Calculate stats
  const stats: PipelineStats = {
    total: applications.length,
    applied: applications.filter(a => a.status === 'applied').length,
    screened: applications.filter(a => a.status === 'screened').length,
    interviewed: applications.filter(a => a.status === 'interviewed').length,
    offer: applications.filter(a => a.status === 'offer').length,
    closed: applications.filter(a => a.status === 'closed').length,
  };

  // Filter applications
  const filteredApplications = applications.filter(app => {
    const matchesSearch =
      app.candidateName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.positionTitle.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.candidateEmail.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = filterStatus === 'all' || app.status === filterStatus;

    return matchesSearch && matchesStatus;
  });

  const handleViewDetails = (applicationId: string) => {
    const app = applications.find(a => a.id === applicationId);
    if (app) {
      setSelectedApplication(app);
      setShowDetailModal(true);
    }
  };

  const handleScheduleInterview = (applicationId: string) => {
    // TODO: Implement interview scheduling
    console.log('Schedule interview for:', applicationId);
  };

  const handleAddFeedback = (
    feedback: Omit<Pipeline.Feedback, 'id' | 'date'>
  ) => {
    if (!selectedApplication) return;

    const newFeedback: Pipeline.Feedback = {
      id: `fb-${Date.now()}`,
      ...feedback,
      date: new Date(),
    };

    const updatedApplications = applications.map(app =>
      app.id === selectedApplication.id
        ? { ...app, feedback: [...app.feedback, newFeedback] }
        : app
    );

    setApplications(updatedApplications);
    setSelectedApplication({
      ...selectedApplication,
      feedback: [...selectedApplication.feedback, newFeedback],
    });
  };

  const handleGeneratePrepGuide = async (
    positionTitle: string,
    candidateName: string
  ): Promise<Pipeline.InterviewPrepGuide> => {
    // Simulate API call to Claude
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          focusAreas: [
            'System Design and Architecture',
            'Microservices and Distributed Systems',
            'Database Design and Optimization',
            'API Design and RESTful principles',
          ],
          keyQuestions: [
            `Tell me about a complex system you've designed. What were the key challenges?`,
            `How would you design a scalable e-commerce backend?`,
            `Explain your approach to database optimization and indexing.`,
            `What patterns do you use for handling failures in distributed systems?`,
          ],
          commonChallenges: [
            'May struggle with real-world scalability constraints',
            'Might need clarification on trade-offs between consistency and availability',
          ],
          prepTips: [
            'Review SOLID principles and design patterns',
            'Practice explaining architectural decisions',
            'Be prepared to discuss trade-offs and why you made specific choices',
            'Have recent project examples ready to discuss',
          ],
        });
      }, 1500);
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Applications Tracking"
        subtitle="Manage and track job applications through the pipeline"
        icon="Briefcase"
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs text-muted-foreground">Total</p>
            <p className="text-2xl font-bold text-blue-600">{stats.total}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs text-muted-foreground">Applied</p>
            <p className="text-2xl font-bold text-blue-500">{stats.applied}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs text-muted-foreground">Screened</p>
            <p className="text-2xl font-bold text-purple-500">{stats.screened}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs text-muted-foreground">Interviewed</p>
            <p className="text-2xl font-bold text-indigo-500">{stats.interviewed}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs text-muted-foreground">Offer</p>
            <p className="text-2xl font-bold text-yellow-500">{stats.offer}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs text-muted-foreground">Closed</p>
            <p className="text-2xl font-bold text-green-600">{stats.closed}</p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filter */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex gap-2 flex-col sm:flex-row">
            <div className="flex-1 flex gap-2">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search applications..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>
              <select
                value={filterStatus}
                onChange={e => setFilterStatus(e.target.value as any)}
                className="px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              >
                <option value="all">All Status</option>
                <option value="applied">Applied</option>
                <option value="screened">Screened</option>
                <option value="interviewed">Interviewed</option>
                <option value="offer">Offer</option>
                <option value="closed">Closed</option>
              </select>
            </div>
            <Button className="gap-2">
              <Plus className="w-4 h-4" />
              New Application
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Applications View */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="gallery">Gallery View</TabsTrigger>
          <TabsTrigger value="pipeline">Pipeline View</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        {/* Gallery View */}
        <TabsContent value="gallery" className="space-y-4">
          {filteredApplications.length === 0 ? (
            <Card>
              <CardContent className="pt-8 text-center">
                <AlertCircle className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-muted-foreground">No applications found</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filteredApplications.map(app => (
                <ApplicationCard
                  key={app.id}
                  application={app}
                  onViewDetails={handleViewDetails}
                  onScheduleInterview={handleScheduleInterview}
                  featured={app.isUrgent}
                />
              ))}
            </div>
          )}
        </TabsContent>

        {/* Pipeline View */}
        <TabsContent value="pipeline" className="space-y-4">
          {['applied', 'screened', 'interviewed', 'offer', 'closed'].map(status => {
            const stageApps = applications.filter(a => a.status === status);
            return (
              <div key={status}>
                <h3 className="font-semibold mb-3 capitalize">{status}</h3>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {stageApps.map(app => (
                    <ApplicationCard
                      key={app.id}
                      application={app}
                      onViewDetails={handleViewDetails}
                      onScheduleInterview={handleScheduleInterview}
                      compact={true}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </TabsContent>

        {/* Analytics View */}
        <TabsContent value="analytics">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Pipeline Analytics
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                {[
                  { label: 'Applied', value: stats.applied, total: stats.total },
                  { label: 'Screened', value: stats.screened, total: stats.total },
                  { label: 'Interviewed', value: stats.interviewed, total: stats.total },
                  { label: 'Offer', value: stats.offer, total: stats.total },
                  { label: 'Closed', value: stats.closed, total: stats.total },
                ].map(item => {
                  const percentage = Math.round((item.value / stats.total) * 100);
                  return (
                    <div key={item.label}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium">{item.label}</span>
                        <span className="text-muted-foreground">
                          {item.value}/{stats.total} ({percentage}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Application Detail Modal */}
      {showDetailModal && selectedApplication && (
        <ApplicationDetailModal
          application={selectedApplication}
          isOpen={showDetailModal}
          onClose={() => {
            setShowDetailModal(false);
            setSelectedApplication(null);
          }}
          onScheduleInterview={() => handleScheduleInterview(selectedApplication.id)}
          onAddFeedback={handleAddFeedback}
          onGeneratePrepGuide={handleGeneratePrepGuide}
        />
      )}
    </div>
  );
}
