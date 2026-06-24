// BFF proxy. The browser calls /api/proxy/* and this server-side route forwards
// to the real backend. It injects the LOGGED-IN USER's access token (read from
// the encrypted NextAuth JWT) so the backend enforces per-user authorization.
// Falls back to a service token for unauthenticated/public calls.
//
// IP-safety: no backend secrets, prompts, or governance policy ever reach the
// browser bundle. This file runs only on the server.

import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";

const BACKEND = process.env.BACKEND_API_URL || "https://api.truematch.ai/v1";
const SERVICE_TOKEN = process.env.BACKEND_API_TOKEN;

async function forward(req: NextRequest, segments: string[]) {
  const path = segments.join("/");
  const url = new URL(`${BACKEND}/${path}`);
  url.search = req.nextUrl.search;

  const headers: HeadersInit = {
    // Forward the caller's Accept so SSE endpoints (chat streaming) can
    // negotiate text/event-stream while everything else stays JSON.
    Accept: req.headers.get("accept") ?? "application/json",
    "Content-Type": req.headers.get("content-type") ?? "application/json",
  };

  // Prefer the authenticated user's token; fall back to the service token.
  const jwt = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
  const bearer = (jwt as { accessToken?: string } | null)?.accessToken ?? SERVICE_TOKEN;
  if (bearer) headers["Authorization"] = `Bearer ${bearer}`;

  const init: RequestInit = { method: req.method, headers, cache: "no-store" };
  if (!["GET", "HEAD"].includes(req.method)) {
    // For file uploads with multipart/form-data, preserve binary data
    // Don't convert to text as it corrupts binary files
    const contentType = req.headers.get("content-type") || "";
    if (contentType.includes("multipart/form-data") || contentType.includes("application/octet-stream")) {
      // Use arrayBuffer for binary-safe transmission
      init.body = await req.arrayBuffer();
    } else {
      // Safe to use text for JSON and other text-based content
      init.body = await req.text();
    }
  }

  try {
    const res = await fetch(url.toString(), init);

    // Stream Server-Sent Events straight through (chat token streaming).
    // Buffering with res.text() would collapse the token-by-token UX into a
    // single delayed blob, so pass the upstream ReadableStream through intact.
    const upstreamType = res.headers.get("content-type") ?? "";
    if (upstreamType.includes("text/event-stream") && res.body) {
      return new NextResponse(res.body, {
        status: res.status,
        headers: {
          "Content-Type": "text/event-stream; charset=utf-8",
          "Cache-Control": "no-cache, no-transform",
          Connection: "keep-alive",
          // Disable proxy buffering (nginx and friends) so chunks flush live.
          "X-Accel-Buffering": "no",
        },
      });
    }

    const body = await res.text();
    return new NextResponse(body, {
      status: res.status,
      headers: { "Content-Type": res.headers.get("content-type") ?? "application/json" },
    });
  } catch {
    return NextResponse.json(
      { error: "backend_unreachable", message: "Backend not available." },
      { status: 502 }
    );
  }
}

type Ctx = { params: { path: string[] } };

export const GET = (req: NextRequest, { params }: Ctx) => forward(req, params.path);
export const POST = (req: NextRequest, { params }: Ctx) => forward(req, params.path);
export const PUT = (req: NextRequest, { params }: Ctx) => forward(req, params.path);
export const PATCH = (req: NextRequest, { params }: Ctx) => forward(req, params.path);
export const DELETE = (req: NextRequest, { params }: Ctx) => forward(req, params.path);
