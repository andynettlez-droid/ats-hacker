"use client";
import React, { useState, useRef } from 'react';
import { UploadCloud, CheckCircle, Shield, ArrowRight, FileText } from 'lucide-react';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleCheckout = async () => {
    if (!file) {
      alert("Please upload your resume first!");
      return;
    }
    if (!jobDescription.trim()) {
      alert("Please paste the job description!");
      return;
    }

    setIsLoading(true);
    try {
      // 1. Extract text
      const pdfjsLib = await import('pdfjs-dist');
      pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`;
      
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      let resumeText = '';
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const content = await page.getTextContent();
        resumeText += content.items.map((item: any) => item.str).join(' ') + '\n';
      }

      // 2. Save to sessionStorage
      sessionStorage.setItem('resumeText', resumeText);
      sessionStorage.setItem('jobDescription', jobDescription);
      sessionStorage.setItem('fileName', file.name);

      // 3. Initiate checkout
      const res = await fetch('/api/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          fileName: file.name,
          jobDescription: jobDescription
        }),
      });
      
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        alert("Checkout failed to initiate.");
        setIsLoading(false);
      }
    } catch (err) {
      console.error(err);
      alert("An error occurred during checkout.");
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 font-sans selection:bg-emerald-500/30">
      
      {/* Navigation */}
      <nav className="w-full p-6 flex justify-between items-center max-w-7xl mx-auto">
        <div className="text-2xl font-black tracking-tighter text-white">
          ATS<span className="text-emerald-500">Hacker.</span>
        </div>
        <div className="flex items-center space-x-6 text-sm font-medium text-neutral-400">
          <a href="#how-it-works" className="hover:text-white transition">How it Works</a>
          <a href="#pricing" className="hover:text-white transition">Pricing</a>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-6 pt-20 pb-32">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          
          <div className="space-y-8">
            <div className="inline-flex items-center space-x-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Bypass Workday & Greenhouse Filters</span>
            </div>
            
            <h1 className="text-5xl lg:text-7xl font-black leading-[1.1] tracking-tight">
              Stop getting auto-rejected by <span className="text-emerald-500">robots.</span>
            </h1>
            
            <p className="text-xl text-neutral-400 leading-relaxed max-w-lg">
              90% of resumes are thrown out by Applicant Tracking Systems before a human ever sees them. We rewrite your resume to perfectly match the job description semantics for <span className="text-white font-bold">$5.00</span>.
            </p>

            <div className="space-y-4">
              <div className="flex items-center space-x-3 text-neutral-300">
                <CheckCircle className="w-5 h-5 text-emerald-500" />
                <span>Instantly generated PDF output</span>
              </div>
              <div className="flex items-center space-x-3 text-neutral-300">
                <CheckCircle className="w-5 h-5 text-emerald-500" />
                <span>Perfect semantic keyword matching</span>
              </div>
              <div className="flex items-center space-x-3 text-neutral-300">
                <Shield className="w-5 h-5 text-emerald-500" />
                <span>Zero data retention (100% private)</span>
              </div>
            </div>
          </div>

          {/* The Vending Machine UI */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-3xl p-8 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-600 to-emerald-400"></div>
            
            <h2 className="text-2xl font-bold mb-6">Hack Your Resume</h2>
            
            <div className="space-y-6">
              
              <div className="space-y-2">
                <label className="text-sm font-semibold text-neutral-300">1. Upload Current Resume (PDF)</label>
                
                <input 
                  type="file" 
                  accept=".pdf" 
                  ref={fileInputRef} 
                  className="hidden" 
                  onChange={handleFileChange}
                />

                <div 
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-xl p-8 text-center transition cursor-pointer group
                    ${isDragging ? 'border-emerald-500 bg-emerald-500/10' : 'border-neutral-700 hover:border-emerald-500/50 hover:bg-neutral-800/50'}
                  `}
                >
                  {file ? (
                    <div className="flex flex-col items-center">
                      <FileText className="w-10 h-10 text-emerald-500 mb-3" />
                      <p className="text-sm text-white font-medium">{file.name}</p>
                      <p className="text-xs text-emerald-500 mt-1">Click to replace file</p>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center">
                      <UploadCloud className="w-10 h-10 text-neutral-500 group-hover:text-emerald-500 transition mb-3" />
                      <p className="text-sm text-neutral-400">Drag and drop or <span className="text-emerald-500">browse files</span></p>
                    </div>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-neutral-300">2. Paste Target Job Description</label>
                <textarea 
                  rows={4}
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the raw text of the job description here..."
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-xl p-4 text-sm text-neutral-300 focus:outline-none focus:border-emerald-500 transition resize-none"
                ></textarea>
              </div>

              <button 
                onClick={handleCheckout}
                disabled={isLoading}
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-lg py-4 rounded-xl transition flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>{isLoading ? "Connecting to Stripe..." : "Pay $5.00 to Optimize"}</span>
                {!isLoading && <ArrowRight className="w-5 h-5" />}
              </button>
              
              <p className="text-xs text-center text-neutral-500">
                Secured by Stripe. Results delivered instantly.
              </p>

            </div>
          </div>

        </div>
      </main>

    </div>
  );
}
