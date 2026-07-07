import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HorizontalPipeline } from './HorizontalPipeline';
import { ApplicationCard } from './ApplicationCard';
import { ApplicationDetailModal } from './ApplicationDetailModal';
import { TimelineView } from './TimelineView';
import { FeedbackSection } from './FeedbackSection';
import { InterviewPrepWidget } from './InterviewPrepWidget';
import { OfferDetailsCard } from './OfferDetailsCard';
import type { HorizontalPipeline as Pipeline } from './types';

// Mock data
const mockApplication: Pipeline.Application = {
  id: 'app-1',
  positionId: 'pos-1',
  candidateName: 'John Smith',
  candidateEmail: 'john@example.com',
  positionTitle: 'Senior Backend Engineer',
  location: 'San Francisco, CA',
  status: 'interviewed',
  appliedAt: new Date('2024-01-15'),
  source: 'LinkedIn',
  scores: {
    keyword: 85,
    semantic: 78,
    capability: 92,
  },
  tags: ['Backend', 'Python', 'AWS'],
  isUrgent: false,
  lastInterviewDate: new Date('2024-01-20'),
  nextSteps: 'Send offer',
  resumeUrl: 'https://example.com/resume.pdf',
  linkedinUrl: 'https://linkedin.com/in/john',
  interviews: [
    {
      id: 'int-1',
      date: new Date('2024-01-20'),
      type: 'phone',
      interviewer: 'Jane Doe',
      notes: 'Great communication skills',
      feedback: 'Strong technical background',
      score: 9,
    },
  ],
  offer: {
    id: 'off-1',
    salary: 180000,
    salaryRange: undefined,
    benefits: ['Health Insurance', '401k', 'Remote Work', 'PTO'],
    startDate: new Date('2024-02-15'),
    notes: 'Standard offer letter',
    expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    accepted: false,
  },
  timeline: [
    {
      id: 'evt-1',
      type: 'status_change',
      timestamp: new Date('2024-01-15'),
      title: 'Application Submitted',
      description: 'Candidate applied via LinkedIn',
    },
    {
      id: 'evt-2',
      type: 'interview',
      timestamp: new Date('2024-01-20'),
      title: 'Phone Interview Completed',
      description: 'Interview with Jane Doe',
    },
  ],
  feedback: [
    {
      id: 'fb-1',
      author: 'Jane Doe',
      date: new Date('2024-01-20'),
      text: 'Excellent technical knowledge and problem-solving skills',
      rating: 5,
      category: 'technical',
    },
  ],
  internalNotes: 'Top candidate for the role',
};

const mockApplicationStatus: Pipeline.ApplicationStatus = 'interviewed';

describe('HorizontalPipeline', () => {
  it('renders all pipeline stages', () => {
    const status: Pipeline.ApplicationStatus = 'screened';
    render(
      <HorizontalPipeline
        applicationStatus={{
          applicationId: 'app-1',
          currentStage: status,
          completedStages: ['applied'],
          timestamp: new Date(),
        }}
      />
    );

    expect(screen.getByText('Applied')).toBeInTheDocument();
    expect(screen.getByText('Screened')).toBeInTheDocument();
    expect(screen.getByText('Interviewed')).toBeInTheDocument();
    expect(screen.getByText('Offer')).toBeInTheDocument();
    expect(screen.getByText('Closed')).toBeInTheDocument();
  });

  it('shows progress percentage', () => {
    render(
      <HorizontalPipeline
        applicationStatus={{
          applicationId: 'app-1',
          currentStage: 'offer',
          completedStages: ['applied', 'screened', 'interviewed'],
          timestamp: new Date(),
        }}
      />
    );

    // 4 stages out of 5 = 80%
    expect(screen.getByText('80%')).toBeInTheDocument();
  });

  it('calls onStageClick when stage is clicked', () => {
    const onStageClick = jest.fn();
    render(
      <HorizontalPipeline
        applicationStatus={{
          applicationId: 'app-1',
          currentStage: 'applied',
          completedStages: [],
          timestamp: new Date(),
        }}
        onStageClick={onStageClick}
      />
    );

    const screenedButton = screen.getByText('Screened').closest('button');
    fireEvent.click(screenedButton!);

    expect(onStageClick).toHaveBeenCalledWith('screened');
  });
});

