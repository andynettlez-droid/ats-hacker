import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { SignalMascot } from '@/components/SignalMascot';

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
  const title = `I scored ${s}/100 on Signal by ATSHacker`;
  const description = 'See how well a resume matches a job description, then check your own free ATS match score.';
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
  const color = s >= 75 ? 'text-emerald-600' : s >= 50 ? 'text-amber-600' : 'text-red-600';

  return (
    <div className="min-h-screen bg-white text-slate-900 font-sans flex items-center justify-center p-6 selection:bg-emerald-500/20">
      <div className="bg-white border border-slate-200 rounded-3xl p-10 shadow-sm max-w-md w-full text-center space-y-6">
        <div className="flex items-center justify-center gap-2.5">
          <span className="grid h-10 w-10 place-items-center rounded-2xl border border-cyan-200/40 bg-[#07111f] shadow-[0_0_28px_rgba(56,213,255,0.18),inset_0_0_18px_rgba(56,213,255,0.08)]">
            <SignalMascot className="signal-mascot h-8 w-8" />
          </span>
          <span className="text-2xl font-black tracking-tighter text-slate-900">
            Signal<span className="text-emerald-600">.</span>
          </span>
        </div>
        <p className="text-slate-600">This resume scored</p>
        <div className="flex items-end justify-center">
          <span className={`text-7xl font-black ${color}`}>{s}</span>
          <span className="text-2xl text-slate-400 pb-2">/100</span>
        </div>
        <p className="text-sm text-slate-600">
          {missing > 0
            ? `${missing} job-description keywords were missing.`
            : 'against a target job description.'}
        </p>
        <p className="text-slate-600">
          Most resumes are found through keyword search. See how yours scores against any job, free.
        </p>
        <Link href="/">
          <button className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-lg py-4 rounded-xl transition-all duration-200 active:scale-[0.98] hover:shadow-md inline-flex items-center justify-center space-x-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50 focus-visible:ring-offset-2">
            <span>Check my free match score</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </Link>
      </div>
    </div>
  );
}
