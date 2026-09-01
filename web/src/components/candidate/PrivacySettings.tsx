'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Lock, Eye, EyeOff } from 'lucide-react';

interface PrivacySettingsProps {
  privacyLevel?: 'hidden' | 'passive' | 'active';
  currentEmployer?: string;
  blockedCompanies?: string[];
  onPrivacyLevelChange?: (level: 'hidden' | 'passive' | 'active') => void;
}

const PRIVACY_LEVELS = {
  hidden: {
    label: 'Hidden',
    icon: EyeOff,
    description: 'Your profile is never shared. No recruiter spam.',
    color: 'text-blue-700 bg-blue-50 border-blue-200',
    badge: '🔐',
  },
  passive: {
    label: 'Passive',
    icon: Eye,
    description: 'Only exceptional matches see your profile.',
    color: 'text-amber-700 bg-amber-50 border-amber-200',
    badge: '👁️',
  },
  active: {
    label: 'Active',
    icon: Eye,
    description: 'Open to matches. Your profile is visible to all recruiters.',
    color: 'text-green-700 bg-green-50 border-green-200',
    badge: '🟢',
  },
};

export function PrivacySettings({
  privacyLevel = 'passive',
  currentEmployer = 'Your Company',
  blockedCompanies = [],
  onPrivacyLevelChange,
}: PrivacySettingsProps) {
  const config = PRIVACY_LEVELS[privacyLevel];

  return (
    <Card className={`border-2 ${PRIVACY_LEVELS[privacyLevel].color}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Lock className="h-5 w-5" />
            <CardTitle className="text-lg">🔒 100% Stealth Mode</CardTitle>
          </div>
          <Badge variant="secondary" className="text-xs">
            {config.badge} {config.label}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Current Privacy Level */}
        <div>
          <p className="text-xs text-muted-foreground font-medium mb-2">YOUR PRIVACY LEVEL</p>
          <div className="space-y-2">
            {(Object.entries(PRIVACY_LEVELS) as Array<[keyof typeof PRIVACY_LEVELS, any]>).map(
              ([level, levelConfig]) => (
                <Button
                  key={level}
                  variant={privacyLevel === level ? 'default' : 'outline'}
                  className="w-full justify-start text-left h-auto py-2 px-3"
                  onClick={() => onPrivacyLevelChange?.(level)}
                >
                  <span className="text-lg mr-2">{levelConfig.badge}</span>
                  <div className="flex-1">
                    <p className="font-medium text-sm">{levelConfig.label}</p>
                    <p className="text-xs text-muted-foreground">{levelConfig.description}</p>
                  </div>
                </Button>
              )
            )}
          </div>
        </div>

        {/* Protected Info */}
        <div className="border-t pt-3">
          <p className="text-xs text-muted-foreground font-medium mb-2">🛡️ AUTOMATICALLY PROTECTED</p>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm bg-muted/50 rounded p-2">
              <span>Current employer blocked</span>
              <span className="font-mono text-xs bg-white px-2 py-1 rounded">{currentEmployer}</span>
            </div>
            {blockedCompanies.length > 0 && (
              <div className="text-xs text-muted-foreground">
                <p className="mb-1">Blocked companies:</p>
                <div className="flex flex-wrap gap-1">
                  {blockedCompanies.map((company) => (
                    <Badge key={company} variant="secondary" className="text-xs">
                      {company}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Privacy Guarantee */}
        <div className="border-t pt-3 bg-blue-50/50 rounded p-2">
          <p className="text-xs text-blue-900">
            <span className="font-semibold">Privacy Guaranteed:</span> Your profile, preferences, and career context are
            never shared with companies until you explicitly approve a match.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
