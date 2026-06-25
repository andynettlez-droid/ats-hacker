import type { Metadata } from 'next';

// Post-purchase page — unique title, but should not be indexed.
export const metadata: Metadata = {
  title: 'Your Optimized Resume — ATSHacker',
  description: 'Download your honestly rewritten, keyword-matched resume as a PDF and ATS-friendly .docx.',
  robots: {
    index: false,
    follow: false,
  },
};

export default function SuccessLayout({ children }: { children: React.ReactNode }) {
  return children;
}
