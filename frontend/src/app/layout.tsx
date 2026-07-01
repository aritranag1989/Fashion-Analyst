import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Japan Fashion & Handloom Intelligence Platform",
  description: "Multi-Agent RAG research platform for the Japanese handloom textile industry",
};

const NAV_LINKS = [
  { href: "/search", label: "Search" },
  { href: "/companies", label: "Companies" },
  { href: "/graph", label: "Graph" },
  { href: "/map", label: "Map" },
  { href: "/trade", label: "Trade" },
  { href: "/timeline", label: "Timeline" },
  { href: "/admin", label: "Admin" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-neutral-800 px-6 py-4 flex items-center gap-6">
          <Link href="/" className="font-semibold text-lg">
            Japan Fashion &amp; Handloom Intelligence
          </Link>
          <nav className="flex gap-4 text-sm text-neutral-400">
            {NAV_LINKS.map((link) => (
              <Link key={link.href} href={link.href} className="hover:text-neutral-100">
                {link.label}
              </Link>
            ))}
          </nav>
        </header>
        <main className="max-w-5xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
