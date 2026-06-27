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
    painPoint: "Recruiters at FAANG and Fortune 500 companies search for specific framework versions. If your resume format breaks the parser, your technical skills get stripped out and you rank low in their search results.",
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
    painPoint: "Analyst resumes rank lower when they list generic 'reporting' instead of the exact BI tools and SQL dialects the posting names. The ATS scores you on rigid keyword matches, not on the spirit of your experience.",
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
    painPoint: "Data Science resumes rank low because recruiters search with rigid, exact string matches — the system won't treat TensorFlow and PyTorch as interchangeable, so missing the exact term buries you in the results.",
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
    painPoint: "Healthcare ATS systems like Taleo are notoriously rigid. If your certifications (ACLS, BLS) and unit specialties aren't formatted exactly how the hospital's search expects, your application can drop lower in the recruiter's results.",
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
    painPoint: "Accounting resumes rank lower when they say 'handled finances' instead of the precise terms - GAAP, reconciliation, month-end close - that the ATS is told to require. Vague wording can look like a weak match to the search.",
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
    painPoint: "Sales resumes rank lower when they describe activities instead of leading with numbers and the CRM named in the posting. Recruiters often search for quota attainment and specific tools first.",
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
    painPoint: "Engineering resumes get buried when the CAD tool or acronym is even slightly off — the ATS treats 'SolidWorks' and 'Solid Works' as different, and won't expand GD&T or FEA for you, so you drop out of keyword search results.",
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
    painPoint: "CSM resumes rank lower when they say 'helped customers' instead of the retention metrics and SaaS vocabulary - churn, NRR, QBRs - the ATS is configured to find. The search rewards the exact jargon.",
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
    painPoint: "HR resumes rank lower when certifications and compliance terms aren't spelled out exactly. The ATS screens for 'SHRM-CP', 'FMLA' and the specific HRIS - paraphrasing those costs you the match.",
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
    painPoint: "Finance resumes rank low when they say 'analyzed data' instead of 'financial modeling', 'FP&A' and 'variance analysis'. Recruiters search for those exact phrases, and synonyms don't count, so you get buried.",
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
    painPoint: "BA resumes rank lower when deliverables are described loosely. The ATS hunts for 'requirements gathering', 'BRD' and 'user stories' - say 'wrote docs' and the recruiter search can pass you over.",
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
    painPoint: "Admin resumes rank lower when software and support terms are vague. The ATS screens for the exact tools - 'Outlook', 'Concur' - and phrases like 'executive support'; 'office work' won't match.",
    keywords: ['calendar management', 'scheduling', 'Microsoft Office', 'travel coordination', 'data entry', 'correspondence', 'expense reports', 'office management', 'customer service', 'documentation'],
    tips: [
      'Name the exact software (Outlook, Google Workspace, Concur).',
      'Use the JD’s phrasing: "executive support", "front desk", "office coordination".',
      'Quantify: calendars managed, travel booked, executives supported.',
    ],
  },
  {
    slug: 'nurse-practitioner',
    title: 'Nurse Practitioner',
    painPoint: "NP resumes rank low when certifications, populations, and prescriptive authority aren't spelled out the way the posting expects. Recruiters search for exact credentials like 'FNP-C' and specific EHR systems, so paraphrasing leaves you buried in the results.",
    keywords: ['FNP/AGNP', 'patient assessment', 'diagnosis', 'prescriptive authority', 'EHR/Epic', 'care plans', 'chronic disease management', 'BLS/ACLS', 'patient education', 'differential diagnosis', 'primary care', 'DEA license'],
    tips: [
      'List the exact certification and population focus (FNP-C, AGNP, PMHNP).',
      'Spell out prescriptive authority and DEA/state license status clearly.',
      'Name the EHR (Epic, Cerner) and the setting (primary care, urgent care, telehealth).',
    ],
  },
  {
    slug: 'software-developer',
    title: 'Software Developer',
    painPoint: "Developer resumes rank low when the language or framework version is even slightly off — recruiters search for exact strings, so 'JavaScript' won't surface for a posting that requires 'TypeScript'. Miss the named stack and you drop down the results.",
    keywords: ['JavaScript/TypeScript', 'React', 'Node.js', 'REST APIs', 'SQL', 'Git', 'unit testing', 'Agile', 'CI/CD', 'debugging', 'object-oriented design', 'cloud (AWS/Azure)'],
    tips: [
      'Mirror the exact stack named in the JD — "TypeScript", "React", "PostgreSQL".',
      'Quantify impact: load time, defects reduced, features shipped, users served.',
      'Lead each bullet with the language or framework, not the verb.',
    ],
  },
  {
    slug: 'devops-engineer',
    title: 'DevOps Engineer',
    painPoint: "DevOps resumes get buried when the exact tooling isn't named. Recruiters search for 'Kubernetes', 'Terraform' and specific cloud providers verbatim — write 'containers' or 'automation' instead and your resume ranks below the candidates who matched the strings.",
    keywords: ['CI/CD', 'Kubernetes', 'Docker', 'Terraform', 'AWS', 'Ansible', 'infrastructure as code', 'monitoring', 'Linux', 'Jenkins/GitLab CI', 'Prometheus/Grafana', 'scripting (Bash/Python)'],
    tips: [
      'Name the exact orchestration and IaC tools (Kubernetes, Terraform, Ansible).',
      'Match the cloud provider in the JD — AWS, GCP, or Azure, not just "cloud".',
      'Quantify: deployment frequency, MTTR, uptime, infra cost saved.',
    ],
  },
  {
    slug: 'ux-designer',
    title: 'UX Designer',
    painPoint: "UX resumes get buried when the design tools and process terms don't match the posting. Recruiters search for 'Figma', 'usability testing' and 'wireframing' exactly, and a portfolio link can't be searched — if the keywords aren't in your text, your resume ranks low.",
    keywords: ['Figma', 'user research', 'wireframing', 'prototyping', 'usability testing', 'interaction design', 'design systems', 'information architecture', 'accessibility (WCAG)', 'user flows', 'Sketch', 'personas'],
    tips: [
      'Name the exact tools in the JD (Figma vs Sketch vs Adobe XD).',
      'Show outcomes: task success rate, drop-off reduced, conversion lift.',
      'Use the JD’s process words: "discovery", "usability testing", "design system".',
    ],
  },
  {
    slug: 'data-engineer',
    title: 'Data Engineer',
    painPoint: "Data Engineer resumes rank low when the pipeline tools and warehouses aren't named exactly. Recruiters search for 'Spark', 'Airflow' and 'Snowflake' as literal strings — say 'big data' or 'pipelines' and you fall below candidates who matched the terms.",
    keywords: ['ETL/ELT', 'Spark', 'Airflow', 'SQL', 'Python', 'data warehousing', 'Snowflake/BigQuery', 'Kafka', 'dbt', 'data modeling', 'AWS/GCP', 'pipeline orchestration'],
    tips: [
      'Name the exact warehouse and orchestration tools (Snowflake, Airflow, dbt).',
      'Quantify scale: rows processed, pipeline latency, data volume, cost saved.',
      'Match streaming vs batch terms (Kafka, Spark Streaming) as in the JD.',
    ],
  },
  {
    slug: 'customer-service-representative',
    title: 'Customer Service Representative',
    painPoint: "CSR resumes rank low when they describe duties vaguely instead of the channels, tools, and metrics the posting names. Recruiters search for 'CRM', 'ticketing' and specific platforms — generic 'helped customers' ranks below resumes that matched the exact terms.",
    keywords: ['customer service', 'CRM/Zendesk', 'ticketing', 'conflict resolution', 'phone/email/chat support', 'CSAT', 'order processing', 'troubleshooting', 'data entry', 'de-escalation', 'product knowledge', 'SLA'],
    tips: [
      'Name the support platform (Zendesk, Salesforce, Freshdesk) used or required.',
      'Quantify: tickets/day, CSAT, first-contact resolution, average handle time.',
      'Match the channels in the JD: phone, email, live chat, social.',
    ],
  },
  {
    slug: 'executive-assistant',
    title: 'Executive Assistant',
    painPoint: "EA resumes rank low when the seniority and tools aren't spelled out the way the posting expects. Recruiters search for 'C-suite', 'calendar management' and exact software names — vague 'admin support' ranks below resumes that matched the terms.",
    keywords: ['calendar management', 'executive support', 'travel coordination', 'expense reports', 'Microsoft Office', 'Concur', 'meeting coordination', 'confidentiality', 'board materials', 'stakeholder communication', 'project coordination', 'gatekeeping'],
    tips: [
      'State the seniority you supported (C-suite, VP, founder) explicitly.',
      'Name the exact tools (Outlook, Google Workspace, Concur, Slack).',
      'Quantify: executives supported, calendars managed, travel volume.',
    ],
  },
  {
    slug: 'sales-manager',
    title: 'Sales Manager',
    painPoint: "Sales Manager resumes rank low when leadership impact is described loosely. Recruiters search for 'quota attainment', 'pipeline' and the named CRM first — 'led a team' without the metrics and tools ranks below candidates who matched the exact terms.",
    keywords: ['quota attainment', 'team leadership', 'pipeline management', 'CRM/Salesforce', 'forecasting', 'coaching', 'territory management', 'revenue growth', 'B2B sales', 'sales strategy', 'KPIs', 'account management'],
    tips: [
      'Lead with numbers: team quota %, revenue growth, rep ramp time, retention.',
      'Name the CRM and methodology (Salesforce, MEDDIC, Challenger).',
      'Show leadership scope: team size, territories, segment (SMB/enterprise).',
    ],
  },
  {
    slug: 'recruiter',
    title: 'Recruiter',
    painPoint: "Recruiter resumes rank low when the sourcing tools and metrics aren't named. ATS systems search for 'ATS', 'LinkedIn Recruiter' and 'full-cycle recruiting' verbatim — describe it vaguely and your own resume gets buried the way candidates' do.",
    keywords: ['full-cycle recruiting', 'sourcing', 'LinkedIn Recruiter', 'ATS', 'candidate screening', 'interview coordination', 'Boolean search', 'employer branding', 'offer negotiation', 'pipeline management', 'time-to-fill', 'stakeholder management'],
    tips: [
      'Name the ATS (Greenhouse, Lever, Workday) and sourcing tools you used.',
      'Quantify: roles filled, time-to-fill, offer-accept rate, pipeline built.',
      'Match the focus: technical, executive, high-volume, or agency recruiting.',
    ],
  },
  {
    slug: 'teacher',
    title: 'Teacher',
    painPoint: "Teacher resumes rank low when certifications, grade levels, and methods aren't spelled out exactly. School ATS systems search for the state license, 'classroom management' and 'differentiated instruction' — paraphrasing those ranks you below matched applicants.",
    keywords: ['classroom management', 'lesson planning', 'curriculum development', 'differentiated instruction', 'state certification', 'student assessment', 'IEP', 'classroom technology', 'parent communication', 'Common Core', 'special education', 'data-driven instruction'],
    tips: [
      'Spell out your certification and grade/subject exactly (e.g. "K-6 certified").',
      'Match method terms: "differentiated instruction", "PBIS", "IEP", "SEL".',
      'Quantify outcomes: test score gains, attendance, students taught.',
    ],
  },
  {
    slug: 'network-engineer',
    title: 'Network Engineer',
    painPoint: "Network Engineer resumes rank lower when they list certifications loosely. The ATS screens for exact acronyms like 'CCNA', 'CCNP', or 'JNCIA' and specific hardware vendor terms like 'Cisco Catalysts' or 'Juniper Junos' - if you miss the exact string, you drop down in recruiter searches.",
    keywords: ['routing & switching', 'firewalls (ASA/Palo Alto)', 'Cisco iOS', 'VPN', 'LAN/WAN', 'subnetting', 'network security', 'BGP/OSPF', 'Wireshark', 'troubleshooting'],
    tips: [
      'List certifications (CCNA, CCNP, CompTIA Network+) prominently near the top.',
      'Specify exact hardware vendor names (Cisco Catalyst, Palo Alto, Fortinet) matching the job post.',
      'Detail scale: number of nodes, users, sites, or uptime achieved (e.g. "99.99% uptime").',
    ],
  },
  {
    slug: 'product-designer',
    title: 'Product Designer',
    painPoint: "Product Designer resumes get buried when they rely on PDF portfolios alone instead of readable text. The ATS searches for 'Figma', 'interaction design', and 'user journey maps' as literal text strings — if these terms aren't in your resume copy, the algorithm ranks you lower.",
    keywords: ['Figma', 'interaction design', 'prototyping', 'user research', 'design systems', 'wireframing', 'UI/UX', 'user journey mapping', 'mobile/web design', 'information architecture'],
    tips: [
      'Name exact design tools and developer handoff workflows (Figma, Zeplin, InVision).',
      'Show commercial metrics: conversion rate increases, signup lifts, or usability task time reduced.',
      'Use the exact wording from the JD for design phases (e.g., "rapid prototyping", "user flows").',
    ],
  },
  {
    slug: 'frontend-developer',
    title: 'Frontend Developer',
    painPoint: "Frontend developer resumes rank lower when version-specific tools are missing. Recruiter search queries look for precise matches like 'React 18', 'Next.js', or 'Tailwind CSS'. If your resume lists general frontend skills without these exact keywords, you rank low in the ATS search result page.",
    keywords: ['React.js', 'TypeScript', 'HTML5/CSS3', 'Next.js', 'Tailwind CSS', 'state management (Redux/Zustand)', 'Webpack/Vite', 'unit testing (Jest/RTL)', 'responsive design', 'REST APIs'],
    tips: [
      'List the exact modern rendering frameworks you have used (Next.js, Remix, Astro) to match specific JD requirements.',
      'Show business-facing UI metrics: page performance lift (LCP/FID), conversion rate changes, or accessibility audit compliance.',
      'Specify CSS frameworks explicitly: Tailwind CSS, styled-components, or Sass, as keyword matches are strict.',
    ],
  },
  {
    slug: 'backend-developer',
    title: 'Backend Developer',
    painPoint: "Backend developer resumes get buried when they describe system tasks loosely instead of listing the exact database engines, messaging systems, and runtime versions. If you list 'databases' instead of 'PostgreSQL' or 'Redis', you will fail the strict matching logic of the recruiter's search.",
    keywords: ['Node.js/Go/Java', 'RESTful APIs', 'SQL/NoSQL (PostgreSQL/MongoDB)', 'microservices', 'Docker', 'message queues (RabbitMQ/Kafka)', 'system architecture', 'ORM (Prisma/Hibernate)', 'CI/CD pipelines', 'caching (Redis)'],
    tips: [
      'List your backend runtimes and languages prominently (e.g. Node.js v20, Go, Java Spring Boot).',
      'Quantify API efficiency and scale: throughput, server response time reduction, database query optimizations, or traffic scaling.',
      'Name your primary message brokers and database systems explicitly; generic terms do not rank.',
    ],
  },
  {
    slug: 'fullstack-developer',
    title: 'Fullstack Developer',
    painPoint: "Fullstack developer resumes rank lower when they split their stack skills vaguely. The ATS looks for both frontend and backend tooling in the same profile (e.g. 'React' + 'Node.js' + 'SQL'). If your stack details are spread out or use synonym naming conventions, the system may mark you as an incomplete match.",
    keywords: ['React/Next.js', 'Node.js/Express', 'TypeScript', 'RESTful APIs', 'SQL/PostgreSQL', 'Git/GitHub', 'Docker', 'AWS/GCP', 'HTML5/Tailwind CSS', 'system architecture'],
    tips: [
      'Write a concise stack profile summary at the top naming the exact stack you specialize in (e.g. MERN, Next.js/Postgres).',
      'Detail both user interface accomplishments and system/database optimizations in your bullet points.',
      'Explicitly name hosting and cloud platforms (Vercel, AWS, Heroku) matching the job description.',
    ],
  },
  {
    slug: 'cybersecurity-analyst',
    title: 'Cybersecurity Analyst',
    painPoint: "Cybersecurity resumes rank low when specific compliance frameworks and security tools are missing from the text. Recruiters search with strict strings like 'SIEM', 'SOC', 'NIST', or 'Splunk'. Synonyms or generic 'system monitoring' phrasing will not match, leaving your application buried.",
    keywords: ['SIEM/Splunk', 'incident response', 'vulnerability management', 'network security', 'NIST framework', 'SOC operations', 'firewalls', 'identity & access management (IAM)', 'penetration testing', 'CISSP/CEH'],
    tips: [
      'List certifications (Security+, CISSP, CEH) clearly at the top of your resume.',
      'Name the exact security monitoring and analysis software you are certified in or have used (Splunk, Wireshark, CrowdStrike).',
      'Match the regulatory and standard frameworks listed in the JD (NIST, ISO 27001, SOC 2, HIPAA).',
    ],
  },
  {
    slug: 'it-support-specialist',
    title: 'IT Support Specialist',
    painPoint: "IT Support resumes rank lower when troubleshooting channels and administration suites are described loosely. Recruiter search screens often require terms like 'Active Directory', 'ITIL', or 'SaaS administration'. If your resume lists general 'desktop support', you fall behind matched applicants.",
    keywords: ['Active Directory', 'SaaS administration (Google Workspace/Office 365)', 'troubleshooting', 'helpdesk ticketing (Jira/Zendesk)', 'hardware diagnostics', 'network configuration', 'ITIL guidelines', 'customer service', 'operating systems (Windows/macOS)', 'asset management'],
    tips: [
      'Name the exact administration consoles you managed (Office 365 Admin, Google Workspace Admin console).',
      'Quantify helpdesk volume and resolution metrics: average first-contact resolution time, CSAT ratings, or weekly ticket throughput.',
      'Use standard framework names like ITIL explicitly if the job description mentions them.',
    ],
  },
];

export const roleMap: Record<string, Role> = Object.fromEntries(
  roles.map((r) => [r.slug, r])
);
