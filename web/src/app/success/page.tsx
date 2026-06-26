"use client";
import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { CheckCircle, Loader2, Download, FileText } from 'lucide-react';
import { Document, Page, Text, View, StyleSheet, pdf, Font } from '@react-pdf/renderer';
import * as docx from 'docx';

// Register standard fonts
Font.register({
  family: 'Helvetica',
  fonts: [
    { src: 'https://cdn.jsdelivr.net/npm/open-sans-all@0.1.3/fonts/open-sans-regular.ttf' },
    { src: 'https://cdn.jsdelivr.net/npm/open-sans-all@0.1.3/fonts/open-sans-700.ttf', fontWeight: 'bold' }
  ]
});

const styles = StyleSheet.create({
  page: { padding: 40, fontFamily: 'Helvetica', fontSize: 11, color: '#333' },
  header: { marginBottom: 20, borderBottom: '1px solid #ddd', paddingBottom: 10 },
  name: { fontSize: 24, fontWeight: 'bold', marginBottom: 5, color: '#111' },
  contactInfo: { fontSize: 10, color: '#666', flexDirection: 'row', gap: 10 },
  sectionTitle: { fontSize: 14, fontWeight: 'bold', marginTop: 15, marginBottom: 8, color: '#111', textTransform: 'uppercase' },
  summary: { lineHeight: 1.5, marginBottom: 10 },
  skills: { flexDirection: 'row', flexWrap: 'wrap', gap: 5, marginBottom: 10 },
  skillBadge: { backgroundColor: '#f0f0f0', padding: '4 8', borderRadius: 4, fontSize: 9 },
  job: { marginBottom: 12 },
  jobHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 },
  company: { fontWeight: 'bold', fontSize: 12 },
  dates: { fontSize: 10, color: '#666' },
  title: { fontStyle: 'italic', marginBottom: 4 },
  bullet: { flexDirection: 'row', marginBottom: 3, paddingLeft: 10 },
  bulletPoint: { width: 10, fontSize: 10 },
  bulletText: { flex: 1, lineHeight: 1.4 },
  school: { marginBottom: 5 },
  schoolName: { fontWeight: 'bold' }
});

const ResumePDF = ({ data }: { data: any }) => (
  <Document>
    <Page size="A4" style={styles.page}>
      <View style={styles.header}>
        <Text style={styles.name}>{data.name}</Text>
        <View style={styles.contactInfo}>
          {data.email && <Text>{data.email}</Text>}
          {data.phone && <Text>{data.phone}</Text>}
          {data.location && <Text>{data.location}</Text>}
          {data.linkedin && <Text>{data.linkedin}</Text>}
        </View>
      </View>

      <Text style={styles.sectionTitle}>Professional Summary</Text>
      <Text style={styles.summary}>{data.summary}</Text>

      <Text style={styles.sectionTitle}>Core Competencies</Text>
      <View style={styles.skills}>
        {data.skills?.map((s: string, i: number) => (
          <Text key={i} style={styles.skillBadge}>{s}</Text>
        ))}
      </View>

      <Text style={styles.sectionTitle}>Professional Experience</Text>
      {data.experience?.map((exp: any, i: number) => (
        <View key={i} style={styles.job}>
          <View style={styles.jobHeader}>
            <Text style={styles.company}>{exp.company}</Text>
            <Text style={styles.dates}>{exp.dates}</Text>
          </View>
          <Text style={styles.title}>{exp.title}</Text>
          {exp.bullets?.map((b: string, j: number) => (
            <View key={j} style={styles.bullet}>
              <Text style={styles.bulletPoint}>•</Text>
              <Text style={styles.bulletText}>{b}</Text>
            </View>
          ))}
        </View>
      ))}

      {data.education && data.education.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>Education</Text>
          {data.education.map((edu: any, i: number) => (
            <View key={i} style={styles.school}>
              <View style={styles.jobHeader}>
                <Text style={styles.schoolName}>{edu.school}</Text>
                <Text style={styles.dates}>{edu.year}</Text>
              </View>
              <Text style={styles.title}>{edu.degree}</Text>
            </View>
          ))}
        </>
      )}

      {data.certifications && data.certifications.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>Certifications</Text>
          {data.certifications.map((c: string, i: number) => (
            <View key={i} style={styles.bullet}>
              <Text style={styles.bulletPoint}>•</Text>
              <Text style={styles.bulletText}>{c}</Text>
            </View>
          ))}
        </>
      )}
    </Page>
  </Document>
);

