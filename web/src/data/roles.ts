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
    painPoint: "Technical recruiters often search for specific languages, frameworks, and versions. If those terms are unclear or hidden in a complex format, your strongest skills can be harder to find in search results.",
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
    painPoint: "Analyst resumes are easier to find when they name the exact BI tools, SQL dialects, and business outcomes in the posting. Generic 'reporting' language can undersell relevant experience.",
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
    painPoint: "Data science recruiters often search for exact libraries, modeling methods, and deployment terms. If the posting names TensorFlow, PyTorch, NLP, or MLOps, your resume should make relevant matches obvious.",
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
    painPoint: "Project manager resumes can sound too generic when they say 'ran projects' instead of the role's specific delivery, stakeholder, risk, and cross-functional leadership language.",
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
    painPoint: "Healthcare recruiters often search by license, certification, unit specialty, and EHR. If ACLS, BLS, specialty units, or charting systems are missing or unclear, your fit can be harder to spot.",
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
    painPoint: "Accounting resumes are stronger when they name precise responsibilities like GAAP, reconciliation, month-end close, audit support, and the accounting systems used.",
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
    painPoint: "Marketing resumes can underperform when design takes over and the text does not clearly show channels, tools, metrics, pipeline impact, and campaign outcomes.",
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
    painPoint: "Sales resumes are stronger when they lead with numbers, quota attainment, pipeline ownership, and the CRM named in the posting instead of describing activities broadly.",
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
    painPoint: "Engineering recruiters search for specific CAD tools, standards, and technical acronyms. If SolidWorks, GD&T, FEA, or DFM experience is vague, your strongest technical fit can be missed.",
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
    painPoint: "CSM resumes are easier to find when they use the SaaS language recruiters search for: churn, NRR, QBRs, renewals, onboarding, health scores, and expansion revenue.",
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
    painPoint: "Product manager resumes lose clarity when they say 'managed features' instead of showing roadmap ownership, prioritization, user research, cross-functional leadership, and measurable product outcomes.",
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
    painPoint: "Designer resumes need readable text as well as a portfolio. Recruiters still search for tools, deliverable types, design systems, branding, layout, and UI/UX terms in the resume itself.",
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
    painPoint: "HR resumes are stronger when certifications, compliance terms, HRIS platforms, and employee-relations scope are spelled out clearly instead of hidden behind broad HR language.",
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
    painPoint: "Finance resumes can look generic when they say 'analyzed data' instead of naming financial modeling, FP&A, variance analysis, forecasting, valuation, and budget ownership.",
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
    painPoint: "Business analyst resumes are easier to find when deliverables are named clearly: requirements gathering, BRDs, user stories, process maps, gap analysis, and stakeholder workshops.",
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
    painPoint: "Operations resumes need the methodology and metrics the posting names. Generic 'managed operations' is weaker than Lean/Six Sigma, process optimization, throughput, cost, and team-scope proof.",
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
    painPoint: "Administrative resumes are stronger when they name the exact tools, support scope, scheduling work, travel coordination, expense systems, and executive or office responsibilities.",
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
    painPoint: "Nurse practitioner resumes should make credentials, population focus, prescriptive authority, EHR systems, and clinical settings easy to find for healthcare recruiters.",
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
    painPoint: "Developer resumes are easier to find when the named stack is explicit. If the role asks for TypeScript, React, PostgreSQL, or AWS, those relevant terms should be clear in your skills and bullets.",
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
    painPoint: "DevOps resumes need exact tooling and cloud language. Kubernetes, Terraform, CI/CD, monitoring, and cloud providers should be visible when they match the target role.",
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
    painPoint: "UX resumes need both portfolio links and searchable text. Make tools, research methods, usability testing, wireframing, accessibility, and design-system work clear in the resume.",
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
    painPoint: "Data engineer resumes are stronger when pipeline tools, warehouses, orchestration, cloud platforms, and scale are named directly instead of hidden behind generic 'big data' language.",
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
    painPoint: "Customer service resumes are easier to match when they name channels, ticketing tools, CRM platforms, CSAT, SLAs, de-escalation, and support volume instead of broad service duties.",
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
    painPoint: "Executive assistant resumes should make seniority, calendar ownership, travel coordination, board materials, confidentiality, and the exact tools used easy to find.",
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
    painPoint: "Sales manager resumes need leadership impact in measurable terms. Quota attainment, pipeline, CRM, forecasting, coaching, team size, and revenue growth should be clear.",
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
    painPoint: "Recruiter resumes are stronger when sourcing tools, ATS platforms, full-cycle recruiting, time-to-fill, pipeline metrics, and stakeholder management are named directly.",
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
    painPoint: "Teacher resumes should make certifications, grade levels, subject areas, classroom management, differentiated instruction, IEP work, and measurable student outcomes easy to find.",
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
    painPoint: "Network engineer resumes are easier to find when certifications, routing protocols, firewall platforms, vendors, network scale, and uptime impact are named clearly.",
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
    painPoint: "Product designer resumes need portfolio proof plus searchable text. Tools, interaction design, user journeys, design systems, and product outcomes should be clear in the resume.",
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
    painPoint: "Frontend resumes are stronger when the exact framework, rendering model, styling system, testing stack, accessibility work, and performance impact are easy to scan.",
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
    painPoint: "Backend resumes are easier to match when databases, runtimes, messaging systems, API architecture, caching, and infrastructure choices are named directly.",
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
    painPoint: "Fullstack resumes need a clear stack story across frontend, backend, database, APIs, deployment, and system ownership so recruiters can quickly understand the fit.",
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
    painPoint: "Cybersecurity resumes are stronger when tools, frameworks, environments, incident response work, SIEM/SOC experience, and compliance language are named clearly.",
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
    painPoint: "IT support resumes are easier to match when troubleshooting scope, administration tools, ticketing systems, ITIL practices, SaaS platforms, and support metrics are clear.",
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
