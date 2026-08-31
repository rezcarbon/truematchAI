import type { Metadata } from "next";
import type { ReactNode } from "react";
import "@/styles/globals.css";
import { Providers } from "@/components/providers";

export const metadata: Metadata = {
  title: "TrueMatch: AI-Powered Hiring Assessment | Capability-First Recruiting",
  description:
    "Find exceptional candidates traditional ATS overlook. Evidence-based assessment. Governed by 6 fairness gates. Regulatory-ready.",
  openGraph: {
    title: "Discover exceptional candidates beyond keywords",
    description: "Resume keywords aren't capability. We score both — then show you the difference. That's where great hiring happens.",
    type: "website",
  },
  icons: {
    icon: [
      { url: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><defs><linearGradient id='grad' x1='0%' y1='0%' x2='100%' y2='100%'><stop offset='0%' style='stop-color:%231E40AF;stop-opacity:1' /><stop offset='100%' style='stop-color:%2314B8A6;stop-opacity:1' /></linearGradient></defs><rect width='100' height='100' fill='url(%23grad)'/><text x='50' y='60' font-size='60' font-weight='bold' fill='white' text-anchor='middle'>T</text></svg>" },
    ],
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
