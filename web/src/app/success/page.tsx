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
    </Page>
  </Document>
);

// Build an ATS-friendly .docx (single column, plain text) from the resume JSON.
// Many ATS parse .docx more reliably than PDF, so we offer both.
async function buildDocxBlob(data: any): Promise<Blob> {
  const { Document: Doc, Packer, Paragraph, TextRun, HeadingLevel } = docx;
  const children: docx.Paragraph[] = [];

  children.push(new Paragraph({ text: data.name || 'Resume', heading: HeadingLevel.TITLE }));
  const contact = [data.email, data.phone].filter(Boolean).join('  |  ');
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

        setStatus("Building your optimized resume...");
        const json = await res.json();
        setResumeData(json);

        // Auto-download the PDF for instant gratification.
        const blob = await pdf(<ResumePDF data={json} />).toBlob();
        downloadBlob(blob, `${base}.pdf`);

        setStatus("Resume optimized! Download as PDF or .docx below.");
        setIsDone(true);

        // Cleanup storage so we don't hold sensitive data.
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
    downloadBlob(blob, `${baseName}.pdf`);
  };

  const handleDownloadDocx = async () => {
    if (!resumeData) return;
    const blob = await buildDocxBlob(resumeData);
    downloadBlob(blob, `${baseName}.docx`);
  };

  return (
    <div className="min-h-screen bg-neutral-950 flex items-center justify-center text-white p-6">
      <div className="bg-neutral-900 border border-neutral-800 rounded-3xl p-12 shadow-2xl max-w-md w-full text-center space-y-6">

        {!isDone ? (
          <Loader2 className="w-16 h-16 text-emerald-500 animate-spin mx-auto" />
        ) : (
          <CheckCircle className="w-16 h-16 text-emerald-500 mx-auto" />
        )}

        <h1 className="text-3xl font-bold">Payment Success!</h1>
        <p className="text-neutral-400 font-medium">{status}</p>

        {isDone && (
          <div className="pt-4 space-y-4">
            <p className="text-sm text-neutral-500">
              Your PDF downloaded automatically. ATS often parse .docx more reliably — grab that version too if you&apos;re applying through Workday or Greenhouse.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={handleDownloadPdf}
                className="flex-1 bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 text-white font-bold py-3 rounded-xl transition flex items-center justify-center space-x-2"
              >
                <Download className="w-5 h-5" />
                <span>Download PDF</span>
              </button>
              <button
                onClick={handleDownloadDocx}
                className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-xl transition flex items-center justify-center space-x-2"
              >
                <FileText className="w-5 h-5" />
                <span>Download .docx</span>
              </button>
            </div>
            <a href="/" className="inline-flex items-center space-x-2 text-emerald-500 hover:text-emerald-400 font-bold transition pt-2">
              <span>Optimize another resume</span>
            </a>
          </div>
        )}

      </div>
    </div>
  );
}

import { Suspense } from 'react';
export default function SuccessPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-neutral-950 flex items-center justify-center"><Loader2 className="w-16 h-16 text-emerald-500 animate-spin" /></div>}>
      <SuccessPageContent />
    </Suspense>
  );
}
