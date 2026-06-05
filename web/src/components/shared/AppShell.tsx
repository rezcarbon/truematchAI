"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { UserDropdownMenu } from "@/components/shared/UserDropdownMenu";
import { NotificationCenter } from "@/components/NotificationCenter";
import {
  LayoutDashboard, Briefcase, Users, GitCompare,
  FileSearch, CheckSquare, Bot, Settings,
  ChevronRight, Menu, X
} from "lucide-react";

export interface NavItem {
  href?: string;
  label?: string;
  icon?: React.ElementType;
  badge?: number;
  divider?: boolean;
}

const ICONS: Record<string, React.ElementType> = {
  "Dashboard":   LayoutDashboard,
  "Positions":   Briefcase,
  "Candidates":  Users,
  "Compare":     GitCompare,
  "JD Quality":  FileSearch,
  "Decisions":   CheckSquare,
  "Agents":      Bot,
  "Settings":    Settings,
};

function NavLink({ item, active }: { item: NavItem; active: boolean }) {
  if (!item.href || !item.label) return null;

  const Icon = item.icon ?? ICONS[item.label] ?? ChevronRight;
  return (
    <Link
      href={item.href}
      className={cn(
        "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
        active
          ? "bg-primary text-primary-foreground shadow-sm"
          : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
      )}
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span className="flex-1">{item.label}</span>
      {item.badge !== undefined && item.badge > 0 && (
        <span className={cn(
          "rounded-full px-1.5 py-0.5 text-[10px] font-bold tabular-nums",
          active ? "bg-primary-foreground/20 text-primary-foreground" : "bg-red-100 text-red-700"
        )}>
          {item.badge}
        </span>
      )}
    </Link>
  );
}

export function AppShell({
  role,
  nav,
  children,
}: {
  role: string;
  nav: NavItem[];
  children: ReactNode;
}) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-muted/30">
      {/* Sidebar */}
      <aside className="hidden w-64 shrink-0 border-r bg-card shadow-sm md:flex md:flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center gap-3 border-b px-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-sm shadow-sm">
            TM
          </div>
          <div>
            <span className="font-bold text-sm tracking-tight">TrueMatch</span>
            <p className="text-[10px] text-muted-foreground capitalize">{role} console</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {nav.map((item, idx) => {
            if (item.divider) {
              return <div key={`divider-${idx}`} className="my-2 border-t" />;
            }
            const active =
              item.href === `/${role}/dashboard`
                ? pathname === item.href
                : item.href && pathname.startsWith(item.href);
            return <NavLink key={item.href || `nav-${idx}`} item={item} active={active} />;
          })}
        </nav>

        {/* Bottom - User Menu */}
        <div className="border-t p-3">
          <UserDropdownMenu role={role} />
        </div>
      </aside>

      {/* Main */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Top bar */}
        <header className="flex h-16 shrink-0 items-center justify-between border-b bg-card px-6 shadow-sm">
          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden text-muted-foreground hover:bg-accent rounded-lg p-2 transition-colors"
          >
            {mobileMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </button>

          {/* Breadcrumb hint */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground md:flex flex-1">
            <span className="capitalize font-medium text-foreground">
              {nav.find((n) =>
                pathname === n.href || (n.href !== `/${role}/dashboard` && pathname.startsWith(n.href))
              )?.label ?? "Dashboard"}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <NotificationCenter />
          </div>
        </header>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-b bg-card shadow-sm">
            <nav className="space-y-1 px-3 py-4">
              {nav.map((item, idx) => {
                if (item.divider) {
                  return <div key={`divider-${idx}`} className="my-2 border-t" />;
                }
                const active =
                  item.href === `/${role}/dashboard`
                    ? pathname === item.href
                    : item.href && pathname.startsWith(item.href);
                return <NavLink key={item.href || `nav-${idx}`} item={item} active={active} />;
              })}
            </nav>
          </div>
        )}

        {/* Page */}
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  );
}

export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
    </div>
  );
}