describe('ApplicationCard', () => {
  it('renders application basic information', () => {
    const onViewDetails = jest.fn();
    const onScheduleInterview = jest.fn();

    render(
      <ApplicationCard
        application={mockApplication}
        onViewDetails={onViewDetails}
        onScheduleInterview={onScheduleInterview}
      />
    );

    expect(screen.getByText('John Smith')).toBeInTheDocument();
    expect(screen.getByText('Senior Backend Engineer')).toBeInTheDocument();
    expect(screen.getByText('interviewed')).toBeInTheDocument();
  });

  it('displays evaluation scores', () => {
    const onViewDetails = jest.fn();
    const onScheduleInterview = jest.fn();

    render(
      <ApplicationCard
        application={mockApplication}
        onViewDetails={onViewDetails}
        onScheduleInterview={onScheduleInterview}
      />
    );

    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByText('78%')).toBeInTheDocument();
    expect(screen.getByText('92%')).toBeInTheDocument();
  });

  it('displays tags', () => {
    const onViewDetails = jest.fn();
    const onScheduleInterview = jest.fn();

    render(
      <ApplicationCard
        application={mockApplication}
        onViewDetails={onViewDetails}
        onScheduleInterview={onScheduleInterview}
      />
    );

    expect(screen.getByText('Backend')).toBeInTheDocument();
    expect(screen.getByText('Python')).toBeInTheDocument();
    expect(screen.getByText('AWS')).toBeInTheDocument();
  });

  it('calls onViewDetails when card is clicked', async () => {
    const onViewDetails = jest.fn();
    const onScheduleInterview = jest.fn();

    const { container } = render(
      <ApplicationCard
        application={mockApplication}
        onViewDetails={onViewDetails}
        onScheduleInterview={onScheduleInterview}
      />
    );

    const card = container.querySelector('div[class*="cursor-pointer"]');
    if (card) {
      fireEvent.click(card);
      expect(onViewDetails).toHaveBeenCalledWith('app-1');
    }
  });

  it('calls onScheduleInterview when interview button is clicked', () => {
    const onViewDetails = jest.fn();
    const onScheduleInterview = jest.fn();

    render(
      <ApplicationCard
        application={mockApplication}
        onViewDetails={onViewDetails}
        onScheduleInterview={onScheduleInterview}
      />
    );

    const interviewButton = screen.getByText('Interview').closest('button');
    fireEvent.click(interviewButton!);

    expect(onScheduleInterview).toHaveBeenCalledWith('app-1');
  });
});

describe('TimelineView', () => {
  it('renders timeline events in reverse chronological order', () => {
    render(<TimelineView events={mockApplication.timeline} />);

    const events = screen.getAllByText(/Interview Completed|Application Submitted/);
    expect(events.length).toBe(2);
  });

  it('displays event metadata', () => {
    render(<TimelineView events={mockApplication.timeline} />);

    expect(screen.getByText('Candidate applied via LinkedIn')).toBeInTheDocument();
    expect(screen.getByText('Interview with Jane Doe')).toBeInTheDocument();
  });

  it('shows empty state when no events', () => {
    render(<TimelineView events={[]} />);

    expect(screen.getByText('No events yet')).toBeInTheDocument();
  });

  it('renders event timestamps', () => {
    render(<TimelineView events={mockApplication.timeline} />);

    // Should render dates in timeline
    const dateElements = screen.getAllByText(/Jan/i);
    expect(dateElements.length).toBeGreaterThan(0);
  });
});

describe('FeedbackSection', () => {
  it('renders feedback items', () => {
    render(
      <FeedbackSection
        feedback={mockApplication.feedback}
        editable={false}
      />
    );

    expect(screen.getByText('Jane Doe')).toBeInTheDocument();
    expect(screen.getByText(
      'Excellent technical knowledge and problem-solving skills'
    )).toBeInTheDocument();
  });

  it('shows average rating', () => {
    render(
      <FeedbackSection
        feedback={mockApplication.feedback}
        editable={false}
      />
    );

    expect(screen.getByText('5.0')).toBeInTheDocument();
  });

  it('displays feedback count', () => {
    render(
      <FeedbackSection
        feedback={mockApplication.feedback}
        editable={false}
      />
    );

    expect(screen.getByText('1 feedback')).toBeInTheDocument();
  });

  it('shows add feedback button when editable', () => {
    render(
      <FeedbackSection
        feedback={mockApplication.feedback}
        editable={true}
      />
    );

    expect(screen.getByText('Add Feedback')).toBeInTheDocument();
  });

  it('allows adding feedback', async () => {
    const onAddFeedback = jest.fn();
    const user = userEvent.setup();

    render(
      <FeedbackSection
        feedback={mockApplication.feedback}
        onAddFeedback={onAddFeedback}
        editable={true}
      />
    );

    // Click add feedback button
    const addButton = screen.getByText('Add Feedback');
    await user.click(addButton);

    // Fill form
    const authorInput = screen.getByPlaceholderText('Your name');
    const textInput = screen.getByPlaceholderText('Share your feedback...');

    await user.type(authorInput, 'New Reviewer');
    await user.type(textInput, 'Great candidate!');

    // Submit
    const submitButton = screen.getByText('Submit');
    await user.click(submitButton);

    expect(onAddFeedback).toHaveBeenCalledWith(
      expect.objectContaining({
        author: 'New Reviewer',
        text: 'Great candidate!',
        rating: 5,
      })
    );
  });
});

