"use client";
import React, { useState, useRef, useEffect } from 'react';
import { track } from '@vercel/analytics';
import { 
  UploadCloud, CheckCircle, Shield, ArrowRight, FileText, Gauge, 
  XCircle, Share2, Zap, Lock, BadgeCheck, Star, Sparkles, Award, Layout, BookOpen 
} from 'lucide-react';

// First-touch UTM keys we persist for sale attribution.
const UTM_KEYS = ['utm_source', 'utm_medium', 'utm_campaign'] as const;

function getStoredUtms(): Record<string, string> {
  const out: Record<string, string> = {};
  try {
    for (const key of UTM_KEYS) {
      const val = sessionStorage.getItem(key);
      if (val) out[key] = val;
    }
  } catch {
    /* sessionStorage unavailable */
  }
  return out;
}

interface ScoreResult {
  score: number;
  matchedKeywords: string[];
  missingKeywords: string[];
  verdict: string;
}

const BASE = (process.env.NEXT_PUBLIC_SITE_URL || 'https://ats-hacker-swart.vercel.app').replace(/\/$/, '');

const productSchema = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'ATSHacker',
  applicationCategory: 'BusinessApplication',
  operatingSystem: 'Web',
  url: BASE,
  description:
    'Free ATS keyword match score plus an honest $9.99 resume rewrite and cover letter generation that semantically matches the target job description so your resume ranks higher in recruiter search.',
  offers: [
    {
      '@type': 'Offer',
      name: 'Resume Optimization',
      priceCurrency: 'USD',
      price: '9.99',
      availability: 'https://schema.org/InStock',
      url: BASE,
    },
    {
      '@type': 'Offer',
      name: 'Cover Letter Generation',
      priceCurrency: 'USD',
      price: '9.99',
      availability: 'https://schema.org/InStock',
      url: BASE,
    },
    {
      '@type': 'Offer',
      name: 'Resume & Cover Letter Bundle',
      priceCurrency: 'USD',
      price: '14.99',
      availability: 'https://schema.org/InStock',
      url: BASE,
    }
  ],
};

const faqSchema = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: [
    {
      '@type': 'Question',
      name: 'Does an ATS auto-reject resumes?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'No. An Applicant Tracking System does not automatically reject you. It stores and indexes resumes so recruiters can search and rank them by keyword. Resumes that closely match the job description rank higher and are far more likely to be seen — roughly 3x — while poorly matched resumes get buried lower in the results.',
      },
    },
    {
      '@type': 'Question',
      name: 'What is an ATS match score?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'It is a 0–100 measure of how closely your resume’s keywords and skills overlap with a specific job description. A higher score means your resume is more likely to surface near the top when a recruiter searches their ATS for that role.',
      },
    },
    {
      '@type': 'Question',
      name: 'How does the cover letter builder work?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'It analyzes your resume and the target job description to write a professional cover letter. It uses the exact matching design, headers, and fonts as your optimized resume, creating a cohesive personal brand that highlights matching semantic keywords.',
      },
    },
    {
      '@type': 'Question',
      name: 'Do you fabricate experience to boost the score?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'No. We never invent jobs, skills, or experience you do not have. We rewrite and reframe your real background to surface the keywords and accomplishments that genuinely match the job description.',
      },
    },
  ],
};

