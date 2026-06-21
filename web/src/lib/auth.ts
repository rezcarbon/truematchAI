// NextAuth configuration (server-side only). Credentials are validated against
// the TrueMatch backend; the issued access/refresh tokens are kept inside the
// encrypted NextAuth JWT (never exposed to the browser) and forwarded by the
// BFF proxy on the user's behalf. Singpass is handled by the backend OIDC flow
// + the /singpass-callback page.

import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

// Get BACKEND URL - read dynamically to ensure env vars are loaded
function getBackendUrl(): string {
  const backend = process.env.BACKEND_API_URL || "https://api.truematch.ai/v1";
  return backend;
}

function decodeExpMs(jwt: string): number {
  try {
    const payload = jwt.split(".")[1];
    const json = JSON.parse(Buffer.from(payload, "base64").toString("utf8"));
    return (json.exp ?? 0) * 1000;
  } catch {
    return 0;
  }
}

async function refreshTokens(token: Record<string, unknown>) {
  try {
    const backend = getBackendUrl();
    const res = await fetch(`${backend}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: token.refreshToken }),
    });
    if (!res.ok) throw new Error("refresh failed");
    const data = await res.json();
    return {
      ...token,
      accessToken: data.access_token,
      refreshToken: data.refresh_token ?? token.refreshToken,
      accessTokenExpires: decodeExpMs(data.access_token),
      error: undefined,
    };
  } catch {
    return { ...token, error: "RefreshAccessTokenError" };
  }
}

export const authOptions: NextAuthOptions = {
  session: { strategy: "jwt" },
  secret: process.env.NEXTAUTH_SECRET || "dev-secret-change-in-production",
  pages: {
    signIn: "/login",
    error: "/login?error=auth_failed",
  },
  providers: [
    CredentialsProvider({
      name: "Email",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        try {
          const backend = getBackendUrl();
          if (!credentials?.email || !credentials?.password) {
            console.error("Missing email or password");
            return null;
          }
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

          let login;
          try {
            login = await fetch(`${backend}/auth/login`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ email: credentials.email, password: credentials.password }),
              signal: controller.signal,
            });
          } finally {
            clearTimeout(timeoutId);
          }
          if (!login.ok) {
            const errorText = await login.text();
            console.error("Login failed:", errorText);
            console.error("Full login response:", { status: login.status, statusText: login.statusText, body: errorText });
            return null;
          }
          const tokens = await login.json();
          const meRes = await fetch(`${backend}/auth/me`, {
            headers: { Authorization: `Bearer ${tokens.access_token}` },
          });
          if (!meRes.ok) {
            const errorText = await meRes.text();
            console.error("/me endpoint failed:", errorText);
            return null;
          }
          const me = await meRes.json();
          const result = {
            id: me.id,
            email: me.email,
            name: me.display_name ?? me.email,
            role: me.role,
            accessToken: tokens.access_token,
            refreshToken: tokens.refresh_token,
          } as unknown as { id: string };
          return result;
        } catch (error) {
          console.error("Authorization error:", error);
          console.error("Error type:", error instanceof Error ? error.constructor.name : typeof error);
          console.error("Error message:", error instanceof Error ? error.message : String(error));
          if (error instanceof Error && error.stack) {
            console.error("Error stack:", error.stack);
          }
          return null;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        const u = user as unknown as Record<string, unknown>;
        token.role = u.role as string;
        token.accessToken = u.accessToken as string;
        token.refreshToken = u.refreshToken as string;
        token.accessTokenExpires = decodeExpMs(u.accessToken as string);
        return token;
      }
      // Return the existing token while still valid (60s leeway); else refresh.
      const expires = token.accessTokenExpires as number | undefined;
      if (expires && Date.now() < expires - 60_000) return token;
      return refreshTokens(token as Record<string, unknown>);
    },
    async session({ session, token }) {
      try {
        if (session.user) {
          (session.user as { role?: string; accessToken?: string }).role = token.role as string;
          (session.user as { role?: string; accessToken?: string }).accessToken = token.accessToken as string;
        }
        (session as { error?: string; accessToken?: string }).error = token.error as string | undefined;
        (session as { error?: string; accessToken?: string }).accessToken = token.accessToken as string;
        return session;
      } catch (error) {
        console.error("Session callback error:", error);
        throw error;
      }
    },
  },
};
