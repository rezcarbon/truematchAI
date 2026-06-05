'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@clerk/nextjs';
import { PageHeader } from '@/components/shared/AppShell';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { getCapabilityMappings, CapabilityMapping } from '@/lib/api/training';
import { AlertCircle, Zap, TrendingUp, Eye, EyeOff, ThumbsUp, ThumbsDown } from 'lucide-react';
import { input as inputClass } from '@/components/ui/input';

export default function CapabilityMappingsPage() {
  const { getToken } = useAuth();
  const [mappings, setMappings] = useState<CapabilityMapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'confidence' | 'frequency'>('confidence');

  useEffect(() => {
    const loadMappings = async () => {
      try {
        const token = await getToken();
        if (!token) throw new Error('Not authenticated');

        const data = await getCapabilityMappings(token);
        setMappings(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load mappings');
      } finally {
        setLoading(false);
      }
    };

    loadMappings();
  }, [getToken]);

  const filtered = mappings
    .filter(
      (m) =>
        m.cv_keyword.toLowerCase().includes(searchTerm.toLowerCase()) ||
        m.capability.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      if (sortBy === 'confidence') return b.confidence_score - a.confidence_score;
      return b.frequency - a.frequency;
    });

  const stats = {
    total: mappings.length,
    high_confidence: mappings.filter((m) => m.confidence_score >= 0.8).length,
    user_added: mappings.filter((m) => m.is_user_added).length,
    learned: mappings.filter((m) => m.learned_from_feedback).length,
  };

  return (
    <div>
      <PageHeader
        title="Capability Mappings"
        subtitle="CV keywords mapped to job capabilities with confidence scores"
      />

      {/* Stats */}
      <div className="mb-6 grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">Total Mappings</p>
            <p className="mt-2 text-2xl font-bold">{stats.total}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">High Confidence</p>
            <p className="mt-2 text-2xl font-bold">{stats.high_confidence}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">User Added</p>
            <p className="mt-2 text-2xl font-bold">{stats.user_added}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">Learned</p>
            <p className="mt-2 text-2xl font-bold">{stats.learned}</p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Sort */}
      <div className="mb-6 grid gap-4 md:grid-cols-2">
        <div>
          <input
            type="text"
            placeholder="Search keywords or capabilities..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className={`w-full px-4 py-2 rounded-lg border border-input bg-background text-sm`}
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setSortBy('confidence')}
            className={`flex-1 px-4 py-2 rounded-lg border-2 transition-all ${
              sortBy === 'confidence'
                ? 'border-blue-500 bg-blue-50'
                : 'border-border hover:bg-muted'
            }`}
          >
            Sort by Confidence
          </button>
          <button
            onClick={() => setSortBy('frequency')}
            className={`flex-1 px-4 py-2 rounded-lg border-2 transition-all ${
              sortBy === 'frequency'
                ? 'border-blue-500 bg-blue-50'
                : 'border-border hover:bg-muted'
            }`}
          >
            Sort by Frequency
          </button>
        </div>
      </div>

      {/* Mappings List */}
      {loading ? (
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-muted-foreground">Loading capability mappings...</p>
          </CardContent>
        </Card>
      ) : error ? (
        <Card className="border-destructive">
          <CardContent className="flex items-center gap-3 p-6">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div>
              <p className="font-semibold">Error loading mappings</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </CardContent>
        </Card>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Zap className="h-8 w-8 mx-auto mb-4 text-muted-foreground opacity-50" />
            <p className="text-muted-foreground">
              {searchTerm ? 'No mappings found' : 'No capability mappings yet'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((mapping) => (
            <Card key={mapping.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-5">
                <div className="grid grid-cols-1 md:grid-cols-[2fr_2fr_1fr_auto] gap-4">
                  {/* CV Keyword */}
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground">CV KEYWORD</p>
                    <p className="text-sm font-medium mt-1">{mapping.cv_keyword}</p>
                    {mapping.job_category && (
                      <Badge variant="outline" className="mt-2 text-xs">
                        {mapping.job_category}
                      </Badge>
                    )}
                  </div>

                  {/* Capability */}
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground">CAPABILITY</p>
                    <p className="text-sm font-medium mt-1">{mapping.capability}</p>
                    {mapping.industry && (
                      <Badge variant="outline" className="mt-2 text-xs">
                        {mapping.industry}
                      </Badge>
                    )}
                  </div>

                  {/* Confidence Score */}
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground">CONFIDENCE</p>
                    <div className="mt-2">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-semibold">
                          {Math.round(mapping.confidence_score * 100)}%
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {mapping.frequency}x seen
                        </span>
                      </div>
                      <Progress
                        value={mapping.confidence_score * 100}
                        className="h-2"
                      />
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="flex items-center gap-3">
                    <div className="text-center">
                      <div className="flex items-center gap-1 justify-center text-green-600">
                        <ThumbsUp className="h-4 w-4" />
                        <span className="text-sm font-semibold">{mapping.positive_feedback}</span>
                      </div>
                      <div className="flex items-center gap-1 justify-center text-red-600 mt-1">
                        <ThumbsDown className="h-4 w-4" />
                        <span className="text-sm font-semibold">{mapping.negative_feedback}</span>
                      </div>
                    </div>
                    {mapping.is_user_added && (
                      <Badge variant="secondary" className="whitespace-nowrap">
                        User
                      </Badge>
                    )}
                    {mapping.learned_from_feedback && (
                      <Badge variant="default" className="whitespace-nowrap">
                        Learned
                      </Badge>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
