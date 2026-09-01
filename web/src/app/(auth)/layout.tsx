import type { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 px-4">
      <div className="w-full max-w-md">
        <div className="mb-6 flex items-center justify-center gap-2">
          <div className="h-7 w-7 rounded-md bg-primary" />
          <span className="text-lg font-bold">TrueMatch</span>
        </div>
        {children}
      </div>
    </div>
  );
}
