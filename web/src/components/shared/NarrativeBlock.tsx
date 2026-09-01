import type { ReactNode } from "react";

export function NarrativeBlock({
  title,
  children,
}: {
  title?: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-lg border bg-card p-5">
      {title && <h4 className="mb-2 text-sm font-semibold text-muted-foreground">{title}</h4>}
      <div className="prose prose-sm max-w-none leading-relaxed text-foreground">{children}</div>
    </div>
  );
}
