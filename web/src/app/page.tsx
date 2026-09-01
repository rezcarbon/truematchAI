'use client';

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowRight, GitCompareArrows, FileText, Link2, CheckCircle2, AlertCircle, BarChart3, Lock } from "lucide-react";

const FeatureCard = ({ number, title, description, tag, tagColor }: {
  number: string;
  title: string;
  description: string;
  tag: string;
  tagColor: 'primary' | 'accent' | 'success';
}) => {
  const colorClasses = {
    primary: 'bg-blue-50 dark:bg-blue-950 border-l-4 border-l-blue-600 dark:border-l-blue-400',
    accent: 'bg-emerald-50 dark:bg-emerald-950 border-l-4 border-l-emerald-600 dark:border-l-emerald-400',
    success: 'bg-green-50 dark:bg-green-950 border-l-4 border-l-green-600 dark:border-l-green-400',
  };

  const numberBgClasses = {
    primary: 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300',
    accent: 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300',
    success: 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300',
  };

  const tagClasses = {
    primary: 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300',
    accent: 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300',
    success: 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300',
  };

  return (
    <div className={`rounded-lg p-6 transition-all hover:shadow-lg hover:-translate-y-1 ${colorClasses[tagColor]}`}>
      <div className={`mb-4 inline-flex h-10 w-10 items-center justify-center rounded-full font-bold text-sm ${numberBgClasses[tagColor]}`}>
        {number}
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground mb-3">{description}</p>
      <span className={`inline-block px-2 py-1 rounded text-xs font-semibold ${tagClasses[tagColor]}`}>
        {tag}
      </span>
    </div>
  );
};

