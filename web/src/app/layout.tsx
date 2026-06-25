import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";

// Set NEXT_PUBLIC_SITE_URL in your env (e.g. https://atshacker.com).
const BASE = (process.env.NEXT_PUBLIC_SITE_URL || "https://ats-hacker-swart.vercel.app").replace(/\/$/, "");
const DEFAULT_OG = `${BASE}/api/og?score=86`;

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const TITLE = "ATSHacker — Get Your Resume Past the Keyword Filter";
const DESCRIPTION =
  "Recruiters search and rank resumes by keyword. ATSHacker rewrites your resume to semantically match the job description so it ranks higher and gets seen ~3x more often — a one-time $9.99, no subscription.";

export const metadata: Metadata = {
  metadataBase: new URL(BASE),
  title: TITLE,
  description: DESCRIPTION,
  alternates: {
    canonical: "/",
  },
  icons: {
    icon: "/logo.png",
  },
  openGraph: {
    type: "website",
    siteName: "ATSHacker",
    title: TITLE,
    description: DESCRIPTION,
    url: BASE,
    images: [{ url: DEFAULT_OG, width: 1200, height: 630, alt: "ATSHacker — ATS match score" }],
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
    images: [DEFAULT_OG],
  },
};

// Site-wide structured data: Organization + WebSite.
const orgSchema = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "ATSHacker",
  url: BASE,
  logo: `${BASE}/logo.png`,
  description:
    "ATSHacker gives you a free ATS keyword match score and an honest $9.99 resume rewrite that semantically matches the job description.",
};

const websiteSchema = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "ATSHacker",
  url: BASE,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-white text-slate-900">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(orgSchema) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteSchema) }}
        />
        {children}
        <Analytics />
      </body>
    </html>
  );
}
