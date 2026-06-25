import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';

const BASE = (process.env.NEXT_PUBLIC_SITE_URL || 'https://ats-hacker-swart.vercel.app').replace(/\/$/, '');

type Params = { score: string };
type Search = { m?: string };

function clampScore(raw: string) {
  return Math.max(0, Math.min(100, parseInt(raw, 10) || 0));
}

export async function generateMetadata({
  params,
  searchParams,
}: {
  params: Promise<Params>;
  searchParams: Promise<Search>;
}): Promise<Metadata> {
  const { score } = await params;
  const { m } = await searchParams;
  const s = clampScore(score);
  const missing = Math.max(0, parseInt(m || '0', 10) || 0);
  const og = `${BASE}/api/og?score=${s}${missing ? `&m=${missing}` : ''}`;
  const title = `I scored ${s}/100 on ATSHacker`;
  const description = 'See how well a resume matches a job description — then check your own free ATS match score.';
  return {
    title,
    description,
    openGraph: {
      title,
      description,
      url: `${BASE}/s/${s}`,
      images: [{ url: og, width: 1200, height: 630 }],
    },
    twitter: { card: 'summary_large_image', title, description, images: [og] },
  };
}

export default async function SharePage({ params, searchParams }: { params: Promise<Params>; searchParams: Promise<Search> }) {
  const { score } = await params;
  const { m } = await searchParams;
  const s = clampScore(score);
  const missing = Math.max(0, parseInt(m || '0', 10) || 0);
  const color = s >= 75 ? 'text-emerald-500' : s >= 50 ? 'text-yellow-500' : 'text-red-500';

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 font-sans flex items-center justify-center p-6 selection:bg-emerald-500/30">
      <div className="bg-neutral-900 border border-neutral-800 rounded-3xl p-10 shadow-2xl max-w-md w-full text-center space-y-6">
        <div className="text-2xl font-black tracking-tighter text-white">
          ATS<span className="text-emerald-500">Hacker.</span>
        </div>
        <p className="text-neutral-400">This resume scored</p>
        <div className="flex items-end justify-center">
          <span className={`text-7xl font-black ${color}`}>{s}</span>
          <span className="text-2xl text-neutral-500 pb-2">/100</span>
        </div>
        <p className="text-sm text-neutral-400">
          {missing > 0
            ? `${missing} job-description keywords were missing.`
            : 'against a target job description.'}
        </p>
        <p className="text-neutral-400">
          Most resumes are ranked by keyword match. See how yours scores against any job — free.
        </p>
        <Link href="/">
          <button className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-lg py-4 rounded-xl transition inline-flex items-center justify-center space-x-2">
            <span>Check my free match score</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </Link>
      </div>
    </div>
  );
}
