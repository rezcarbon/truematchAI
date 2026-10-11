"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { signIn } from "next-auth/react";
import { cn } from "@/lib/utils";

function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-lg border border-gray-200 bg-white shadow-sm", className)} {...props} />;
}
function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />;
}
function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h2 className={cn("text-2xl font-semibold", className)} {...props} />;
}
function CardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-6 pt-0", className)} {...props} />;
}

export default function SingpassCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state");

    if (!code || !state) {
      setError("Missing authentication parameters");
      return;
    }

    // Handle callback
    signIn("singpass", { code, state, redirect: false }).then((result) => {
      if (result?.error) {
        setError(result.error);
      } else if (result?.ok) {
        router.replace("/chat");
      }
    });
  }, [router, searchParams]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Authenticating with Singpass</CardTitle>
      </CardHeader>
      <CardContent>
        {error ? (
          <p className="text-red-600">{error}</p>
        ) : (
          <p>Please wait while we authenticate you...</p>
        )}
      </CardContent>
    </Card>
  );
}
