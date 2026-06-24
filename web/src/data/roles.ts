// Role dataset powering the programmatic /tailor/[job-title] SEO pages.
// Each role has a unique keyword list, pain-point paragraph, and tips so pages
// are NOT thin/duplicate content.

export interface Role {
  slug: string;
  title: string;
  painPoint: string;
  keywords: string[];
  tips: string[];
}

export const roles: Role[] = [
  {
    slug: 'software-engineer',
    title: 'Software Engineer',
    painPoint: "Applicant Tracking Systems at FAANG and Fortune 500 companies filter aggressively for specific framework versions. If your resume format breaks their parser, your technical skills get stripped out entirely and you're instantly rejected.",
    keywords: ['CI/CD', 'REST APIs', 'microservices', 'unit testing', 'Agile/Scrum', 'code review', 'system design', 'cloud (AWS/GCP/Azure)', 'Git', 'distributed systems'],
    tips: [
      'Lead each bullet with a language or framework the JD names (e.g. "Built React + Node services…").',
      'Quantify impact: latency reduced, throughput, users served, uptime.',
      'Mirror the JD’s exact stack terms — "TypeScript" not just "JavaScript" if they ask for it.',
    ],
  },
  {
    slug: 'data-analyst',
    title: 'Data Analyst',
    painPoint: "Analyst resumes get filtered when they list generic 'reporting' instead of the exact BI tools and SQL dialects the posting names. The ATS scores you on rigid keyword matches, not on the spirit of your experience.",
    keywords: ['SQL', 'data visualization', 'Tableau', 'Power BI', 'Excel', 'A/B testing', 'ETL', 'Python/pandas', 'dashboards', 'KPIs'],
    tips: [
      'Name the BI tools in the JD explicitly — ATS matches "Power BI", not "BI tools".',
      'Show business impact, not just queries: "drove 12% lift via cohort analysis".',
      'Include both "SQL" and the specific dialect if mentioned (e.g. BigQuery, Snowflake).',
    ],
  },
  {
    slug: 'data-scientist',
    title: 'Data Scientist',
    painPoint: "Data Science resumes fail ATS tests because recruiters program rigid, exact string matches — the system won't treat TensorFlow and PyTorch as interchangeable, so missing the exact term means instant rejection.",
    keywords: ['machine learning', 'Python/R', 'data visualization', 'statistical modeling', 'SQL', 'deep learning', 'feature engineering', 'A/B testing', 'NLP', 'model deployment'],
    tips: [
      'Match the exact library named (TensorFlow vs PyTorch vs scikit-learn).',
      'Quantify model impact: accuracy lift, revenue, cost saved, latency.',
      'Include both "machine learning" and the specific techniques in the JD.',
    ],
  },
  {
    slug: 'project-manager',
    title: 'Project Manager',
    painPoint: "PM resumes are vulnerable because the role is defined by soft, semantic skills. If you write 'ran projects' instead of the JD's 'stakeholder management' and 'cross-functional leadership', the ATS assumes you lack the core competencies.",
    keywords: ['stakeholder management', 'Agile', 'Scrum', 'risk management', 'budget management', 'PMP', 'Jira', 'roadmap', 'cross-functional', 'deliverables'],
    tips: [
      'If the JD lists PMP/CSM/PRINCE2, put the exact acronym near the top.',
      'Quantify scope: budget size, team size, on-time delivery rate.',
      'Use the methodology word they use — "Agile", "Waterfall", or "hybrid".',
    ],
  },
  {
    slug: 'registered-nurse',
    title: 'Registered Nurse',
    painPoint: "Healthcare ATS systems like Taleo are notoriously rigid. If your certifications (ACLS, BLS) and unit specialties aren't formatted exactly how the hospital's algorithm expects, your application is automatically discarded.",
    keywords: ['patient care', 'BLS/ACLS', 'EHR/EMR', 'medication administration', 'care plans', 'HIPAA', 'triage', 'vital signs', 'patient education', 'charting'],
    tips: [
      'List certifications and licenses exactly (RN, BLS, ACLS, state license).',
      'Match the specialty wording: "med-surg", "ICU", "telemetry", as in the JD.',
      'Name the EHR system you used (Epic, Cerner) if the posting mentions one.',
    ],
  },
  {
    slug: 'accountant',
    title: 'Accountant',
    painPoint: "Accounting resumes get filtered when they say 'handled finances' instead of the precise terms — GAAP, reconciliation, month-end close — that the ATS is told to require. Vague wording reads as 'unqualified' to the algorithm.",
    keywords: ['GAAP', 'accounts payable', 'accounts receivable', 'reconciliation', 'general ledger', 'QuickBooks', 'month-end close', 'financial reporting', 'audit', 'Excel'],
    tips: [
      'Include "GAAP" and any software named (QuickBooks, NetSuite, SAP).',
      'Quantify: number of accounts, close timelines, dollar volumes handled.',
      'Spell out CPA status clearly if you hold or are pursuing it.',
    ],
  },
  {
    slug: 'marketing-manager',
    title: 'Marketing Manager',
    painPoint: "Marketing resumes get rejected when they lean on design instead of parsing-friendly text. The ATS strips your formatting and looks purely for ROI metrics and exact tool competencies — if those words aren't there, neither are you.",
    keywords: ['SEO', 'content marketing', 'campaign management', 'Google Analytics', 'marketing automation', 'lead generation', 'brand strategy', 'social media', 'ROI', 'A/B testing'],
    tips: [
      'Quantify results: leads, CAC, ROAS, conversion rate, pipeline influenced.',
      'Name the platforms in the JD (HubSpot, Marketo, GA4, Meta Ads).',
      'Match channel terms exactly — "paid search" vs "SEM" vs "PPC".',
    ],
  },
  {
    slug: 'sales-representative',
    title: 'Sales Representative',
    painPoint: "Sales resumes get filtered when they describe activities instead of leading with numbers and the CRM named in the posting. Recruiters set the ATS to screen for quota attainment and specific tools first.",
    keywords: ['quota attainment', 'pipeline management', 'CRM/Salesforce', 'prospecting', 'cold calling', 'closing', 'B2B/B2C', 'account management', 'upselling', 'lead qualification'],
    tips: [
      'Lead with numbers: % of quota, revenue closed, deal size, ranking.',
      'Name the CRM (Salesforce, HubSpot) and sales methodology (SPIN, Challenger).',
      'Use the JD’s segment language: SMB, mid-market, enterprise.',
    ],
  },
  {
    slug: 'mechanical-engineer',
    title: 'Mechanical Engineer',
    painPoint: "Engineering resumes get auto-rejected when the CAD tool or acronym is even slightly off — the ATS treats 'SolidWorks' and 'Solid Works' as different, and won't expand GD&T or FEA for you.",
    keywords: ['CAD', 'SolidWorks', 'AutoCAD', 'GD&T', 'FEA', 'prototyping', 'DFM', 'tolerancing', 'product development', 'ASME'],
    tips: [
      'Name the CAD tool exactly as the JD does (SolidWorks vs CATIA vs Creo).',
      'Include "GD&T", "FEA", "DFM" if listed — ATS matches the acronyms.',
      'Quantify: cost reductions, cycle time, tolerances achieved.',
    ],
  },
  {
    slug: 'customer-success-manager',
    title: 'Customer Success Manager',
    painPoint: "CSM resumes get filtered when they say 'helped customers' instead of the retention metrics and SaaS vocabulary — churn, NRR, QBRs — the ATS is configured to find. The algorithm rewards the exact jargon.",
    keywords: ['customer retention', 'churn reduction', 'onboarding', 'upsell/cross-sell', 'NPS', 'account management', 'SaaS', 'renewals', 'CRM', 'QBRs'],
    tips: [
      'Quantify retention: churn %, NRR, renewal rate, expansion revenue.',
      'Match SaaS terms: "ARR", "NRR", "QBR", "health score".',
      'Name the CS platform (Gainsight, Totango) if the JD mentions one.',
    ],
  },
  {
    slug: 'product-manager',
    title: 'Product Manager',
    painPoint: "Product Manager resumes are uniquely vulnerable because PM skills are highly semantic. Write 'managed features' instead of 'cross-functional leadership' and 'product roadmap', and the system assumes you don't meet the core competencies.",
    keywords: ['product roadmap', 'user research', 'A/B testing', 'go-to-market', 'KPIs/OKRs', 'stakeholder management', 'Agile', 'prioritization', 'analytics', 'wireframing'],
    tips: [
      'Show outcomes: adoption, retention, revenue moved — not just "shipped features".',
      'Use the JD’s framework words: "OKRs", "JTBD", "RICE prioritization".',
      'Name analytics tools (Amplitude, Mixpanel) if listed.',
    ],
  },
  {
    slug: 'graphic-designer',
    title: 'Graphic Designer',
    painPoint: "Designers get burned twice: heavy visual layouts confuse the parser, and tool names must match exactly — 'Adobe Creative Cloud' won't match a posting that says 'Creative Suite'. The ATS reads text, not your portfolio.",
    keywords: ['Adobe Creative Suite', 'Photoshop', 'Illustrator', 'InDesign', 'Figma', 'typography', 'branding', 'layout', 'UI/UX', 'visual design'],
    tips: [
      'Match the exact tool name — "Adobe Creative Cloud" vs "Creative Suite" matters to ATS.',
      'List Figma/Sketch if the role is digital/product design.',
      'Link a portfolio and reference deliverable types named in the JD.',
    ],
  },
  {
    slug: 'human-resources-manager',
    title: 'Human Resources Manager',
    painPoint: "HR resumes get filtered when certifications and compliance terms aren't spelled out exactly. The ATS screens for 'SHRM-CP', 'FMLA' and the specific HRIS — paraphrasing those costs you the match.",
    keywords: ['talent acquisition', 'employee relations', 'HRIS', 'onboarding', 'performance management', 'compliance', 'benefits administration', 'FMLA', 'PHR/SHRM', 'compensation'],
    tips: [
      'Spell out certifications exactly (PHR, SPHR, SHRM-CP).',
      'Name the HRIS (Workday, BambooHR, ADP) used or required.',
      'Match compliance terms: FMLA, FLSA, EEO, ADA as in the posting.',
    ],
  },
  {
    slug: 'financial-analyst',
    title: 'Financial Analyst',
    painPoint: "Finance resumes get auto-rejected when they say 'analyzed data' instead of 'financial modeling', 'FP&A' and 'variance analysis'. The ATS is tuned for those exact phrases, and synonyms don't count.",
    keywords: ['financial modeling', 'forecasting', 'variance analysis', 'Excel', 'budgeting', 'valuation', 'P&L', 'FP&A', 'data analysis', 'GAAP'],
    tips: [
      'Include "financial modeling", "FP&A", and "variance analysis" verbatim if listed.',
      'Quantify: budget size, forecast accuracy, cost savings identified.',
      'Name tools: Excel (advanced), SQL, Tableau, SAP, Hyperion.',
    ],
  },
  {
    slug: 'business-analyst',
    title: 'Business Analyst',
    painPoint: "BA resumes get filtered when deliverables are described loosely. The ATS hunts for 'requirements gathering', 'BRD' and 'user stories' — say 'wrote docs' and the algorithm passes you over.",
    keywords: ['requirements gathering', 'process improvement', 'stakeholder management', 'SQL', 'data analysis', 'user stories', 'Agile', 'documentation', 'gap analysis', 'BRD'],
    tips: [
      'Match artifact terms exactly: "BRD", "user stories", "use cases".',
      'Show measurable process improvements (time saved, error reduction).',
      'Name modeling/diagram tools (Visio, Lucidchart) if mentioned.',
    ],
  },
  {
    slug: 'operations-manager',
    title: 'Operations Manager',
    painPoint: "Ops resumes get screened out when they omit the methodology and metrics the posting names. The ATS looks for 'Lean/Six Sigma', 'process optimization' and hard numbers — generic 'managed operations' doesn't register.",
    keywords: ['process optimization', 'supply chain', 'KPIs', 'Lean/Six Sigma', 'inventory management', 'P&L', 'team leadership', 'logistics', 'continuous improvement', 'vendor management'],
    tips: [
      'List Lean/Six Sigma belt level exactly if you hold one.',
      'Quantify: cost reduction %, throughput, headcount managed.',
      'Match the domain: manufacturing, fulfillment, or service ops.',
    ],
  },
  {
    slug: 'administrative-assistant',
    title: 'Administrative Assistant',
    painPoint: "Admin resumes get filtered when software and support terms are vague. The ATS screens for the exact tools — 'Outlook', 'Concur' — and phrases like 'executive support'; 'office work' won't match.",
    keywords: ['calendar management', 'scheduling', 'Microsoft Office', 'travel coordination', 'data entry', 'correspondence', 'expense reports', 'office management', 'customer service', 'documentation'],
    tips: [
      'Name the exact software (Outlook, Google Workspace, Concur).',
      'Use the JD’s phrasing: "executive support", "front desk", "office coordination".',
      'Quantify: calendars managed, travel booked, executives supported.',
    ],
  },
];

export const roleMap: Record<string, Role> = Object.fromEntries(
  roles.map((r) => [r.slug, r])
);
