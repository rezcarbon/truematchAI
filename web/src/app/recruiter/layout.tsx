import type { ReactNode } from "react";
import { AppShell, type NavItem } from "@/components/shared/AppShell";

const nav: NavItem[] = [
  { href: "/recruiter/dashboard",      label: "Dashboard" },
  { href: "/chat",                     label: "AI Assistant" },
  { href: "/recruiter/profile",        label: "Profile" },
  { divider: true },
  { href: "/recruiter/pipeline",       label: "Pipeline" },
  { href: "/recruiter/positions",      label: "Positions" },
  { href: "/recruiter/candidates",     label: "Candidates" },
  { href: "/recruiter/upload-resume",  label: "Upload Resume" },
  { divider: true },
  { href: "/recruiter/compare",        label: "Compare" },
  { href: "/recruiter/internal-mobility", label: "Internal Mobility" },
  { href: "/recruiter/transition-metrics", label: "Mandate Impact" },
  { href: "/recruiter/jd-quality",     label: "JD Quality" },
  { href: "/recruiter/jd-simulation",  label: "JD Simulation" },
  { href: "/recruiter/decisions",      label: "Decisions" },
  { href: "/recruiter/agents",         label: "Agents" },
];

export default function RecruiterLayout({ children }: { children: ReactNode }) {
  return (
    <AppShell role="recruiter" nav={nav}>
      {children}
    </AppShell>
  );
}
