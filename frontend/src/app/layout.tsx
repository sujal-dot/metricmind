import type { Metadata } from "next";
import "./globals.css";
import Providers from "@/providers";
import { AppShell } from "@/components/AppShell";

export const metadata: Metadata = {
  title: "MetricMind",
  description: "Agentic Business Intelligence Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`h-full antialiased font-sans`}
      suppressHydrationWarning
    >
      <body className="min-h-full bg-gray-50" suppressHydrationWarning>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
