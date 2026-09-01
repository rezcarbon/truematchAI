"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, AlertCircle } from "lucide-react";

// Singpass (OIDC) callback. The browser only relays the `code` + `state` to the
// backend via the BFF proxy; the authorization-code exchange, ID-token
// decryption, and verification all happen server-side. No identity tokens are
// processed in the browser.
//
// NOTE (Web track B): persisting the returned tokens into the NextAuth session
// is handled where auth is wired. Here we perform the exchange and surface
// success/error; on success we hand off to the dashboard.
type Phase = "working" | "success" | "error";

export default function SingpassCallbackPage() {
  return (
    <Suspense fallback={null}>
      <SingpassCallback />
    </Suspense>
  );
}

function SingpassCallback() {
  const router = useRouter();
  const params = useSearchParams();
  const [phase, setPhase] = useState<Phase>("working");
  const [message, setMessage] = useState<string>("");

  useEffect(() => {
    const code = params.get("code");
    const state = params.get("state");
    if (!code || !state) {
      setPhase("error");
      setMessage("Missing authorization code or state.");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/proxy/auth/singpass/callback", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code, state }),
        });
        if (!res.ok) throw new Error(`Exchange failed (${res.status})`);
        if (cancelled) return;
        setPhase("success");
        // Land on the AI Assistant (chat) by default, consistent with password login.
        router.replace("/chat");
      } catch (err) {
        if (cancelled) return;
        setPhase("error");
        setMessage(err instanceof Error ? err.message : "Sign-in failed.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [params, router]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {phase === "error" ? (
            <AlertCircle className="h-5 w-5 text-destructive" />
          ) : (
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
          )}
          {phase === "error" ? "Sign-in could not be completed" : "Completing Singpass sign-in"}
        </CardTitle>
        <CardDescription>
          {phase === "error"
            ? "Your identity could not be verified."
            : "We're verifying your identity and setting up your session."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {phase === "error" && (
          <>
            <p className="text-sm text-destructive">{message}</p>
            <Link href="/login">
              <Button className="w-full" variant="outline">
                Back to sign in
              </Button>
            </Link>
          </>
        )}
        {phase !== "error" && (
          <p className="text-sm text-muted-foreground">
            The authorization-code exchange is handled server-side; no identity tokens are
            processed in the browser.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
