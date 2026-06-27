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

const TITLE = "Signal by ATSHacker - Resume and Cover Letter Copilot";
const DESCRIPTION =
  "Signal compares your resume to a real job description, finds language recruiters may miss, and helps rewrite your real experience without inventing facts.";

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
    siteName: "Signal by ATSHacker",
    title: TITLE,
    description: DESCRIPTION,
    url: BASE,
    images: [{ url: DEFAULT_OG, width: 1200, height: 630, alt: "Signal by ATSHacker ATS match score" }],
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
  name: "Signal by ATSHacker",
  url: BASE,
  logo: `${BASE}/logo.png`,
  description:
    "Signal by ATSHacker gives users a free ATS keyword match score and honest one-time resume and cover letter optimization.",
};

const websiteSchema = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "Signal by ATSHacker",
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
