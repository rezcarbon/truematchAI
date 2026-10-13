import { Metadata } from 'next';
// import { JDOptimizer } from '@/components/JDOptimizer'; (needs manual conversion)

export const metadata: Metadata = {
  title: 'JD Optimizer - TrueMatch',
  description: 'Optimize your job descriptions with AI-powered analysis',
};

export default function JDOptimizerPage() {
  return <JDOptimizer apiEndpoint="/api/jd-optimizer" />;
}
