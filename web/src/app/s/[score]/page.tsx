import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowRight, CheckCircle, Share2, XCircle } from 'lucide-react';
import { SignalMascot } from '@/components/SignalMascot';

const BASE = (process.env.NEXT_PUBLIC_SITE_URL || 'https://ats-hacker-swart.vercel.app').replace(/\/$/, '');

type Params = { score: string };
type Search = { m?: string; mk?: string; hit?: string };

function clampScore(raw: string) {
  return Math.max(0, Math.min(100, parseInt(raw, 10) || 0));
}

function safeCount(raw?: string) {
  return Math.max(0, Math.min(99, parseInt(raw || '0', 10) || 0));
}

function sanitizeKeyword(keyword: string): string {
  const normalized = keyword
    .replace(/[^\w\s+#./-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return normalized.length > 34 ? `${normalized.slice(0, 31)}...` : normalized;
}

function parseSamples(raw?: string, limit = 3): string[] {
  const seen = new Set<string>();
  return (raw || '')
    .split('|')
    .map(sanitizeKeyword)
    .filter((keyword) => {
      const key = keyword.toLowerCase();
      if (!keyword || seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .slice(0, limit);
}

function scoreLabel(score: number) {
  if (score >= 75) return 'Strong Signal';
  if (score >= 50) return 'Needs Sharper Targeting';
  return 'Qualified, But Invisible';
}

function scoreColor(score: number) {
  if (score >= 75) return 'text-emerald-400';
  if (score >= 50) return 'text-amber-300';
  return 'text-red-300';
}

function buildQuery(score: number, missing: number, missingSamples: string[], matchedSamples: string[]) {
  const params = new URLSearchParams();
  params.set('score', String(score));
  params.set('m', String(missing));
  if (missingSamples.length) params.set('mk', missingSamples.join('|'));
  if (matchedSamples.length) params.set('hit', matchedSamples.join('|'));
  return params.toString();
}

function buildSharePath(score: number, missing: number, missingSamples: string[], matchedSamples: string[]) {
  const params = new URLSearchParams();
  params.set('m', String(missing));
  if (missingSamples.length) params.set('mk', missingSamples.join('|'));
  if (matchedSamples.length) params.set('hit', matchedSamples.join('|'));
  return `/s/${score}?${params.toString()}`;
}

export async function generateMetadata({
  params,
  searchParams,
}: {
  params: Promise<Params>;
  searchParams: Promise<Search>;
}): Promise<Metadata> {
  const { score } = await params;
  const { m, mk, hit } = await searchParams;
  const s = clampScore(score);
  const missing = safeCount(m);
  const missingSamples = parseSamples(mk, 3);
  const matchedSamples = parseSamples(hit, 2);
  const og = `${BASE}/api/og?${buildQuery(s, missing, missingSamples, matchedSamples)}`;
  const title = `Signal score: ${s}/100 - ${scoreLabel(s)}`;
  const description =
    missing > 0
      ? `${missing} target-job gaps found. Check your own free Signal match score before you apply.`
      : 'Check your own free Signal match score before you apply.';
  const sharePath = buildSharePath(s, missing, missingSamples, matchedSamples);
  return {
    title,
    description,
    openGraph: {
      title,
      description,
      url: `${BASE}${sharePath}`,
      images: [{ url: og, width: 1200, height: 630 }],
    },
    twitter: { card: 'summary_large_image', title, description, images: [og] },
  };
}

export default async function SharePage({ params, searchParams }: { params: Promise<Params>; searchParams: Promise<Search> }) {
  const { score } = await params;
  const { m, mk, hit } = await searchParams;
  const s = clampScore(score);
  const missing = safeCount(m);
  const missingSamples = parseSamples(mk, 3);
  const matchedSamples = parseSamples(hit, 2);
  const label = scoreLabel(s);
  const color = scoreColor(s);

  return (
    <div className="min-h-screen bg-[#030712] text-slate-50 font-sans selection:bg-cyan-500/20">
      <main className="mx-auto flex min-h-screen w-full max-w-6xl items-center px-5 py-10">
        <div className="grid w-full gap-5 lg:grid-cols-[1.05fr_0.95fr]">
          <section className="rounded-[2rem] border border-cyan-300/20 bg-[#07111f]/95 p-6 shadow-[0_28px_110px_rgba(0,0,0,0.38),inset_0_0_70px_rgba(56,213,255,0.05)] sm:p-8">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl border border-cyan-200/30 bg-[#020617]/80 shadow-[0_0_34px_rgba(56,213,255,0.22),inset_0_0_22px_rgba(56,213,255,0.08)]">
                  <SignalMascot className="signal-mascot h-11 w-11" />
                </span>
                <div>
                  <p className="text-2xl font-black tracking-tighter">
                    Signal<span className="text-emerald-400">.</span>
                  </p>
                  <p className="text-xs font-bold uppercase tracking-widest text-cyan-100/60">by ATSHacker</p>
                </div>
              </div>
              <span className="inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-2 text-xs font-black uppercase tracking-widest text-cyan-100">
                <Share2 className="h-3.5 w-3.5" />
                Score Card
              </span>
            </div>

            <div className="mt-10">
              <p className="text-sm font-black uppercase tracking-[0.24em] text-cyan-100/70">{label}</p>
              <div className="mt-3 flex items-end leading-none">
                <span className={`text-[7rem] font-black tabular-nums sm:text-[9rem] ${color}`}>{s}</span>
                <span className="pb-4 text-4xl font-black text-slate-500">/100</span>
              </div>
              <p className="max-w-xl text-xl font-bold leading-snug text-slate-200">
                {missing > 0
                  ? `${missing} target-job gaps could keep this resume harder to find in recruiter search.`
                  : 'This resume has strong target-job language for recruiter search.'}
              </p>
            </div>

            <div className="mt-8 rounded-2xl border border-white/10 bg-white/[0.04] p-4">
              <p className="text-xs font-black uppercase tracking-widest text-slate-400">Privacy note</p>
              <p className="mt-2 text-sm font-semibold leading-relaxed text-slate-300">
                This public card shares only a score and keyword examples. It does not include resume text, job description text, or personal details.
              </p>
            </div>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link href="/" className="inline-flex min-h-12 flex-1 items-center justify-center gap-2 rounded-xl border border-cyan-200/40 bg-gradient-to-r from-blue-600 via-cyan-600 to-emerald-500 px-5 text-sm font-extrabold text-white shadow-[0_18px_60px_rgba(56,213,255,0.22)] transition hover:brightness-110">
                <span>Check my free Signal score</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </section>

          <aside className="rounded-[2rem] border border-cyan-300/15 bg-white/[0.04] p-6 shadow-[inset_0_0_52px_rgba(56,213,255,0.035)] sm:p-8">
            <div className="space-y-6">
              <div>
                <p className="text-xs font-black uppercase tracking-widest text-cyan-100/70">Recruiter search proof</p>
                <h1 className="mt-3 text-3xl font-black tracking-tight text-slate-50">A better resume is easier to find.</h1>
                <p className="mt-3 text-sm font-semibold leading-relaxed text-slate-300">
                  Signal compares the resume against a target job, then shows the gaps a recruiter search may miss.
                </p>
              </div>

              <div className="rounded-2xl border border-red-300/20 bg-red-400/10 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="flex items-center gap-2 text-sm font-black text-red-100">
                    <XCircle className="h-4 w-4" />
                    Missing gaps
                  </p>
                  <span className="rounded-full bg-red-300/10 px-3 py-1 text-xs font-black text-red-100">{missing}</span>
                </div>
                {missingSamples.length > 0 ? (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {missingSamples.map((keyword) => (
                      <span key={keyword} className="rounded-lg border border-red-200/10 bg-[#020617]/45 px-2.5 py-1.5 text-xs font-bold text-red-50">
                        {keyword}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="mt-3 text-sm font-semibold text-red-50/70">No keyword examples were shared.</p>
                )}
              </div>

              <div className="rounded-2xl border border-emerald-300/20 bg-emerald-400/10 p-4">
                <p className="flex items-center gap-2 text-sm font-black text-emerald-100">
                  <CheckCircle className="h-4 w-4" />
                  Language already matched
                </p>
                {matchedSamples.length > 0 ? (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {matchedSamples.map((keyword) => (
                      <span key={keyword} className="rounded-lg border border-emerald-200/10 bg-[#020617]/45 px-2.5 py-1.5 text-xs font-bold text-emerald-50">
                        {keyword}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="mt-3 text-sm font-semibold text-emerald-50/70">Run a free scan to see matched keywords for your own resume.</p>
                )}
              </div>

              <div className="rounded-2xl border border-cyan-300/15 bg-[#020617]/45 p-4">
                <p className="text-sm font-bold leading-relaxed text-slate-300">
                  Qualified people get missed when their resume uses vague language. Signal helps turn real experience into clearer job-description signal.
                </p>
              </div>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
