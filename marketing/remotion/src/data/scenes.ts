export interface Scene {
  id: string;
  start: number;
  end: number;
  caption: string;
  voiceover: string;
  visual: string;
  emphasis?: string[];
  warnings?: string[];
  signalExpression?: string;
  keywords?: string[];
  warning?: string;
  before?: string;
  after?: string;
  scoreBefore?: number;
  scoreAfter?: number;
  resumeState?: string;
  checklist?: string[];
  score?: number;
  signalLogoPhaseOut?: boolean;
  brand?: string;
  tagline?: string;
}

export const scenes: Scene[] = [
  {
    id: "cold-open",
    start: 0,
    end: 90,
    caption: "Your resume might be hard to find.",
    voiceover: "Your resume is not rejected by a robot. But it can be hard to find in a recruiter search.",
    visual: "Resume floats toward ATS gate with red scanning beams.",
    emphasis: ["hard to find"],
  },
  {
    id: "ats-ranking",
    start: 90,
    end: 210,
    caption: "Low match scores sink visibility.",
    voiceover: "Recruiters search by keyword before they ever open a resume.",
    visual: "ATS warnings appear: missing keywords, weak impact, poor formatting.",
    warnings: ["Missing keywords", "Weak impact", "Poor formatting", "No clear match"],
  },
  {
    id: "tool-reveal",
    start: 210,
    end: 330,
    caption: "Meet Signal.",
    voiceover: "That is where Signal by ATSHacker comes in.",
    visual: "Atomic light particles form the assistant mascot.",
    signalExpression: "friendly",
  },
  {
    id: "job-scan",
    start: 330,
    end: 510,
    caption: "Scanning job requirements...",
    voiceover: "Signal reads the job description and finds the role language your resume should honestly reflect.",
    visual: "Job description keywords stream into a structured requirements list.",
    keywords: [
      "SQL",
      "Leadership",
      "Customer Growth",
      "Product Strategy",
      "Automation",
      "Stakeholder Management",
    ],
  },
  {
    id: "gap-detection",
    start: 510,
    end: 750,
    caption: "Skill gaps found.",
    voiceover: "It finds what your resume is missing: skills, keywords, structure, and proof.",
    visual: "Weak resume bullet highlighted with HUD warning.",
    warning: "Too vague. No measurable impact.",
  },
  {
    id: "bullet-transform",
    start: 750,
    end: 1020,
    caption: "No fake experience. Clearer proof.",
    voiceover: "Not by inventing experience. By translating what you actually did into language companies understand.",
    visual: "A vague bullet transforms into a specific, evidence-backed bullet.",
    before: "Helped improve team workflow.",
    after: "Improved team workflow by automating weekly reporting, reducing manual tracking time by 35%.",
    scoreBefore: 42,
    scoreAfter: 76,
  },
  {
    id: "resume-merge",
    start: 1020,
    end: 1290,
    caption: "Rebuilding the resume...",
    voiceover: "Then the improvements fold back into your resume.",
    visual: "The assistant breaks into particles and streams into a half-formed resume.",
    resumeState: "half-formed",
  },
  {
    id: "ats-pass",
    start: 1290,
    end: 1560,
    caption: "ATS Match: 94%",
    voiceover: "Formatting becomes clean. Keywords become aligned. Achievements become obvious.",
    visual: "Checklist items light up while the ATS gate opens.",
    checklist: ["Formatting", "Keywords", "Experience", "Relevance", "Impact"],
    score: 94,
  },
  {
    id: "human-review",
    start: 1560,
    end: 1860,
    caption: "Ready for human review.",
    voiceover: "And when a hiring manager opens it...",
    visual: "Resume appears on hiring manager monitor, half normal and half particle-formed.",
    signalLogoPhaseOut: true,
  },
  {
    id: "payoff",
    start: 1860,
    end: 2040,
    caption: "Not louder. Clearer.",
    voiceover: "What is left is you, clearly matched to the job.",
    visual: "Finished resume glows subtly as hiring manager leans in.",
  },
  {
    id: "cta",
    start: 2040,
    end: 2220,
    caption: "Signal by ATSHacker. Check your score.",
    voiceover: "Check your free score and see what the job description is asking for.",
    visual: "ATSHacker brand lockup with electric pulse.",
    brand: "SIGNAL",
    tagline: "by ATSHacker",
  },
];
