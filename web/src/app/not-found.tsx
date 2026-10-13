import Link from 'next/link';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ============================================================================
// BUTTON COMPONENT
// ============================================================================

const buttonVariants = {
  default: "bg-blue-600 text-white hover:bg-blue-700",
  outline: "border border-gray-300 bg-white hover:bg-gray-50",
  ghost: "hover:bg-gray-100",
}

const buttonSizes = {
  default: "px-4 py-2",
  sm: "px-3 py-1 text-sm",
  lg: "px-6 py-3 text-lg",
}

type ButtonVariant = "default" | "outline" | "ghost"
type ButtonSize = "default" | "sm" | "lg"

function Button({
  className,
  variant = "default" as ButtonVariant,
  size = "default" as ButtonSize,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
  size?: ButtonSize
}) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none",
        buttonVariants[variant],
        buttonSizes[size],
        className
      )}
      {...props}
    />
  )
}

// ============================================================================
// NOT FOUND PAGE COMPONENT
// ============================================================================

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-8 text-center">
      <h1 className="text-3xl font-bold">404</h1>
      <p className="max-w-md text-sm text-muted-foreground">
        We couldn&apos;t find that page.
      </p>
      <Link href="/">
        <Button variant="outline">Back to home</Button>
      </Link>
    </div>
  );
}
// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

