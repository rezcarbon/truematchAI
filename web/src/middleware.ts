// Role-based route protection. Unauthenticated users are redirected to /login;
// authenticated users without the required role are denied. Gates the three
// role areas; everything else (landing, auth pages, /api) is public.

import { withAuth } from "next-auth/middleware";

export default withAuth({
  pages: { signIn: "/login" },
  callbacks: {
    authorized: ({ token, req }) => {
      const path = req.nextUrl.pathname;
      if (path.startsWith("/admin")) return token?.role === "admin";
      if (path.startsWith("/recruiter")) {
        return token?.role === "recruiter" || token?.role === "admin";
      }
      if (path.startsWith("/candidate")) return !!token;
      return true;
    },
  },
});

export const config = {
  matcher: ["/candidate/:path*", "/recruiter/:path*", "/admin/:path*"],
};
