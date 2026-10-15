export const sampleCandidateProfile = {
  fullName: "Priya Sharma",
  email: "priya.sharma@example.com",
  targetRole: "Product Operations & Strategy Lead",
  previousRole: "Senior Business Analyst (FinTech)",
  totalExperience: "5.5 years",
  breakDuration: "3.5 years (Maternity & Eldercare)",
  preferredWorkMode: "Hybrid / Remote",
  preferredLocation: "Bengaluru / Pune / Remote (India)",
  resumeFileName: "Priya_Sharma_Resume_2026.pdf",
  resumeFileSize: "248 KB",
  uploadedAt: "Just now",
};

export const sampleAnalysisData = {
  isDemo: true,
  candidate: sampleCandidateProfile,
  overallReadiness: 74, // purely descriptive progress indicator
  readinessLabel: "Strong Foundation — Fast Track Ready",
  readinessSummary: "Your solid analytical background, stakeholder communication, and domain knowledge form a resilient baseline. Bridging contemporary product lifecycle tools and agile discovery practices will make your relaunch seamless.",
  
  skillBreakdown: {
    existing: [
      { name: "Cross-Functional Leadership", category: "Transferable", strength: "High" },
      { name: "SQL & Data Modeling", category: "Technical", strength: "High" },
      { name: "Stakeholder Management", category: "Professional", strength: "High" },
      { name: "Business Process Mapping", category: "Technical", strength: "Proficient" },
      { name: "Financial Analysis & KPI Reporting", category: "Technical", strength: "High" },
      { name: "Agile / Scrum Foundations", category: "Methodology", strength: "Moderate" },
    ],
    toStrengthen: [
      { 
        name: "Modern Product Analytics (Mixpanel / Amplitude)", 
        category: "Technical", 
        importance: "Critical for target role",
        gapDescription: "Familiarity with event tracking pipelines and funnel retention cohorts."
      },
      { 
        name: "AI-Assisted Workflow Tools (Jira Product Discovery, Linear)", 
        category: "Product Tech", 
        importance: "High",
        gapDescription: "Contemporary PRD authoring and backlog triage frameworks."
      },
      { 
        name: "Product-Led Growth (PLG) Metrics", 
        category: "Strategy", 
        importance: "Medium",
        gapDescription: "Understanding customer acquisition cost (CAC) vs. natural viral loops."
      },
      { 
        name: "Interview Case Practice for Returnees", 
        category: "Relaunch Readiness", 
        importance: "High",
        gapDescription: "Articulating the career break with confidence and impact stories."
      }
    ],
    strengthsHighlights: [
      {
        title: "Resilient Analytical Acumen",
        desc: "Over 5 years of proven experience digesting complex operational metrics and driving executive consensus."
      },
      {
        title: "High Emotional Intelligence & Empathy",
        desc: "Caregiving builds unmatched negotiation, crisis management, and prioritization instincts that translate directly to team leadership."
      },
      {
        title: "Fast-Learner Trajectory",
        desc: "Previous record of mastering domain architectures within brief onboarding sprints."
      }
    ]
  },

  recommendedNextSteps: [
    {
      action: "Review Your 4-Week Custom Roadmap",
      link: "/roadmap",
      detail: "Focused weekly sprint modules covering modern analytics, mock cases, and portfolio building."
    },
    {
      action: "Explore 5 Curated Returnships",
      link: "/returnships",
      detail: "Organizations with active cohort programs, flexible onboarding, and dedicated mentorship for returning women."
    },
    {
      action: "Tune Your Resume Narrative",
      link: "/roadmap",
      detail: "Reframe gap months using our modern returnee project showcase templates."
    }
  ]
};
