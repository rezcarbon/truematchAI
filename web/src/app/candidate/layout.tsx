import type { ReactNode } from "react";
import { AppShell, type NavItem } from "@/components/shared/AppShell";

const nav: NavItem[] = [
  { href: "/candidate/dashboard", label: "Dashboard" },
  { href: "/chat", label: "AI Assistant" },
  { href: "/candidate/cv-analysis", label: "CV Analysis" },
  { href: "/candidate/capability-translation", label: "Capability Translation" },
  { href: "/candidate/transition-intelligence", label: "Transition Pathways" },
  { href: "/candidate/upload", label: "Upload Resume" },
  { href: "/candidate/jobs", label: "Jobs" },
  { href: "/candidate/history", label: "Assessment History" },
  { href: "/refer", label: "Refer & Earn" },
  { href: "/pricing", label: "Pricing" },
  { href: "/candidate/profile", label: "Profile" },
];

export default function CandidateLayout({ children }: { children: ReactNode }) {
  return (
    <AppShell role="candidate" nav={nav}>
      {children}
    </AppShell>
  );
}
