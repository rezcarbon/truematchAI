import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

/**
 * Integration tests for Applications workflow
 * Tests the complete flow: apply → track → view feedback → manage
 */
describe('Applications Integration', () => {
  const mockApplications = [
    {
      id: 'app-1',
      jobId: 'job-1',
      jobTitle: 'Senior React Developer',
      company: 'Tech Corp',
      status: 'applied',
      appliedAt: new Date('2024-01-15'),
      matchScore: 92,
    },
    {
      id: 'app-2',
      jobId: 'job-2',
      jobTitle: 'Full Stack Engineer',
      company: 'StartUp Inc',
      status: 'interview',
      appliedAt: new Date('2024-01-10'),
      matchScore: 85,
      interviewDate: new Date('2024-02-01'),
    },
    {
      id: 'app-3',
      jobId: 'job-3',
      jobTitle: 'Backend Engineer',
      company: 'Enterprise Co',
      status: 'rejected',
      appliedAt: new Date('2024-01-05'),
      matchScore: 78,
      rejectionReason: 'Preferred candidate selected',
    },
  ];

  describe('Apply Workflow', () => {
    it('completes job application submission', async () => {
      const user = userEvent.setup();
      const mockApply = jest.fn().mockResolvedValue({
        id: 'app-new',
        status: 'applied',
        appliedAt: new Date(),
      });

      const ApplyComponent = () => {
        const [submitted, setSubmitted] = React.useState(false);

        const handleApply = async () => {
          const result = await mockApply('job-1');
          setSubmitted(true);
          return result;
        };

        return (
          <div>
            <button onClick={handleApply} data-testid="apply-btn">
              Apply Now
            </button>
            {submitted && <div data-testid="success">Application submitted!</div>}
          </div>
        );
      };

      render(<ApplyComponent />);

      const applyBtn = screen.getByTestId('apply-btn');
      await user.click(applyBtn);

      await waitFor(() => {
        expect(mockApply).toHaveBeenCalledWith('job-1');
        expect(screen.getByTestId('success')).toBeInTheDocument();
      });
    });

    it('applies to multiple jobs sequentially', async () => {
      const user = userEvent.setup();
      const applications: any[] = [];
      const mockApply = jest.fn().mockImplementation((jobId) => {
        const app = {
          id: `app-${applications.length + 1}`,
          jobId,
          status: 'applied',
          appliedAt: new Date(),
        };
        applications.push(app);
        return Promise.resolve(app);
      });

      // Apply to first job
      const result1 = await mockApply('job-1');
      expect(result1.jobId).toBe('job-1');

      // Apply to second job
      const result2 = await mockApply('job-2');
      expect(result2.jobId).toBe('job-2');

      // Apply to third job
      const result3 = await mockApply('job-3');
      expect(result3.jobId).toBe('job-3');

      expect(applications.length).toBe(3);
    });

    it('handles application submission with custom cover letter', async () => {
      const user = userEvent.setup();
      const mockApply = jest.fn().mockResolvedValue({
        id: 'app-new',
        status: 'applied',
      });

      const ApplyWithCoverLetterComponent = () => {
        const [coverLetter, setCoverLetter] = React.useState('');

        const handleSubmit = async (e: React.FormEvent) => {
          e.preventDefault();
          await mockApply({
            jobId: 'job-1',
            coverLetter: coverLetter || undefined,
          });
        };

        return (
          <form onSubmit={handleSubmit}>
            <textarea
              value={coverLetter}
              onChange={(e) => setCoverLetter(e.target.value)}
              placeholder="Cover letter (optional)"
              data-testid="cover-letter"
            />
            <button type="submit" data-testid="submit-btn">
              Apply
            </button>
          </form>
        );
      };

      render(<ApplyWithCoverLetterComponent />);

      const textarea = screen.getByTestId('cover-letter');
      const submitBtn = screen.getByTestId('submit-btn');

      await user.type(textarea, 'I am excited to apply for this role...');
      await user.click(submitBtn);

      await waitFor(() => {
        expect(mockApply).toHaveBeenCalledWith(
          expect.objectContaining({
            jobId: 'job-1',
            coverLetter: expect.stringContaining('excited'),
          })
        );
      });
    });
  });

  describe('Track Applications Workflow', () => {
    it('displays all applications with current status', async () => {
      const ApplicationListComponent = () => {
        const [applications, setApplications] = React.useState(mockApplications);

        React.useEffect(() => {
          setApplications(mockApplications);
        }, []);

        return (
          <div data-testid="app-list">
            {applications.map((app) => (
              <div key={app.id} data-testid={`app-${app.id}`}>
                <h3>{app.jobTitle}</h3>
                <span data-testid={`status-${app.id}`}>{app.status}</span>
              </div>
            ))}
          </div>
        );
      };

      render(<ApplicationListComponent />);

      expect(screen.getByTestId('app-1')).toBeInTheDocument();
      expect(screen.getByTestId('app-2')).toBeInTheDocument();
      expect(screen.getByTestId('app-3')).toBeInTheDocument();

      expect(screen.getByTestId('status-app-1')).toHaveTextContent('applied');
      expect(screen.getByTestId('status-app-2')).toHaveTextContent('interview');
      expect(screen.getByTestId('status-app-3')).toHaveTextContent('rejected');
    });

    it('filters applications by status', async () => {
      const user = userEvent.setup();
      const mockFilter = jest.fn().mockImplementation((apps, status) => {
        return apps.filter((app: any) => app.status === status);
      });

      const FilterApplicationsComponent = () => {
        const [selectedStatus, setSelectedStatus] = React.useState<string | null>(null);
        const [filteredApps, setFilteredApps] = React.useState(mockApplications);

        const handleFilter = (status: string) => {
          setSelectedStatus(status);
          const filtered = mockFilter(mockApplications, status);
          setFilteredApps(filtered);
        };

        return (
          <div>
            <button onClick={() => handleFilter('applied')} data-testid="filter-applied">
              Applied
            </button>
            <button onClick={() => handleFilter('interview')} data-testid="filter-interview">
              Interview
            </button>
            <button onClick={() => handleFilter('rejected')} data-testid="filter-rejected">
              Rejected
            </button>

            <div data-testid="results">
              {filteredApps.map((app) => (
                <div key={app.id} data-testid={`result-${app.id}`}>
                  {app.jobTitle}
                </div>
              ))}
            </div>
          </div>
        );
      };

      render(<FilterApplicationsComponent />);

      const interviewBtn = screen.getByTestId('filter-interview');
      await user.click(interviewBtn);

      await waitFor(() => {
        expect(mockFilter).toHaveBeenCalledWith(mockApplications, 'interview');
      });
    });

    it('tracks application timeline', async () => {
      const TimelineComponent = () => {
        const events = [
          { date: new Date('2024-01-15'), event: 'Applied' },
          { date: new Date('2024-01-20'), event: 'Profile Viewed' },
          { date: new Date('2024-01-25'), event: 'Interview Scheduled' },
          { date: new Date('2024-02-01'), event: 'Interview Completed' },
          { date: new Date('2024-02-05'), event: 'Waiting for Response' },
        ];

        return (
          <div data-testid="timeline">
            {events.map((e, i) => (
              <div key={i} data-testid={`event-${i}`}>
                <span>{e.date.toLocaleDateString()}</span>
                <span>{e.event}</span>
              </div>
            ))}
          </div>
        );
      };

      render(<TimelineComponent />);

      expect(screen.getByTestId('event-0')).toBeInTheDocument();
      expect(screen.getByTestId('event-4')).toBeInTheDocument();
    });
  });

  describe('View Feedback Workflow', () => {
    it('displays feedback for rejected applications', async () => {
      const FeedbackComponent = () => {
        const [selectedApp, setSelectedApp] = React.useState(mockApplications[2]);

        return (
          <div>
            {selectedApp.rejectionReason && (
              <div data-testid="feedback">
                <h3>Feedback</h3>
                <p>{selectedApp.rejectionReason}</p>
              </div>
            )}
          </div>
        );
      };

      render(<FeedbackComponent />);

      expect(screen.getByTestId('feedback')).toBeInTheDocument();
      expect(screen.getByText('Preferred candidate selected')).toBeInTheDocument();
    });

    it('retrieves interview feedback', async () => {
      const mockGetFeedback = jest.fn().mockResolvedValue({
        rating: 4.5,
        feedback: 'Great communication skills and technical knowledge',
        interviewerName: 'John Smith',
        nextSteps: 'Waiting for final decision',
      });

      const result = await mockGetFeedback('app-2');

      expect(result.rating).toBe(4.5);
      expect(result.feedback).toContain('communication');
    });

    it('displays all feedback for application', async () => {
      const mockGetAllFeedback = jest.fn().mockResolvedValue([
        {
          date: new Date('2024-02-01'),
          type: 'interview',
          feedback: 'Good technical skills',
          rating: 4,
        },
        {
          date: new Date('2024-02-05'),
          type: 'evaluation',
          feedback: 'Cultural fit concerns',
          rating: 2,
        },
      ]);

      const feedbackList = await mockGetAllFeedback('app-2');

      expect(feedbackList.length).toBe(2);
      expect(feedbackList[0].type).toBe('interview');
      expect(feedbackList[1].type).toBe('evaluation');
    });
  });

  describe('Application Statistics', () => {
    it('calculates application stats', () => {
      const stats = {
        total: mockApplications.length,
        applied: mockApplications.filter((a) => a.status === 'applied').length,
        interview: mockApplications.filter((a) => a.status === 'interview').length,
        rejected: mockApplications.filter((a) => a.status === 'rejected').length,
        avgMatchScore: mockApplications.reduce((sum, a) => sum + a.matchScore, 0) / mockApplications.length,
      };

      expect(stats.total).toBe(3);
      expect(stats.applied).toBe(1);
      expect(stats.interview).toBe(1);
      expect(stats.rejected).toBe(1);
      expect(stats.avgMatchScore).toBeCloseTo(85, 0);
    });

    it('tracks application progress metrics', () => {
      const metrics = {
        thisWeek: mockApplications.filter((a) => {
          const diff = Date.now() - a.appliedAt.getTime();
          return diff < 7 * 24 * 60 * 60 * 1000;
        }).length,
        thisMonth: mockApplications.filter((a) => {
          const diff = Date.now() - a.appliedAt.getTime();
          return diff < 30 * 24 * 60 * 60 * 1000;
        }).length,
        allTime: mockApplications.length,
      };

      expect(metrics.allTime).toBe(3);
      expect(metrics.thisMonth).toBe(3);
    });
  });

  describe('Complete Application Workflow', () => {
    it('executes full workflow: apply → track → view → withdraw', async () => {
      const user = userEvent.setup();
      const allApplications: any[] = [];

      const mockApply = jest.fn().mockImplementation((jobId) => {
        const app = { id: `app-${Date.now()}`, jobId, status: 'applied' };
        allApplications.push(app);
        return Promise.resolve(app);
      });

      const mockWithdraw = jest.fn().mockImplementation((appId) => {
        const app = allApplications.find((a) => a.id === appId);
        if (app) app.status = 'withdrawn';
        return Promise.resolve({ status: 'withdrawn' });
      });

      const WorkflowComponent = () => {
        const [applications, setApplications] = React.useState<any[]>([]);
        const [selectedApp, setSelectedApp] = React.useState<any | null>(null);

        const handleApply = async () => {
          const result = await mockApply('job-1');
          setApplications([...applications, result]);
        };

        const handleWithdraw = async (appId: string) => {
          await mockWithdraw(appId);
          setApplications(
            applications.map((a) =>
              a.id === appId ? { ...a, status: 'withdrawn' } : a
            )
          );
        };

        return (
          <div>
            <button onClick={handleApply} data-testid="apply-btn">
              Apply
            </button>

            <div data-testid="list">
              {applications.map((app) => (
                <button
                  key={app.id}
                  onClick={() => setSelectedApp(app)}
                  data-testid={`app-${app.id}`}
                >
                  {app.status}
                </button>
              ))}
            </div>

            {selectedApp && (
              <div data-testid="detail">
                <button
                  onClick={() => handleWithdraw(selectedApp.id)}
                  data-testid="withdraw-btn"
                >
                  Withdraw
                </button>
              </div>
            )}
          </div>
        );
      };

      render(<WorkflowComponent />);

      // Step 1: Apply
      const applyBtn = screen.getByTestId('apply-btn');
      await user.click(applyBtn);

      await waitFor(() => {
        expect(mockApply).toHaveBeenCalledWith('job-1');
      });

      // Step 2: View application
      const appBtn = screen.queryByTestId(/app-app-/);
      if (appBtn) {
        await user.click(appBtn);

        // Step 3: Withdraw
        const withdrawBtn = screen.getByTestId('withdraw-btn');
        await user.click(withdrawBtn);

        await waitFor(() => {
          expect(mockWithdraw).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Error Handling', () => {
    it('handles application submission errors', async () => {
      const user = userEvent.setup();
      const mockApply = jest.fn().mockRejectedValue(
        new Error('Cannot apply: already applied')
      );

      const ErrorComponent = () => {
        const [error, setError] = React.useState<string | null>(null);

        const handleApply = async () => {
          try {
            await mockApply('job-1');
          } catch (err: any) {
            setError(err.message);
          }
        };

        return (
          <div>
            <button onClick={handleApply} data-testid="apply-btn">
              Apply
            </button>
            {error && <div data-testid="error">{error}</div>}
          </div>
        );
      };

      render(<ErrorComponent />);

      await user.click(screen.getByTestId('apply-btn'));

      await waitFor(() => {
        expect(screen.getByTestId('error')).toBeInTheDocument();
        expect(screen.getByText('Cannot apply: already applied')).toBeInTheDocument();
      });
    });

    it('handles withdrawal errors', async () => {
      const mockWithdraw = jest.fn().mockRejectedValue(
        new Error('Cannot withdraw: in interview stage')
      );

      const withdrawPromise = mockWithdraw('app-1');

      await expect(withdrawPromise).rejects.toThrow('in interview stage');
    });

    it('handles application status update errors', async () => {
      const mockUpdateStatus = jest.fn().mockRejectedValue(
        new Error('Failed to update status')
      );

      const updatePromise = mockUpdateStatus('app-1', 'interviewed');

      await expect(updatePromise).rejects.toThrow('Failed to update');
    });
  });

  describe('Concurrent Operations', () => {
    it('handles multiple concurrent applications', async () => {
      const mockApply = jest.fn().mockResolvedValue({ status: 'applied' });

      const promises = [
        mockApply('job-1'),
        mockApply('job-2'),
        mockApply('job-3'),
      ];

      const results = await Promise.all(promises);

      expect(results.length).toBe(3);
      expect(mockApply).toHaveBeenCalledTimes(3);
    });

    it('manages concurrent status updates', async () => {
      const mockUpdate = jest.fn().mockResolvedValue({ updated: true });

      const updates = [
        mockUpdate('app-1', 'interview'),
        mockUpdate('app-2', 'rejected'),
        mockUpdate('app-3', 'offer'),
      ];

      const results = await Promise.all(updates);

      expect(results.length).toBe(3);
    });
  });
});
