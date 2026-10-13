"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Lightweight, dependency-free AlertDialog primitives.
 *
 * Provides the same named exports the app's components expect
 * (AlertDialog, AlertDialogContent, AlertDialogTitle, AlertDialogDescription,
 * AlertDialogAction, AlertDialogCancel) without pulling in @radix-ui. The
 * dialog renders as a fixed overlay + centered panel and is controlled via the
 * `open` prop on <AlertDialog>.
 */

export function AlertDialog({
  open = true,
  children,
}: {
  open?: boolean;
  children: React.ReactNode;
}) {
  if (!open) return null;
  return (
    <div
      role="alertdialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <div className="absolute inset-0 bg-black/50" />
      {children}
    </div>
  );
}

export function AlertDialogContent({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "relative z-10 w-full max-w-lg rounded-lg border bg-card p-6 text-card-foreground shadow-lg",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function AlertDialogHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("space-y-2", className)} {...props} />;
}

export function AlertDialogFooter({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end",
        className
      )}
      {...props}
    />
  );
}

export function AlertDialogTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h2 className={cn("text-lg font-semibold", className)} {...props} />
  );
}

export function AlertDialogDescription({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-sm text-muted-foreground", className)} {...props} />
  );
}

export function AlertDialogAction({
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cn(
        "inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
}

export function AlertDialogCancel({
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cn(
        "inline-flex h-10 items-center justify-center rounded-md border border-input bg-background px-4 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground disabled:pointer-events-none disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
}