const ProblemCard = ({ number, title, description, color }: {
  number: string;
  title: string;
  description: string;
  color: string;
}) => {
  const numberColor = {
    'red': 'text-red-600 dark:text-red-400',
    'amber': 'text-amber-600 dark:text-amber-400',
    'purple': 'text-purple-600 dark:text-purple-400',
  }[color] || 'text-red-600';

  const borderColor = {
    'red': 'border-t-red-600 dark:border-t-red-400',
    'amber': 'border-t-amber-600 dark:border-t-amber-400',
    'purple': 'border-t-purple-600 dark:border-t-purple-400',
  }[color] || 'border-t-red-600';

  return (
    <div className={`bg-card rounded-lg p-6 border-t-4 ${borderColor}`}>
      <div className={`text-4xl font-black leading-none mb-3 ${numberColor}`}>{number}</div>
      <h3 className="text-lg font-bold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
};

const RoleCard = ({ role, items }: {
  role: string;
  items: { label: string; value: string | number; description: string }[];
}) => {
  const roleColors = {
    'Recruiters': 'border-t-blue-600 dark:border-t-blue-400',
    'Admins': 'border-t-emerald-600 dark:border-t-emerald-400',
    'Candidates': 'border-t-green-600 dark:border-t-green-400',
  };

  return (
    <div className={`bg-card rounded-lg p-6 border-t-4 ${roleColors[role as keyof typeof roleColors]}`}>
      <h3 className="text-lg font-bold mb-4">{`For ${role}`}</h3>
      <div className="space-y-4">
        {items.map((item, idx) => (
          <div key={idx} className="pb-4 border-b last:pb-0 last:border-b-0">
            <div className="text-3xl font-black mb-1">{item.value}</div>
            <div className="text-xs font-semibold text-muted-foreground uppercase mb-1">{item.label}</div>
            <p className="text-sm text-muted-foreground">{item.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur border-b">
        <div className="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded-md bg-gradient-to-br from-blue-600 to-emerald-600" />
            <span className="font-bold text-lg">TrueMatch</span>
          </div>
          <nav className="flex items-center gap-2">
            <Link href="/login">
              <Button variant="ghost" size="sm">Log in</Button>
            </Link>
            <Link href="/signup">
              <Button size="sm">Get started</Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-900 via-blue-800 to-blue-700 dark:from-blue-950 dark:via-blue-900 dark:to-blue-800 text-white py-20">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <div className="mb-6 inline-block bg-emerald-500/20 border border-emerald-500 px-4 py-2 rounded-full">
            <span className="text-sm font-semibold text-emerald-100">AI-Powered Hiring Intelligence</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-black leading-tight tracking-tight mb-6">
            Discover exceptional candidates beyond keywords
          </h1>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto leading-relaxed">
            Resume keywords aren't capability. We score both — then show you the difference. That's where great hiring happens.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link href="/signup">
              <Button size="lg" className="bg-emerald-500 hover:bg-emerald-600 text-white">
                Start Free Assessment <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline" className="border-blue-200 text-blue-100 hover:bg-blue-800/50">
                See How It Works
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Feature Cards */}
      <section className="py-16 px-6">
        <div className="mx-auto max-w-6xl grid gap-6 md:grid-cols-3">
          <FeatureCard
            number="1"
            title="Dual Scoring"
            description="Two independent signals reveal overlooked talent. Keywords ≠ capability. We show both."
            tag="Why it matters"
            tagColor="primary"
          />
          <FeatureCard
            number="2"
            title="Capability Narrative"
            description="Evidence grounded in real work. GitHub. DOI. Certifications. Your best candidates proved it."
            tag="Why it matters"
            tagColor="accent"
          />
          <FeatureCard
            number="3"
            title="Governed by Design"
            description="6 non-bypassable fairness gates. Built-in compliance. Every decision is defensible."
            tag="Why it matters"
            tagColor="success"
          />
        </div>
      </section>

      {/* Problems Section */}
      <section className="py-16 px-6 bg-muted/30">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <span className="text-xs font-bold text-primary uppercase tracking-wide">The Challenge</span>
            <h2 className="text-4xl font-black mt-2">Five reasons your best candidates almost didn't make it here</h2>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            <ProblemCard
              number="01"
              title="Keyword-Only Matching"
              description="Misses 40% of capable candidates. ATS rejected someone who can do the job because they used different terminology."
              color="red"
            />
            <ProblemCard
              number="02"
              title="Credentials Don't Equal Capability"
              description="Did they actually lead that team? Or just have the title? We verify. Competitors guess."
              color="amber"
            />
            <ProblemCard
              number="03"
              title="Bias Hiding in Plain Sight"
              description="Unconscious decision criteria multiply hiring mistakes. Traditional systems hide it. Compliance liability follows."
              color="purple"
            />
          </div>
        </div>
      </section>

      {/* Three Signals Section */}
      <section className="py-16 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <span className="text-xs font-bold text-primary uppercase tracking-wide">How It Works</span>
            <h2 className="text-4xl font-black mt-2">Three independent checks. One shared truth.</h2>
          </div>

          <div className="grid gap-6 md:grid-cols-3 mb-12">
            <div className="bg-card rounded-lg p-6 border border-border">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 font-bold mb-4">1</div>
              <h3 className="text-lg font-bold mb-2">Keyword Score</h3>
              <p className="text-sm text-muted-foreground mb-4">What traditional ATS do. Resume words vs job description words.</p>
              <div className="bg-muted/50 p-3 rounded text-xs italic text-muted-foreground">"JavaScript" + "React" = Match</div>
            </div>
            <div className="bg-card rounded-lg p-6 border border-border">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300 font-bold mb-4">2</div>
              <h3 className="text-lg font-bold mb-2">Semantic Score</h3>
              <p className="text-sm text-muted-foreground mb-4">Meaning, not just words. "System design" matches "ecosystem leadership."</p>
              <div className="bg-muted/50 p-3 rounded text-xs italic text-muted-foreground">"Built infrastructure" ≈ "Designed systems"</div>
            </div>
            <div className="bg-card rounded-lg p-6 border border-border">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 font-bold mb-4">3</div>
              <h3 className="text-lg font-bold mb-2">Capability Score</h3>
              <p className="text-sm text-muted-foreground mb-4">What they actually did. Evidence verified. Grounded in GitHub, DOI, work history.</p>
              <div className="bg-muted/50 p-3 rounded text-xs italic text-muted-foreground">847 commits + 2 papers + 12 years history</div>
            </div>
          </div>

          {/* Delta Visualization */}
          <div className="bg-card border border-border rounded-lg p-8">
            <h3 className="font-bold mb-8 text-center">The Delta Is The Product</h3>
            <div className="flex items-end justify-center gap-8 mb-8 h-48">
              <div className="flex flex-col items-center">
                <div className="text-2xl font-black mb-4">32</div>
                <div className="w-16 bg-gray-400 rounded-t-lg" style={{ height: '80px' }}></div>
                <div className="text-xs font-semibold mt-3 text-muted-foreground">Keyword</div>
              </div>
              <div className="flex flex-col items-center">
                <div className="text-2xl font-black mb-4">68</div>
                <div className="w-16 bg-blue-500 rounded-t-lg" style={{ height: '130px' }}></div>
                <div className="text-xs font-semibold mt-3 text-muted-foreground">Semantic</div>
              </div>
              <div className="flex flex-col items-center">
                <div className="text-2xl font-black mb-4 text-white">85</div>
                <div className="w-16 bg-emerald-500 rounded-t-lg flex items-end justify-center" style={{ height: '160px' }}></div>
                <div className="text-xs font-semibold mt-3 text-muted-foreground">Capability</div>
              </div>
            </div>
            <div className="bg-emerald-50 dark:bg-emerald-950 border border-emerald-600/30 rounded-lg p-4 text-center">
              <div className="text-xs font-bold text-emerald-700 dark:text-emerald-300 uppercase mb-2">🎯 +53 Point Delta</div>
              <p className="text-sm text-emerald-900 dark:text-emerald-100">That's your hidden gem candidate. The M Agent flags them automatically with specific evidence.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Role-Specific Value Section */}
      <section className="py-16 px-6 bg-muted/30">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <span className="text-xs font-bold text-primary uppercase tracking-wide">Role-Specific Value</span>
            <h2 className="text-4xl font-black mt-2">Built for every person in the hiring process</h2>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            <RoleCard
              role="Recruiters"
              items={[
                { label: "Faster Time-to-Hire", value: "40%", description: "Spend less time screening. More time on great candidates." },
                { label: "Fewer Mis-Hires", value: "30%", description: "Evidence-based verdicts catch red flags your gut misses." },
                { label: "Saved Per Avoided Mis-Hire", value: "$15-50K", description: "One bad hire costs $50K. We prevent them." },
              ]}
            />
            <RoleCard
              role="Admins"
              items={[
                { label: "Audit Trail Coverage", value: "100%", description: "Regulators see exactly how you hire. No dark corners." },
                { label: "Fairness Gates", value: "6", description: "One gate fails = verdict blocked. No override buttons." },
                { label: "Manual Compliance Work", value: "0h", description: "Built-in from day one. Bias detection automatic." },
              ]}
            />
            <RoleCard
              role="Candidates"
              items={[
                { label: "Fair Assessment", value: "✓", description: "Your actual capability is scored, not buzzwords." },
                { label: "Transparent Feedback", value: "✓", description: "See exactly why you matched. What to improve." },
                { label: "Interview Prep", value: "✓", description: "AI coaching before your interview." },
              ]}
            />
          </div>
        </div>
      </section>

      {/* Three Pillars Section */}
      <section className="py-16 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <span className="text-xs font-bold text-primary uppercase tracking-wide">Platform</span>
            <h2 className="text-4xl font-black mt-2">Expert infrastructure. Three roles. One decision engine.</h2>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {[
              {
                icon: FileText,
                title: "CV Analysis",
                subtitle: "What they've actually done (not just claimed)",
                color: "blue",
                roles: [
                  { label: "For Recruiters", text: "Stop taking resumes at face value. See verified capability." },
                  { label: "For Admins", text: "Auditable from day one. Governance built in." },
                  { label: "For Candidates", text: "Your real skills get recognized. (Buzzwords don't.)" },
                ]
              },
              {
                icon: BarChart3,
                title: "JD Assessment",
                subtitle: "Job descriptions that actually attract the right people",
                color: "emerald",
                roles: [
                  { label: "For Recruiters", text: "Impossible requirements flagged. Clarity scores drive applications up 30%." },
                  { label: "For Admins", text: "Watch job quality evolve. Compliance and clarity tracked." },
                  { label: "For Candidates", text: "No more \"must-have\" skills that are actually nice-to-haves." },
                ]
              },
              {
                icon: Link2,
                title: "Matching & Governance",
                subtitle: "Smart matching with six non-bypassable fairness gates",
                color: "green",
                roles: [
                  { label: "For Recruiters", text: "Counter-recommendations fire when capability exceeds keywords. Find diamonds." },
                  { label: "For Admins", text: "Six fairness gates. Built-in documentation. Full compliance visibility." },
                  { label: "For Candidates", text: "What you can do matters more than where you went. Transparent feedback." },
                ]
              },
            ].map((pillar) => (
              <div key={pillar.title} className="bg-card rounded-lg overflow-hidden border border-border">
                <div className={`p-6 border-b-4 ${
                  pillar.color === 'blue' ? 'border-b-blue-600 dark:border-b-blue-400' :
                  pillar.color === 'emerald' ? 'border-b-emerald-600 dark:border-b-emerald-400' :
                  'border-b-green-600 dark:border-b-green-400'
                }`}>
                  <pillar.icon className={`h-8 w-8 mb-3 ${
                    pillar.color === 'blue' ? 'text-blue-600 dark:text-blue-400' :
                    pillar.color === 'emerald' ? 'text-emerald-600 dark:text-emerald-400' :
                    'text-green-600 dark:text-green-400'
                  }`} />
                  <h3 className="text-lg font-bold">{pillar.title}</h3>
                  <p className="text-sm text-muted-foreground mt-1">{pillar.subtitle}</p>
                </div>
                <div className="p-6 space-y-4">
                  {pillar.roles.map((role) => (
                    <div key={role.label} className="pb-4 border-b last:pb-0 last:border-b-0">
                      <div className={`text-xs font-bold uppercase tracking-wide mb-1 ${
                        pillar.color === 'blue' ? 'text-blue-600 dark:text-blue-400' :
                        pillar.color === 'emerald' ? 'text-emerald-600 dark:text-emerald-400' :
                        'text-green-600 dark:text-green-400'
                      }`}>
                        {role.label}
                      </div>
                      <p className="text-sm text-muted-foreground">{role.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Governance Section */}
      <section className="py-16 px-6 bg-muted/30">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <span className="text-xs font-bold text-primary uppercase tracking-wide">Built-In Oversight</span>
            <h2 className="text-4xl font-black mt-2">Regulatory-ready from day one. No retrofitting.</h2>
            <p className="text-lg text-muted-foreground mt-4 max-w-2xl mx-auto">Six patent gates. Every hiring decision passes through all six. No exceptions. No overrides. That's by design.</p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {[
              { title: "Coherence Gate", description: "All signals align. Keyword + semantic + capability scores tell one story, not three." },
              { title: "Temporal Depth", description: "Timeline is physically possible. Simultaneous C-level roles? Caught." },
              { title: "Lipschitz Constraint", description: "Confidence bounded by evidence. Score can't exceed evidence density." },
              { title: "Evidence Integrator", description: "All claims verified. GitHub commits. Peer-reviewed papers. Unverified: blocked." },
              { title: "Logic Separator", description: "Every reasoning step logged. Auditors trace how we got to this verdict." },
              { title: "Gate Orchestrator", description: "One gate fails = verdict blocked. No exceptions. No override buttons." },
            ].map((gate) => (
              <div key={gate.title} className="bg-card rounded-lg p-4 border border-border">
                <div className="flex items-start gap-3">
                  <Lock className="h-5 w-5 text-primary flex-shrink-0 mt-1" />
                  <div>
                    <h4 className="font-bold text-sm mb-1">{gate.title}</h4>
                    <p className="text-xs text-muted-foreground">{gate.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="grid gap-6 md:grid-cols-3 mt-8">
            <div className="bg-card rounded-lg p-6 border border-border">
              <CheckCircle2 className="h-8 w-8 text-emerald-600 dark:text-emerald-400 mb-3" />
              <h4 className="font-bold mb-2">EU AI Act</h4>
              <p className="text-sm text-muted-foreground">Article 12-15: Explainability. Every verdict explainable. Human review built-in.</p>
            </div>
            <div className="bg-card rounded-lg p-6 border border-border">
              <CheckCircle2 className="h-8 w-8 text-emerald-600 dark:text-emerald-400 mb-3" />
              <h4 className="font-bold mb-2">NYC Local Law 144</h4>
              <p className="text-sm text-muted-foreground">Discrimination Prevention. Bias auditing on every decision. Automatic notification.</p>
            </div>
            <div className="bg-card rounded-lg p-6 border border-border">
              <CheckCircle2 className="h-8 w-8 text-emerald-600 dark:text-emerald-400 mb-3" />
              <h4 className="font-bold mb-2">GDPR & PDPA</h4>
              <p className="text-sm text-muted-foreground">Data Protection. AES-256 encryption. Immutable audit trail. No deletion.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-6 bg-gradient-to-r from-blue-600 to-emerald-600 dark:from-blue-700 dark:to-emerald-700 text-white">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-4xl font-black mb-6">Ready to hire smarter?</h2>
          <p className="text-lg mb-8 text-blue-50">Start your free assessment. No credit card required.</p>
          <div className="flex gap-4 justify-center">
            <Link href="/signup">
              <Button size="lg" className="bg-white text-blue-700 hover:bg-blue-50">
                Start Free Assessment <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline" className="border-blue-200 text-white hover:bg-blue-600">
                View Full Demo
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t px-6 py-12 text-center text-sm text-muted-foreground">
        <div className="mx-auto max-w-6xl">
          <p className="mb-6">© {new Date().getFullYear()} TrueMatch. Capability-first hiring.</p>
          <div className="flex justify-center gap-6">
            <Link href="/privacy" className="hover:text-foreground">Privacy</Link>
            <Link href="/terms" className="hover:text-foreground">Terms</Link>
            <Link href="/contact" className="hover:text-foreground">Contact</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
