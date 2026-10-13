import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useRef, useEffect, useContext, createContext, useCallback } from "react";
import type { ReactNode } from "react";
import { useSession, signOut } from "next-auth/react";
import {
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
'use client';
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ============================================================================
// TYPES
// ============================================================================

export interface NavItem {
  href?: string;
  label?: string;
  icon?: React.ElementType;
  badge?: number;
  divider?: boolean;
  indent?: boolean;
}

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration?: number;
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (message: string, type: ToastType, duration?: number) => void;
  removeToast: (id: string) => void;
}

interface WebSocketMessage<T = Record<string, unknown>> {
  type: string;
  timestamp?: string;
  data?: T;
  [key: string]: unknown;
}

type WebSocketMessageHandler = (message: WebSocketMessage) => void;

// ============================================================================
// TOAST PROVIDER & HOOK
// ============================================================================

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback(
    (message: string, type: ToastType = 'info', duration: number = 3000) => {
      const id = Math.random().toString(36).substr(2, 9);
      const toast: Toast = { id, message, type, duration };

      setToasts((prev) => [...prev, toast]);

      if (duration > 0) {
        setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== id));
        }, duration);
      }
    },
    []
  );

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
}

interface ToastContainerProps {
  toasts: Toast[];
  onRemove: (id: string) => void;
}

function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-3 pointer-events-none">
      {toasts.map((toast) => (
        <ToastItem
          key={toast.id}
          toast={toast}
          onRemove={onRemove}
        />
      ))}
    </div>
  );
}

interface ToastItemProps {
  toast: Toast;
  onRemove: (id: string) => void;
}

