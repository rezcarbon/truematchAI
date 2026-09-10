'use client';

import { JDOptimizer } from '@/components/JDOptimizer';

// NOTE: `metadata` cannot be exported from a Client Component. This page renders
// the client-only <JDOptimizer>, so the title/description live in the route
// segment's layout instead of here.

export default function JDOptimizerPage() {
  return <JDOptimizer apiEndpoint="/api/jd-optimizer" />;
}
