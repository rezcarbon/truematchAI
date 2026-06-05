import type { ReactNode } from "react";
import { AppShell, type NavItem } from "@/components/shared/AppShell";

const nav: NavItem[] = [
  { href: "/candidate/dashboard", label: "Dashboard" },
  { href: "/candidate/cv-analysis", label: "CV Analysis" },
  { href: "/candidate/upload", label: "Upload Resume" },
  { href: "/candidate/jobs", label: "Jobs" },
  { href: "/candidate/history", label: "Assessment History" },
  { href: "/candidate/profile", label: "Profile" },
];

export default function CandidateLayout({ children }: { children: ReactNode }) {
  return (
    <AppShell role="candidate" nav={nav}>
      {children}
    </AppShell>
  );
}
