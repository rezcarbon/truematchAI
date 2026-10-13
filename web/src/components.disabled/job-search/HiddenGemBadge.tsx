'use client';

/**
 * Badge component for hidden gem jobs
 */

import React from 'react';
import { Sparkles } from 'lucide-react';

interface HiddenGemBadgeProps {
  reason?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function HiddenGemBadge({ reason, size = 'md' }: HiddenGemBadgeProps) {
  const sizeStyles = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  return (
    <div
      className={`
        inline-flex items-center gap-1.5
        ${sizeStyles[size]}
        bg-gradient-to-r from-purple-100 to-pink-100
        border border-purple-300
        rounded-full
        font-semibold
        text-purple-700
        whitespace-nowrap
        group relative
      `}
    >
      <Sparkles className="w-4 h-4" />
      <span>Hidden Gem</span>

      {reason && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10">
          <div className="bg-gray-900 text-white text-xs px-3 py-2 rounded whitespace-nowrap">
            {reason}
            <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
          </div>
        </div>
      )}
    </div>
  );
}
