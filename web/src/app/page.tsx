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
          <div className="flex items-center gap-2 select-none cursor-pointer">
            <div className="bg-blue-600 text-white font-extrabold text-sm px-2.5 py-1.5 rounded-lg flex items-center justify-center shadow-sm">
              AE
            </div>
            <span className="text-xl font-black text-slate-900 tracking-tight">ATSHacker</span>
          </div>
          <div className="flex items-center gap-8 text-sm font-bold text-slate-600">
            <button onClick={() => scrollToTool('resume')} className="hover:text-blue-600 transition">Features</button>
            <a href="#templates" className="hover:text-blue-600 transition">Templates</a>
            <a href="#pricing" className="hover:text-blue-600 transition">Pricing</a>
            <button onClick={() => scrollToTool('resume')} className="hover:text-blue-600 transition">Blog</button>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={() => scrollToTool('resume')} 
              className="text-slate-600 hover:text-blue-600 text-sm font-bold transition"
            >
              Log In
            </button>
            <button 
              onClick={() => scrollToTool('resume')} 
              className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-extrabold px-4 py-2.5 rounded-lg transition shadow-sm hidden md:block"
            >
              Sign Up
            </button>
          </div>
        </div>
      </nav>

      {/* Zety-inspired Hero Section */}
      <header className="bg-gradient-to-b from-white to-slate-50 border-b border-slate-100 py-16 lg:py-24 overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Hero Content */}
          <div className="lg:col-span-7 space-y-8">
            <div className="inline-flex items-center gap-2 bg-blue-50/70 border border-blue-100 text-blue-800 px-4 py-1.5 rounded-full text-xs font-bold shadow-sm">
              <Shield className="w-3.5 h-3.5 fill-blue-600/10 text-blue-600" />
              <span>100% secure checkout via Stripe • One-time payment, no subscriptions</span>
            </div>
            
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 leading-none">
              The professional resume and cover letter builder designed for ATS.
            </h1>
            
            <p className="text-lg text-slate-600 leading-relaxed max-w-2xl">
              Beat the bots, get noticed, and land your dream job with resumes tailored to specific job descriptions.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 pt-2">
              <button 
                onClick={() => scrollToTool('resume')} 
                className="bg-blue-600 hover:bg-blue-500 text-white font-extrabold text-base px-8 py-4 rounded-xl transition duration-200 shadow-md hover:shadow-lg flex items-center justify-center gap-2"
              >
                <span>Create Your Optimized Resume Now</span>
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
            <div className="absolute inset-0 bg-blue-500/10 rounded-3xl blur-3xl -z-10 transform scale-95"></div>
            <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-2xl space-y-4">
              <div className="text-center pb-2 border-b border-slate-100">
                <h3 className="text-xs font-black text-slate-500 tracking-wider uppercase">
                  ATS Match Score Transformation
                </h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Column 1: Poor Original Resume */}
                <div className="space-y-3">
                  <div className="text-center">
                    <span className="inline-block bg-red-50 border border-red-150 text-red-700 text-[10px] font-black px-2 py-0.5 rounded-md">
                      Poor Original Resume (34/100)
                    </span>
                  </div>
                  {/* Mini Resume Card */}
                  <div className="border border-red-200 bg-white rounded-xl p-2.5 shadow-sm relative flex flex-col justify-between h-[210px] overflow-hidden select-none hover:scale-[1.02] hover:-rotate-1 transition-all duration-300 cursor-default">
                    {/* Header */}
                    <div className="flex items-center gap-1.5 border-b border-slate-150 pb-1.5 mb-1.5">
                      <img 
                        src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=80&h=80" 
                        alt="Emily Carter" 
                        className="w-7 h-7 rounded-full object-cover border border-slate-200"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-[9px] font-black text-slate-800 truncate leading-none">Emily Carter</div>
                        <div className="text-[7px] text-slate-500 font-bold truncate leading-none mt-0.5">Sales Manager, Chicago</div>
                      </div>
                    </div>
                    {/* Two column preview */}
                    <div className="flex-grow grid grid-cols-12 gap-1 text-[7px] leading-none mb-1">
                      {/* Left Side (30%) */}
                      <div className="col-span-4 bg-rose-50/50 p-1 rounded space-y-1 border-r border-slate-100 flex flex-col justify-between">
                        <div className="space-y-0.5">
                          <div className="h-0.5 w-4 bg-rose-200 rounded"></div>
                          <div className="space-y-0.5">
                            <div className="flex items-center gap-0.5">
                              <span className="w-0.5 h-0.5 rounded-full bg-rose-400"></span>
                              <div className="h-0.5 w-6 bg-slate-200 rounded"></div>
                            </div>
                            <div className="flex items-center gap-0.5">
                              <span className="w-0.5 h-0.5 rounded-full bg-rose-400"></span>
                              <div className="h-0.5 w-5 bg-slate-200 rounded"></div>
                            </div>
                          </div>
                        </div>
                        <div className="space-y-0.5">
                          <div className="h-0.5 w-6 bg-slate-200 rounded"></div>
                          <div className="h-0.5 w-5 bg-slate-200 rounded"></div>
                        </div>
                      </div>
                      {/* Right Side (70%) */}
                      <div className="col-span-8 p-1 flex flex-col justify-between">
                        <div className="space-y-1">
                          <div className="h-0.5 w-8 bg-slate-350 rounded"></div>
                          <div className="space-y-0.5 pl-1 border-l border-slate-200">
                            <div className="h-0.5 w-12 bg-slate-200 rounded"></div>
                            <div className="h-0.5 w-10 bg-slate-150 rounded"></div>
                          </div>
                        </div>
                        <div className="space-y-0.5">
                          <div className="h-0.5 w-6 bg-slate-350 rounded"></div>
                          <div className="h-0.5 w-10 bg-slate-200 rounded"></div>
                        </div>
                      </div>
                    </div>
                    {/* Stamp score */}
                    <div className="absolute bottom-2 right-2 bg-red-500 text-white text-[9px] font-black px-1.5 py-0.5 rounded shadow">
                      34/100
                    </div>
                  </div>
                  {/* Bullets */}
                  <div className="space-y-1 text-left text-[10px] leading-tight">
                    <p className="font-bold text-red-700">
                      • Missing Keywords: <span className="font-extrabold text-red-900">BGP Routing, VPN Security, Cloud Architecture</span>
                    </p>
                    <p className="text-slate-500 pl-2">
                      <span className="font-bold text-slate-700">Example:</span> Vague ineffective bullets with vague, and-ineffective resume bullet.
                    </p>
                  </div>
                </div>

                {/* Column 2: Optimized Resume */}
                <div className="space-y-3">
                  <div className="text-center">
                    <span className="inline-block bg-emerald-50 border border-emerald-150 text-emerald-700 text-[10px] font-black px-2 py-0.5 rounded-md">
                      Optimized Resume (92/100)
                    </span>
                  </div>
                  {/* Mini Resume Card */}
                  <div className="border border-emerald-350 bg-white rounded-xl p-2.5 shadow-md relative flex flex-col justify-between h-[210px] overflow-hidden select-none hover:scale-[1.02] hover:rotate-1 transition-all duration-300 cursor-default">
                    {/* Header */}
                    <div className="flex items-center gap-1.5 border-b border-slate-150 pb-1.5 mb-1.5">
                      <img 
                        src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=80&h=80" 
                        alt="Sarah Jenkins" 
                        className="w-7 h-7 rounded-full object-cover border border-slate-200"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-[9px] font-black text-slate-800 truncate leading-none">Sarah Jenkins</div>
                        <div className="text-[7px] text-slate-500 font-bold truncate leading-none mt-0.5">Software Engineer, Austin</div>
                      </div>
                    </div>
                    {/* Two column preview */}
                    <div className="flex-grow grid grid-cols-12 gap-1 text-[7px] leading-none mb-1">
                      {/* Left Side (30%) */}
                      <div className="col-span-4 bg-emerald-50/50 p-1 rounded space-y-1 border-r border-slate-100 flex flex-col justify-between">
                        <div className="space-y-0.5">
                          <div className="h-0.5 w-4 bg-emerald-300 rounded"></div>
                          <div className="space-y-0.5">
                            <div className="flex items-center gap-0.5">
                              <span className="w-0.5 h-0.5 rounded-full bg-emerald-400"></span>
                              <div className="h-0.5 w-6 bg-slate-200 rounded"></div>
                            </div>
                            <div className="flex items-center gap-0.5">
                              <span className="w-0.5 h-0.5 rounded-full bg-emerald-400"></span>
                              <div className="h-0.5 w-5 bg-slate-200 rounded"></div>
                            </div>
                          </div>
                        </div>
                        <div className="space-y-0.5">
                          <div className="h-0.5 w-6 bg-slate-200 rounded"></div>
                          <div className="h-0.5 w-5 bg-slate-200 rounded"></div>
                        </div>
                      </div>
                      {/* Right Side (70%) */}
                      <div className="col-span-8 p-1 flex flex-col justify-between">
                        <div className="space-y-1">
                          <div className="h-0.5 w-8 bg-slate-350 rounded"></div>
                          <div className="space-y-0.5 pl-1 border-l border-slate-200">
                            <div className="h-0.5 w-12 bg-slate-200 rounded"></div>
                            <div className="h-0.5 w-10 bg-slate-150 rounded"></div>
                          </div>
                        </div>
                        <div className="space-y-0.5">
                          <div className="h-0.5 w-6 bg-slate-350 rounded"></div>
                          <div className="h-0.5 w-10 bg-slate-200 rounded"></div>
                        </div>
                      </div>
                    </div>
                    {/* Stamp score */}
                    <div className="absolute bottom-2 right-2 bg-emerald-600 text-white text-[9px] font-black px-1.5 py-0.5 rounded shadow">
                      92/100
                    </div>
                  </div>
                  {/* Bullets */}
                  <div className="space-y-1 text-left text-[10px] leading-tight">
                    <p className="font-bold text-emerald-700">
                      • Matched Keywords: <span className="font-extrabold text-emerald-800">BGP Routing, VPN Security, Cloud Architecture</span>
                    </p>
                    <p className="text-slate-600 pl-2">
                      <span className="font-bold text-slate-800">Example:</span> Designed and implemented secure multi-site VPN networks, improving connectivity by 40% and enhancing overall system security.
                    </p>
                  </div>
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
                ${activeTab === 'resume' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-blue-600 hover:bg-slate-50'}`}
            >
              <FileText className="w-4 h-4" />
              <span>Resume Tailoring</span>
            </button>
            <button
              onClick={() => { setActiveTab('cover_letter'); setScore(null); }}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-all duration-200
                ${activeTab === 'cover_letter' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-blue-600 hover:bg-slate-50'}`}
            >
              <Sparkles className="w-4 h-4" />
              <span>Cover Letter Generator</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
          {/* Tool Card: Col-span 7 */}
          <div className="lg:col-span-7 bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-md relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-600 to-blue-400"></div>
            
            <h3 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
              {activeTab === 'resume' ? <FileText className="text-blue-600" /> : <Sparkles className="text-blue-600" />}
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
                  className={`border-2 border-dashed rounded-2xl p-8 text-center transition cursor-pointer group focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/40
                    ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-slate-300 hover:border-blue-500/60 hover:bg-slate-50'}`}
                >
                  {file ? (
                    <div className="flex flex-col items-center">
                      <FileText className="w-12 h-12 text-blue-600 mb-3" />
                      <p className="text-sm text-slate-900 font-bold">{file.name}</p>
                      <p className="text-xs text-blue-600 mt-1">Click to replace file</p>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center">
                      <UploadCloud className="w-12 h-12 text-slate-400 group-hover:text-blue-600 transition mb-3" />
                      <p className="text-sm text-slate-600 font-semibold">Drag and drop your resume PDF or <span className="text-blue-600">browse files</span></p>
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
                  className="w-full bg-white border border-slate-300 rounded-2xl p-4 text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 transition resize-none"
                ></textarea>
              </div>

              {/* Active Tab Logic CTAs */}
              {activeTab === 'resume' ? (
                <div className="space-y-4">
                  <button
                    onClick={handleScore}
                    disabled={isScoring}
                    className="w-full bg-white hover:bg-slate-50 hover:border-blue-300 border border-slate-300 text-slate-900 font-bold text-base py-3.5 rounded-xl transition flex items-center justify-center space-x-2 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  >
                    <Gauge className="w-5 h-5 text-blue-600" />
                    <span>{isScoring ? "Scoring..." : "Check My Free ATS Score"}</span>
                  </button>

                  <button
                    onClick={() => handleCheckout('resume')}
                    disabled={isLoading}
                    className="w-full bg-blue-600 hover:bg-blue-500 text-white font-extrabold text-lg py-4 rounded-xl transition shadow-md hover:shadow-lg flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    <span>{isLoading ? "Connecting..." : "Optimize Resume — $9.99"}</span>
                    {!isLoading && <ArrowRight className="w-5 h-5" />}
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => handleCheckout('cover_letter')}
                  disabled={isLoading}
                  className="w-full bg-blue-600 hover:bg-blue-500 text-white font-extrabold text-lg py-4 rounded-xl transition shadow-md hover:shadow-lg flex items-center justify-center space-x-2 disabled:opacity-50"
                >
                  <span>{isLoading ? "Connecting..." : "Generate Cohesive Cover Letter — $9.99"}</span>
                  {!isLoading && <ArrowRight className="w-5 h-5" />}
                </button>
              )}

              {/* Bundle Upsell Promo (only when NOT checking out bundle already) */}
              <div className="bg-blue-50 border border-blue-100 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <h4 className="font-extrabold text-blue-950 text-sm flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-blue-600" />
                    <span>Recommended: Get the Bundle & Save 25%!</span>
                  </h4>
                  <p className="text-xs text-blue-800 mt-1 font-medium">Get both the ATS-optimized resume + matching tailored cover letter.</p>
                </div>
                <button
                  onClick={() => handleCheckout('bundle')}
                  disabled={isLoading}
                  className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-extrabold py-2.5 px-4 rounded-xl transition shadow-sm self-stretch sm:self-auto text-center"
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
                  className="w-full bg-blue-600 hover:bg-blue-500 text-white font-extrabold text-base py-3.5 rounded-xl transition shadow-md hover:shadow-lg flex items-center justify-center gap-2"
                >
                  <span>Fix all missing gaps — $9.99</span>
                  <ArrowRight className="w-4 h-4" />
                </button>

                <button
                  onClick={shareScore}
                  className="w-full bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 text-xs font-bold py-2.5 rounded-xl transition flex items-center justify-center gap-1.5"
                >
                  <Share2 className="w-4 h-4 text-blue-600" />
                  <span>Share My Score</span>
                </button>
              </div>
            ) : (
              <div className="bg-slate-100/50 border border-slate-200/60 rounded-3xl p-6 sm:p-8 space-y-6">
                <h4 className="font-extrabold text-slate-800 text-lg">Why optimize with ATSHacker?</h4>
                <ul className="space-y-4">
                  <li className="flex gap-3">
                    <BadgeCheck className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-bold text-slate-900">Semantic AI Matching</p>
                      <p className="text-xs text-slate-500 mt-0.5">We reframe your accomplishments to match the Job Description without fabricating experience.</p>
                    </div>
                  </li>
                  <li className="flex gap-3">
                    <Layout className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-bold text-slate-900">Single-Column Formats</p>
                      <p className="text-xs text-slate-500 mt-0.5">Tested against Workday, Taleo, and Greenhouse to prevent text extraction errors.</p>
                    </div>
                  </li>
                  <li className="flex gap-3">
                    <Award className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
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

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {[
              {
                name: 'Emily Carter',
                title: 'Sales Manager, Chicago',
                avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=150&h=150',
                themeBg: 'bg-rose-50/30',
                accentText: 'text-rose-600',
                accentBg: 'bg-rose-500',
                accentBorder: 'border-rose-200',
                skills: ['Sales Strategy', 'CRM (Salesforce)', 'Client Relations', 'Team Leadership'],
                email: 'emily.carter@gmail.com',
                phone: '312-555-0199',
                address: 'Chicago, IL',
                jobs: [
                  {
                    company: 'Sertons Sormon',
                    role: 'Sales Manager',
                    date: 'Apr 2018 - Apr 2023',
                    bullets: [
                      'Led and managed sales operations, increasing revenue by 34%.',
                      'Maintained a customer satisfaction rating of 96% via accounts management.'
                    ]
                  },
                  {
                    company: 'Sertons Sormon',
                    role: 'Sales Associate',
                    date: 'Apr 2017 - Apr 2018',
                    bullets: [
                      'Exceeded individual sales targets by 15% each quarter.'
                    ]
                  }
                ],
                education: {
                  school: 'Chicago State University',
                  degree: 'B.S. in Business Administration',
                  date: 'Graduated 2016'
                }
              },
              {
                name: 'John Doe',
                title: 'Network Engineer, Dallas',
                avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&q=80&w=150&h=150',
                themeBg: 'bg-blue-50/30',
                accentText: 'text-blue-600',
                accentBg: 'bg-blue-600',
                accentBorder: 'border-blue-200',
                skills: ['BGP/OSPF Routing', 'VPN Security', 'AWS Cloud Architecture', 'Network Automation'],
                email: 'john.doe@gmail.com',
                phone: '214-555-0120',
                address: 'Dallas, TX',
                jobs: [
                  {
                    company: 'Jehoo Engineer',
                    role: 'Network Engineer',
                    date: 'Apr 2020 - Aug 2024',
                    bullets: [
                      'Designed and deployed secure multi-site VPN networks, improving connectivity by 40%.',
                      'Configured dynamic BGP routing protocols, cutting latency by 30%.'
                    ]
                  },
                  {
                    company: 'Jehoo Engineer',
                    role: 'Junior Administrator',
                    date: 'Apr 2017 - Aug 2020',
                    bullets: [
                      'Monitored network systems and troubleshot routing issues.'
                    ]
                  }
                ],
                education: {
                  school: 'University of Texas at Dallas',
                  degree: 'B.S. in Computer Science',
                  date: 'Graduated 2016'
                }
              },
              {
                name: 'Sarah Jenkins',
                title: 'Software Engineer, Austin',
                avatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=150&h=150',
                themeBg: 'bg-slate-50',
                accentText: 'text-slate-700',
                accentBg: 'bg-slate-700',
                accentBorder: 'border-slate-300',
                skills: ['React / Next.js', 'Node.js / Express', 'TypeScript', 'System Architecture'],
                email: 'sarah.jenkins@gmail.com',
                phone: '512-555-0145',
                address: 'Austin, TX',
                jobs: [
                  {
                    company: 'Software Engineer',
                    role: 'Senior Software Engineer',
                    date: 'Apr 2015 - Dec 2020',
                    bullets: [
                      'Re-architected client dashboard, improving load times by 45% using Next.js.',
                      'Mentored 4 junior developers and established code review standards.'
                    ]
                  },
                  {
                    company: 'Software Engineer',
                    role: 'Software Developer',
                    date: 'Apr 2013 - Apr 2015',
                    bullets: [
                      'Designed and implemented secure REST APIs handling 10k daily requests.'
                    ]
                  }
                ],
                education: {
                  school: 'University of Texas at Austin',
                  degree: 'B.S. in Software Engineering',
                  date: 'Graduated 2012'
                }
              }
            ].map((cand, idx) => (
              <div key={idx} className="group bg-white border border-slate-200 rounded-3xl shadow-lg hover:shadow-2xl hover:scale-[1.02] transition-all duration-300 transform overflow-hidden cursor-pointer flex flex-col">
                {/* Resume Paper Container */}
                <div className="flex-grow grid grid-cols-12 text-left bg-white min-h-[500px]">
                  {/* Left Column (35%) */}
                  <div className={`col-span-4 ${cand.themeBg} p-4 border-r border-slate-100 flex flex-col justify-between`}>
                    <div className="space-y-6">
                      {/* Avatar */}
                      <div className="text-center">
                        <img 
                          src={cand.avatar} 
                          alt={cand.name}
                          className="w-16 h-16 md:w-20 md:h-20 rounded-full mx-auto object-cover border border-slate-200 shadow-md"
                        />
                      </div>
                      
                      {/* Skills */}
                      <div className="space-y-3">
                        <h5 className="text-[10px] font-black text-slate-800 uppercase tracking-widest border-b border-slate-200 pb-1">
                          Skills
                        </h5>
                        <div className="space-y-2">
                          {cand.skills.map((skill, sIdx) => (
                            <div key={sIdx} className="space-y-0.5">
                              <div className="text-[9px] font-bold text-slate-700 leading-none">{skill}</div>
                              <div className="h-1 w-full bg-slate-200 rounded-full overflow-hidden">
                                <div className={`h-full ${cand.accentBg} rounded-full`} style={{ width: `${85 - sIdx * 8}%` }}></div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Contact */}
                      <div className="space-y-3">
                        <h5 className="text-[10px] font-black text-slate-800 uppercase tracking-widest border-b border-slate-200 pb-1">
                          Contact
                        </h5>
                        <div className="space-y-1.5 text-[9px] text-slate-600 font-medium">
                          <p className="truncate"><span className="font-bold text-slate-700">Email:</span><br />{cand.email}</p>
                          <p><span className="font-bold text-slate-700">Phone:</span><br />{cand.phone}</p>
                          <p><span className="font-bold text-slate-700">Address:</span><br />{cand.address}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Right Column (65%) */}
                  <div className="col-span-8 p-6 flex flex-col justify-between">
                    <div>
                      {/* Name & Title */}
                      <div className="mb-6">
                        <h4 className="text-xl font-black text-slate-900 leading-tight">{cand.name}</h4>
                        <p className="text-[10px] font-bold text-slate-500 mt-1">({cand.title})</p>
                      </div>

                      {/* Work History */}
                      <div className="space-y-4">
                        <h5 className="text-[10px] font-black text-slate-800 uppercase tracking-widest border-b border-slate-200 pb-1">
                          Work History
                        </h5>
                        <div className="relative pl-4 border-l border-slate-150 space-y-4">
                          {cand.jobs.map((job, jIdx) => (
                            <div key={jIdx} className="relative space-y-1">
                              {/* Timeline dot */}
                              <span className={`absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full ${cand.accentBg} border-2 border-white shadow-sm`}></span>
                              <div className="flex justify-between items-baseline gap-2">
                                <div className="text-[10px] font-black text-slate-800">{job.role}</div>
                                <div className="text-[8px] text-slate-500 font-bold whitespace-nowrap">{job.date}</div>
                              </div>
                              <div className="text-[9px] text-slate-500 font-bold italic leading-none mb-1.5">{job.company}</div>
                              <ul className="space-y-1 list-disc pl-3">
                                {job.bullets.map((b, bIdx) => (
                                  <li key={bIdx} className="text-[9px] text-slate-600 leading-relaxed">
                                    {b}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Education */}
                      <div className="space-y-3 mt-6">
                        <h5 className="text-[10px] font-black text-slate-800 uppercase tracking-widest border-b border-slate-200 pb-1">
                          Education
                        </h5>
                        <div className="space-y-1">
                          <div className="flex justify-between items-baseline gap-2">
                            <div className="text-[10px] font-black text-slate-800">{cand.education.school}</div>
                            <div className="text-[8px] text-slate-500 font-bold whitespace-nowrap">{cand.education.date}</div>
                          </div>
                          <p className="text-[9px] text-slate-600 font-medium">{cand.education.degree}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
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
          <div className="bg-white border border-slate-200 rounded-3xl p-8 flex flex-col justify-between shadow-sm transition hover:border-blue-300 hover:shadow-md">
            <div>
              <h3 className="font-extrabold text-slate-900 text-xl mb-2">Resume Tailoring</h3>
              <p className="text-xs text-slate-500 font-semibold mb-6">Perfect for individual target job descriptions.</p>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-black text-slate-900">$9.99</span>
                <span className="text-slate-400 text-xs font-bold">/ rewrite</span>
              </div>
              <ul className="space-y-3 text-sm text-slate-600 border-t border-slate-100 pt-6">
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" /><span>Free ATS score analysis</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" /><span>AI semantic keyword alignment</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" /><span>Honest, non-fabricated experience</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" /><span>Clean PDF & Word formats</span></li>
              </ul>
            </div>
            <button 
              onClick={() => scrollToTool('resume')} 
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-extrabold py-3.5 rounded-xl transition text-center shadow-sm mt-8 block"
            >
              Get Started
            </button>
          </div>

          {/* Card 2: Bundle */}
          <div className="bg-white border-2 border-blue-500 rounded-3xl p-8 flex flex-col justify-between shadow-md relative hover:shadow-xl transition transform -translate-y-2">
            <span className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-blue-500 text-white text-[10px] font-black uppercase tracking-widest px-4 py-1 rounded-full shadow-sm">
              Best Value (Save 25%)
            </span>
            <div>
              <h3 className="font-extrabold text-slate-900 text-xl mb-2 flex items-center gap-1.5">
                <span>Resume & CL Bundle</span>
                <Sparkles className="w-4 h-4 text-blue-600" />
              </h3>
              <p className="text-xs text-slate-500 font-semibold mb-6">Complete tailored job application toolkit.</p>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-black text-slate-900">$14.99</span>
                <span className="text-slate-400 text-xs font-bold">/ package</span>
              </div>
              <ul className="space-y-3 text-sm text-slate-600 border-t border-slate-100 pt-6">
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" /><span>All Resume Tailoring features</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" /><span>Cohesive matching Cover Letter</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" /><span>Matching typography & headers</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" /><span>PDF & Word copies for both docs</span></li>
              </ul>
            </div>
            <button 
              onClick={() => handleCheckout('bundle')} 
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-extrabold py-3.5 rounded-xl transition text-center shadow-md mt-8 block"
            >
              Tailor Both Now
            </button>
          </div>

          {/* Card 3: Cover Letter */}
          <div className="bg-white border border-slate-200 rounded-3xl p-8 flex flex-col justify-between shadow-sm transition hover:border-blue-300 hover:shadow-md">
            <div>
              <h3 className="font-extrabold text-slate-900 text-xl mb-2">Cover Letter Only</h3>
              <p className="text-xs text-slate-500 font-semibold mb-6">Perfect for quick matching intros.</p>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-black text-slate-900">$9.99</span>
                <span className="text-slate-400 text-xs font-bold">/ document</span>
              </div>
              <ul className="space-y-3 text-sm text-slate-600 border-t border-slate-100 pt-6">
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" /><span>Tailored to target job description</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" /><span>Aligned with candidate's true history</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" /><span>Cohesive layout and spacing design</span></li>
                <li className="flex items-start gap-2.5"><CheckCircle className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" /><span>Clean PDF & Word formats</span></li>
              </ul>
            </div>
            <button 
              onClick={() => scrollToTool('cover_letter')} 
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-extrabold py-3.5 rounded-xl transition text-center shadow-sm mt-8 block"
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
            <div className="flex items-center gap-2 select-none cursor-pointer mb-1.5">
              <div className="bg-blue-600 text-white font-extrabold text-[10px] px-1.5 py-1 rounded flex items-center justify-center shadow-sm">
                AE
              </div>
              <span className="text-sm font-black text-slate-900 tracking-tight">ATSHacker</span>
            </div>
            <p className="text-xs text-slate-500 font-medium">Honest resume & cover letter keyword optimization — no monthly subscriptions.</p>
          </div>
          <div className="flex items-center gap-6 text-sm font-bold text-slate-500">
            <button onClick={() => scrollToTool('resume')} className="hover:text-blue-600 transition">Optimize Resume</button>
            <button onClick={() => scrollToTool('cover_letter')} className="hover:text-blue-600 transition">Write Cover Letter</button>
            <a href="#pricing" className="hover:text-blue-600 transition">Pricing</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
