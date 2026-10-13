"use client";

import { SessionProvider } from "next-auth/react";
import type { ReactNode } from "react";
import { ToastProvider } from "@/components/providers/ToastProvider";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import { cn } from "@/lib/utils";

// Card components
export function Card({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-lg border border-gray-200 bg-white shadow-sm", className)}
      {...props}
    />
  );
}

export function CardHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col space-y-1.5 p-6", className)}
      {...props}
    />
  );
}

export function CardTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h2
      className={cn("text-2xl font-semibold leading-none tracking-tight", className)}
      {...props}
    />
  );
}

export function CardDescription({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn("text-sm text-gray-500", className)}
      {...props}
    />
  );
}

export function CardContent({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("p-6 pt-0", className)} {...props} />
  );
}

// Button component
const buttonVariants = {
  default: "bg-blue-600 text-white hover:bg-blue-700",
  outline: "border border-gray-300 bg-white hover:bg-gray-50",
  ghost: "hover:bg-gray-100",
};

const buttonSizes = {
  default: "px-4 py-2",
  sm: "px-3 py-1 text-sm",
  lg: "px-6 py-3 text-lg",
};

export function Button({
  className,
  variant = "default",
  size = "default",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "outline" | "ghost";
  size?: "default" | "sm" | "lg";
}) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none",
        buttonVariants[variant as keyof typeof buttonVariants],
        buttonSizes[size as keyof typeof buttonSizes],
        className
      )}
      {...props}
    />
  );
}

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <SessionProvider>
        <ToastProvider>{children}</ToastProvider>
      </SessionProvider>
    </ThemeProvider>
  );
}
