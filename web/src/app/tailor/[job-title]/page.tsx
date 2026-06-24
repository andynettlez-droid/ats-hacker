import React from 'react';
import { CheckCircle, Shield, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function TailoredLandingPage({ params }: { params: { 'job-title': string } }) {
  // Convert "software-engineer" to "Software Engineer"
  const rawTitle = params['job-title'];
  const formattedTitle = rawTitle.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 font-sans selection:bg-emerald-500/30">
      <nav className="w-full p-6 flex justify-between items-center max-w-7xl mx-auto">
        <div className="text-2xl font-black tracking-tighter text-white">
          ATS<span className="text-emerald-500">Hacker.</span>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-6 pt-20 pb-32 text-center">
        <div className="inline-flex items-center space-x-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-4 py-1.5 rounded-full text-sm font-bold tracking-wide mb-8">
          <span>Targeted specifically for {formattedTitle} roles</span>
        </div>
        
        <h1 className="text-5xl lg:text-7xl font-black leading-[1.1] tracking-tight mb-8">
          Land your dream <span className="text-emerald-500">{formattedTitle}</span> job.
        </h1>
        
        <p className="text-xl text-neutral-400 leading-relaxed max-w-2xl mx-auto mb-12">
          The Applicant Tracking System is automatically rejecting your resume because you aren't using the exact keywords expected for a {formattedTitle}. We'll fix it in 5 seconds.
        </p>

        <Link href="/">
          <button className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xl py-5 px-12 rounded-2xl transition inline-flex items-center space-x-3 shadow-[0_0_40px_-10px_rgba(16,185,129,0.5)]">
            <span>Hack the {formattedTitle} ATS</span>
            <ArrowRight className="w-6 h-6" />
          </button>
        </Link>
      </main>
    </div>
  );
}