function ToastItem({ toast, onRemove }: ToastItemProps) {
  const bgColor = {
    success: 'bg-green-50 border-green-200',
    error: 'bg-red-50 border-red-200',
    warning: 'bg-yellow-50 border-yellow-200',
    info: 'bg-blue-50 border-blue-200',
  }[toast.type];

  const textColor = {
    success: 'text-green-800',
    error: 'text-red-800',
    warning: 'text-yellow-800',
    info: 'text-blue-800',
  }[toast.type];

  const Icon = {
    success: CheckCircle2,
    error: AlertCircle,
    warning: AlertCircle,
    info: Info,
  }[toast.type];

  return (
    <div
      className={cn(
        'pointer-events-auto flex items-start gap-3 rounded-lg border p-4 shadow-lg animate-in slide-in-from-right-full duration-300',
        bgColor
      )}
    >
      <Icon className={cn('h-5 w-5 flex-shrink-0 mt-0.5', textColor)} />
      <p className={cn('flex-1 text-sm font-medium', textColor)}>
        {toast.message}
      </p>
      <button
        onClick={() => onRemove(toast.id)}
        className={cn(
          'flex-shrink-0 rounded hover:bg-black/10 p-1 transition-colors',
          textColor
        )}
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

// ============================================================================
// UI COMPONENTS
// ============================================================================

function Button({
  className,
  variant = "default",
  size = "default",
  ...props
}: {
  className?: string;
  variant?: "default" | "outline" | "ghost";
  size?: "default" | "sm" | "lg";
  [key: string]: unknown;
}) {
  const variants = {
    default: "bg-blue-600 text-white hover:bg-blue-700",
    outline: "border border-gray-300 bg-white hover:bg-gray-50",
    ghost: "hover:bg-gray-100",
  };

  const sizes = {
    default: "px-4 py-2",
    sm: "px-3 py-1 text-sm",
    lg: "px-6 py-3 text-lg",
  };

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  );
}

// ============================================================================
// WEBSOCKET HOOK
// ============================================================================

function useNotificationWebSocket(
  onNotification: WebSocketMessageHandler,
  enabled: boolean = false
): { isConnected: boolean } {
  const { data: session } = useSession();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const accessToken = (session as any)?.accessToken;

  useEffect(() => {
    if (!enabled || !accessToken) return;

    const connectWebSocket = () => {
      const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const backendHost = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
      const url = `${protocol}//${backendHost}:8000/api/v1/notifications/ws?token=${accessToken}`;

      try {
        const ws = new WebSocket(url);

        ws.onopen = () => {
          console.log('WebSocket connected to notifications');
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            onNotification(message);

            if (message.notification_id) {
              ws.send(JSON.stringify({ type: 'ack', notification_id: message.notification_id }));
            }
          } catch (err) {
            console.error('Failed to parse notification:', err);
          }
        };

        ws.onerror = (error) => {
          console.error('Notification WebSocket error:', error);
        };

        ws.onclose = () => {
          console.log('Notification WebSocket disconnected, reconnecting...');
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
        };

        wsRef.current = ws;
      } catch (err) {
        console.error('Failed to connect notification WebSocket:', err);
      }
    };

    connectWebSocket();

    const pingInterval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [enabled, accessToken, onNotification]);

  return { isConnected: wsRef.current?.readyState === WebSocket.OPEN };
}

// ============================================================================
// USER DROPDOWN MENU
// ============================================================================

function getInitials(name?: string | null | undefined, email?: string | null | undefined): string {
  if (name && name.trim()) {
    const parts = name.trim().split(' ');
    return (parts[0][0] + (parts[1]?.[0] || '')).toUpperCase();
  }
  if (email) {
    const localPart = email.split('@')[0];
    const parts = localPart.split(/[._-]/);
    return (parts[0][0] + (parts[1]?.[0] || '')).toUpperCase();
  }
  return '?';
}

function UserDropdownMenu({ role }: { role: string }) {
  const { data: session } = useSession();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const user = session?.user;
  const initials = getInitials(user?.name, user?.email);
  const displayName = user?.name || user?.email?.split('@')[0] || 'User';

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 rounded-lg px-3 py-2 hover:bg-accent transition-colors w-full"
      >
        <div className={cn(
          'flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold flex-shrink-0',
          'bg-gradient-to-br from-primary to-primary/70 text-primary-foreground'
        )}>
          {initials}
        </div>
        <div className="flex-1 min-w-0 text-left">
          <p className="text-xs font-medium truncate">{displayName}</p>
          <p className="text-[10px] text-muted-foreground truncate">{user?.email}</p>
        </div>
        <ChevronDown
          className={cn(
            'h-4 w-4 text-muted-foreground transition-transform flex-shrink-0',
            isOpen && 'rotate-180'
          )}
        />
      </button>

      {isOpen && (
        <div className="absolute bottom-full mb-2 left-0 right-0 bg-card border rounded-lg shadow-lg z-50 overflow-hidden">
          <div className="px-3 py-2 border-b">
            <p className="text-xs text-muted-foreground px-1">Logged in as</p>
            <p className="text-sm font-medium px-1 mt-1">{displayName}</p>
            <p className="text-xs text-muted-foreground px-1">{user?.email}</p>
          </div>

          <div className="py-1">
            <Link
              href={`/${role}/profile`}
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-3 py-2 text-sm hover:bg-accent transition-colors"
            >
              <User className="h-4 w-4 text-muted-foreground" />
              <span>View profile</span>
            </Link>

            <Link
              href={`/${role}/settings`}
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-3 py-2 text-sm hover:bg-accent transition-colors"
            >
              <Settings className="h-4 w-4 text-muted-foreground" />
              <span>Settings</span>
            </Link>
          </div>

          <div className="border-t py-1">
            <button
              onClick={() => signOut({ callbackUrl: '/login' })}
              className="flex items-center gap-3 px-3 py-2 text-sm hover:bg-accent transition-colors w-full text-left text-red-600"
            >
              <LogOut className="h-4 w-4" />
              <span>Sign out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// NOTIFICATION CENTER
// ============================================================================

interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  action_url?: string;
}

function NotificationCenter() {
  const { addToast } = useToast();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    setLoading(false);
  }, []);

  useNotificationWebSocket(
    (message) => {
      if (message.type !== 'pong' && message.type !== 'connected') {
        const newNotification: Notification = {
          id: (message.notification_id as string) || `notif-${Date.now()}`,
          type: message.type,
          title: (message.title as string) || 'New Notification',
          message: (message.message as string) || '',
          timestamp: new Date().toISOString(),
          read: false,
          action_url: message.action_url as string | undefined,
        };

        setNotifications((prev) => [newNotification, ...prev]);
        addToast(newNotification.title, 'info');
      }
    },
    false
  );

  const unreadCount = notifications.filter((n) => !n.read).length;

  const handleMarkAsRead = async (notificationId: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n))
    );
  };

  const handleMarkAllAsRead = async () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    addToast('All notifications marked as read', 'success');
  };

  const handleDelete = async (notificationId: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== notificationId));
    addToast('Notification deleted', 'success');
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 hover:bg-gray-100 rounded-lg transition-colors"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
            {unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
          <div className="p-4 border-b flex items-center justify-between">
            <h3 className="font-semibold">Notifications</h3>
            {unreadCount > 0 && (
              <Button
                size="sm"
                variant="ghost"
                onClick={handleMarkAllAsRead}
                className="text-xs"
              >
                Mark all as read
              </Button>
            )}
          </div>

          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-5 w-5 animate-spin" />
              </div>
            ) : notifications.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p className="text-sm">No notifications yet</p>
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 border-b hover:bg-gray-50 transition-colors ${
                    !notification.read ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-1">
                      <p className="font-medium text-sm">{notification.title}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {notification.message}
                      </p>
                      <p className="text-xs text-muted-foreground mt-2">
                        {new Date(notification.timestamp).toLocaleTimeString()}
                      </p>
                    </div>

                    <div className="flex gap-1">
                      {!notification.read && (
                        <button
                          onClick={() => handleMarkAsRead(notification.id)}
                          className="p-1 hover:bg-gray-200 rounded transition-colors"
                          title="Mark as read"
                        >
                          <Check className="h-4 w-4 text-green-600" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(notification.id)}
                        className="p-1 hover:bg-gray-200 rounded transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4 text-red-600" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {notifications.length > 0 && (
            <div className="p-3 border-t text-center">
              <Button
                variant="ghost"
                size="sm"
                className="w-full text-xs"
                onClick={() => setIsOpen(false)}
              >
                Close
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// NAV LINK COMPONENT
// ============================================================================

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
        item.indent && "pl-8",
        active
          ? "bg-primary text-primary-foreground shadow-sm"
          : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
      )}
    >
      {!item.indent && <Icon className="h-4 w-4 shrink-0" />}
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

// ============================================================================
// APP SHELL COMPONENT
// ============================================================================

function AppShell({
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
                : !!(item.href && pathname.startsWith(item.href));
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
                pathname === n.href || (n.href && n.href !== `/${role}/dashboard` && pathname.startsWith(n.href))
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
                    : !!(item.href && pathname.startsWith(item.href));
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

// ============================================================================
// LAYOUT COMPONENT
// ============================================================================

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
    <ToastProvider>
      <AppShell role="admin" nav={nav}>
        {children}
      </AppShell>
    </ToastProvider>
  );
}

  LayoutDashboard, Briefcase, Users, GitCompare,
  FileSearch, CheckSquare, Bot, Settings,
  ChevronRight, Menu, X, ChevronDown, User, LogOut,
  Bell, Loader2, Trash2, Check,
  CheckCircle2, AlertCircle, Info
} from "lucide-react";

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

