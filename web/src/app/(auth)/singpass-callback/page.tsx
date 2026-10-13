"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { signIn } from "next-auth/react";

export default function SingpassCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get the auth code from the callback
        const code = searchParams.get("code");
        const state = searchParams.get("state");
        const error = searchParams.get("error");

        // Handle errors from Singpass
        if (error) {
          setError(`Singpass login failed: ${error}`);
          setLoading(false);
          return;
        }

        if (!code) {
          setError("No authorization code received");
          setLoading(false);
          return;
        }

        // Sign in with the Singpass code
        const result = await signIn("singpass", {
          code,
          state,
          redirect: false,
        });

        if (result?.error) {
          setError(`Authentication failed: ${result.error}`);
          setLoading(false);
          return;
        }

        if (result?.ok) {
          // Redirect to the appropriate dashboard
          router.push("/candidate/dashboard");
        }
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "An error occurred";
        setError(`Error: ${message}`);
        setLoading(false);
      }
    };

    handleCallback();
  }, [searchParams, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-900 to-slate-800">
        <div className="text-center text-white">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mb-4"></div>
          <p className="text-lg">Completing Singpass login...</p>
          <p className="text-sm text-gray-400 mt-2">
            Please wait while we verify your credentials
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-900 to-slate-800 p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
              <svg
                className="h-6 w-6 text-red-600"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Login Failed
            </h3>
            <p className="text-sm text-gray-600 mb-4">{error}</p>
            <div className="flex gap-3">
              <a
                href="/auth/login"
                className="flex-1 px-4 py-2 text-center rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50 font-medium"
              >
                Back to Login
              </a>
              <a
                href="/auth/signup"
                className="flex-1 px-4 py-2 text-center rounded-md bg-blue-600 text-white hover:bg-blue-700 font-medium"
              >
                Sign Up
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // This should not be reached if callback is successful
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-900 to-slate-800">
      <div className="text-center text-white">
        <p className="text-lg">Authentication complete</p>
        <p className="text-sm text-gray-400 mt-2">Redirecting...</p>
      </div>
    </div>
  );
}
