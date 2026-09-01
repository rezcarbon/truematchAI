'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Copy, Download, Eye, EyeOff } from 'lucide-react';

interface JDComparisonViewProps {
  originalJD: string;
  optimizedJD: string;
  positionTitle?: string;
  onClose?: () => void;
}

interface DiffSegment {
  type: 'added' | 'removed' | 'unchanged';
  content: string;
}

/**
 * Generates a simple diff between original and optimized JD
 * Uses word-level comparison for better readability
 */
function generateDiff(original: string, optimized: string): DiffSegment[] {
  const originalWords = original.split(/(\s+)/);
  const optimizedWords = optimized.split(/(\s+)/);

  const segments: DiffSegment[] = [];
  let i = 0;
  let j = 0;

  while (i < originalWords.length || j < optimizedWords.length) {
    if (i < originalWords.length && j < optimizedWords.length && originalWords[i] === optimizedWords[j]) {
      // Same word
      segments.push({ type: 'unchanged', content: originalWords[i] });
      i++;
      j++;
    } else if (
      j < optimizedWords.length &&
      (!segments.length || segments[segments.length - 1].type !== 'added')
    ) {
      // Word added in optimized version
      segments.push({ type: 'added', content: optimizedWords[j] });
      j++;
    } else if (i < originalWords.length) {
      // Word removed from original
      segments.push({ type: 'removed', content: originalWords[i] });
      i++;
    } else {
      break;
    }
  }

  return segments;
}

export function JDComparisonView({
  originalJD,
  optimizedJD,
  positionTitle = 'Job Description',
  onClose,
}: JDComparisonViewProps) {
  const [viewMode, setViewMode] = useState<'side-by-side' | 'diff'>('side-by-side');
  const [showDiff, setShowDiff] = useState(true);
  const [copiedText, setCopiedText] = useState<string | null>(null);

  const diff = generateDiff(originalJD, optimizedJD);

  const handleCopyText = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(label);
    setTimeout(() => setCopiedText(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Comparison: {positionTitle}</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Review the changes made to optimize your job description
          </p>
        </div>
        {onClose && (
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        )}
      </div>

      {/* View Mode Toggle */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex gap-2 bg-muted rounded-lg p-1">
          <Button
            variant={viewMode === 'side-by-side' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('side-by-side')}
            className="text-xs"
          >
            Side by Side
          </Button>
          <Button
            variant={viewMode === 'diff' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('diff')}
            className="text-xs"
          >
            Diff View
          </Button>
        </div>

        {viewMode === 'diff' && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowDiff(!showDiff)}
            className="text-xs"
          >
            {showDiff ? (
              <>
                <Eye className="h-3 w-3 mr-1" />
                Hide Unchanged
              </>
            ) : (
              <>
                <EyeOff className="h-3 w-3 mr-1" />
                Show All
              </>
            )}
          </Button>
        )}
      </div>

      {/* Side by Side View */}
      {viewMode === 'side-by-side' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Original */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Original</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleCopyText(originalJD, 'Original')}
                  className="text-xs"
                >
                  <Copy className="h-3 w-3 mr-1" />
                  {copiedText === 'Original' ? 'Copied!' : 'Copy'}
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-muted rounded-lg p-4 max-h-[600px] overflow-y-auto font-mono text-sm whitespace-pre-wrap break-words">
                {originalJD}
              </div>
            </CardContent>
          </Card>

          {/* Optimized */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Optimized</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleCopyText(optimizedJD, 'Optimized')}
                  className="text-xs"
                >
                  <Copy className="h-3 w-3 mr-1" />
                  {copiedText === 'Optimized' ? 'Copied!' : 'Copy'}
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-muted rounded-lg p-4 max-h-[600px] overflow-y-auto font-mono text-sm whitespace-pre-wrap break-words">
                {optimizedJD}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Diff View */}
      {viewMode === 'diff' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Changes Highlighted</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleCopyText(optimizedJD, 'Optimized')}
                className="text-xs"
              >
                <Copy className="h-3 w-3 mr-1" />
                {copiedText === 'Optimized' ? 'Copied!' : 'Copy'}
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-muted rounded-lg p-4 max-h-[600px] overflow-y-auto font-mono text-sm space-y-2">
              <div className="space-y-1">
                {diff.map((segment, idx) => {
                  // Skip showing unchanged segments unless user opts in
                  if (!showDiff && segment.type === 'unchanged') {
                    return null;
                  }

                  if (segment.type === 'unchanged') {
                    return (
                      <span key={idx} className="text-foreground">
                        {segment.content}
                      </span>
                    );
                  } else if (segment.type === 'added') {
                    return (
                      <span
                        key={idx}
                        className="bg-green-200 dark:bg-green-900 text-green-900 dark:text-green-100 px-1 rounded"
                      >
                        {segment.content}
                      </span>
                    );
                  } else {
                    return (
                      <span
                        key={idx}
                        className="bg-red-200 dark:bg-red-900 text-red-900 dark:text-red-100 px-1 rounded line-through"
                      >
                        {segment.content}
                      </span>
                    );
                  }
                })}
              </div>
            </div>

            {/* Legend */}
            <div className="mt-4 flex gap-4 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-green-200 dark:bg-green-900" />
                <span>Added</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-red-200 dark:bg-red-900" />
                <span>Removed</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Download */}
      <div className="flex justify-end">
        <Button
          onClick={() => {
            const element = document.createElement('a');
            element.setAttribute(
              'href',
              'data:text/plain;charset=utf-8,' + encodeURIComponent(optimizedJD)
            );
            element.setAttribute('download', `${positionTitle}-optimized.txt`);
            element.style.display = 'none';
            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
          }}
          className="gap-2"
        >
          <Download className="h-4 w-4" />
          Download Optimized JD
        </Button>
      </div>
    </div>
  );
}
