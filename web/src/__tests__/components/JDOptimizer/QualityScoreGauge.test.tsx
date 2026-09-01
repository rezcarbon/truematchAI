import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import QualityScoreGauge from '@/components/JDOptimizer/QualityScoreGauge';

describe('QualityScoreGauge', () => {
  describe('Rendering', () => {
    it('should render gauge component with initial score', () => {
      render(<QualityScoreGauge score={50} />);

      expect(screen.getByText('Score')).toBeInTheDocument();
    });

    it('should render SVG circle elements', () => {
      const { container } = render(<QualityScoreGauge score={50} />);

      const circles = container.querySelectorAll('circle');
      expect(circles.length).toBeGreaterThan(0);
    });

    it('should display quality label text', () => {
      render(<QualityScoreGauge score={85} />);

      expect(screen.getByText('Excellent')).toBeInTheDocument();
    });
  });

  describe('Animation', () => {
    it('should animate score from 0 to target value', async () => {
      const { rerender } = render(<QualityScoreGauge score={0} />);

      await waitFor(() => {
        const scoreText = screen.getByText('0');
        expect(scoreText).toBeInTheDocument();
      });

      rerender(<QualityScoreGauge score={75} />);

      await waitFor(() => {
        const scoreText = screen.getByText(/^(7[0-5]|75)$/);
        expect(scoreText).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('should reset animation on score change', async () => {
      const { rerender } = render(<QualityScoreGauge score={30} />);

      await waitFor(() => {
        expect(screen.getByText(/3[0-9]/)).toBeInTheDocument();
      }, { timeout: 1000 });

      rerender(<QualityScoreGauge score={90} />);

      await waitFor(() => {
        expect(screen.getByText('Good')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('should handle immediate zero score', async () => {
      const { rerender } = render(<QualityScoreGauge score={50} />);

      await waitFor(() => {
        expect(screen.getByText(/5[0-9]/)).toBeInTheDocument();
      });

      rerender(<QualityScoreGauge score={0} />);

      await waitFor(() => {
        expect(screen.getByText('0')).toBeInTheDocument();
      });
    });
  });

  describe('Score Ranges and Labels', () => {
    it('should display "Excellent" for scores 80+', () => {
      render(<QualityScoreGauge score={80} />);

      expect(screen.getByText('Excellent')).toBeInTheDocument();
      expect(screen.getByText('Minor improvements available')).toBeInTheDocument();
    });

    it('should display "Good" for scores 60-79', async () => {
      render(<QualityScoreGauge score={70} />);

      await waitFor(() => {
        expect(screen.getByText('Good')).toBeInTheDocument();
        expect(screen.getByText('Some improvements recommended')).toBeInTheDocument();
      });
    });

    it('should display "Fair" for scores 40-59', async () => {
      render(<QualityScoreGauge score={50} />);

      await waitFor(() => {
        expect(screen.getByText('Fair')).toBeInTheDocument();
        expect(screen.getByText('Several improvements needed')).toBeInTheDocument();
      });
    });

    it('should display "Needs Improvement" for scores below 40', async () => {
      render(<QualityScoreGauge score={30} />);

      await waitFor(() => {
        expect(screen.getByText('Needs Improvement')).toBeInTheDocument();
        expect(screen.getByText('Significant improvements needed')).toBeInTheDocument();
      });
    });

    it('should display perfect message for 100 score', async () => {
      render(<QualityScoreGauge score={100} />);

      await waitFor(() => {
        expect(screen.getByText('Perfect job description!')).toBeInTheDocument();
      });
    });
  });

  describe('Color Coding', () => {
    it('should apply green color class for high scores', async () => {
      const { container } = render(<QualityScoreGauge score={85} />);

      await waitFor(() => {
        const scoreSpan = container.querySelector('.text-4xl.font-bold');
        expect(scoreSpan).toHaveClass('text-green-600');
      });
    });

    it('should apply yellow color class for good scores', async () => {
      const { container } = render(<QualityScoreGauge score={70} />);

      await waitFor(() => {
        const scoreSpan = container.querySelector('.text-4xl.font-bold');
        expect(scoreSpan).toHaveClass('text-yellow-600');
      });
    });

    it('should apply orange color class for fair scores', async () => {
      const { container } = render(<QualityScoreGauge score={50} />);

      await waitFor(() => {
        const scoreSpan = container.querySelector('.text-4xl.font-bold');
        expect(scoreSpan).toHaveClass('text-orange-600');
      });
    });

    it('should apply red color class for low scores', async () => {
      const { container } = render(<QualityScoreGauge score={25} />);

      await waitFor(() => {
        const scoreSpan = container.querySelector('.text-4xl.font-bold');
        expect(scoreSpan).toHaveClass('text-red-600');
      });
    });
  });

  describe('SVG Gauge Visual', () => {
    it('should have correct SVG viewBox', () => {
      const { container } = render(<QualityScoreGauge score={50} />);

      const svg = container.querySelector('svg');
      expect(svg).toHaveAttribute('viewBox', '0 0 120 120');
    });

    it('should update SVG stroke dash offset based on score', async () => {
      const { container, rerender } = render(<QualityScoreGauge score={0} />);

      let circles = container.querySelectorAll('circle[stroke="#e5e7eb"]');
      expect(circles[0]).toHaveAttribute('strokeDashoffset', '282.74');

      rerender(<QualityScoreGauge score={50} />);

      await waitFor(() => {
        circles = container.querySelectorAll('circle');
        const progressCircle = circles[1];
        expect(progressCircle).toHaveAttribute('strokeDashoffset');
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle score of 0', () => {
      render(<QualityScoreGauge score={0} />);

      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('should handle score of 100', async () => {
      render(<QualityScoreGauge score={100} />);

      await waitFor(() => {
        expect(screen.getByText('100')).toBeInTheDocument();
      });
    });

    it('should handle fractional scores', async () => {
      render(<QualityScoreGauge score={55.5} />);

      await waitFor(() => {
        const scoreText = screen.getByText(/5[0-9]/);
        expect(scoreText).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper text hierarchy with semantic structure', () => {
      const { container } = render(<QualityScoreGauge score={75} />);

      const paragraphs = container.querySelectorAll('p');
      expect(paragraphs.length).toBeGreaterThan(0);
    });

    it('should have sufficient color contrast in labels', () => {
      render(<QualityScoreGauge score={50} />);

      const label = screen.getByText('Fair');
      expect(label).toBeInTheDocument();
      expect(label).toHaveClass('text-sm', 'font-medium', 'text-gray-900');
    });

    it('should have descriptive text for different score ranges', () => {
      render(<QualityScoreGauge score={45} />);

      // Verify descriptive text is present
      expect(screen.getByText('Fair')).toBeInTheDocument();
      expect(screen.getByText('Several improvements needed')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('should cleanup interval on unmount', () => {
      const { unmount } = render(<QualityScoreGauge score={75} />);

      const clearIntervalSpy = jest.spyOn(global, 'clearInterval');

      unmount();

      expect(clearIntervalSpy).toHaveBeenCalled();

      clearIntervalSpy.mockRestore();
    });

    it('should not cause memory leaks with multiple score changes', async () => {
      const { rerender } = render(<QualityScoreGauge score={20} />);

      for (let i = 20; i <= 100; i += 10) {
        rerender(<QualityScoreGauge score={i} />);
        await waitFor(() => {
          expect(screen.getByText('Score')).toBeInTheDocument();
        });
      }
    });
  });
});
