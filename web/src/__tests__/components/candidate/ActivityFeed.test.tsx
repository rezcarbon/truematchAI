import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  ActivityFeed,
  type ActivityFeedItem,
} from '@/components/candidate/ActivityFeed';

describe('ActivityFeed Component', () => {
  const mockItems: ActivityFeedItem[] = [
    {
      id: '1',
      type: 'assessment',
      title: 'Assessment Completed',
      description: 'You completed the Senior Engineer assessment',
      timestamp: new Date().toISOString(),
      actor: { name: 'System' },
    },
    {
      id: '2',
      type: 'application',
      title: 'Applied to Position',
      description: 'You applied to Senior Backend Engineer at TechCorp',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      actor: { name: 'You' },
    },
    {
      id: '3',
      type: 'interview',
      title: 'Interview Scheduled',
      description: 'Your interview is scheduled for tomorrow at 2 PM',
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      actor: { name: 'Recruiter', role: 'HR Manager' },
      actionLabel: 'Prepare',
      onAction: jest.fn(),
    },
  ];

  it('renders activity feed with title', () => {
    render(<ActivityFeed items={mockItems} title="Recent Activity" />);

    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
  });

  it('displays activity count badge', () => {
    render(<ActivityFeed items={mockItems} />);

    expect(screen.getByText('3 new')).toBeInTheDocument();
  });

  it('renders all activity items', () => {
    render(<ActivityFeed items={mockItems} />);

    expect(screen.getByText('Assessment Completed')).toBeInTheDocument();
    expect(screen.getByText('Applied to Position')).toBeInTheDocument();
    expect(screen.getByText('Interview Scheduled')).toBeInTheDocument();
  });

  it('displays item descriptions', () => {
    render(<ActivityFeed items={mockItems} />);

    expect(
      screen.getByText('You completed the Senior Engineer assessment')
    ).toBeInTheDocument();
    expect(
      screen.getByText('You applied to Senior Backend Engineer at TechCorp')
    ).toBeInTheDocument();
  });

  it('displays actor information when available', () => {
    render(<ActivityFeed items={mockItems} />);

    expect(screen.getByText('by System')).toBeInTheDocument();
    expect(screen.getByText('by You')).toBeInTheDocument();
  });

  it('displays actor role when available', () => {
    render(<ActivityFeed items={mockItems} />);

    expect(screen.getByText('HR Manager')).toBeInTheDocument();
  });

  it('shows empty state when no items', () => {
    render(<ActivityFeed items={[]} />);

    expect(screen.getByText('No recent activity')).toBeInTheDocument();
  });

  it('respects maxItems prop', () => {
    render(<ActivityFeed items={mockItems} maxItems={2} />);

    expect(screen.getByText('Assessment Completed')).toBeInTheDocument();
    expect(screen.getByText('Applied to Position')).toBeInTheDocument();
    expect(
      screen.queryByText('Interview Scheduled')
    ).not.toBeInTheDocument();
  });

  it('displays view all button when maxItems exceeded', () => {
    render(<ActivityFeed items={mockItems} maxItems={2} />);

    expect(screen.getByText(/view all activity/i)).toBeInTheDocument();
  });

  it('calls onViewAll when view all button clicked', async () => {
    const onViewAll = jest.fn();
    render(
      <ActivityFeed
        items={mockItems}
        maxItems={2}
        onViewAll={onViewAll}
      />
    );

    const viewAllButton = screen.getByText(/view all activity/i);
    await userEvent.click(viewAllButton);

    expect(onViewAll).toHaveBeenCalledTimes(1);
  });

  it('displays action button when actionLabel provided', () => {
    render(<ActivityFeed items={mockItems} />);

    expect(screen.getByText('Prepare')).toBeInTheDocument();
  });

  it('calls action callback when action button clicked', async () => {
    const actionCallback = jest.fn();
    const itemsWithAction: ActivityFeedItem[] = [
      {
        id: '1',
        type: 'interview',
        title: 'Interview Ready',
        description: 'Start your interview prep',
        timestamp: new Date().toISOString(),
        actionLabel: 'Start Prep',
        onAction: actionCallback,
      },
    ];

    render(<ActivityFeed items={itemsWithAction} />);

    const actionButton = screen.getByText('Start Prep');
    await userEvent.click(actionButton);

    expect(actionCallback).toHaveBeenCalledTimes(1);
  });

  it('displays relative timestamps correctly', () => {
    render(<ActivityFeed items={mockItems} />);

    // "Just now" or similar time indicator
    expect(screen.getByText(/ago|now/i)).toBeInTheDocument();
  });

  it('applies custom title', () => {
    render(
      <ActivityFeed
        items={mockItems}
        title="Your Recent Updates"
      />
    );

    expect(screen.getByText('Your Recent Updates')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <ActivityFeed items={mockItems} className="custom-class" />
    );

    const card = container.querySelector('.custom-class');
    expect(card).toBeInTheDocument();
  });

  it('displays activity type badges', () => {
    render(<ActivityFeed items={mockItems} />);

    expect(screen.getByText('Assessment')).toBeInTheDocument();
    expect(screen.getByText('Application')).toBeInTheDocument();
    expect(screen.getByText('Interview')).toBeInTheDocument();
  });

  it('handles items without actor gracefully', () => {
    const itemsNoActor: ActivityFeedItem[] = [
      {
        id: '1',
        type: 'update',
        title: 'System Update',
        timestamp: new Date().toISOString(),
      },
    ];

    render(<ActivityFeed items={itemsNoActor} />);

    expect(screen.getByText('System Update')).toBeInTheDocument();
  });

  it('handles items without description gracefully', () => {
    const itemsNoDescription: ActivityFeedItem[] = [
      {
        id: '1',
        type: 'notification',
        title: 'Profile Updated',
        timestamp: new Date().toISOString(),
      },
    ];

    render(<ActivityFeed items={itemsNoDescription} />);

    expect(screen.getByText('Profile Updated')).toBeInTheDocument();
  });

  it('renders activity icons for different types', () => {
    const { container } = render(<ActivityFeed items={mockItems} />);

    const icons = container.querySelectorAll('svg');
    expect(icons.length).toBeGreaterThan(0);
  });

  it('displays correct badges for all activity types', () => {
    const itemsAllTypes: ActivityFeedItem[] = [
      { id: '1', type: 'assessment', title: 'A', timestamp: new Date().toISOString() },
      { id: '2', type: 'application', title: 'B', timestamp: new Date().toISOString() },
      { id: '3', type: 'message', title: 'C', timestamp: new Date().toISOString() },
      { id: '4', type: 'offer', title: 'D', timestamp: new Date().toISOString() },
    ];

    render(<ActivityFeed items={itemsAllTypes} maxItems={10} />);

    expect(screen.getByText('Assessment')).toBeInTheDocument();
    expect(screen.getByText('Application')).toBeInTheDocument();
    expect(screen.getByText('Message')).toBeInTheDocument();
    expect(screen.getByText('Offer')).toBeInTheDocument();
  });
});