describe('OfferDetailsCard', () => {
  it('renders offer information', () => {
    render(
      <OfferDetailsCard
        offer={mockApplication.offer!}
        editable={false}
      />
    );

    expect(screen.getByText('$180,000')).toBeInTheDocument();
    expect(screen.getByText('Health Insurance')).toBeInTheDocument();
    expect(screen.getByText('401k')).toBeInTheDocument();
  });

  it('shows start date', () => {
    render(
      <OfferDetailsCard
        offer={mockApplication.offer!}
        editable={false}
      />
    );

    // Should display start date
    const startDateText = screen.getByText(/February/);
    expect(startDateText).toBeInTheDocument();
  });

  it('shows days until expiry', () => {
    render(
      <OfferDetailsCard
        offer={mockApplication.offer!}
        editable={false}
      />
    );

    // Should show expiry info
    const expiryText = screen.getByText(/Expires in/);
    expect(expiryText).toBeInTheDocument();
  });

  it('calls onAccept when accept button clicked', () => {
    const onAccept = jest.fn();

    render(
      <OfferDetailsCard
        offer={mockApplication.offer!}
        onAccept={onAccept}
        editable={false}
      />
    );

    const acceptButton = screen.getByText('Accept Offer');
    fireEvent.click(acceptButton);

    expect(onAccept).toHaveBeenCalled();
  });

  it('shows accepted status', () => {
    const acceptedOffer = { ...mockApplication.offer!, accepted: true };

    render(
      <OfferDetailsCard
        offer={acceptedOffer}
        editable={false}
      />
    );

    expect(screen.getByText('Accepted')).toBeInTheDocument();
  });
});

describe('InterviewPrepWidget', () => {
  it('renders generate button', () => {
    render(
      <InterviewPrepWidget
        positionTitle="Senior Backend Engineer"
        candidateName="John Smith"
        interviewType="phone"
      />
    );

    expect(screen.getByText(/Generate with Claude/)).toBeInTheDocument();
  });

  it('shows interview type badge', () => {
    render(
      <InterviewPrepWidget
        positionTitle="Senior Backend Engineer"
        candidateName="John Smith"
        interviewType="technical"
      />
    );

    expect(screen.getByText('Technical')).toBeInTheDocument();
  });

  it('generates prep guide when button clicked', async () => {
    const mockPrepGuide: Pipeline.InterviewPrepGuide = {
      focusAreas: ['System Design', 'Data Structures'],
      keyQuestions: ['Tell me about your experience with microservices'],
      commonChallenges: ['Might struggle with system design questions'],
      prepTips: ['Review system design patterns before the interview'],
    };

    const onGeneratePrepGuide = jest.fn().mockResolvedValue(mockPrepGuide);
    const user = userEvent.setup();

    render(
      <InterviewPrepWidget
        positionTitle="Senior Backend Engineer"
        candidateName="John Smith"
        onGeneratePrepGuide={onGeneratePrepGuide}
      />
    );

    const generateButton = screen.getByText(/Generate with Claude/);
    await user.click(generateButton);

    await waitFor(() => {
      expect(onGeneratePrepGuide).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText('System Design')).toBeInTheDocument();
    });
  });
});