const CoverLetterPDF = ({ data }: { data: any }) => {
  const cl = data.coverLetter || {};
  const paragraphs = cl.bodyParagraphs || [];

  return (
    <Document>
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.name}>{data.name}</Text>
          <View style={styles.contactInfo}>
            {data.email && <Text>{data.email}</Text>}
            {data.phone && <Text>{data.phone}</Text>}
            {data.location && <Text>{data.location}</Text>}
            {data.linkedin && <Text>{data.linkedin}</Text>}
          </View>
        </View>

        <View style={{ marginTop: 15, marginBottom: 15 }}>
          <Text style={{ fontSize: 10, color: '#666', marginBottom: 15 }}>
            {cl.date || new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </Text>
          <Text style={{ fontWeight: 'bold', fontSize: 11, marginBottom: 2 }}>{cl.recipientName || 'Hiring Manager'}</Text>
          <Text style={{ fontSize: 11, color: '#333' }}>{cl.companyName || 'The Company'}</Text>
        </View>

        <Text style={{ fontSize: 11, marginBottom: 12, fontWeight: 'bold' }}>{cl.salutation || 'Dear Hiring Manager,'}</Text>

        {paragraphs.map((para: string, idx: number) => (
          <Text key={idx} style={{ fontSize: 11, lineHeight: 1.6, marginBottom: 12 }}>{para}</Text>
        ))}

        <Text style={{ fontSize: 11, marginTop: 15, lineHeight: 1.6 }}>{cl.signOff || `Sincerely,\n\n${data.name}`}</Text>
      </Page>
    </Document>
  );
};

// Build an ATS-friendly .docx (single column, plain text) from the resume JSON.
async function buildDocxBlob(data: any): Promise<Blob> {
  const { Document: Doc, Packer, Paragraph, TextRun, HeadingLevel } = docx;
  const children: docx.Paragraph[] = [];

  children.push(new Paragraph({ text: data.name || 'Resume', heading: HeadingLevel.TITLE }));
  const contact = [data.email, data.phone, data.location, data.linkedin].filter(Boolean).join('  |  ');
  if (contact) children.push(new Paragraph({ children: [new TextRun({ text: contact, color: '666666' })] }));

  if (data.summary) {
    children.push(new Paragraph({ text: 'Professional Summary', heading: HeadingLevel.HEADING_2 }));
    children.push(new Paragraph({ text: data.summary }));
  }

  if (data.skills?.length) {
    children.push(new Paragraph({ text: 'Core Competencies', heading: HeadingLevel.HEADING_2 }));
    children.push(new Paragraph({ text: data.skills.join(' • ') }));
  }

  if (data.experience?.length) {
    children.push(new Paragraph({ text: 'Professional Experience', heading: HeadingLevel.HEADING_2 }));
    for (const exp of data.experience) {
      children.push(new Paragraph({
        children: [
          new TextRun({ text: exp.company || '', bold: true }),
          new TextRun({ text: exp.dates ? `   ${exp.dates}` : '', color: '666666' }),
        ],
      }));
      if (exp.title) children.push(new Paragraph({ children: [new TextRun({ text: exp.title, italics: true })] }));
      for (const b of exp.bullets || []) {
        children.push(new Paragraph({ text: b, bullet: { level: 0 } }));
      }
    }
  }

  if (data.education?.length) {
    children.push(new Paragraph({ text: 'Education', heading: HeadingLevel.HEADING_2 }));
    for (const edu of data.education) {
      children.push(new Paragraph({
        children: [
          new TextRun({ text: edu.school || '', bold: true }),
          new TextRun({ text: edu.year ? `   ${edu.year}` : '', color: '666666' }),
        ],
      }));
      if (edu.degree) children.push(new Paragraph({ children: [new TextRun({ text: edu.degree, italics: true })] }));
    }
  }

  if (data.certifications?.length) {
    children.push(new Paragraph({ text: 'Certifications', heading: HeadingLevel.HEADING_2 }));
    for (const c of data.certifications) {
      children.push(new Paragraph({ text: c, bullet: { level: 0 } }));
    }
  }

  const document = new Doc({ sections: [{ children }] });
  return Packer.toBlob(document);
}

