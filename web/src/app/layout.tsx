import type { Metadata } from "next";
import type { ReactNode } from "react";
import "@/styles/globals.css";
import { Providers } from "@/components/providers";

export const metadata: Metadata = {
  title: "TrueMatch — Capability-first hiring",
  description:
    "TrueMatch reads candidates for demonstrated capability, not just keyword match — surfacing the gap traditional ATS systems miss.",
  icons: {
    icon: [
      { url: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' fill='%230066FF'/><text x='50' y='60' font-size='60' font-weight='bold' fill='white' text-anchor='middle'>T</text></svg>" },
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
