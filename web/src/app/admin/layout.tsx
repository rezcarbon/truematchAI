import type { ReactNode } from "react";
import { AppShell, type NavItem } from "@/components/shared/AppShell";

const nav: NavItem[] = [
  { href: "/admin/dashboard", label: "Dashboard" },
  { href: "/chat", label: "AI Assistant" },
  { href: "/admin/profile", label: "Profile" },
  { divider: true },
  { href: "/admin/configuration", label: "Configuration" },
  { divider: true },
  { href: "/admin/cv-analysis", label: "CV Analysis" },
  { href: "/admin/jd-simulation", label: "JD Simulation" },
  { href: "/admin/upload-resume", label: "Upload Resume" },
  { divider: true },
  { href: "/admin/training", label: "Training System" },
  { href: "/admin/training/upload", label: "Upload Data", indent: true },
  { href: "/admin/training/chat", label: "Training Chat", indent: true },
  { href: "/admin/training/feedback", label: "Feedback", indent: true },
  { href: "/admin/training/mappings", label: "Capability Mappings", indent: true },
  { href: "/admin/training/insights", label: "Insights & Analytics", indent: true },
  { divider: true },
  { href: "/admin/scrapers", label: "Job Scrapers" },
  { href: "/admin/uploads", label: "Bulk Upload" },
  { divider: true },
  { href: "/admin/users", label: "Users" },
  { href: "/admin/billing", label: "Billing & Fulfillment" },
  { href: "/admin/audit", label: "Audit" },
  { href: "/admin/compliance", label: "Compliance" },
  { divider: true },
  { href: "/admin/analytics/pipeline", label: "Pipeline Analytics" },
  { href: "/admin/analytics/sources", label: "Source Analytics" },
  { href: "/admin/analytics/three-signal", label: "Three-Signal Analytics" },
  { href: "/admin/analytics/recruiter-performance", label: "Recruiter Performance" },
  { href: "/admin/analytics/dei", label: "DEI Analytics" },
  { divider: true },
  { href: "/admin/email-templates", label: "Email Templates" },
];

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <AppShell role="admin" nav={nav}>
      {children}
    </AppShell>
  );
}
