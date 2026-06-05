'use client';

import React from 'react';
import * as LucideIcons from 'lucide-react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  icon?: keyof typeof LucideIcons;
}

export function PageHeader({ title, subtitle, icon }: PageHeaderProps) {
  // Get the icon component if provided
  const IconComponent = icon ? (LucideIcons[icon] as React.ComponentType<{ className?: string }>) : null;

  return (
    <div className="bg-gradient-to-r from-primary/10 to-primary/5 border-b">
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-start gap-4">
          {IconComponent && (
            <div className="flex-shrink-0">
              <IconComponent className="h-8 w-8 text-primary" />
            </div>
          )}
          <div className="flex-1">
            <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
            {subtitle && (
              <p className="mt-2 text-base text-muted-foreground">{subtitle}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
