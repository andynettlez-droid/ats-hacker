import type { Metadata } from 'next';

// Admin dashboard must never be indexed.
export const metadata: Metadata = {
  title: 'Admin — ATSHacker',
  robots: {
    index: false,
    follow: false,
  },
};

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return children;
}
