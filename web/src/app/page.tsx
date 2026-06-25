"use client";
import React, { useState, useRef, useEffect } from 'react';
import { track } from '@vercel/analytics';
import { UploadCloud, CheckCircle, Shield, ArrowRight, FileText, Gauge, XCircle, Share2, Zap, Lock, BadgeCheck } from 'lucide-react';

// First-touch UTM keys we persist for sale attribution.
const UTM_KEYS = ['utm_source', 'utm_medium', 'utm_campaign'] as const;

// Read persisted (first-touch) UTM values from sessionStorage. Returns only
// the keys that have a stored value. Guarded so it never throws (SSR / privacy).
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

// Animated count-up to a target number. Honors prefers-reduced-motion by
// snapping straight to the target. Guarded for SSR.
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
      // easeOutCubic for a satisfying settle.
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

  const fileInputRef = useRef<HTMLInputElement>(null);
  const animatedScore = useCountUp(score ? score.score : null);

  // On first load, capture UTM params from the URL and persist them (first-touch:
  // only set if not already stored). Used later for sale attribution at checkout.
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
      /* ignore: URL/sessionStorage unavailable */
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

  // Extract text from the uploaded PDF and cache resume + JD in sessionStorage.
  const extractResumeText = async (): Promise<string> => {
    const pdfjsLib = await import('pdfjs-dist');
    // jsdelivr serves the npm package directly, so the worker always matches the
    // installed pdfjs-dist version. (cdnjs does NOT host the v6 worker → 404 → checkout broke.)
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

  // FREE: get the ATS match score before paying.
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
        // Funnel analytics: a free score was returned. Guarded so it never throws.
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

  const handleCheckout = async () => {
    if (!validateInputs()) return;
    setIsLoading(true);
    // Funnel analytics: user initiated payment. Guarded so it never throws.
    try {
      track('checkout_started');
    } catch {
      /* analytics best-effort */
    }
    try {
      // Reuse cached text if we already scored; otherwise extract now.
      if (!sessionStorage.getItem('resumeText')) await extractResumeText();
      // Attach first-touch UTM params so Stripe metadata can attribute the sale.
      const utms = getStoredUtms();
      const res = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileName: file!.name, jobDescription, ...utms }),
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
      /* user cancelled share */
    }
  };

  const scoreColor = score
    ? score.score >= 75 ? 'text-emerald-600' : score.score >= 50 ? 'text-amber-600' : 'text-red-600'
    : '';
  const scoreBar = score
    ? score.score >= 75 ? 'bg-emerald-500' : score.score >= 50 ? 'bg-amber-500' : 'bg-red-500'
    : 'bg-emerald-500';

  return (
    <div className="min-h-screen bg-white text-slate-900 font-sans selection:bg-emerald-500/20">

      {/* Navigation */}
      <nav className="w-full px-6 py-5 flex justify-between items-center max-w-7xl mx-auto">
        <div className="flex items-center gap-2.5">
          <img src="/logo-full.png" alt="ATSHacker" className="h-9 w-auto" />
        </div>
        <div className="flex items-center gap-6 text-sm font-medium text-slate-600">
          <a href="#how-it-works" className="hover:text-emerald-600 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/40 rounded">How it Works</a>
          <a href="#pricing" className="hover:text-emerald-600 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/40 rounded">Pricing</a>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-6 pt-8 pb-24 lg:pt-12 lg:pb-32">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">

          {/* Left: pitch */}
          <div className="space-y-7">
            <div className="inline-flex items-center gap-2 bg-emerald-100 border border-emerald-200 text-emerald-800 px-3.5 py-1.5 rounded-full text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Built for how Workday &amp; Greenhouse rank you</span>
            </div>

            <h1 className="text-5xl lg:text-7xl font-black leading-[1.05] tracking-tight text-slate-900">
              Stop getting buried by the <span className="text-emerald-600">keyword filter.</span>
            </h1>

            <p className="text-lg lg:text-xl text-slate-600 leading-relaxed max-w-xl">
              Recruiters search and rank resumes by keyword, and keyword-matched resumes are about <span className="text-slate-900 font-bold">3x more likely</span> to get seen. Check your match score free, then rewrite your resume to match the job for <span className="text-slate-900 font-bold">$9.99</span>.
            </p>

            <div className="space-y-3.5 pt-1">
              <div className="flex items-center space-x-3 text-slate-700">
                <Gauge className="w-5 h-5 text-emerald-600 shrink-0" />
                <span>Free instant ATS match score</span>
              </div>
              <div className="flex items-center space-x-3 text-slate-700">
                <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
                <span>Semantic keyword matching against the real job description</span>
              </div>
              <div className="flex items-center space-x-3 text-slate-700">
                <Shield className="w-5 h-5 text-emerald-600 shrink-0" />
                <span>Your resume is never stored on our servers</span>
              </div>
            </div>
          </div>

          {/* Right: the tool */}
          <div className="space-y-4">
            <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-sm relative overflow-hidden transition-all duration-300 hover:shadow-lg hover:border-emerald-300">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-600 to-emerald-400"></div>

              <h2 className="text-2xl font-bold mb-6 text-slate-900">Check Your Resume</h2>

              <div className="space-y-6">

                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-700">1. Upload Current Resume (PDF)</label>
                  <input type="file" accept=".pdf" ref={fileInputRef} className="hidden" onChange={handleFileChange} />
                  <div
                    role="button"
                    tabIndex={0}
                    aria-label="Upload your resume PDF. Drag and drop a file or press Enter to browse."
                    onClick={() => fileInputRef.current?.click()}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        fileInputRef.current?.click();
                      }
                    }}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={`border-2 border-dashed rounded-xl p-8 text-center transition cursor-pointer group focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/40
                      ${isDragging ? 'border-emerald-500 bg-emerald-50' : 'border-slate-300 hover:border-emerald-500/60 hover:bg-slate-50'}`}
                  >
                    {file ? (
                      <div className="flex flex-col items-center">
                        <FileText className="w-10 h-10 text-emerald-600 mb-3" />
                        <p className="text-sm text-slate-900 font-medium">{file.name}</p>
                        <p className="text-xs text-emerald-600 mt-1">Click to replace file</p>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center">
                        <UploadCloud className="w-10 h-10 text-slate-400 group-hover:text-emerald-600 transition mb-3" />
                        <p className="text-sm text-slate-600">Drag and drop or <span className="text-emerald-600">browse files</span></p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-700">2. Paste Target Job Description</label>
                  <textarea
                    rows={4}
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    placeholder="Paste the raw text of the job description here..."
                    className="w-full bg-white border border-slate-300 rounded-xl p-4 text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/30 transition resize-none"
                  ></textarea>
                </div>

                {/* FREE score button */}
                <button
                  onClick={handleScore}
                  disabled={isScoring}
                  className="w-full bg-white hover:bg-slate-50 hover:border-emerald-300 border border-slate-300 text-slate-900 font-bold text-base py-3 rounded-xl transition-all duration-200 active:scale-[0.98] flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/40"
                >
                  <Gauge className="w-5 h-5 text-emerald-600" />
                  <span>{isScoring ? "Scoring..." : "Get Free Match Score"}</span>
                </button>

                {/* Score result panel — the score is the hero */}
                {score && (
                  <div className="ath-reveal bg-white border border-slate-200 rounded-2xl p-6 space-y-5 shadow-sm">
                    {/* Hero score number */}
                    <div className="flex flex-col items-center text-center pt-1">
                      <span className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-1">Your ATS Match Score</span>
                      <div className="flex items-end justify-center leading-none">
                        <span className={`ath-score-pop text-7xl font-black tabular-nums ${scoreColor}`}>{animatedScore}</span>
                        <span className="text-2xl font-bold text-slate-300 mb-1.5">/100</span>
                      </div>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                      <div className={`${scoreBar} h-2 rounded-full transition-all duration-700 ease-out`} style={{ width: `${animatedScore}%` }}></div>
                    </div>
                    {score.verdict && <p className="text-sm text-slate-600 text-center leading-relaxed">{score.verdict}</p>}

                    {score.matchedKeywords?.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-emerald-700 mb-2 flex items-center"><CheckCircle className="w-4 h-4 mr-1" /> Matched keywords ({score.matchedKeywords.length})</p>
                        <div className="flex flex-wrap gap-2">
                          {score.matchedKeywords.map((k, i) => (
                            <span key={i} className="inline-flex items-center bg-emerald-100 text-emerald-800 px-2.5 py-1 rounded-md text-xs font-medium">{k}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {score.missingKeywords?.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-red-700 mb-2 flex items-center"><XCircle className="w-4 h-4 mr-1" /> Missing keywords ({score.missingKeywords.length})</p>
                        <div className="flex flex-wrap gap-2">
                          {score.missingKeywords.map((k, i) => (
                            <span key={i} className="inline-flex items-center bg-red-100 text-red-800 px-2.5 py-1 rounded-md text-xs font-medium">{k}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Primary CTA at peak intent — right inside the score panel. */}
                    <button
                      onClick={handleCheckout}
                      disabled={isLoading}
                      className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-base py-3.5 rounded-xl transition-all duration-200 active:scale-[0.98] hover:shadow-md flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50 focus-visible:ring-offset-2"
                    >
                      <span>
                        {isLoading
                          ? "Connecting to Stripe..."
                          : score.missingKeywords?.length > 0
                            ? `Fix these ${score.missingKeywords.length} gaps — $9.99`
                            : "Optimize my resume — $9.99"}
                      </span>
                      {!isLoading && <ArrowRight className="w-5 h-5" />}
                    </button>
                    {/* Share-first: prominent after a score. */}
                    <button
                      onClick={shareScore}
                      className="w-full bg-white hover:bg-slate-50 hover:border-emerald-300 border border-slate-300 text-slate-900 text-sm font-semibold py-3 rounded-xl transition-all duration-200 active:scale-[0.98] flex items-center justify-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/40"
                    >
                      <Share2 className="w-4 h-4 text-emerald-600" />
                      <span>Share my score</span>
                    </button>
                  </div>
                )}

                {/* PAID unlock (shown before a score is run) */}
                {!score && (
                  <button
                    onClick={handleCheckout}
                    disabled={isLoading}
                    className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-lg py-4 rounded-xl transition-all duration-200 active:scale-[0.98] hover:shadow-md flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50 focus-visible:ring-offset-2"
                  >
                    <span>{isLoading ? "Connecting to Stripe..." : "Pay $9.99 to Optimize"}</span>
                    {!isLoading && <ArrowRight className="w-5 h-5" />}
                  </button>
                )}

                <p className="text-xs text-center text-slate-400">Secured by Stripe. Results delivered instantly.</p>

              </div>
            </div>

            {/* Honest trust row — truthful signals only, no ratings/testimonials. */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <div className="flex flex-col items-center text-center gap-1.5 bg-slate-50 border border-slate-200 rounded-xl px-2 py-3 transition-all duration-200 hover:-translate-y-0.5 hover:border-emerald-300 hover:bg-white hover:shadow-sm">
                <BadgeCheck className="w-5 h-5 text-emerald-600" />
                <span className="text-[11px] leading-tight text-slate-600 font-medium">No subscription</span>
              </div>
              <div className="flex flex-col items-center text-center gap-1.5 bg-slate-50 border border-slate-200 rounded-xl px-2 py-3 transition-all duration-200 hover:-translate-y-0.5 hover:border-emerald-300 hover:bg-white hover:shadow-sm">
                <Lock className="w-5 h-5 text-emerald-600" />
                <span className="text-[11px] leading-tight text-slate-600 font-medium">Your resume is never stored</span>
              </div>
              <div className="flex flex-col items-center text-center gap-1.5 bg-slate-50 border border-slate-200 rounded-xl px-2 py-3 transition-all duration-200 hover:-translate-y-0.5 hover:border-emerald-300 hover:bg-white hover:shadow-sm">
                <Shield className="w-5 h-5 text-emerald-600" />
                <span className="text-[11px] leading-tight text-slate-600 font-medium">Honest rewrite — no fabricated experience</span>
              </div>
              <div className="flex flex-col items-center text-center gap-1.5 bg-slate-50 border border-slate-200 rounded-xl px-2 py-3 transition-all duration-200 hover:-translate-y-0.5 hover:border-emerald-300 hover:bg-white hover:shadow-sm">
                <Zap className="w-5 h-5 text-emerald-600" />
                <span className="text-[11px] leading-tight text-slate-600 font-medium">Instant</span>
              </div>
            </div>
          </div>

        </div>

        {/* How it works */}
        <section id="how-it-works" className="pt-28 scroll-mt-24">
          <h2 className="text-3xl lg:text-4xl font-black text-center tracking-tight text-slate-900">How it works</h2>
          <p className="text-slate-600 text-center mt-3 mb-12">Three steps. About 60 seconds.</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-emerald-300 hover:shadow-md">
              <div className="flex items-center gap-3 mb-3"><span className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-700 font-bold flex items-center justify-center">1</span><UploadCloud className="w-5 h-5 text-emerald-600" /></div>
              <h3 className="font-bold text-lg mb-1 text-slate-900">Upload &amp; paste</h3>
              <p className="text-sm text-slate-600">Drop in your resume (PDF) and paste the job description you&apos;re targeting.</p>
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-emerald-300 hover:shadow-md">
              <div className="flex items-center gap-3 mb-3"><span className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-700 font-bold flex items-center justify-center">2</span><Gauge className="w-5 h-5 text-emerald-600" /></div>
              <h3 className="font-bold text-lg mb-1 text-slate-900">Get your free score</h3>
              <p className="text-sm text-slate-600">See your 0&ndash;100 keyword match and the exact terms your resume is missing &mdash; free.</p>
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-emerald-300 hover:shadow-md">
              <div className="flex items-center gap-3 mb-3"><span className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-700 font-bold flex items-center justify-center">3</span><Zap className="w-5 h-5 text-emerald-600" /></div>
              <h3 className="font-bold text-lg mb-1 text-slate-900">Optimize for $9.99</h3>
              <p className="text-sm text-slate-600">We rewrite it to match the job &mdash; honestly &mdash; and hand back a clean PDF and .docx.</p>
            </div>
          </div>
        </section>

        {/* Pricing */}
        <section id="pricing" className="pt-28 scroll-mt-24 max-w-md mx-auto w-full">
          <h2 className="text-3xl lg:text-4xl font-black text-center tracking-tight text-slate-900">Simple pricing</h2>
          <p className="text-slate-600 text-center mt-3 mb-10">No subscription. Pay only when you want the rewrite.</p>
          <div className="bg-white border border-slate-200 rounded-3xl p-8 relative overflow-hidden shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-emerald-300 hover:shadow-lg">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-600 to-emerald-400"></div>
            <div className="flex items-baseline gap-2 mb-6"><span className="text-5xl font-black text-slate-900">$9.99</span><span className="text-slate-500">/ one resume</span></div>
            <ul className="space-y-3 mb-8">
              {[
                "Free ATS match score + missing keywords",
                "Honest rewrite — no fabricated experience",
                "Polished PDF and ATS-friendly .docx",
                "No subscription, no account required",
              ].map((t) => (
                <li key={t} className="flex items-start gap-3 text-sm text-slate-700"><CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" /><span>{t}</span></li>
              ))}
            </ul>
            <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-4 rounded-xl transition-all duration-200 active:scale-[0.98] hover:shadow-md flex items-center justify-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50 focus-visible:ring-offset-2">
              <span>Check my score — free</span><ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6 py-10 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3 text-center sm:text-left">
            <div>
              <img src="/logo-full.png" alt="ATSHacker" className="h-7 w-auto mb-1.5" />
              <p className="text-xs text-slate-500">Honest resume keyword matching — no subscription.</p>
            </div>
          </div>
          <div className="flex items-center gap-6 text-sm font-medium text-slate-600">
            <a href="#how-it-works" className="hover:text-emerald-600 transition-colors">How it Works</a>
            <a href="#pricing" className="hover:text-emerald-600 transition-colors">Pricing</a>
          </div>
        </div>
      </footer>

    </div>
  );
}
