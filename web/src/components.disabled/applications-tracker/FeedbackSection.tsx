'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Star, Plus, MessageCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { HorizontalPipeline as Pipeline } from './types';

interface FeedbackSectionProps {
  feedback: Pipeline.Feedback[];
  onAddFeedback?: (feedback: Omit<Pipeline.Feedback, 'id' | 'date'>) => void;
  editable?: boolean;
}

const categoryColors = {
  technical: 'bg-blue-100 text-blue-800',
  cultural: 'bg-purple-100 text-purple-800',
  communication: 'bg-green-100 text-green-800',
  experience: 'bg-yellow-100 text-yellow-800',
};

export function FeedbackSection({
  feedback,
  onAddFeedback,
  editable = false,
}: FeedbackSectionProps) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    author: '',
    text: '',
    rating: 5,
    category: 'technical' as const,
  });

  const handleAddFeedback = () => {
    if (formData.author && formData.text) {
      onAddFeedback?.({
        author: formData.author,
        text: formData.text,
        rating: formData.rating,
        category: formData.category,
      });
      setFormData({ author: '', text: '', rating: 5, category: 'technical' });
      setShowAddForm(false);
    }
  };

  const averageRating = feedback.length > 0
    ? Math.round(
      (feedback.reduce((sum, f) => sum + (f.rating || 0), 0) / feedback.length) * 10
    ) / 10
    : 0;

  return (
    <div className="space-y-4">
      {/* Summary stats */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold">Feedback & Ratings</h3>
          <p className="text-sm text-muted-foreground">
            {feedback.length} feedback{feedback.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex items-center gap-1">
          <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
          <span className="font-semibold">{averageRating.toFixed(1)}</span>
        </div>
      </div>

      {/* Add feedback button */}
      {editable && (
        <Button
          size="sm"
          variant="outline"
          onClick={() => setShowAddForm(!showAddForm)}
          className="w-full"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Feedback
        </Button>
      )}

      {/* Add feedback form */}
      {showAddForm && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-4 space-y-3">
            <div>
              <label className="text-sm font-medium">Author</label>
              <input
                type="text"
                value={formData.author}
                onChange={e => setFormData({ ...formData, author: e.target.value })}
                placeholder="Your name"
                className="w-full mt-1 px-3 py-2 border rounded-md text-sm"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Category</label>
              <select
                value={formData.category}
                onChange={e => setFormData({
                  ...formData,
                  category: e.target.value as any,
                })}
                className="w-full mt-1 px-3 py-2 border rounded-md text-sm"
              >
                <option value="technical">Technical</option>
                <option value="cultural">Cultural</option>
                <option value="communication">Communication</option>
                <option value="experience">Experience</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium">Rating (1-5)</label>
              <div className="flex gap-1 mt-2">
                {[1, 2, 3, 4, 5].map(rating => (
                  <button
                    key={rating}
                    onClick={() => setFormData({ ...formData, rating })}
                    className="p-1"
                  >
                    <Star
                      className={cn(
                        'w-5 h-5',
                        rating <= formData.rating
                          ? 'fill-yellow-400 text-yellow-400'
                          : 'text-gray-300'
                      )}
                    />
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-sm font-medium">Feedback</label>
              <textarea
                value={formData.text}
                onChange={e => setFormData({ ...formData, text: e.target.value })}
                placeholder="Share your feedback..."
                className="w-full mt-1 px-3 py-2 border rounded-md text-sm resize-none"
                rows={3}
              />
            </div>

            <div className="flex gap-2 pt-2">
              <Button
                size="sm"
                onClick={handleAddFeedback}
                disabled={!formData.author || !formData.text}
              >
                Submit
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowAddForm(false)}
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Feedback list */}
      <div className="space-y-3">
        {feedback.length === 0 ? (
          <div className="text-center py-6 text-muted-foreground text-sm">
            No feedback yet
          </div>
        ) : (
          feedback.map(item => (
            <Card key={item.id} className="border">
              <CardContent className="pt-4">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-sm">{item.author}</p>
                      {item.category && (
                        <Badge
                          variant="secondary"
                          className={cn(
                            'text-xs',
                            categoryColors[item.category]
                          )}
                        >
                          {item.category}
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(item.date).toLocaleDateString()}
                    </p>
                  </div>

                  {item.rating && (
                    <div className="flex gap-0.5">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={cn(
                            'w-3 h-3',
                            i < item.rating!
                              ? 'fill-yellow-400 text-yellow-400'
                              : 'text-gray-300'
                          )}
                        />
                      ))}
                    </div>
                  )}
                </div>

                <p className="text-sm mt-3 leading-relaxed text-foreground">
                  {item.text}
                </p>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