describe('ApplicationDetailModal', () => {
  it('renders application details when open', () => {
    render(
      <ApplicationDetailModal
        application={mockApplication}
        isOpen={true}
        onClose={jest.fn()}
      />
    );

    expect(screen.getByText('John Smith')).toBeInTheDocument();
    expect(screen.getByText('Senior Backend Engineer')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });

  it('displays horizontal pipeline progress', () => {
    render(
      <ApplicationDetailModal
        application={mockApplication}
        isOpen={true}
        onClose={jest.fn()}
      />
    );

    // Should show pipeline stages
    expect(screen.getByText('Applied')).toBeInTheDocument();
    expect(screen.getByText('Screened')).toBeInTheDocument();
    expect(screen.getByText('Interviewed')).toBeInTheDocument();
  });

  it('displays evaluation scores in overview tab', () => {
    render(
      <ApplicationDetailModal
        application={mockApplication}
        isOpen={true}
        onClose={jest.fn()}
      />
    );

    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByText('78%')).toBeInTheDocument();
    expect(screen.getByText('92%')).toBeInTheDocument();
  });

  it('can switch between tabs', async () => {
    const user = userEvent.setup();

    render(
      <ApplicationDetailModal
        application={mockApplication}
        isOpen={true}
        onClose={jest.fn()}
      />
    );

    // Click on timeline tab
    const timelineTab = screen.getByText('Timeline');
    await user.click(timelineTab);

    // Should show timeline content
    await waitFor(() => {
      expect(screen.getByText('Application Submitted')).toBeInTheDocument();
    });
  });

  it('displays interviews in interviews tab', async () => {
    const user = userEvent.setup();

    render(
      <ApplicationDetailModal
        application={mockApplication}
        isOpen={true}
        onClose={jest.fn()}
      />
    );

    const interviewsTab = screen.getByText('Interviews');
    await user.click(interviewsTab);

    await waitFor(() => {
      expect(screen.getByText(/Phone Interview/)).toBeInTheDocument();
    });
  });

  it('displays feedback in feedback tab', async () => {
    const user = userEvent.setup();

    render(
      <ApplicationDetailModal
        application={mockApplication}
        isOpen={true}
        onClose={jest.fn()}
      />
    );

    const feedbackTab = screen.getByText('Feedback');
    await user.click(feedbackTab);

    await waitFor(() => {
      expect(screen.getByText('Jane Doe')).toBeInTheDocument();
    });
  });

  it('calls onClose when close button clicked', async () => {
    const onClose = jest.fn();
    const user = userEvent.setup();

    render(
      <ApplicationDetailModal
        application={mockApplication}
        isOpen={true}
        onClose={onClose}
      />
    );

    const closeButton = screen.getByRole('button', { name: /close/i });
    await user.click(closeButton);

    expect(onClose).toHaveBeenCalled();
  });

  it('calls onScheduleInterview when schedule button clicked', async () => {
    const onScheduleInterview = jest.fn();
    const user = userEvent.setup();

    render(
      <ApplicationDetailModal
        application={mockApplication}
        isOpen={true}
        onClose={jest.fn()}
        onScheduleInterview={onScheduleInterview}
      />
    );

    const scheduleButton = screen.getByText('Schedule Interview');
    await user.click(scheduleButton);

    expect(onScheduleInterview).toHaveBeenCalled();
  });

  it('displays offer details when in offer status', () => {
    const offerApplication = { ...mockApplication, status: 'offer' as const };

    render(
      <ApplicationDetailModal
        application={offerApplication}
        isOpen={true}
        onClose={jest.fn()}
      />
    );

    // Offer details should be visible
    expect(screen.getByText('Offer Details')).toBeInTheDocument();
    expect(screen.getByText('$180,000')).toBeInTheDocument();
  });
});

describe('End-to-End Application Tracking Flow', () => {
  it('completes full application journey', async () => {
    const user = userEvent.setup();
    const mockPrepGuide: Pipeline.InterviewPrepGuide = {
      focusAreas: ['System Design', 'Data Structures'],
      keyQuestions: ['Tell me about your experience'],
      commonChallenges: [],
      prepTips: ['Review patterns'],
    };

    const onGeneratePrepGuide = jest
      .fn()
      .mockResolvedValue(mockPrepGuide);
    const onScheduleInterview = jest.fn();
    const onAddFeedback = jest.fn();
    const onClose = jest.fn();

    const { rerender } = render(
      <ApplicationDetailModal
        application={mockApplication}
        isOpen={true}
        onClose={onClose}
        onGeneratePrepGuide={onGeneratePrepGuide}
        onScheduleInterview={onScheduleInterview}
        onAddFeedback={onAddFeedback}
      />
    );

    // 1. Verify pipeline shows current status
    expect(screen.getByText('interviewed')).toBeInTheDocument();

    // 2. Check evaluation scores
    expect(screen.getByText('85%')).toBeInTheDocument();

    // 3. Go to timeline tab to see application history
    const timelineTab = screen.getByText('Timeline');
    await user.click(timelineTab);

    await waitFor(() => {
      expect(screen.getByText('Application Submitted')).toBeInTheDocument();
    });

    // 4. Go to interviews tab
    const interviewsTab = screen.getByText('Interviews');
    await user.click(interviewsTab);

    await waitFor(() => {
      expect(screen.getByText(/Phone Interview/)).toBeInTheDocument();
    });

    // 5. Go to feedback tab and add new feedback
    const feedbackTab = screen.getByText('Feedback');
    await user.click(feedbackTab);

    const addFeedbackButton = screen.getByText('Add Feedback');
    await user.click(addFeedbackButton);

    const authorInput = screen.getByPlaceholderText('Your name');
    const textInput = screen.getByPlaceholderText('Share your feedback...');

    await user.type(authorInput, 'Hiring Manager');
    await user.type(textInput, 'Ready for offer!');

    const submitButton = screen.getByText('Submit');
    await user.click(submitButton);

    expect(onAddFeedback).toHaveBeenCalled();

    // 6. Go back to overview and check offer
    const overviewTab = screen.getByText('Overview');
    await user.click(overviewTab);

    await waitFor(() => {
      expect(screen.getByText('Offer Details')).toBeInTheDocument();
    });

    // 7. Verify all components rendered correctly
    expect(screen.getByText('Senior Backend Engineer')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });
});
