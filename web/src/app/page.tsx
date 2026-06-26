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
  const [candDocTypes, setCandDocTypes] = useState<Record<number, 'resume' | 'cover_letter'>>({
    0: 'resume',
    1: 'resume',
    2: 'resume'
  });

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
    if (file && (file as any).isMockTemplate) {
      const mockText = (file as any).mockText || '';
      sessionStorage.setItem('resumeText', mockText);
      sessionStorage.setItem('jobDescription', jobDescription);
      sessionStorage.setItem('fileName', file.name);
      return mockText;
    }
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
          <div className="flex items-center gap-2 select-none cursor-pointer" onClick={() => scrollToTool('resume')}>
            <img src="/logo-full.png" alt="ATSHacker" className="h-9 w-auto" />
          </div>
          <div className="flex items-center gap-8 text-sm font-bold text-slate-600">
            <button onClick={() => scrollToTool('resume')} className="hover:text-emerald-600 transition">Features</button>
            <a href="#templates" className="hover:text-emerald-600 transition">Templates</a>
            <a href="#pricing" className="hover:text-emerald-600 transition">Pricing</a>
            <button onClick={() => scrollToTool('resume')} className="hover:text-emerald-600 transition">Blog</button>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={() => scrollToTool('resume')} 
              className="text-slate-600 hover:text-emerald-600 text-sm font-bold transition"
            >
              Log In
            </button>
            <button 
              onClick={() => scrollToTool('resume')} 
              className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-extrabold px-4 py-2.5 rounded-lg transition shadow-sm hidden md:block"
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
            <div className="inline-flex items-center gap-2 bg-emerald-50/70 border border-emerald-100 text-emerald-800 px-4 py-1.5 rounded-full text-xs font-bold shadow-sm">
              <Shield className="w-3.5 h-3.5 fill-emerald-600/10 text-emerald-600" />
              <span>100% secure checkout via Stripe • One-time payment, no subscriptions</span>
            </div>
            
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 leading-none">
              The professional resume and <span className="text-emerald-600">cover letter builder</span> designed for ATS.
            </h1>
            
            <p className="text-lg text-slate-600 leading-relaxed max-w-2xl">
              Beat the bots, get noticed, and land your dream job with resumes tailored to specific job descriptions.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 pt-2">
              <button 
                onClick={() => scrollToTool('resume')} 
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-base px-8 py-4 rounded-xl transition duration-200 shadow-md hover:shadow-lg flex items-center justify-center gap-2"
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
            <div className="absolute inset-0 bg-emerald-500/10 rounded-3xl blur-3xl -z-10 transform scale-95"></div>
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
                    <span className="inline-block bg-red-50 border border-red-150 text-red-700 text-[10px] font-black px-2 py-0.5 rounded-md animate-float-slow">
                      Poor Original Resume (34/100)
                    </span>
                  </div>
                  {/* Mini Original Resume Card */}
                  <div className="border border-red-200 bg-white rounded-xl p-2.5 shadow-sm relative flex flex-col justify-between h-[230px] overflow-hidden select-none hover:scale-[1.02] hover:-rotate-1 transition-all duration-300 cursor-default">
                    {/* Header */}
                    <div className="flex items-center gap-1.5 border-b border-slate-150 pb-1.5 mb-1">
                      <img 
                        src="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&q=80&w=80&h=80" 
                        alt="Michael Torres" 
                        className="w-7 h-7 rounded-full object-cover border border-slate-200"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-[9px] font-black text-slate-800 truncate leading-none">Michael Torres</div>
                        <div className="text-[7px] text-slate-500 font-bold truncate leading-none mt-0.5">Marketing, Chicago IL</div>
                      </div>
                    </div>
                    {/* Single column — no structure */}
                    <div className="flex-grow text-[5.5px] text-slate-500 leading-tight text-left space-y-1.5">
                      <div className="font-extrabold text-[6px] text-slate-700 uppercase tracking-wide border-b border-rose-100 pb-0.5">Objective</div>
                      <p className="italic text-slate-400 text-[5px] leading-tight">"Looking for a marketing role where I can use my skills and grow professionally."</p>
                      <div className="font-extrabold text-[6px] text-slate-700 uppercase tracking-wide border-b border-rose-100 pb-0.5 mt-1">Experience</div>
                      <div className="pl-1 space-y-0.5">
                        <p className="font-bold text-[6px] text-slate-700">Marketing Manager — Growth Labs</p>
                        <p className="text-[5px] text-slate-400">2021 - Present</p>
                        <p className="text-[5px] italic text-slate-500">• Responsible for social media</p>
                        <p className="text-[5px] italic text-slate-500">• Helped with marketing campaigns</p>
                        <p className="text-[5px] italic text-slate-500">• Managed the team</p>
                      </div>
                      <div className="font-extrabold text-[6px] text-slate-700 uppercase tracking-wide border-b border-rose-100 pb-0.5 mt-1">Skills</div>
                      <p className="text-[5px] text-slate-400">Social Media, Team Player, Writing, Microsoft Word, PowerPoint</p>
                      <div className="font-extrabold text-[6px] text-slate-700 uppercase tracking-wide border-b border-rose-100 pb-0.5">Education</div>
                      <p className="text-[5px] text-slate-600">DePaul University — Marketing</p>
                    </div>
                  </div>
                  {/* Bullets */}
                  <div className="space-y-1 text-left text-[10px] leading-tight">
                    <p className="font-bold text-red-700">
                      <XCircle className="w-3 h-3 inline mr-0.5 -mt-0.5" /> Missing: <span className="font-extrabold text-red-900">LinkedIn Ads, Demand Gen, Marketing Ops, HubSpot, CAC/LTV</span>
                    </p>
                    <p className="text-slate-500 pl-2">
                      <span className="font-bold text-slate-700">Vague:</span> "Responsible for social media. Helped with campaigns. Managed the team."
                    </p>
                  </div>
                </div>

                {/* Column 2: Optimized Resume */}
                <div className="space-y-3">
                  <div className="text-center">
                    <span className="inline-block bg-emerald-50 border border-emerald-200 text-emerald-700 text-[10px] font-black px-2 py-0.5 rounded-md animate-float-slower">
                      ATS-Optimized (92/100)
                    </span>
                  </div>
                  {/* Mini Optimized Resume Card */}
                  <div className="optimized-card border border-emerald-300 bg-white rounded-xl p-2.5 shadow-md relative flex flex-col justify-between h-[230px] overflow-hidden select-none hover:scale-[1.02] hover:rotate-1 transition-all duration-300 cursor-default">
                    {/* Header */}
                    <div className="flex items-center gap-1.5 border-b border-emerald-100 pb-1.5 mb-1">
                      <img 
                        src="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&q=80&w=80&h=80" 
                        alt="Michael Torres" 
                        className="w-7 h-7 rounded-full object-cover border-2 border-emerald-200"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-[9px] font-black text-slate-800 truncate leading-none">Michael Torres</div>
                        <div className="text-[7px] text-emerald-700 font-bold truncate leading-none mt-0.5">Senior Marketing Manager • Chicago, IL</div>
                      </div>
                    </div>
                    {/* Two column — professional layout */}
                    <div className="flex-grow grid grid-cols-12 gap-1 text-[5.5px] leading-tight text-left">
                      {/* Left sidebar */}
                      <div className="col-span-4 bg-emerald-50/40 p-1 rounded border-r border-emerald-100 flex flex-col justify-between">
                        <div className="space-y-1">
                          <div className="font-extrabold text-[5px] text-emerald-700 uppercase tracking-wide border-b border-emerald-100 pb-0.5 mb-0.5">Core Skills</div>
                          <div className="space-y-0.5 font-semibold text-emerald-800 text-[5px]">
                            <p className="highlight-keyword px-0.5 rounded">• Demand Generation</p>
                            <p className="highlight-keyword px-0.5 rounded">• LinkedIn/Meta Ads</p>
                            <p className="highlight-keyword px-0.5 rounded">• HubSpot & Marketo</p>
                            <p className="highlight-keyword px-0.5 rounded">• CAC/LTV Analysis</p>
                          </div>
                          <div className="font-extrabold text-[5px] text-emerald-700 uppercase tracking-wide border-b border-emerald-100 pb-0.5 mt-1 mb-0.5">Certifications</div>
                          <div className="text-[4.5px] text-slate-600 font-medium space-y-0.5">
                            <p>• Google Analytics 4</p>
                            <p>• HubSpot Inbound Mktg</p>
                          </div>
                        </div>
                        <div className="text-[4.5px] font-medium border-t border-emerald-100 pt-0.5 mt-1">
                          <p className="font-extrabold text-[4px] uppercase text-slate-400">Contact</p>
                          <p className="text-slate-600">Chicago, IL 60611</p>
                          <p className="text-slate-600 truncate">m.torres@gmail.com</p>
                        </div>
                      </div>
                      {/* Right content */}
                      <div className="col-span-8 p-0.5 flex flex-col justify-between">
                        <div className="space-y-1">
                          <div className="font-extrabold text-[5px] text-slate-700 uppercase tracking-wide border-b border-slate-100 pb-0.5 mb-0.5">Professional Experience</div>
                          <div className="space-y-1 pl-1 border-l border-emerald-300">
                            <div>
                              <p className="font-extrabold text-[6px] text-slate-800 leading-none">Senior Marketing Manager</p>
                              <p className="text-[4.5px] text-slate-400 font-bold">Growth Labs Inc. • Jan 2021 – Present</p>
                              <p className="text-[5px] text-slate-700 font-medium mt-0.5 leading-tight">
                                • Scaled <span className="highlight-keyword font-bold px-0.5 rounded">B2B demand gen</span> pipeline from $800K to <span className="highlight-keyword font-bold px-0.5 rounded">$2.4M ARR</span>
                              </p>
                              <p className="text-[5px] text-slate-700 font-medium leading-tight">
                                • Cut <span className="highlight-keyword font-bold px-0.5 rounded">CAC by 32%</span> via <span className="highlight-keyword font-bold px-0.5 rounded">LinkedIn Ads</span> audience segmentation
                              </p>
                              <p className="text-[5px] text-slate-700 font-medium leading-tight">
                                • Built <span className="highlight-keyword font-bold px-0.5 rounded">HubSpot</span> lead scoring workflow; 3x MQL-to-SQL rate
                              </p>
                            </div>
                            <div>
                              <p className="font-extrabold text-[5.5px] text-slate-800 leading-none">Marketing Specialist</p>
                              <p className="text-[4.5px] text-slate-400 font-bold">Growth Labs Inc. • 2018 – 2020</p>
                              <p className="text-[5px] text-slate-600 font-medium mt-0.5">• Grew LinkedIn following 140%; launched gated content program</p>
                            </div>
                          </div>
                        </div>
                        <div className="border-t border-slate-100 pt-0.5 mt-0.5">
                          <div className="font-extrabold text-[4.5px] text-slate-400 uppercase">Education</div>
                          <p className="text-[5px] font-bold text-slate-700">DePaul University — B.A. Marketing & Comm.</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  {/* Bullets */}
                  <div className="space-y-1 text-left text-[10px] leading-tight">
                    <p className="font-bold text-emerald-700">
                      <CheckCircle className="w-3 h-3 inline mr-0.5 -mt-0.5" /> Matched: <span className="highlight-keyword font-extrabold text-emerald-800 px-0.5 rounded">Demand Gen</span>, <span className="highlight-keyword font-extrabold text-emerald-800 px-0.5 rounded">LinkedIn Ads</span>, <span className="highlight-keyword font-extrabold text-emerald-800 px-0.5 rounded">HubSpot</span>, <span className="highlight-keyword font-extrabold text-emerald-800 px-0.5 rounded">CAC/LTV</span>
                    </p>
                    <p className="text-slate-650 pl-2">
                      <span className="font-bold text-slate-800">Impact:</span> Scaled B2B pipeline from $800K → $2.4M ARR. Cut CAC by 32% via LinkedIn audience segmentation.
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
                ${activeTab === 'resume' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-600 hover:text-emerald-600 hover:bg-slate-50'}`}
            >
              <FileText className="w-4 h-4" />
              <span>Resume Tailoring</span>
            </button>
            <button
              onClick={() => { setActiveTab('cover_letter'); setScore(null); }}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-all duration-200
                ${activeTab === 'cover_letter' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-600 hover:text-emerald-600 hover:bg-slate-50'}`}
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

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {[
              {
                name: 'Priya Ramirez',
                title: 'Product Manager, San Francisco',
                avatar: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&q=80&w=150&h=150',
                themeBg: 'bg-violet-50/30',
                accentText: 'text-violet-600',
                accentBg: 'bg-violet-600',
                accentBorder: 'border-violet-200',
                accentBorderL: 'border-l-violet-600',
                layout: 'pm',
                skills: ['Product Roadmapping', 'Agile / Scrum', 'SQL & Amplitude', 'Stakeholder Mgmt'],
                email: 'priya.ramirez@gmail.com',
                phone: '415-555-0182',
                address: 'San Francisco, CA',
                jobs: [
                  {
                    company: 'Convoy Logistics',
                    role: 'Senior Product Manager',
                    date: 'Mar 2021 - Present',
                    bullets: [
                      'Owned end-to-end roadmap for a $12M ARR freight-matching platform serving 4,000+ carriers.',
                      'Ran 14 A/B tests that lifted shipper conversion by 22% and reduced churn by 11%.'
                    ]
                  },
                  {
                    company: 'Convoy Logistics',
                    role: 'Associate Product Manager',
                    date: 'Jun 2019 - Feb 2021',
                    bullets: [
                      'Shipped carrier onboarding flow redesign, cutting drop-off rate from 38% to 17%.'
                    ]
                  }
                ],
                education: {
                  school: 'UC Berkeley',
                  degree: 'B.S. in Cognitive Science',
                  date: 'Graduated 2018'
                },
                coverLetter: {
                  date: 'June 26, 2026',
                  recipient: 'Head of Product\nStripe Inc.\nSan Francisco, CA 94103',
                  subject: 'Subject: Application for Senior Product Manager — Payments',
                  body: [
                    'Dear Head of Product,',
                    'I am excited to apply for the Senior Product Manager role on the Payments team at Stripe. At Convoy Logistics, I own the roadmap for a $12M ARR freight-matching platform. I have led 14 A/B experiments that lifted shipper conversion by 22% and significantly reduced churn.',
                    'My background in cognitive science gives me a research-first approach to user problems. I write detailed PRDs, run SQL analyses in Amplitude to validate hypotheses, and collaborate cross-functionally with engineering, design, and data science.',
                    'I am drawn to Stripe\'s developer-first culture and would love the opportunity to drive measurable product impact on the Payments experience. Thank you for your consideration.',
                    'Sincerely,',
                    'Priya Ramirez'
                  ]
                },
                mockText: `Priya Ramirez\n415-555-0182 | priya.ramirez@gmail.com | San Francisco, CA\n\nProfessional Summary:\nAnalytical and customer-centric Senior Product Manager with 5+ years of experience leading cross-functional teams to design, build, and scale B2B SaaS and logistics products. Proven track record of owning end-to-end roadmap strategy for a $12M ARR logistics platform, running high-impact A/B experiments, and using data-driven insights (SQL, Amplitude) to increase conversion and reduce churn.\n\nSkills:\nProduct Roadmapping, Agile/Scrum Methodologies, SQL, Amplitude, Product Analytics, Stakeholder Management, User Research, A/B Testing, PRD Writing, Jira.\n\nWork Experience:\nConvoy Logistics | Senior Product Manager | San Francisco, CA | March 2021 – Present\n- Owned the end-to-end product strategy and roadmap for a $12M ARR freight-matching web and mobile platform serving over 4,000 active carriers.\n- Designed and ran 14 A/B experiments that successfully lifted shipper booking conversion rates by 22% and decreased carrier churn by 11%.\n- Authored detailed PRDs, mapped user journeys, and collaborated with a 12-person cross-functional squad of engineers, designers, and data scientists.\n\nConvoy Logistics | Associate Product Manager | San Francisco, CA | June 2019 – February 2021\n- Led the redesign of the carrier onboarding flow, simplifying verification steps and cutting candidate drop-off rate from 38% to 17%.\n- Conducted 30+ qualitative user interviews to understand driver pain points, translating insights into key feature enhancements.\n\nEducation:\nUC Berkeley | B.S. in Cognitive Science | San Francisco, CA | Graduated 2018`,
                mockJobDescription: `Stripe is looking for a Senior Product Manager to lead product strategy and execution for our Core Payments platform.\n\nKey Responsibilities:\n- Own the end-to-end product roadmap for Stripe's payments APIs, developer portals, and merchant onboarding flows.\n- Collaborate with engineering, data science, and design to ship highly reliable payments infrastructure.\n- Use data-driven product analytics (SQL, Amplitude, Tableau) to design A/B experiments and optimize merchant conversion.\n- Engage directly with key enterprise merchant stakeholders to gather product requirements.\n\nRequired Qualifications:\n- 4+ years of product management experience, preferably in B2B SaaS, API products, or fintech.\n- Deep expertise in Agile / Scrum methodologies, PRD writing, and product roadmapping.\n- Strong analytical skills with the ability to write SQL queries and run A/B testing frameworks.\n- Exceptional stakeholder management and communication skills.`
              },
              {
                name: 'David Nakamura',
                title: 'Registered Nurse (BSN), Denver',
                avatar: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&q=80&w=150&h=150',
                themeBg: 'bg-sky-50/30',
                accentText: 'text-sky-600',
                accentBg: 'bg-sky-600',
                accentBorder: 'border-sky-200',
                accentBorderL: 'border-l-sky-600',
                layout: 'nurse',
                skills: ['ICU / Critical Care', 'Epic EMR', 'Patient Assessment', 'BLS / ACLS Certified'],
                email: 'david.nakamura@gmail.com',
                phone: '720-555-0137',
                address: 'Denver, CO',
                jobs: [
                  {
                    company: 'UCHealth Medical Center',
                    role: 'ICU Registered Nurse',
                    date: 'Aug 2020 - Present',
                    bullets: [
                      'Provided critical care for a 22-bed Medical ICU, managing ventilators, vasopressors, and central lines for 4–5 patients per shift.',
                      'Reduced medication error rate by 18% by implementing barcode scanning protocols in Epic EMR.'
                    ]
                  },
                  {
                    company: 'UCHealth Medical Center',
                    role: 'Med-Surg RN',
                    date: 'May 2018 - Jul 2020',
                    bullets: [
                      'Managed care for 6 post-surgical patients; achieved 94% patient satisfaction score.'
                    ]
                  }
                ],
                education: {
                  school: 'University of Colorado',
                  degree: 'Bachelor of Science in Nursing (BSN)',
                  date: 'Graduated 2018'
                },
                coverLetter: {
                  date: 'June 26, 2026',
                  recipient: 'Nurse Recruiter\nMayo Clinic\nRochester, MN 55905',
                  subject: 'Subject: Application for ICU Registered Nurse',
                  body: [
                    'Dear Nurse Recruiter,',
                    'I am writing to apply for the ICU Registered Nurse position at Mayo Clinic. I bring four years of critical care experience in a 22-bed Medical ICU at UCHealth, where I manage ventilators, vasopressors, and central line care for high-acuity patients.',
                    'I implemented barcode medication administration protocols using Epic EMR that reduced medication errors by 18%. I hold active BLS, ACLS, and CCRN certifications and am passionate about evidence-based nursing practice.',
                    'Mayo Clinic\'s reputation for interdisciplinary patient care aligns with my professional values. I look forward to contributing to your ICU team. Thank you for your time.',
                    'Sincerely,',
                    'David Nakamura, BSN, RN'
                  ]
                },
                mockText: `David Nakamura, BSN, RN\n720-555-0137 | david.nakamura@gmail.com | Denver, CO\n\nProfessional Summary:\nDedicated, clinical ICU Registered Nurse (BSN, RN) with 6+ years of experience providing high-acuity care in fast-paced ICU settings. Proven expert in patient assessment, ventilator management, central line care, and vasopressor administration. Commended for team collaboration, patient advocacy, and maintaining compliance with clinical safety guidelines. Expert user of Epic EMR.\n\nSkills:\nICU/Critical Care Nursing, Epic EMR, Patient Assessment, Ventilator Management, Vasopressor Administration, Central Line Care, BLS & ACLS Certified, Patient Safety, EKG Monitoring.\n\nWork Experience:\nUCHealth Medical Center | ICU Registered Nurse | Denver, CO | August 2020 – Present\n- Delivered critical care for high-acuity patients in a 22-bed Medical Intensive Care Unit (MICU), managing complex ventilators, vasopressors, and arterial lines.\n- Led clinical pilot for Epic EMR barcode scanning protocols, reducing ward medication administration errors by 18%.\n- Coordinated with interdisciplinary teams of physicians, respiratory therapists, and pharmacologists to manage critical care plans for 4-5 patients per shift.\n\nUCHealth Medical Center | Med-Surg RN | Denver, CO | May 2018 – July 2020\n- Provided comprehensive post-surgical care for up to 6 patients simultaneously on a busy medical-surgical unit.\n- Maintained a 94% patient satisfaction rating based on post-discharge patient care surveys.\n\nEducation & Credentials:\nUniversity of Colorado | Bachelor of Science in Nursing (BSN) | Denver, CO | Graduated 2018\n- RN License, State of Colorado (Active)\n- BLS (Basic Life Support) & ACLS (Advanced Cardiovascular Life Support) Certified (Active)\n- CCRN (Critical Care Registered Nurse) Certified (Active)`,
                mockJobDescription: `Mayo Clinic is seeking a skilled ICU Registered Nurse (RN) to join our Critical Care Intensive Care Unit.\n\nKey Responsibilities:\n- Provide direct, evidence-based nursing care to high-acuity ICU patients.\n- Monitor patient vital signs, perform comprehensive patient assessments, and manage advanced equipment including ventilators, central lines, and arterial lines.\n- Administer critical care medications including vasopressors, antiarrhythmics, and sedatives.\n- Document clinical notes and assessments accurately using Epic EMR system.\n- Work collaboratively with ICU physicians and clinical specialists to adjust patient care plans.\n\nRequired Qualifications:\n- BSN (Bachelor of Science in Nursing) degree from an accredited school of nursing.\n- Active Registered Nurse (RN) license in good standing.\n- Current certifications in BLS (Basic Life Support) and ACLS (Advanced Cardiovascular Life Support). CCRN certification is a strong plus.\n- Experience with patient assessment and Critical Care / Intensive Care Nursing protocols.`
              },
              {
                name: 'Rachel Whitfield',
                title: 'Financial Analyst, New York',
                avatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=150&h=150',
                themeBg: 'bg-amber-50/30',
                accentText: 'text-amber-700',
                accentBg: 'bg-amber-600',
                accentBorder: 'border-amber-200',
                accentBorderL: 'border-l-amber-600',
                layout: 'finance',
                skills: ['Financial Modeling', 'Excel (VBA/Macros)', 'Power BI / Tableau', 'GAAP Compliance'],
                email: 'rachel.whitfield@gmail.com',
                phone: '917-555-0163',
                address: 'New York, NY',
                jobs: [
                  {
                    company: 'Meridian Capital Group',
                    role: 'Senior Financial Analyst',
                    date: 'Jan 2022 - Present',
                    bullets: [
                      'Built 3-statement financial models for $200M+ commercial real estate transactions.',
                      'Automated monthly variance reporting with VBA macros, saving 12 hours per cycle.'
                    ]
                  },
                  {
                    company: 'Meridian Capital Group',
                    role: 'Financial Analyst',
                    date: 'Jun 2019 - Dec 2021',
                    bullets: [
                      'Prepared quarterly board decks and supported due diligence for 8 M&A deals totaling $75M.'
                    ]
                  }
                ],
                education: {
                  school: 'NYU Stern School of Business',
                  degree: 'B.S. in Finance & Accounting',
                  date: 'Graduated 2019'
                },
                coverLetter: {
                  date: 'June 26, 2026',
                  recipient: 'Finance Hiring Manager\nGoldman Sachs\nNew York, NY 10282',
                  subject: 'Subject: Application for Vice President — FP&A',
                  body: [
                    'Dear Finance Hiring Manager,',
                    'I am writing to apply for the VP of FP&A role at Goldman Sachs. In my current role at Meridian Capital Group, I build 3-statement financial models for commercial real estate transactions exceeding $200M and present variance analyses to C-suite stakeholders.',
                    'I automated our monthly reporting pipeline using VBA and Power BI, saving 12 hours per cycle and eliminating manual data-entry errors. I also supported due diligence across 8 M&A transactions totaling $75M.',
                    'Goldman Sachs\' emphasis on analytical rigor and operational excellence resonates strongly with my career trajectory. I would welcome the opportunity to discuss how my modeling and reporting skills can contribute to the FP&A function.',
                    'Sincerely,',
                    'Rachel Whitfield'
                  ]
                },
                mockText: `Rachel Whitfield\n917-555-0163 | rachel.whitfield@gmail.com | New York, NY\n\nProfessional Summary:\nMeticulous and results-oriented Senior Financial Analyst with 5+ years of experience building complex financial models and managing corporate FP&A pipelines. Proven track record in 3-statement modeling, M&A due diligence, and budgeting. Expert in automating reporting processes using Excel VBA macros, Power BI, and Tableau to drive data-driven executive decisions.\n\nSkills:\nFinancial Modeling, Excel (VBA & Advanced Macros), Power BI, Tableau, Corporate FP&A, GAAP Compliance, Budgeting & Forecasting, Variance Analysis, Due Diligence, SQL.\n\nWork Experience:\nMeridian Capital Group | Senior Financial Analyst | New York, NY | January 2022 – Present\n- Built and maintained dynamic 3-statement financial models (income, balance sheet, cash flow) for commercial real estate transactions exceeding $200M.\n- Automated monthly corporate budget variance reporting using Excel VBA macros and Power BI, saving the finance team 12 hours per reporting cycle.\n- Conducted financial analysis and prepared detailed board decks for presentation to C-suite executives and board members.\n\nMeridian Capital Group | Financial Analyst | New York, NY | June 2019 – December 2021\n- Supported financial due diligence for 8 M&A acquisitions totaling $75M in deal volume, reviewing historical financial statements for GAAP compliance.\n- Monitored and reported on weekly departmental spend, identifying $40K in annual software duplication savings.\n\nEducation:\nNYU Stern School of Business | B.S. in Finance & Accounting | New York, NY | Graduated 2019`,
                mockJobDescription: `Goldman Sachs is hiring a Vice President of FP&A (Financial Planning & Analysis) to join our Corporate Treasury and Finance Division in New York.\n\nKey Responsibilities:\n- Direct the division's corporate budgeting, forecasting, and long-term financial modeling processes.\n- Construct complex 3-statement financial models to simulate different economic scenarios and evaluate strategic investments.\n- Automate manual finance processes and build executive reporting dashboards in Power BI or Tableau.\n- Perform detailed monthly variance analyses comparing actual spend against target budget.\n- Coordinate due diligence for internal corporate development and strategic acquisition deals.\n- Ensure all financial planning and reporting remains in strict compliance with GAAP standards.\n\nRequired Qualifications:\n- 5+ years of experience in corporate finance, investment banking, FP&A, or accounting.\n- Exceptional expertise in Excel (advanced modeling, VBA, macros) and business intelligence tools (Power BI, Tableau).\n- Thorough understanding of GAAP compliance and corporate accounting.\n- Proven experience building 3-statement models and performing due diligence.`
              }
            ].map((cand, idx) => (
              <div key={idx} className="group bg-white border border-slate-200 rounded-3xl shadow-lg hover:shadow-2xl hover:scale-[1.02] transition-all duration-300 transform overflow-hidden flex flex-col">
                {/* Doc Type Toggle Header */}
                <div className="bg-slate-50 border-b border-slate-100 px-4 py-3 flex justify-between items-center select-none">
                  <span className="text-[10px] font-black uppercase tracking-wider text-slate-400">Template Showcase</span>
                  <div className="bg-white border border-slate-200 rounded-xl p-1 inline-flex gap-1 shadow-sm">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setCandDocTypes(prev => ({ ...prev, [idx]: 'resume' }));
                      }}
                      className={`px-3 py-1 rounded-lg text-[10px] font-black transition-all duration-250 cursor-pointer ${
                        candDocTypes[idx] === 'resume'
                          ? 'bg-emerald-600 text-white shadow-sm'
                          : 'text-slate-650 hover:text-emerald-600 hover:bg-slate-50'
                      }`}
                    >
                      Resume
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setCandDocTypes(prev => ({ ...prev, [idx]: 'cover_letter' }));
                      }}
                      className={`px-3 py-1 rounded-lg text-[10px] font-black transition-all duration-250 cursor-pointer ${
                        candDocTypes[idx] === 'cover_letter'
                          ? 'bg-emerald-600 text-white shadow-sm'
                          : 'text-slate-650 hover:text-emerald-600 hover:bg-slate-50'
                      }`}
                    >
                      Cover Letter
                    </button>
                  </div>
                </div>

                {/* Resume Paper Container */}
                <div className="flex-grow flex flex-col text-left bg-white min-h-[500px]">
                  {candDocTypes[idx] === 'resume' ? (
                    // Resume View
                    cand.layout === 'pm' ? (
                      // Modern PM Executive Template (Top Banner)
                      <div className="flex-grow flex flex-col">
                        {/* Top banner across 100% */}
                        <div className="bg-violet-950 text-white p-5 border-b border-violet-800">
                          <div className="flex items-center justify-between gap-4">
                            <div>
                              <h4 className="text-xl font-black tracking-tight">{cand.name}</h4>
                              <p className="text-[10px] text-violet-300 font-bold uppercase tracking-wider mt-1">{cand.title}</p>
                            </div>
                            <img src={cand.avatar} alt={cand.name} className="w-12 h-12 rounded-full object-cover border-2 border-violet-400 shadow-sm" />
                          </div>
                        </div>
                        {/* Body 2-columns */}
                        <div className="flex-grow grid grid-cols-12">
                          {/* Left col */}
                          <div className="col-span-4 bg-violet-50/20 p-4 border-r border-slate-100 space-y-4">
                            <div className="space-y-2">
                              <h5 className="text-[9px] font-black text-violet-900 uppercase tracking-widest border-b border-violet-100 pb-1">Skills</h5>
                              <div className="space-y-1.5">
                                {cand.skills.map((skill, sIdx) => (
                                  <div key={sIdx} className="space-y-0.5">
                                    <div className="text-[8px] font-bold text-slate-700 leading-none">{skill}</div>
                                    <div className="h-1 w-full bg-slate-200 rounded-full overflow-hidden">
                                      <div className={`h-full ${cand.accentBg} rounded-full`} style={{ width: `${85 - sIdx * 8}%` }}></div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                            <div className="space-y-2 pt-2 border-t border-violet-100">
                              <h5 className="text-[9px] font-black text-violet-900 uppercase tracking-widest">Contact</h5>
                              <div className="space-y-1 text-[8.5px] text-slate-650 font-medium">
                                <p className="truncate"><span className="font-bold text-slate-700">Email:</span> {cand.email}</p>
                                <p><span className="font-bold text-slate-700">Phone:</span> {cand.phone}</p>
                                <p><span className="font-bold text-slate-700">Address:</span> {cand.address}</p>
                              </div>
                            </div>
                          </div>
                          {/* Right col */}
                          <div className="col-span-8 p-5 space-y-4">
                            <div className="space-y-3">
                              <h5 className="text-[9px] font-black text-violet-900 uppercase tracking-widest border-b border-slate-200 pb-1">Work History</h5>
                              <div className="relative pl-3.5 border-l border-slate-155 space-y-3">
                                {cand.jobs.map((job, jIdx) => (
                                  <div key={jIdx} className="relative space-y-0.5">
                                    <span className={`absolute -left-[18.5px] top-1 w-2 h-2 rounded-full ${cand.accentBg} border border-white shadow-sm`}></span>
                                    <div className="flex justify-between items-baseline gap-2">
                                      <div className="text-[9px] font-black text-slate-800">{job.role}</div>
                                      <div className="text-[7.5px] text-slate-500 font-bold whitespace-nowrap">{job.date}</div>
                                    </div>
                                    <div className="text-[8px] text-slate-500 font-bold italic leading-none">{job.company}</div>
                                    <ul className="space-y-0.5 list-disc pl-3 mt-1">
                                      {job.bullets.map((b, bIdx) => (
                                        <li key={bIdx} className="text-[8.5px] text-slate-655 leading-relaxed">{b}</li>
                                      ))}
                                    </ul>
                                  </div>
                                ))}
                              </div>
                            </div>
                            <div className="space-y-1.5 pt-2 border-t border-slate-100">
                              <h5 className="text-[9px] font-black text-violet-900 uppercase tracking-widest">Education</h5>
                              <div className="flex justify-between items-baseline gap-2 text-[8.5px]">
                                <div className="font-black text-slate-800">{cand.education.school}</div>
                                <div className="text-slate-500 font-bold">{cand.education.date}</div>
                              </div>
                              <p className="text-[8px] text-slate-600 font-medium">{cand.education.degree}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : cand.layout === 'nurse' ? (
                      // Clinical Standard Template (Pure Single-Column Linear)
                      <div className="flex-grow p-5 space-y-4">
                        {/* Centered Clinical Header */}
                        <div className="text-center space-y-1 border-b border-sky-205 pb-3">
                          <div className="flex items-center justify-center gap-3">
                            <img src={cand.avatar} alt={cand.name} className="w-10 h-10 rounded-full object-cover border border-slate-200 shadow-sm" />
                            <div className="text-left">
                              <h4 className="text-xl font-black text-slate-900 leading-none">{cand.name}</h4>
                              <p className="text-[9px] font-bold text-sky-700 uppercase tracking-wider mt-1">{cand.title}</p>
                            </div>
                          </div>
                          <div className="text-[8px] text-slate-500 font-semibold flex flex-wrap justify-center gap-x-2 gap-y-0.5 mt-2">
                            <span>{cand.address}</span>
                            <span>•</span>
                            <span>{cand.phone}</span>
                            <span>•</span>
                            <span className="truncate">{cand.email}</span>
                          </div>
                        </div>
                        {/* Professional Summary */}
                        <div className="space-y-1">
                          <h5 className="text-[9px] font-black text-sky-900 uppercase tracking-widest border-b border-slate-200 pb-0.5">Professional Summary</h5>
                          <p className="text-[8.5px] text-slate-655 leading-relaxed">Dedicated Clinical Intensive Care Nurse (BSN, RN) with 6+ years of ICU and Med-Surg experience. Certified in ACLS, BLS, and CCRN with clinical expertise in ventilator care, vasopressors, and patient safety.</p>
                        </div>
                        {/* Skills Grid */}
                        <div className="space-y-1">
                          <h5 className="text-[9px] font-black text-sky-900 uppercase tracking-widest border-b border-slate-200 pb-0.5">Clinical Skills</h5>
                          <div className="grid grid-cols-2 gap-2 text-[8px] text-slate-750 font-bold bg-slate-50/50 p-2 rounded-xl border border-slate-100">
                            {cand.skills.map((skill, sIdx) => (
                              <div key={sIdx} className="flex items-center gap-1">
                                <span className="w-1.5 h-1.5 rounded-full bg-sky-500"></span>
                                <span>{skill}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                        {/* Work History */}
                        <div className="space-y-2">
                          <h5 className="text-[9px] font-black text-sky-900 uppercase tracking-widest border-b border-slate-200 pb-0.5">Professional Experience</h5>
                          <div className="space-y-3">
                            {cand.jobs.map((job, jIdx) => (
                              <div key={jIdx} className="space-y-1">
                                <div className="flex justify-between items-baseline gap-2">
                                  <div className="text-[9px] font-black text-slate-800">{job.role} — <span className="text-[8px] text-slate-500 font-bold italic">{job.company}</span></div>
                                  <div className="text-[7.5px] text-slate-500 font-bold whitespace-nowrap">{job.date}</div>
                                </div>
                                <ul className="space-y-0.5 list-disc pl-3">
                                  {job.bullets.map((b, bIdx) => (
                                    <li key={bIdx} className="text-[8.5px] text-slate-655 leading-relaxed">{b}</li>
                                  ))}
                                </ul>
                              </div>
                            ))}
                          </div>
                        </div>
                        {/* Education */}
                        <div className="space-y-1">
                          <h5 className="text-[9px] font-black text-sky-900 uppercase tracking-widest border-b border-slate-200 pb-0.5">Education & Credentials</h5>
                          <div className="flex justify-between items-baseline gap-2 text-[8.5px]">
                            <div className="font-black text-slate-800">{cand.education.school}</div>
                            <div className="text-slate-500 font-bold">{cand.education.date}</div>
                          </div>
                          <p className="text-[8px] text-slate-600 font-medium">{cand.education.degree}</p>
                        </div>
                      </div>
                    ) : (
                      // Corporate Analyst Template (Left Accent Sidebar)
                      <div className="flex-grow grid grid-cols-12">
                        {/* Left column sidebar (Accent border, no fill) */}
                        <div className="col-span-4 p-4 border-r-2 border-amber-500 flex flex-col justify-between space-y-4">
                          <div className="space-y-4">
                            {/* Initials Badge */}
                            <div className="flex items-center gap-2">
                              <img src={cand.avatar} alt={cand.name} className="w-12 h-12 rounded-xl object-cover border border-amber-200 shadow-sm" />
                              <div>
                                <span className="text-[12px] font-black text-amber-800 uppercase block tracking-wider leading-none">RW</span>
                                <span className="text-[7.5px] text-slate-400 font-bold block mt-0.5">Finance</span>
                              </div>
                            </div>
                            {/* Skills progress */}
                            <div className="space-y-2">
                              <h5 className="text-[9px] font-black text-amber-805 uppercase tracking-widest border-b border-slate-200 pb-0.5">Core Skills</h5>
                              <div className="space-y-1.5">
                                {cand.skills.map((skill, sIdx) => (
                                  <div key={sIdx} className="space-y-0.5">
                                    <div className="text-[8px] font-bold text-slate-700 leading-none">{skill}</div>
                                    <div className="h-1 w-full bg-slate-100 rounded-full overflow-hidden">
                                      <div className="h-full bg-amber-500" style={{ width: `${90 - sIdx * 6}%` }}></div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                          <div className="space-y-1.5 text-[8px] text-slate-500 font-semibold border-t border-slate-105 pt-2">
                            <p className="truncate"><span className="text-slate-700 font-bold">Email:</span> {cand.email}</p>
                            <p><span className="text-slate-700 font-bold">Phone:</span> {cand.phone}</p>
                            <p><span className="text-slate-700 font-bold">Location:</span> {cand.address}</p>
                          </div>
                        </div>
                        {/* Right column */}
                        <div className="col-span-8 p-5 space-y-4 flex flex-col justify-between">
                          <div className="space-y-3">
                            <div>
                              <h4 className="text-xl font-black text-slate-900 leading-none">{cand.name}</h4>
                              <p className="text-[9px] font-bold text-amber-700 mt-1 uppercase tracking-wider">{cand.title}</p>
                            </div>
                            <div className="space-y-2">
                              <h5 className="text-[9px] font-black text-slate-800 uppercase tracking-widest border-b border-slate-100 pb-0.5">Experience</h5>
                              <div className="space-y-3">
                                {cand.jobs.map((job, jIdx) => (
                                  <div key={jIdx} className="space-y-1">
                                    <div className="flex justify-between items-baseline gap-2 leading-none">
                                      <div className="text-[9px] font-black text-slate-800">{job.role}</div>
                                      <div className="text-[7.5px] text-slate-500 font-bold whitespace-nowrap">{job.date}</div>
                                    </div>
                                    <div className="text-[8px] text-slate-400 font-bold leading-none">{job.company}</div>
                                    <ul className="space-y-0.5 list-disc pl-3">
                                      {job.bullets.map((b, bIdx) => (
                                        <li key={bIdx} className="text-[8.5px] text-slate-655 leading-relaxed">{b}</li>
                                      ))}
                                    </ul>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                          <div className="space-y-1 pt-2 border-t border-slate-100">
                            <h5 className="text-[9px] font-black text-slate-800 uppercase tracking-widest">Education</h5>
                            <div className="flex justify-between items-baseline gap-2 text-[8.5px]">
                              <div className="font-black text-slate-800">{cand.education.school}</div>
                              <div className="text-slate-500 font-bold">{cand.education.date}</div>
                            </div>
                            <p className="text-[8px] text-slate-650 font-medium">{cand.education.degree}</p>
                          </div>
                        </div>
                      </div>
                    )
                  ) : (
                    // Cover Letter View
                    cand.layout === 'pm' ? (
                      <div className="flex-grow flex flex-col">
                        <div className="bg-violet-955 text-white p-5 border-b border-violet-800 flex items-center justify-between gap-4">
                          <div>
                            <h4 className="text-xl font-black tracking-tight">{cand.name}</h4>
                            <p className="text-[9px] text-violet-300 font-bold uppercase tracking-wider mt-1">Cover Letter • {cand.title}</p>
                          </div>
                          <img src={cand.avatar} alt={cand.name} className="w-12 h-12 rounded-full object-cover border-2 border-violet-400 shadow-sm" />
                        </div>
                        <div className="flex-grow grid grid-cols-12">
                          <div className="col-span-4 bg-violet-50/20 p-4 border-r border-slate-100 text-[8.5px] text-slate-600 space-y-2">
                            <p className="font-extrabold text-violet-900 uppercase">Applicant</p>
                            <p>{cand.email}<br />{cand.phone}<br />{cand.address}</p>
                          </div>
                          <div className="col-span-8 p-5 space-y-3 text-[8.5px] leading-relaxed text-slate-600">
                            <div>
                              <p className="font-extrabold text-slate-800">{cand.coverLetter.date}</p>
                              <p className="mt-1 text-slate-400 whitespace-pre-line leading-normal">{cand.coverLetter.recipient}</p>
                            </div>
                            <p className="font-black text-slate-900 border-l-2 border-violet-650 pl-2">
                              {cand.coverLetter.subject}
                            </p>
                            <div className="space-y-2 mt-2 text-slate-655">
                              {cand.coverLetter.body.map((p, pIdx) => (
                                <p key={pIdx}>{p}</p>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : cand.layout === 'nurse' ? (
                      <div className="flex-grow p-5 space-y-3">
                        <div className="text-center space-y-1 border-b border-sky-200 pb-3">
                          <h4 className="text-xl font-black text-slate-900 leading-none">{cand.name}</h4>
                          <p className="text-[9px] font-bold text-sky-700 uppercase tracking-wider">Cover Letter • {cand.title}</p>
                          <div className="text-[8px] text-slate-500 font-semibold flex justify-center gap-2 mt-2">
                            <span>{cand.address}</span><span>•</span><span>{cand.phone}</span><span>•</span><span>{cand.email}</span>
                          </div>
                        </div>
                        <div className="text-[8.5px] leading-relaxed text-slate-600 space-y-2.5">
                          <div>
                            <p className="font-extrabold text-slate-800">{cand.coverLetter.date}</p>
                            <p className="mt-0.5 text-slate-400 whitespace-pre-line leading-normal">{cand.coverLetter.recipient}</p>
                          </div>
                          <p className="font-black text-slate-900 border-l-2 border-sky-600 pl-2">
                            {cand.coverLetter.subject}
                          </p>
                          <div className="space-y-2 text-slate-655">
                            {cand.coverLetter.body.map((p, pIdx) => (
                              <p key={pIdx}>{p}</p>
                            ))}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="flex-grow grid grid-cols-12">
                        <div className="col-span-4 p-4 border-r-2 border-amber-500 flex flex-col justify-between">
                          <div className="space-y-4">
                            <div className="flex items-center gap-2">
                              <img src={cand.avatar} alt={cand.name} className="w-10 h-10 rounded-xl object-cover border border-amber-200" />
                              <span className="text-[12px] font-black text-amber-800 uppercase block tracking-wider leading-none">RW</span>
                            </div>
                            <div className="space-y-1.5 text-[8px] text-slate-500 font-semibold">
                              <p className="font-extrabold text-amber-800">Sender Info</p>
                              <p>{cand.email}</p>
                              <p>{cand.phone}</p>
                              <p>{cand.address}</p>
                            </div>
                          </div>
                        </div>
                        <div className="col-span-8 p-5 space-y-3 text-[8.5px] leading-relaxed text-slate-650">
                          <div>
                            <h4 className="text-xl font-black text-slate-900 leading-none">{cand.name}</h4>
                            <p className="text-[9px] font-bold text-amber-700 mt-1 uppercase tracking-wider">{cand.title}</p>
                          </div>
                          <div className="border-t border-slate-100 pt-2">
                            <p className="font-extrabold text-slate-800">{cand.coverLetter.date}</p>
                            <p className="mt-0.5 text-slate-400 whitespace-pre-line leading-normal">{cand.coverLetter.recipient}</p>
                          </div>
                          <p className="font-black text-slate-900 border-l-2 border-amber-600 pl-2">
                            {cand.coverLetter.subject}
                          </p>
                          <div className="space-y-2 text-slate-655">
                            {cand.coverLetter.body.map((p, pIdx) => (
                              <p key={pIdx}>{p}</p>
                            ))}
                          </div>
                        </div>
                      </div>
                    )
                  )}
                </div>

                {/* Try Template Button Container */}
                <div className="p-4 bg-slate-50 border-t border-slate-100 text-center select-none">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      // Create a mock File object
                      const mockFile = new File([""], `${cand.name.replace(/\s+/g, '_')}_Resume.pdf`, { type: 'application/pdf' });
                      (mockFile as any).isMockTemplate = true;
                      (mockFile as any).mockText = cand.mockText;
                      (mockFile as any).mockJobDescription = cand.mockJobDescription;
                      
                      setFile(mockFile);
                      setJobDescription(cand.mockJobDescription);
                      setActiveTab(candDocTypes[idx] || 'resume');
                      setScore(null);
                      
                      toolSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
                    }}
                    className="w-full bg-white hover:bg-slate-50 hover:border-emerald-400 border border-slate-300 text-slate-700 font-extrabold py-2.5 rounded-xl transition text-center text-xs flex items-center justify-center gap-1.5 cursor-pointer shadow-sm active:scale-[0.99]"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Try this Template in Tool</span>
                  </button>
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
          <div className="bg-white border border-slate-200 rounded-3xl p-8 flex flex-col justify-between shadow-sm transition hover:border-emerald-300 hover:shadow-md">
            <div>
              <h3 className="font-extrabold text-slate-900 text-xl mb-2">Resume Tailoring</h3>
              <p className="text-xs text-slate-500 font-semibold mb-6">Perfect for individual target job descriptions.</p>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-black text-slate-900">$9.99</span>
                <span className="text-slate-400 text-xs font-bold">/ rewrite</span>
              </div>
              <ul className="space-y-3 text-sm text-slate-650 border-t border-slate-100 pt-6">
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
              <ul className="space-y-3 text-sm text-slate-650 border-t border-slate-100 pt-6">
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
              <ul className="space-y-3 text-sm text-slate-650 border-t border-slate-100 pt-6">
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
            <div className="flex items-center gap-2 select-none cursor-pointer mb-1.5" onClick={() => scrollToTool('resume')}>
              <img src="/logo-full.png" alt="ATSHacker" className="h-7 w-auto" />
            </div>
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
