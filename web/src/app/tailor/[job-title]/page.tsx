import React from 'react';
import type { Metadata } from 'next';
import { CheckCircle, ArrowRight, XCircle, Lightbulb } from 'lucide-react';
import Link from 'next/link';
import { roles, roleMap, type Role } from '@/data/roles';

type Params = { 'job-title': string };

// Pre-render a page for every role in the dataset at build time (great for SEO).
export function generateStaticParams() {
  return roles.map((r) => ({ 'job-title': r.slug }));
}

function titleFromSlug(slug: string) {
  return slug.split('-').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function getRole(slug: string): Role {
  return (
    roleMap[slug] || {
      slug,
      title: titleFromSlug(slug),
      painPoint: "Recruiters search and rank candidates by keyword. If your resume doesn't semantically match the job description, it ranks low and gets buried before a human ever scrolls to it.",
      keywords: [],
      tips: [
        'Mirror the exact keywords and job title from the posting near the top of your resume.',
        'Quantify your achievements with numbers wherever possible.',
        'Use a clean, single-column layout so the ATS can parse every section.',
      ],
    }
  );
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { 'job-title': slug } = await params;
  const title = getRole(slug).title;
  return {
    title: `${title} Resume Keywords — Beat the ATS | ATSHacker`,
    description: `Recruiters rank ${title} resumes by keyword, and resumes that miss the right ones get buried. See the ATS keywords for ${title} roles and optimize your resume for $9.99.`,
    alternates: { canonical: `/tailor/${slug}` },
  };
}

export default async function TailoredLandingPage({ params }: { params: Promise<Params> }) {
  const { 'job-title': slug } = await params;
  const role = getRole(slug);
  const { title, painPoint, keywords, tips } = role;

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 font-sans selection:bg-emerald-500/30">
      <nav className="w-full p-6 flex justify-between items-center max-w-7xl mx-auto">
        <Link href="/" className="text-2xl font-black tracking-tighter text-white">
          ATS<span className="text-emerald-500">Hacker.</span>
        </Link>
      </nav>

      <main className="max-w-4xl mx-auto px-6 pt-16 pb-32 text-center">
        <div className="inline-flex items-center space-x-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-4 py-1.5 rounded-full text-sm font-bold tracking-wide mb-8">
          <span>Targeted specifically for {title} roles</span>
        </div>

        <h1 className="text-5xl lg:text-7xl font-black leading-[1.1] tracking-tight mb-8">
          Land your dream{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">{title}</span>{' '}
          job.
        </h1>

        <p className="text-xl text-neutral-400 leading-relaxed max-w-2xl mx-auto mb-6">
          {painPoint}
        </p>
        <p className="text-base text-neutral-500 leading-relaxed max-w-2xl mx-auto mb-12">
          Keyword-matched resumes are about 3x more likely to get seen. Check your {title} match score free, then we&apos;ll fix every gap for a one-time $9.99 — no subscription.
        </p>

        <Link href="/">
          <button className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xl py-5 px-12 rounded-2xl transition inline-flex items-center space-x-3 shadow-[0_0_40px_-10px_rgba(16,185,129,0.5)]">
            <span>Get my free {title} match score</span>
            <ArrowRight className="w-6 h-6" />
          </button>
        </Link>

        {/* Unique, role-specific content (keywords + tips) for SEO depth */}
        {keywords.length > 0 && (
          <section className="mt-20 text-left">
            <h2 className="text-2xl font-bold mb-2 flex items-center">
              <XCircle className="w-6 h-6 text-red-500 mr-2" />
              ATS keywords for {title} resumes
            </h2>
            <p className="text-neutral-400 mb-6">
              These are the terms an ATS most often scans for in {title} job descriptions. If your resume is missing them, you&apos;re likely being filtered out:
            </p>
            <div className="flex flex-wrap gap-3 mb-12">
              {keywords.map((k, i) => (
                <span key={i} className="bg-neutral-900 border border-neutral-800 text-neutral-200 px-3 py-1.5 rounded-lg text-sm">{k}</span>
              ))}
            </div>
          </section>
        )}

        <section className="text-left">
          <h2 className="text-2xl font-bold mb-6 flex items-center">
            <Lightbulb className="w-6 h-6 text-emerald-500 mr-2" />
            How to optimize a {title} resume for the ATS
          </h2>
          <ul className="space-y-4">
            {tips.map((tip, i) => (
              <li key={i} className="flex items-start space-x-3 text-neutral-300">
                <CheckCircle className="w-5 h-5 text-emerald-500 mt-0.5 shrink-0" />
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </section>

        <div className="mt-16">
          <Link href="/">
            <button className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-lg py-4 px-10 rounded-2xl transition inline-flex items-center space-x-3">
              <span>Score &amp; optimize my {title} resume</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </Link>
        </div>
      </main>
    </div>
  );
}
