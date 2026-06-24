export const seoData = [
  {
    slug: "software-engineer",
    title: "Software Engineer",
    painPointDescription: "Applicant Tracking Systems at FAANG and Fortune 500 companies use aggressive filtering for specific framework versions. If your resume format breaks their parser, your technical skills get entirely stripped out and you are instantly rejected.",
    keywords: ["React.js", "Node.js", "Microservices", "RESTful APIs", "CI/CD Pipeline"]
  },
  {
    slug: "product-manager",
    title: "Product Manager",
    painPointDescription: "Product Manager resumes are uniquely vulnerable to ATS filters because PM skills are highly semantic. If you use the word 'managed' instead of 'cross-functional leadership', the system assumes you don't meet the core competencies.",
    keywords: ["Cross-functional Leadership", "Agile/Scrum", "Product Roadmap", "Go-To-Market Strategy", "Data-Driven Decisions"]
  },
  {
    slug: "data-scientist",
    title: "Data Scientist",
    painPointDescription: "Data Science resumes fail ATS tests because human recruiters don't understand the difference between TensorFlow and PyTorch, so they program the ATS to require exact, rigid string matches. We fix that.",
    keywords: ["Machine Learning", "Python/R", "Data Visualization", "Statistical Modeling", "SQL"]
  },
  {
    slug: "registered-nurse",
    title: "Registered Nurse",
    painPointDescription: "Healthcare ATS systems like Taleo are notoriously rigid. If your certifications (ACLS, BLS) and unit specialties aren't formatted exactly how the hospital's algorithm expects, your application is automatically discarded.",
    keywords: ["Patient Care", "Electronic Health Records (EHR)", "Clinical Triage", "ACLS/BLS Certified", "Medication Administration"]
  },
  {
    slug: "marketing-manager",
    title: "Marketing Manager",
    painPointDescription: "Marketing resumes get rejected when they focus too much on design instead of parsing-friendly text. The ATS strips out your formatting and looks purely for ROI metrics and exact tool competencies.",
    keywords: ["Campaign Strategy", "SEO/SEM", "Customer Acquisition Cost (CAC)", "Content Marketing", "Data Analytics"]
  }
];

export function getJobData(slug: string) {
  const job = seoData.find(j => j.slug === slug);
  if (!job) {
    return {
      slug,
      title: slug.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '),
      painPointDescription: "Applicant Tracking Systems are ruthless. If your resume doesn't semantically match the job description, you get auto-rejected.",
      keywords: ["Leadership", "Communication", "Project Management", "Problem Solving", "Collaboration"]
    };
  }
  return job;
}