// Build an ATS-friendly .docx for the cover letter
async function buildCoverLetterDocxBlob(data: any): Promise<Blob> {
  const { Document: Doc, Packer, Paragraph, TextRun, HeadingLevel } = docx;
  const children: docx.Paragraph[] = [];
  const cl = data.coverLetter || {};

  children.push(new Paragraph({ text: data.name || 'Cover Letter', heading: HeadingLevel.TITLE }));
  const contact = [data.email, data.phone, data.location, data.linkedin].filter(Boolean).join('  |  ');
  if (contact) children.push(new Paragraph({ children: [new TextRun({ text: contact, color: '666666' })] }));

  children.push(new Paragraph({ text: '' }));
  const dateStr = cl.date || new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  children.push(new Paragraph({ text: dateStr }));
  children.push(new Paragraph({ text: cl.recipientName || 'Hiring Manager', children: [new TextRun({ text: cl.recipientName || 'Hiring Manager', bold: true })] }));
  children.push(new Paragraph({ text: cl.companyName || 'The Company' }));
  children.push(new Paragraph({ text: '' }));

  children.push(new Paragraph({ text: cl.salutation || 'Dear Hiring Manager,', children: [new TextRun({ text: cl.salutation || 'Dear Hiring Manager,', bold: true })] }));
  children.push(new Paragraph({ text: '' }));

  for (const para of cl.bodyParagraphs || []) {
    children.push(new Paragraph({ text: para }));
    children.push(new Paragraph({ text: '' }));
  }

  children.push(new Paragraph({ text: cl.signOff || `Sincerely,\n\n${data.name}` }));

  const document = new Doc({ sections: [{ children }] });
  return Packer.toBlob(document);
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function SuccessPageContent() {
  const [status, setStatus] = useState("Initializing Optimizer...");
  const [isDone, setIsDone] = useState(false);
  const [resumeData, setResumeData] = useState<any>(null);
  const [baseName, setBaseName] = useState("optimized_resume");
  const [beforeScore, setBeforeScore] = useState<number | null>(null);
  const [afterScore, setAfterScore] = useState<number | null>(null);
  const [optimizationLow, setOptimizationLow] = useState(false);
  const [copied, setCopied] = useState(false);
  const searchParams = useSearchParams();

  useEffect(() => {
    const processResume = async () => {
      const sessionId = searchParams.get('session_id');
      if (!sessionId) {
        setStatus("Invalid session. Did you pay?");
        return;
      }

      const resumeText = sessionStorage.getItem('resumeText');
      const jobDescription = sessionStorage.getItem('jobDescription');
      const rawName = sessionStorage.getItem('fileName') || 'optimized_resume.pdf';
      const base = rawName.replace(/\.pdf$/i, '') + '_ats_optimized';
      setBaseName(base);

      if (!resumeText || !jobDescription) {
        setStatus("Error: We couldn't find your uploaded resume in the browser storage.");
        return;
      }

      setStatus("Sending to OpenAI for Semantic Optimization...");

      try {
        const res = await fetch('/api/rewrite', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ resumeText, jobDescription, sessionId })
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.error || "Failed to process");
        }

        setStatus("Building optimized files...");
        const json = await res.json();
        setResumeData(json);
        if (json._warning === 'optimization_low') setOptimizationLow(true);

        // Auto-download files based on purchase type
        if (json.coverLetter && !json.experience) {
          // Cover Letter only
          const clBlob = await pdf(<CoverLetterPDF data={json} />).toBlob();
          downloadBlob(clBlob, `${base}_cover_letter.pdf`);
        } else if (json.coverLetter && json.experience) {
          // Bundle
          const resumeBlob = await pdf(<ResumePDF data={json} />).toBlob();
          downloadBlob(resumeBlob, `${base}_resume.pdf`);
          const clBlob = await pdf(<CoverLetterPDF data={json} />).toBlob();
          downloadBlob(clBlob, `${base}_cover_letter.pdf`);
        } else {
          // Resume only
          const resumeBlob = await pdf(<ResumePDF data={json} />).toBlob();
          downloadBlob(resumeBlob, `${base}_resume.pdf`);
        }

        setStatus("Optimization completed! Download files below.");
        setIsDone(true);

        // Score check if resume was rewritten
        if (json.experience) {
          const optimizedText = [
            json.summary,
            (json.skills || []).join(' '),
            (json.experience || []).map((e: any) => `${e.title} ${e.company} ${(e.bullets || []).join(' ')}`).join(' '),
            (json.certifications || []).join(' '),
            (json.education || []).map((e: any) => `${e.school} ${e.degree}`).join(' '),
          ].filter(Boolean).join(' ');

          const scoreOf = (text: string) =>
            fetch('/api/score', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ resumeText: text, jobDescription }),
            })
              .then((r) => (r.ok ? r.json() : null))
              .catch(() => null);

          Promise.all([scoreOf(resumeText), scoreOf(optimizedText)]).then(([b, a]) => {
            if (b && typeof b.score === 'number') setBeforeScore(b.score);
            if (a && typeof a.score === 'number') setAfterScore(a.score);
          });
        }

        // Cleanup storage
        sessionStorage.removeItem('resumeText');
        sessionStorage.removeItem('jobDescription');

      } catch (err: any) {
        setStatus(`Error: ${err.message}`);
      }
    };

    processResume();
  }, [searchParams]);

  const handleDownloadPdf = async () => {
    if (!resumeData) return;
    const blob = await pdf(<ResumePDF data={resumeData} />).toBlob();
    downloadBlob(blob, `${baseName}_resume.pdf`);
  };

  const handleDownloadDocx = async () => {
    if (!resumeData) return;
    const blob = await buildDocxBlob(resumeData);
    downloadBlob(blob, `${baseName}_resume.docx`);
  };

  const handleDownloadCoverLetterPdf = async () => {
    if (!resumeData || !resumeData.coverLetter) return;
    const blob = await pdf(<CoverLetterPDF data={resumeData} />).toBlob();
    downloadBlob(blob, `${baseName}_cover_letter.pdf`);
  };

  const handleDownloadCoverLetterDocx = async () => {
    if (!resumeData || !resumeData.coverLetter) return;
    const blob = await buildCoverLetterDocxBlob(resumeData);
    downloadBlob(blob, `${baseName}_cover_letter.docx`);
  };

  const handleCopyCoverLetter = () => {
    if (!resumeData?.coverLetter) return;
    const cl = resumeData.coverLetter;
    const text = [
      cl.date || new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }),
      '',
      cl.recipientName || 'Hiring Manager',
      cl.companyName || 'The Company',
      '',
      cl.salutation || 'Dear Hiring Manager,',
      '',
      ...(cl.bodyParagraphs || []),
      '',
      cl.signOff || `Sincerely,\n\n${resumeData.name}`
    ].join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-900 p-6">
      <div className={`bg-white border border-slate-200 rounded-3xl p-8 md:p-12 shadow-md w-full transition-all duration-300 ${resumeData?.coverLetter ? 'max-w-2xl' : 'max-w-md'} text-center space-y-6`}>

        <a href="/" className="flex items-center justify-center gap-2.5">
          <img src="/logo-mark.png" alt="ATSHacker" width="32" height="32" className="rounded-full" />
          <span className="text-xl font-black tracking-tighter text-slate-900">
            ATS<span className="text-emerald-600">Hacker.</span>
          </span>
        </a>

        {!isDone ? (
          <Loader2 className="w-16 h-16 text-emerald-600 animate-spin mx-auto" />
        ) : (
          <CheckCircle className="ath-score-pop w-16 h-16 text-emerald-600 mx-auto" />
        )}

        <h1 className="text-3xl font-bold text-slate-900">Successful Optimization!</h1>
        <p className="text-slate-600 font-medium">{status}</p>

        {isDone && (
          <div className="ath-reveal pt-4 space-y-6 text-left">
            {beforeScore !== null && afterScore !== null && resumeData?.experience && (
              <div className="bg-emerald-50/50 border border-emerald-100 rounded-2xl p-5 text-center">
                <p className="text-xs font-semibold text-slate-400 mb-3 tracking-wide">ATS MATCH SCORE</p>
                <div className="flex items-center justify-center gap-6">
                  <div className="text-center">
                    <div className="text-3xl font-black text-red-600">{beforeScore}</div>
                    <div className="text-[10px] uppercase tracking-wide text-slate-400 font-bold">Before</div>
                  </div>
                  <span className="text-2xl text-slate-300">&rarr;</span>
                  <div className="text-center">
                    <div className="text-3xl font-black text-emerald-600">{afterScore}</div>
                    <div className="text-[10px] uppercase tracking-wide text-slate-400 font-bold">After</div>
                  </div>
                </div>
                {afterScore > beforeScore && (
                  <p className="text-xs text-emerald-700 font-medium mt-3">+{afterScore - beforeScore} point keyword-match improvement.</p>
                )}
              </div>
            )}

            {optimizationLow && (
              <div className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-left">
                <p className="text-xs text-slate-600">
                  This resume was already fairly well-matched to the job — we still tightened the keywords and phrasing for a cleaner read.
                </p>
              </div>
            )}

            <div className="space-y-4">
              {resumeData?.experience && (
                <div className="border border-slate-200 rounded-2xl p-5 bg-slate-50/50 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div className="flex items-start gap-3">
                    <div className="p-2.5 bg-emerald-50 text-emerald-700 rounded-lg">
                      <FileText className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900">ATS-Optimized Resume</h3>
                      <p className="text-xs text-slate-500 font-medium">Tailored semantic keywords and achievements.</p>
                    </div>
                  </div>
                  <div className="flex gap-2 w-full md:w-auto">
                    <button
                      onClick={handleDownloadPdf}
                      className="flex-1 md:flex-none bg-white hover:bg-slate-50 hover:border-emerald-300 border border-slate-300 text-slate-905 font-bold py-2 px-4 rounded-xl text-sm transition-all duration-200 active:scale-[0.98] flex items-center justify-center space-x-1"
                    >
                      <span>PDF</span>
                    </button>
                    <button
                      onClick={handleDownloadDocx}
                      className="flex-1 md:flex-none bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 px-4 rounded-xl text-sm transition-all duration-200 active:scale-[0.98] flex items-center justify-center space-x-1"
                    >
                      <span>Word</span>
                    </button>
                  </div>
                </div>
              )}

              {resumeData?.coverLetter && (
                <div className="border border-slate-200 rounded-2xl p-5 bg-slate-50/50 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div className="flex items-start gap-3">
                    <div className="p-2.5 bg-emerald-50 text-emerald-700 rounded-lg">
                      <FileText className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900">Tailored Cover Letter</h3>
                      <p className="text-xs text-slate-500 font-medium">Cohesive styling matching your new resume.</p>
                    </div>
                  </div>
                  <div className="flex gap-2 w-full md:w-auto">
                    <button
                      onClick={handleDownloadCoverLetterPdf}
                      className="flex-1 md:flex-none bg-white hover:bg-slate-50 hover:border-emerald-300 border border-slate-300 text-slate-905 font-bold py-2 px-4 rounded-xl text-sm transition-all duration-200 active:scale-[0.98] flex items-center justify-center space-x-1"
                    >
                      <span>PDF</span>
                    </button>
                    <button
                      onClick={handleDownloadCoverLetterDocx}
                      className="flex-1 md:flex-none bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 px-4 rounded-xl text-sm transition-all duration-200 active:scale-[0.98] flex items-center justify-center space-x-1"
                    >
                      <span>Word</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {resumeData?.coverLetter && (
              <div className="border border-slate-200 rounded-2xl p-6 bg-slate-50/30 space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="font-bold text-slate-950">Cover Letter Preview</h3>
                  <button
                    onClick={handleCopyCoverLetter}
                    className="bg-white hover:bg-slate-100 border border-slate-300 text-slate-700 text-xs font-bold py-1.5 px-3 rounded-lg transition-all"
                  >
                    {copied ? 'Copied!' : 'Copy Text'}
                  </button>
                </div>
                <div className="bg-white border border-slate-200 rounded-xl p-5 text-xs text-slate-800 space-y-3 font-mono leading-relaxed max-h-60 overflow-y-auto">
                  <p>{resumeData.coverLetter.date || new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
                  <div>
                    <p className="font-bold">{resumeData.coverLetter.recipientName}</p>
                    <p>{resumeData.coverLetter.companyName}</p>
                  </div>
                  <p className="font-bold">{resumeData.coverLetter.salutation}</p>
                  {(resumeData.coverLetter.bodyParagraphs || []).map((p: string, i: number) => (
                    <p key={i}>{p}</p>
                  ))}
                  <p className="whitespace-pre-line">{resumeData.coverLetter.signOff}</p>
                </div>
              </div>
            )}

            <div className="text-center pt-2">
              <a href="/" className="inline-flex items-center space-x-2 text-emerald-600 hover:text-emerald-500 font-bold transition">
                <span>Tailor another document</span>
              </a>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

import { Suspense } from 'react';
export default function SuccessPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-white flex items-center justify-center"><Loader2 className="w-16 h-16 text-emerald-600 animate-spin" /></div>}>
      <SuccessPageContent />
    </Suspense>
  );
}