function useCountUp(target: number | null, durationMs = 1100): number {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (target == null) { setValue(0); return; }

    const prefersReduced =
      typeof window !== 'undefined' &&
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReduced || typeof requestAnimationFrame !== 'function') {
      setValue(target);
      return;
    }

    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(Math.round(target * eased));
      if (t < 1) raf = requestAnimationFrame(tick);
      else setValue(target);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, durationMs]);
  return value;
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isScoring, setIsScoring] = useState(false);
  const [score, setScore] = useState<ScoreResult | null>(null);
  const [activeTab, setActiveTab] = useState<'resume' | 'cover_letter'>('resume');

  const fileInputRef = useRef<HTMLInputElement>(null);
  const toolSectionRef = useRef<HTMLDivElement>(null);
  const animatedScore = useCountUp(score ? score.score : null);

  useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      for (const key of UTM_KEYS) {
        const incoming = params.get(key);
        if (incoming && !sessionStorage.getItem(key)) {
          sessionStorage.setItem(key, incoming.slice(0, 200));
        }
      }
    } catch {
      /* ignore */
    }
  }, []);

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(false); };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) setFile(e.dataTransfer.files[0]);
  };
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) setFile(e.target.files[0]);
  };

  const extractResumeText = async (): Promise<string> => {
    const pdfjsLib = await import('pdfjs-dist');
    pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`;

    const arrayBuffer = await file!.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    let resumeText = '';
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      resumeText += content.items.map((item: any) => ('str' in item ? item.str : '')).join(' ') + '\n';
    }
    sessionStorage.setItem('resumeText', resumeText);
    sessionStorage.setItem('jobDescription', jobDescription);
    sessionStorage.setItem('fileName', file!.name);
    return resumeText;
  };

  const validateInputs = () => {
    if (!file) { alert("Please upload your resume first!"); return false; }
    if (!jobDescription.trim()) { alert("Please paste the job description!"); return false; }
    return true;
  };

  const handleScore = async () => {
    if (!validateInputs()) return;
    setIsScoring(true);
    setScore(null);
    try {
      const resumeText = await extractResumeText();
      const res = await fetch('/api/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resumeText, jobDescription }),
      });
      const contentType = res.headers.get('content-type');
      if (contentType && contentType.includes('text/html')) {
        alert("Vercel Preview Protection is blocking the API! Please test on the Production URL (https://ats-hacker-swart.vercel.app) instead of this Preview URL.");
        setIsScoring(false);
        return;
      }
      const data = await res.json();
      if (res.ok) {
        setScore(data);
        try {
          track('score_completed', { score: data?.score ?? 0 });
        } catch {
          /* analytics best-effort */
        }
      } else alert(data.error || "Could not score your resume.");
    } catch (err) {
      console.error(err);
      alert("An error occurred while scoring.");
    } finally {
      setIsScoring(false);
    }
  };

  const handleCheckout = async (type: 'resume' | 'cover_letter' | 'bundle') => {
    if (!validateInputs()) return;
    setIsLoading(true);
    try {
      track('checkout_started', { type });
    } catch {
      /* analytics best-effort */
    }
    try {
      if (!sessionStorage.getItem('resumeText')) await extractResumeText();
      const utms = getStoredUtms();
      const res = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type, fileName: file!.name, jobDescription, ...utms }),
      });
      const contentType = res.headers.get('content-type');
      if (contentType && contentType.includes('text/html')) {
        alert("Vercel Preview Protection is blocking the API! Please test on the Production URL (https://ats-hacker-swart.vercel.app) instead of this Preview URL.");
        setIsLoading(false);
        return;
      }
      const data = await res.json();
      if (data.url) window.location.href = data.url;
      else { alert("Checkout failed to initiate."); setIsLoading(false); }
    } catch (err) {
      console.error(err);
      alert("An error occurred during checkout.");
      setIsLoading(false);
    }
  };

  const scrollToTool = (tab: 'resume' | 'cover_letter') => {
    setActiveTab(tab);
    toolSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const shareScore = async () => {
    if (!score) return;
    const missing = score.missingKeywords?.length || 0;
    const url = `${window.location.origin}/s/${score.score}?m=${missing}`;
    const text = `My resume scored ${score.score}/100 on ATSHacker for this job. Check yours free:`;
    try {
      if (navigator.share) {
        await navigator.share({ title: 'ATSHacker', text, url });
      } else {
        await navigator.clipboard.writeText(`${text} ${url}`);
        alert('Share link copied to clipboard!');
      }
    } catch {
      /* ignore */
    }
  };

  const scoreColor = score
    ? score.score >= 75 ? 'text-emerald-600' : score.score >= 50 ? 'text-amber-600' : 'text-red-600'
    : '';
  const scoreBar = score
    ? score.score >= 75 ? 'bg-emerald-500' : score.score >= 50 ? 'bg-amber-500' : 'bg-red-500'
    : 'bg-emerald-500';

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-emerald-500/20 antialiased">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(productSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />

      {/* Modern Navigation */}
      <nav className="w-full bg-white border-b border-slate-100 sticky top-0 z-50 shadow-sm backdrop-blur-md bg-white/90">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <img src="/logo-full.png" alt="ATSHacker" className="h-9 w-auto" />
          </div>
          <div className="flex items-center gap-8 text-sm font-bold text-slate-600">
            <button onClick={() => scrollToTool('resume')} className="hover:text-emerald-600 transition">Optimize Resume</button>
            <button onClick={() => scrollToTool('cover_letter')} className="hover:text-emerald-600 transition">Write Cover Letter</button>
            <a href="#templates" className="hover:text-emerald-600 transition hidden sm:block">Templates</a>
            <a href="#pricing" className="hover:text-emerald-600 transition">Pricing</a>
          </div>
          <button 
            onClick={() => scrollToTool('resume')} 
            className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-extrabold px-4 py-2 rounded-lg transition shadow-sm hidden md:block"
          >
            Get Started
          </button>
        </div>
      </nav>

      {/* Zety-inspired Hero Section */}
      <header className="bg-gradient-to-b from-white to-slate-50 border-b border-slate-100 py-16 lg:py-24 overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Hero Content */}
          <div className="lg:col-span-7 space-y-8">
            <div className="inline-flex items-center gap-2 bg-emerald-50/70 border border-emerald-100 text-emerald-800 px-4 py-1.5 rounded-full text-xs font-bold shadow-sm">
              <Shield className="w-3.5 h-3.5 fill-emerald-600/10 text-emerald-600" />
              <span>100% secure checkout via Stripe • One-time payment, no subscriptions</span>
            </div>
            
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 leading-none">
              The professional resume and <span className="text-emerald-600">cover letter builder</span> designed for ATS.
            </h1>
            
            <p className="text-lg text-slate-600 leading-relaxed max-w-2xl">
              ATS databases search and rank candidates by job description keywords. Keyword-matched documents are <span className="text-slate-950 font-extrabold">3x more likely</span> to secure interviews. Check your match rate free, then optimize in 60 seconds.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 pt-2">
              <button 
                onClick={() => scrollToTool('resume')} 
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-base px-8 py-4 rounded-xl transition duration-200 shadow-md hover:shadow-lg flex items-center justify-center gap-2"
              >
                <span>Optimize My Resume</span>
                <ArrowRight className="w-5 h-5" />
              </button>
              <button 
                onClick={() => scrollToTool('cover_letter')} 
                className="bg-white hover:bg-slate-50 border border-slate-200 text-slate-800 font-extrabold text-base px-8 py-4 rounded-xl transition duration-200 shadow-sm flex items-center justify-center gap-2"
              >
                <span>Create Matching Cover Letter</span>
              </button>
            </div>

            {/* Key benefits metrics */}
            <div className="grid grid-cols-3 gap-6 pt-4 border-t border-slate-200/60 max-w-xl">
              <div>
                <p className="text-3xl font-black text-slate-900">3x</p>
                <p className="text-xs text-slate-500 font-semibold mt-1">More Callbacks</p>
              </div>
              <div>
                <p className="text-3xl font-black text-slate-900">60s</p>
                <p className="text-xs text-slate-500 font-semibold mt-1">Average Setup</p>
              </div>
              <div>
                <p className="text-3xl font-black text-slate-900">100%</p>
                <p className="text-xs text-slate-500 font-semibold mt-1">ATS Compatible</p>
              </div>
            </div>
          </div>

          {/* Right Hero Video/Graphic Mockup */}
          <div className="lg:col-span-5 relative">
            <div className="absolute inset-0 bg-emerald-500/10 rounded-3xl blur-3xl -z-10 transform scale-95"></div>
            <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-400"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
                  <div className="w-3 h-3 rounded-full bg-green-400"></div>
                </div>
                <div className="bg-slate-50 rounded-lg px-4 py-1 text-xs text-slate-500 font-semibold">
                  ats-match-score-reveal.pdf
                </div>
              </div>
              <div className="relative overflow-hidden rounded-xl bg-slate-950 aspect-[4/3] flex items-center justify-center">
                <div className="text-center p-8 space-y-3">
                  <Gauge className="w-12 h-12 text-emerald-500 mx-auto animate-bounce" />
                  <p className="text-emerald-500 font-extrabold text-3xl">89 / 100</p>
                  <p className="text-slate-400 text-xs max-w-xs">AI has successfully woven 12 missing semantic keywords into the resume bullets.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Interactive Tool Section */}
      <section ref={toolSectionRef} className="max-w-7xl mx-auto px-6 py-20 scroll-mt-24">
        <div className="text-center max-w-3xl mx-auto mb-12 space-y-3">
          <h2 className="text-3xl sm:text-4xl font-black text-slate-900">Get Started in 3 Steps</h2>
          <p className="text-slate-600 text-base sm:text-lg">
            Choose your tool option below, upload your PDF resume, and paste the job description you are targeting.
          </p>
        </div>

        {/* Tab Selection */}
        <div className="flex justify-center mb-8">
          <div className="bg-white border border-slate-200 rounded-2xl p-1.5 shadow-sm inline-flex gap-1.5">
            <button
              onClick={() => { setActiveTab('resume'); setScore(null); }}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-all duration-200
                ${activeTab === 'resume' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'}`}
            >
              <FileText className="w-4 h-4" />
              <span>Resume Tailoring</span>
            </button>
            <button
              onClick={() => { setActiveTab('cover_letter'); setScore(null); }}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-all duration-200
                ${activeTab === 'cover_letter' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'}`}
            >
              <Sparkles className="w-4 h-4" />
              <span>Cover Letter Generator</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
          {/* Tool Card: Col-span 7 */}
          <div className="lg:col-span-7 bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-md relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-600 to-emerald-400"></div>
            
            <h3 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
              {activeTab === 'resume' ? <FileText className="text-emerald-600" /> : <Sparkles className="text-emerald-600" />}
              {activeTab === 'resume' ? 'ATS Resume Tailoring Input' : 'Matching Cover Letter Tailoring Input'}
            </h3>

            <div className="space-y-6">
              {/* File Upload */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700">1. Upload Current Resume (PDF)</label>
                <input type="file" accept=".pdf" ref={fileInputRef} className="hidden" onChange={handleFileChange} />
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() => fileInputRef.current?.click()}
                  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInputRef.current?.click(); } }}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-2xl p-8 text-center transition cursor-pointer group focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/40
                    ${isDragging ? 'border-emerald-500 bg-emerald-50' : 'border-slate-300 hover:border-emerald-500/60 hover:bg-slate-50'}`}
                >
                  {file ? (
                    <div className="flex flex-col items-center">
                      <FileText className="w-12 h-12 text-emerald-600 mb-3" />
                      <p className="text-sm text-slate-900 font-bold">{file.name}</p>
                      <p className="text-xs text-emerald-600 mt-1">Click to replace file</p>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center">
                      <UploadCloud className="w-12 h-12 text-slate-400 group-hover:text-emerald-600 transition mb-3" />
                      <p className="text-sm text-slate-600 font-semibold">Drag and drop your resume PDF or <span className="text-emerald-600">browse files</span></p>
                    </div>
                  )}
                </div>
              </div>

              {/* Textarea */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700">2. Paste Target Job Description</label>
                <textarea
                  rows={5}
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the target job description requirements here..."
                  className="w-full bg-white border border-slate-300 rounded-2xl p-4 text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/30 transition resize-none"
                ></textarea>
              </div>

              {/* Active Tab Logic CTAs */}
              {activeTab === 'resume' ? (
                <div className="space-y-4">
                  <button
                    onClick={handleScore}
                    disabled={isScoring}
                    className="w-full bg-white hover:bg-slate-50 hover:border-emerald-300 border border-slate-300 text-slate-900 font-bold text-base py-3.5 rounded-xl transition flex items-center justify-center space-x-2 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
                  >
                    <Gauge className="w-5 h-5 text-emerald-600" />
                    <span>{isScoring ? "Scoring..." : "Check My Free ATS Score"}</span>
                  </button>

                  <button
                    onClick={() => handleCheckout('resume')}
                    disabled={isLoading}
                    className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-lg py-4 rounded-xl transition shadow-md hover:shadow-lg flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    <span>{isLoading ? "Connecting..." : "Optimize Resume — $9.99"}</span>
                    {!isLoading && <ArrowRight className="w-5 h-5" />}
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => handleCheckout('cover_letter')}
                  disabled={isLoading}
                  className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-lg py-4 rounded-xl transition shadow-md hover:shadow-lg flex items-center justify-center space-x-2 disabled:opacity-50"
                >
                  <span>{isLoading ? "Connecting..." : "Generate Cohesive Cover Letter — $9.99"}</span>
                  {!isLoading && <ArrowRight className="w-5 h-5" />}
                </button>
              )}

              {/* Bundle Upsell Promo (only when NOT checking out bundle already) */}
              <div className="bg-emerald-50 border border-emerald-100 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <h4 className="font-extrabold text-emerald-950 text-sm flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-emerald-600" />
                    <span>Recommended: Get the Bundle & Save 25%!</span>
                  </h4>
                  <p className="text-xs text-emerald-800 mt-1 font-medium">Get both the ATS-optimized resume + matching tailored cover letter.</p>
                </div>
                <button
                  onClick={() => handleCheckout('bundle')}
                  disabled={isLoading}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-extrabold py-2.5 px-4 rounded-xl transition shadow-sm self-stretch sm:self-auto text-center"
                >
                  Get Bundle — $14.99
                </button>
              </div>

              <p className="text-xs text-center text-slate-400">Secured with Stripe. Resume data is never stored on our servers.</p>
            </div>
          </div>

          {/* Results Sidebar / Info Card: Col-span 5 */}
          <div className="lg:col-span-5 space-y-6">
            {score ? (
              <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-md space-y-5">
                <div className="text-center pt-2">
                  <span className="text-[10px] font-black uppercase tracking-widest text-slate-400 block mb-1">ATS MATCH SCORE</span>
                  <div className="flex items-end justify-center leading-none">
                    <span className={`text-7xl font-black tabular-nums ${scoreColor}`}>{animatedScore}</span>
                    <span className="text-2xl font-bold text-slate-300 mb-1.5">/100</span>
                  </div>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                  <div className={`${scoreBar} h-2 rounded-full transition-all duration-700 ease-out`} style={{ width: `${animatedScore}%` }}></div>
                </div>
                {score.verdict && <p className="text-sm text-slate-600 text-center leading-relaxed font-semibold">{score.verdict}</p>}

                {score.missingKeywords?.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-xs font-bold text-red-700 flex items-center"><XCircle className="w-4 h-4 mr-1 shrink-0" /> Missing keywords ({score.missingKeywords.length})</p>
                    <div className="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto p-1 bg-slate-50 border border-slate-100 rounded-xl">
                      {score.missingKeywords.map((k, i) => (
                        <span key={i} className="inline-flex items-center bg-red-50 text-red-800 px-2 py-0.5 rounded-md text-[10px] font-bold">{k}</span>
                      ))}
                    </div>
                  </div>
                )}

                {score.matchedKeywords?.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-xs font-bold text-emerald-700 flex items-center"><CheckCircle className="w-4 h-4 mr-1 shrink-0" /> Matched keywords ({score.matchedKeywords.length})</p>
                    <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto p-1 bg-slate-50 border border-slate-100 rounded-xl">
                      {score.matchedKeywords.map((k, i) => (
                        <span key={i} className="inline-flex items-center bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded-md text-[10px] font-bold">{k}</span>
                      ))}
                    </div>
                  </div>
                )}

                <button
                  onClick={() => handleCheckout('resume')}
                  disabled={isLoading}
                  className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-base py-3.5 rounded-xl transition shadow-md hover:shadow-lg flex items-center justify-center gap-2"
                >
                  <span>Fix all missing gaps — $9.99</span>
                  <ArrowRight className="w-4 h-4" />
                </button>

                <button
                  onClick={shareScore}
                  className="w-full bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 text-xs font-bold py-2.5 rounded-xl transition flex items-center justify-center gap-1.5"
                >
                  <Share2 className="w-4 h-4 text-emerald-600" />
                  <span>Share My Score</span>
                </button>
              </div>
            ) : (
              <div className="bg-slate-100/50 border border-slate-200/60 rounded-3xl p-6 sm:p-8 space-y-6">
                <h4 className="font-extrabold text-slate-800 text-lg">Why optimize with ATSHacker?</h4>
                <ul className="space-y-4">
                  <li className="flex gap-3">
                    <BadgeCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-bold text-slate-900">Semantic AI Matching</p>
                      <p className="text-xs text-slate-500 mt-0.5">We reframe your accomplishments to match the Job Description without fabricating experience.</p>
                    </div>
                  </li>
                  <li className="flex gap-3">
                    <Layout className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-bold text-slate-900">Single-Column Formats</p>
                      <p className="text-xs text-slate-500 mt-0.5">Tested against Workday, Taleo, and Greenhouse to prevent text extraction errors.</p>
                    </div>
                  </li>
                  <li className="flex gap-3">
                    <Award className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-bold text-slate-900">Cohesive Personal Branding</p>
                      <p className="text-xs text-slate-500 mt-0.5">Get a matching cover letter utilizing the same formatting styles for a highly polished application.</p>
                    </div>
                  </li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Visual Template Previews Section */}
      <section id="templates" className="bg-white border-t border-b border-slate-100 py-20">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <h2 className="text-3xl font-black text-slate-900">Cohesive Document Templates</h2>
            <p className="text-slate-600">
              Both your resume and cover letter will share identical styling tokens for a consistent professional appearance.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              {
                name: 'Modern Slate',
                color: 'bg-slate-800',
                desc: 'Minimal layout with a bold heading header structure.',
                initials: 'JD',
                candName: 'John Doe',
                candTitle: 'Network Engineer',
                skills: 'Cisco • Python • AWS',
                bullets: [
                  'Optimized core network infrastructure for 40% speed-up.',
                  'Implemented secure VPN tunnels and firewall policies.',
                  'Configured dynamic OSPF/BGP routing protocols.'
                ]
              },
              {
                name: 'Professional Emerald',
                color: 'bg-emerald-800',
                desc: 'Curated corporate design highlighting core competencies.',
                initials: 'SJ',
                candName: 'Sarah Jenkins',
                candTitle: 'Software Engineer',
                skills: 'React • Node.js • TypeScript',
                bullets: [
                  'Re-architected legacy dashboard using Next.js/Turbopack.',
                  'Reduced bundle sizes by 45% and page load times.',
                  'Collaborated closely with cross-functional designer teams.'
                ]
              },
              {
                name: 'Minimal Clean',
                color: 'bg-gray-100 border border-slate-200',
                desc: 'Ultra-clean single column optimized for dense records.',
                initials: 'AR',
                candName: 'Alex Rivera',
                candTitle: 'Product Designer',
                skills: 'Figma • UI/UX • Design Systems',
                bullets: [
                  'Redesigned core checkout UI resulting in 20% conversion bump.',
                  'Created scalable UI component library for Figma workflow.',
                  'Conducted 15+ user testing sessions to iterate prototypes.'
                ]
              },
              {
                name: 'Creative Orange',
                color: 'bg-orange-600',
                desc: 'Vibrant highlight accents to separate sections clearly.',
                initials: 'EC',
                candName: 'Emily Chen',
                candTitle: 'Marketing Specialist',
                skills: 'SEO • Content • Analytics',
                bullets: [
                  'Grew organic traffic by 150% via targeted search campaigns.',
                  'Designed visual newsletter templates for 50k subscribers.',
                  'Analyzed weekly conversion funnels using Google Analytics.'
                ]
              },
            ].map((tmpl, idx) => (
              <div key={idx} className="group border border-slate-100 bg-slate-50 rounded-2xl p-4 hover:shadow-lg transition duration-300">
                <div className="aspect-[3/4] rounded-xl bg-white shadow-sm overflow-hidden p-5 flex flex-col justify-between relative text-left">
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center font-black text-slate-700 text-[10px]">{tmpl.initials}</div>
                      <div className="flex-1 min-w-0">
                        <div className="text-xs font-black text-slate-900 truncate leading-tight">{tmpl.candName}</div>
                        <div className="text-[9px] text-slate-500 font-bold truncate leading-none mt-0.5">{tmpl.candTitle}</div>
                      </div>
                    </div>
                    
                    <div className="border-t border-slate-100 pt-2 space-y-2">
                      <div>
                        <div className="text-[8px] font-black text-slate-400 uppercase tracking-wider mb-0.5">Skills</div>
                        <div className="text-[9px] text-slate-600 font-bold leading-none">{tmpl.skills}</div>
                      </div>
                      
                      <div className="space-y-1 pt-1 border-t border-slate-100">
                        <div className="text-[8px] font-black text-slate-400 uppercase tracking-wider">Experience Highlights</div>
                        {tmpl.bullets.map((b, bIdx) => (
                          <div key={bIdx} className="flex gap-1 items-start text-[8px] text-slate-600 leading-normal">
                            <span className="text-emerald-500 font-bold mt-0.5">•</span>
                            <p className="flex-1 line-clamp-2">{b}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className={`h-1.5 w-full ${tmpl.color} rounded-full`}></div>
                </div>
                <h4 className="font-bold text-slate-900 mt-4 text-center">{tmpl.name}</h4>
                <p className="text-xs text-slate-500 text-center mt-1 px-2">{tmpl.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Plans */}
      <section id="pricing" className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center max-w-2xl mx-auto mb-16 space-y-3">
          <h2 className="text-3xl font-black text-slate-900">Simple, Pay-As-You-Go Pricing</h2>
          <p className="text-slate-600">No monthly subscriptions or hidden cancellation fees. Pay only when you apply.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch max-w-6xl mx-auto">
          {/* Card 1: Resume */}
          <div className="bg-white border border-slate-200 rounded-3xl p-8 flex flex-col justify-between shadow-sm transition hover:border-emerald-300 hover:shadow-md">
            <div>
              <h3 className="font-extrabold text-slate-900 text-xl mb-2">Resume Tailoring</h3>
              <p className="text-xs text-slate-500 font-semibold mb-6">Perfect for individual target job descriptions.</p>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-black text-slate-900">$9.99</span>
                <span className="text-slate-400 text-xs font-bold">/ rewrite</span>
              </div>
              <ul className="space-y-3 text-sm text-slate-600 border-t border-slate-100 pt-6">
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" /><span>Free ATS score analysis</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" /><span>AI semantic keyword alignment</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" /><span>Honest, non-fabricated experience</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" /><span>Clean PDF & Word formats</span></li>
              </ul>
            </div>
            <button 
              onClick={() => scrollToTool('resume')} 
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold py-3.5 rounded-xl transition text-center shadow-sm mt-8 block"
            >
              Get Started
            </button>
          </div>

          {/* Card 2: Bundle */}
          <div className="bg-white border-2 border-emerald-500 rounded-3xl p-8 flex flex-col justify-between shadow-md relative hover:shadow-xl transition transform -translate-y-2">
            <span className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-emerald-500 text-white text-[10px] font-black uppercase tracking-widest px-4 py-1 rounded-full shadow-sm">
              Best Value (Save 25%)
            </span>
            <div>
              <h3 className="font-extrabold text-slate-900 text-xl mb-2 flex items-center gap-1.5">
                <span>Resume & CL Bundle</span>
                <Sparkles className="w-4 h-4 text-emerald-600" />
              </h3>
              <p className="text-xs text-slate-500 font-semibold mb-6">Complete tailored job application toolkit.</p>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-black text-slate-900">$14.99</span>
                <span className="text-slate-400 text-xs font-bold">/ package</span>
              </div>
              <ul className="space-y-3 text-sm text-slate-600 border-t border-slate-100 pt-6">
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" /><span>All Resume Tailoring features</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" /><span>Cohesive matching Cover Letter</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" /><span>Matching typography & headers</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" /><span>PDF & Word copies for both docs</span></li>
              </ul>
            </div>
            <button 
              onClick={() => handleCheckout('bundle')} 
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold py-3.5 rounded-xl transition text-center shadow-md mt-8 block"
            >
              Tailor Both Now
            </button>
          </div>

          {/* Card 3: Cover Letter */}
          <div className="bg-white border border-slate-200 rounded-3xl p-8 flex flex-col justify-between shadow-sm transition hover:border-emerald-300 hover:shadow-md">
            <div>
              <h3 className="font-extrabold text-slate-900 text-xl mb-2">Cover Letter Only</h3>
              <p className="text-xs text-slate-500 font-semibold mb-6">Perfect for quick matching intros.</p>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-black text-slate-900">$9.99</span>
                <span className="text-slate-400 text-xs font-bold">/ document</span>
              </div>
              <ul className="space-y-3 text-sm text-slate-600 border-t border-slate-100 pt-6">
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" /><span>Tailored to target job description</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" /><span>Aligned with candidate's true history</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" /><span>Cohesive layout and spacing design</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" /><span>Clean PDF & Word formats</span></li>
              </ul>
            </div>
            <button 
              onClick={() => scrollToTool('cover_letter')} 
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold py-3.5 rounded-xl transition text-center shadow-sm mt-8 block"
            >
              Get Started
            </button>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="bg-slate-100/50 border-t border-slate-200/60 py-20">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-3xl font-black text-center text-slate-900 mb-12">Frequently Asked Questions</h2>
          <div className="space-y-6">
            {[
              {
                q: "Does an ATS auto-reject resumes?",
                a: "No. An Applicant Tracking System does not automatically reject you. It stores and indexes resumes so recruiters can search and rank them by keyword. Resumes that closely match the job description rank higher and are far more likely to be seen — roughly 3x — while poorly matched resumes get buried lower in the results."
              },
              {
                q: "What is an ATS match score?",
                a: "It is a 0–100 measure of how closely your resume’s keywords and skills overlap with a specific job description. A higher score means your resume is more likely to surface near the top when a recruiter searches their ATS for that role."
              },
              {
                q: "How does the Cover Letter matching work?",
                a: "It reads the target job description and your uploaded resume details. Then, it drafts a custom letter emphasizing how your actual skills fulfill their requirements. It shares the identical fonts, borders, and margins as your resume, creating a clean, cohesive application package."
              },
              {
                q: "Do you fabricate experience to boost the score?",
                a: "No. We never invent jobs, skills, or experience you do not have. We rewrite and reframe your real background to surface the keywords and accomplishments that genuinely match the job description."
              }
            ].map((item, idx) => (
              <div key={idx} className="bg-white border border-slate-200/60 rounded-2xl p-6 shadow-sm">
                <h4 className="font-extrabold text-slate-900 text-base mb-2">{item.q}</h4>
                <p className="text-sm text-slate-600 leading-relaxed">{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-10 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div>
            <img src="/logo-full.png" alt="ATSHacker" className="h-7 w-auto mb-1.5 animate-pulse" />
            <p className="text-xs text-slate-500 font-medium">Honest resume & cover letter keyword optimization — no monthly subscriptions.</p>
          </div>
          <div className="flex items-center gap-6 text-sm font-bold text-slate-500">
            <button onClick={() => scrollToTool('resume')} className="hover:text-emerald-600 transition">Optimize Resume</button>
            <button onClick={() => scrollToTool('cover_letter')} className="hover:text-emerald-600 transition">Write Cover Letter</button>
            <a href="#pricing" className="hover:text-emerald-600 transition">Pricing</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
