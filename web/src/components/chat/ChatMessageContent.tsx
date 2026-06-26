"use client";

// Renders an assistant message as GitHub-flavored markdown (headings, bold,
// tables, lists, rules) instead of raw text, and upgrades a
// ```truematch-dashboard fenced JSON block into an interactive DashboardWidget.
//
// Streaming-safe: while tokens arrive the dashboard JSON may be incomplete, so
// parsing is defensive — an unparseable block falls back to a quiet skeleton
// until the closing fence streams in and it becomes valid.

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { DashboardWidget, type DashboardData } from "./DashboardWidget";

const DASHBOARD_LANG = "language-truematch-dashboard";

export function ChatMessageContent({
  content,
  onPrompt,
}: {
  content: string;
  onPrompt?: (text: string) => void;
}) {
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none break-words prose-headings:mt-3 prose-headings:mb-1 prose-p:my-1.5 prose-ul:my-1.5 prose-li:my-0.5 prose-pre:my-2 prose-table:my-2">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ className, children, ...props }) {
            // Intercept the dashboard block; render everything else as code.
            if (className?.includes("truematch-dashboard")) {
              const raw = String(children).trim();
              let data: DashboardData | null = null;
              try {
                data = JSON.parse(raw) as DashboardData;
              } catch {
                // Incomplete/streaming JSON — show a subtle placeholder.
                return (
                  <span className="block animate-pulse rounded-md bg-secondary/40 px-3 py-2 text-xs text-muted-foreground not-prose">
                    Rendering dashboard…
                  </span>
                );
              }
              return <DashboardWidget data={data} onPrompt={onPrompt} />;
            }
            return (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

export { DASHBOARD_LANG };
