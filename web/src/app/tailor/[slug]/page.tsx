import React from 'react';
import { CheckCircle, ArrowRight } from 'lucide-react';
import { getJobData } from '@/lib/seo-data';
import Link from 'next/link';

export async function generateMetadata({ params }: { params: { slug: string } }) {
  const job = getJobData(params.slug);
  return {
    title: `Optimize your ${job.title} Resume for ATS | ATS Hacker`,
    description: `Stop getting auto-rejected. We rewrite your ${job.title} resume to perfectly match job descriptions and beat Applicant Tracking Systems.`,
  };
}

export default function TailoredLandingPage({ params }: { params: { slug: string } }) {
  const job = getJobData(params.slug);

  return (
    <div className="min-h-screen bg-neutral-950 text-white flex flex-col items-center justify-center p-6 lg:p-12">
      <div className="max-w-6xl w-full mx-auto grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
        
        <div className="space-y-8">
          <div className="inline-block px-4 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-sm font-bold tracking-widest uppercase mb-4 border border-emerald-500/20">
            {job.title} Resume Optimizer
          </div>
          <h1 className="text-5xl lg:text-7xl font-extrabold tracking-tight leading-[1.1]">
            Pass the ATS for <br/>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
              {job.title} Roles.
            </span>
          </h1>
          <p className="text-xl text-neutral-400 leading-relaxed max-w-xl">
            {job.painPointDescription}
          </p>
          
          <div className="pt-4">
            <Link href="/" className="inline-flex items-center justify-center w-full sm:w-auto px-8 py-4 text-lg font-bold text-white bg-emerald-600 rounded-xl hover:bg-emerald-500 transition shadow-[0_0_40px_-10px_rgba(16,185,129,0.4)]">
              Start Semantic Optimization
              <ArrowRight className="w-5 h-5 ml-2" />
            </Link>
            <p className="text-sm text-neutral-500 mt-4">Takes 10 seconds. $5.00 one-time fee. No subscriptions.</p>
          </div>
        </div>

        <div className="bg-neutral-900 border border-neutral-800 p-8 rounded-3xl shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/10 blur-[100px] rounded-full pointer-events-none"></div>
          
          <h3 className="text-2xl font-bold mb-6 flex items-center">
            <div className="w-2 h-8 bg-emerald-500 rounded-full mr-4"></div>
            Crucial {job.title} Keywords
          </h3>
          <p className="text-neutral-400 mb-8">
            If your resume does not contain exact semantic matches for these core competencies, you will be automatically filtered out by Workday and Greenhouse:
          </p>
          
          <ul className="space-y-4">
            {job.keywords.map(kw => (
              <li key={kw} className="flex items-center text-lg text-neutral-200 bg-neutral-950 p-4 rounded-xl border border-neutral-800/50">
                <CheckCircle className="w-6 h-6 text-emerald-500 mr-4 flex-shrink-0" /> 
                {kw}
              </li>
            ))}
          </ul>
        </div>

      </div>
    </div>
  );
}
