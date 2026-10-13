import type { Metadata } from "next";
import { getServerSession } from "next-auth/next";

export const metadata: Metadata = {
  title: "TrueMatch - AI-Powered Job Matching",
  description: "Find the perfect match between candidates and opportunities",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getServerSession();

  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>
        <main>{children}</main>
      </body>
    </html>
  );
}
