'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Sparkles, Loader2, Copy, Check, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { HorizontalPipeline as Pipeline } from './types';

interface InterviewPrepWidgetProps {
  positionTitle: string;
  candidateName: string;
  interviewType?: 'phone' | 'technical' | 'onsite' | 'final';
  onGeneratePrepGuide?: (
    positionTitle: string,
    candidateName: string
  ) => Promise<Pipeline.InterviewPrepGuide>;
}

export function InterviewPrepWidget({
  positionTitle,
  candidateName,
  interviewType = 'phone',
  onGeneratePrepGuide,
}: InterviewPrepWidgetProps) {
  const [loading, setLoading] = useState(false);
  const [prepGuide, setPrepGuide] = useState<Pipeline.InterviewPrepGuide | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const handleGeneratePrepGuide = async () => {
    if (!onGeneratePrepGuide) return;

    setLoading(true);
    try {
      const guide = await onGeneratePrepGuide(positionTitle, candidateName);
      setPrepGuide(guide);
      setExpanded(true);
    } catch (error) {
      console.error('Failed to generate prep guide:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <Card className="border-blue-200 bg-blue-50/50">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-blue-600" />
            <CardTitle className="text-base">Interview Prep</CardTitle>
          </div>
          <Badge variant="outline" className="text-xs">
            {interviewType.charAt(0).toUpperCase() + interviewType.slice(1)}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground mt-1">
          Generate personalized prep guide for {candidateName}
        </p>
      </CardHeader>

      <CardContent className="space-y-3">
        {!prepGuide ? (
          <Button
            onClick={handleGeneratePrepGuide}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Generating prep guide...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Generate with Claude
              </>
            )}
          </Button>
        ) : (
          <div className="space-y-3">
            {/* Focus Areas */}
            <div>
              <button
                onClick={() => setExpanded(!expanded)}
                className="w-full flex items-center justify-between pb-2 border-b hover:bg-gray-50 p-2 rounded"
              >
                <h4 className="font-medium text-sm">Focus Areas</h4>
                {expanded ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </button>

              {expanded && (
                <ul className="space-y-2 mt-2">
                  {prepGuide.focusAreas.map((area, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-sm text-foreground p-2 bg-white rounded"
                    >
                      <span className="text-blue-600 font-semibold mt-0.5">•</span>
                      <span>{area}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Key Questions */}
            <div>
              <h4 className="font-medium text-sm pb-2 border-b">Key Questions</h4>
              <ul className="space-y-2 mt-2">
                {prepGuide.keyQuestions.slice(0, 3).map((question, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-foreground">
                    <span className="text-blue-600 font-semibold">Q{i + 1}</span>
                    <div className="flex-1">
                      <p>{question}</p>
                      <button
                        onClick={() => copyToClipboard(question, i)}
                        className="text-xs text-blue-600 hover:underline mt-1 flex items-center gap-1"
                      >
                        {copiedIndex === i ? (
                          <>
                            <Check className="w-3 h-3" />
                            Copied
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            Copy
                          </>
                        )}
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            {/* Common Challenges */}
            {prepGuide.commonChallenges.length > 0 && (
              <div>
                <h4 className="font-medium text-sm pb-2 border-b">Potential Challenges</h4>
                <ul className="space-y-2 mt-2">
                  {prepGuide.commonChallenges.slice(0, 2).map((challenge, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-sm text-foreground p-2 bg-yellow-50 rounded"
                    >
                      <span className="text-yellow-600">⚠</span>
                      <span>{challenge}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Prep Tips */}
            {prepGuide.prepTips.length > 0 && (
              <div>
                <h4 className="font-medium text-sm pb-2 border-b">Prep Tips</h4>
                <ul className="space-y-2 mt-2">
                  {prepGuide.prepTips.slice(0, 2).map((tip, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-sm text-foreground p-2 bg-green-50 rounded"
                    >
                      <span className="text-green-600">✓</span>
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <Button
              size="sm"
              variant="outline"
              className="w-full mt-3"
              onClick={() => setPrepGuide(null)}
            >
              Generate New Guide
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
