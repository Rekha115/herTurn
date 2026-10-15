export const sampleRoadmapData = {
  isDemo: true,
  targetRole: "Product Operations & Strategy Lead",
  personalizedSummary: "A tailored sprint designed to refresh technical product analytics, instill modern AI-assisted product workflows, and polish interview storytelling tailored for career returnees.",
  
  fourWeekPlan: [
    {
      weekNumber: 1,
      title: "Foundations & The Modern Product Landscape",
      theme: "Unlearning legacy toolchains & adopting current industry mental models",
      commitment: "6–8 hours",
      weeklyGoal: "Re-anchor in product lifecycle paradigms, modern metrics (North Star, CAC, LTV, Retention cohorts), and setting up your project workspace.",
      topics: [
        "Product Management & Ops evolution (2022–2026)",
        "Key Metrics Frameworks: HEART, North Star, AARRR pirate metrics",
        "Introduction to AI copilot workflows in product discovery"
      ],
      resources: [
        {
          title: "Reforge: Modern Product Metrics & Retention Guide",
          type: "Article / Guide",
          url: "https://www.reforge.com/blog/growth-loops",
          isExternal: true
        },
        {
          title: "Lenny's Newsletter: How top PMs run operations & roadmaps",
          type: "Reading",
          url: "https://www.lennysnewsletter.com",
          isExternal: true
        }
      ],
      tasks: [
        { id: "w1-t1", text: "Audit 3 real product launch case studies and identify their North Star metrics", completed: true },
        { id: "w1-t2", text: "Create a modern Linear or Notion product workspace template", completed: true },
        { id: "w1-t3", text: "Synthesize notes on AI tools transforming backlog grooming and user research", completed: false }
      ]
    },
    {
      weekNumber: 2,
      title: "Data-Driven Discovery & Product Analytics",
      theme: "Bridging the gap in event-based instrumentation and funnel diagnostics",
      commitment: "8–10 hours",
      weeklyGoal: "Gain hands-on familiarity with modern analytics dashboards (Mixpanel / Amplitude) and construct interactive user journey hypotheses.",
      topics: [
        "Event tracking taxonomy: Pageviews vs. custom trigger events",
        "Funnel drop-off diagnosis & churn cohort analysis",
        "Writing SQL queries for daily active users (DAU) and stickiness"
      ],
      resources: [
        {
          title: "Mixpanel Academy: Retention & Conversion Analysis Essentials",
          type: "Interactive Course",
          url: "https://mixpanel.com",
          isExternal: true
        },
        {
          title: "Mode Analytics SQL Tutorial for Product Decision Makers",
          type: "Interactive Lab",
          url: "https://mode.com/sql-tutorial/",
          isExternal: true
        }
      ],
      tasks: [
        { id: "w2-t1", text: "Complete a sample sandbox project in Mixpanel analyzing an onboarding drop-off", completed: false },
        { id: "w2-t2", text: "Draft an event instrumentation schema for a mobile subscription app", completed: false },
        { id: "w2-t3", text: "Write 2 SQL cohort segmentation queries using BigQuery / Postgres syntax", completed: false }
      ]
    },
    {
      weekNumber: 3,
      title: "Cross-Functional Execution & Mini-Project Showcase",
      theme: "Translating prior professional acumen into a tangible portfolio asset",
      commitment: "8–10 hours",
      weeklyGoal: "Author a comprehensive 1-page PRD and launch strategy artifact to demonstrate in interviews.",
      topics: [
        "Writing high-impact 1-page PRDs with clear acceptance criteria",
        "Stakeholder alignment and sprint trade-off matrices (RICE & MoSCoW)",
        "Addressing career gap questions through evidence-based case studies"
      ],
      resources: [
        {
          title: "Atlassian Guide to Agile Product Management & PRD Best Practices",
          type: "Framework Guide",
          url: "https://www.atlassian.com/agile/product-management",
          isExternal: true
        },
        {
          title: "Figma Community: Product Specification & User Flow Wireframing",
          type: "Design Asset",
          url: "https://www.figma.com/community",
          isExternal: true
        }
      ],
      tasks: [
        { id: "w3-t1", text: "Draft a comprehensive PRD for a fictional 'Customer Support AI Assistant'", completed: false },
        { id: "w3-t2", text: "Map an end-to-end user journey with clear edge-case resolutions", completed: false },
        { id: "w3-t3", text: "Package the mini-project into a public Notion or GitHub Pages portfolio link", completed: false }
      ]
    },
    {
      weekNumber: 4,
      title: "Career Narrative, Returnee Branding & Interview Mastery",
      theme: "Owned narratives, behavioral rehearsal, and returnship applications",
      commitment: "6–8 hours",
      weeklyGoal: "Finalize your resume narrative, practice returnee behavioral interviews, and submit your initial 3 returnship applications.",
      topics: [
        "Reframing the career break as a leadership and adaptability asset",
        "STAR technique for product leadership and conflict resolution",
        "Targeting returnships: What hiring managers look for in relaunch candidates"
      ],
      resources: [
        {
          title: "Harvard Business Review: The 4 Keys to Relaunching Your Career",
          type: "Insight Article",
          url: "https://hbr.org",
          isExternal: true
        },
        {
          title: "HerTurn Interview Preparation Playbook for Women Returning to Tech",
          type: "HerTurn Resource",
          url: "/returnships",
          isExternal: false
        }
      ],
      tasks: [
        { id: "w4-t1", text: "Update LinkedIn headline, bio, and resume with modern project highlights", completed: false },
        { id: "w4-t2", text: "Record a 2-minute elevator pitch highlighting transferable skills and break resilience", completed: false },
        { id: "w4-t3", text: "Shortlist and apply to 3 verified returnship programs on the HerTurn Marketplace", completed: false }
      ]
    }
  ],

  sixWeekPlan: [
    {
      weekNumber: 1,
      title: "Foundations & The Modern Product Landscape",
      theme: "Unlearning legacy toolchains & adopting current industry mental models",
      commitment: "5–6 hours",
      weeklyGoal: "Re-anchor in product lifecycle paradigms and modern metrics.",
      topics: [
        "Product Management evolution (2022–2026)",
        "Key Metrics Frameworks: HEART, North Star, AARRR",
        "Introduction to AI copilot workflows"
      ],
      resources: [
        {
          title: "Reforge: Modern Product Metrics & Retention Guide",
          type: "Article / Guide",
          url: "https://www.reforge.com/blog/growth-loops",
          isExternal: true
        }
      ],
      tasks: [
        { id: "w1-t1", text: "Audit 3 real product launch case studies and identify their North Star metrics", completed: true },
        { id: "w1-t2", text: "Create a modern Linear or Notion product workspace template", completed: true }
      ]
    },
    {
      weekNumber: 2,
      title: "Product Analytics & Funnel Diagnostics",
      theme: "Event tracking taxonomy and user journey analysis",
      commitment: "6–7 hours",
      weeklyGoal: "Gain hands-on familiarity with Mixpanel and Amplitude analytics sandboxes.",
      topics: [
        "Event tracking taxonomy & funnel drop-off analysis",
        "User retention cohorts vs. churn rates",
        "A/B testing basics and statistical significance"
      ],
      resources: [
        {
          title: "Mixpanel Academy: Retention & Conversion Analysis",
          type: "Course",
          url: "https://mixpanel.com",
          isExternal: true
        }
      ],
      tasks: [
        { id: "w2-t1", text: "Complete Mixpanel retention sandbox walkthrough", completed: false },
        { id: "w2-t2", text: "Map an analytics instrumentation spec for a signup flow", completed: false }
      ]
    },
    {
      weekNumber: 3,
      title: "Agile Rituals & Contemporary Product Tooling",
      theme: "Figma, Linear, Jira Discovery, and Sprint Planning",
      commitment: "6–7 hours",
      weeklyGoal: "Build fluency with the exact software stacks modern teams use everyday.",
      topics: [
        "Scrum vs. Kanban in fast-moving product teams",
        "Collaborative prototyping in Figma for non-designers",
        "Backlog refinement and sprint capacity modeling"
      ],
      resources: [
        {
          title: "Atlassian Agile Coach & Sprint Planning Guide",
          type: "Guide",
          url: "https://www.atlassian.com/agile",
          isExternal: true
        }
      ],
      tasks: [
        { id: "w3-t1", text: "Build a sprint board with user stories and story points", completed: false },
        { id: "w3-t2", text: "Annotate a wireframe user flow in Figma", completed: false }
      ]
    },
    {
      weekNumber: 4,
      title: "Deep Dive: Building a Capstone Case Study",
      theme: "End-to-end product problem solving & artifact drafting",
      commitment: "7–8 hours",
      weeklyGoal: "Complete the first full draft of your returnee portfolio capstone project.",
      topics: [
        "Identifying pain points with customer empathy",
        "Authoring a crisp 1-page PRD with success metrics",
        "Defining go-to-market and phased rollout plan"
      ],
      resources: [
        {
          title: "Product School: The Ultimate PRD Blueprint",
          type: "Template",
          url: "https://productschool.com",
          isExternal: true
        }
      ],
      tasks: [
        { id: "w4-t1", text: "Write PRD sections: Problem, Goals, Non-goals, and Target Persona", completed: false },
        { id: "w4-t2", text: "Complete risk assessment and technical dependencies outline", completed: false }
      ]
    },
    {
      weekNumber: 5,
      title: "Mock Interviews & Returnee Storytelling",
      theme: "Reframing the career break into your greatest superpower",
      commitment: "6–7 hours",
      weeklyGoal: "Rehearse behavioral questions, master the break explanation, and do 2 peer mock interviews.",
      topics: [
        "Owning your break with grace, poise, and zero apology",
        "STAR framework for tricky situational questions",
        "Product sense questions: 'How would you improve X product?'"
      ],
      resources: [
        {
          title: "Harvard Business Review: The Return-to-Work Playbook",
          type: "Reading",
          url: "https://hbr.org",
          isExternal: true
        }
      ],
      tasks: [
        { id: "w5-t1", text: "Write your 90-second career break narrative script", completed: false },
        { id: "w5-t2", text: "Complete a recorded mock product case interview", completed: false }
      ]
    },
    {
      weekNumber: 6,
      title: "Targeted Outreach & Returnship Cohort Applications",
      theme: "Active pipeline building and executive sponsor outreach",
      commitment: "6–8 hours",
      weeklyGoal: "Submit tailored applications to 5 returnship programs and connect with 5 women returnee alumni.",
      topics: [
        "Cold outreach to returnship program managers on LinkedIn",
        "Customizing cover notes emphasizing maturity and perspective",
        "Negotiation and flexibility parameters for returnee contracts"
      ],
      resources: [
        {
          title: "Path Forward: Advice for Relaunching Professionals",
          type: "Guide",
          url: "https://www.pathforward.org",
          isExternal: true
        }
      ],
      tasks: [
        { id: "w6-t1", text: "Apply to at least 4 returnship cohorts on HerTurn Marketplace", completed: false },
        { id: "w6-t2", text: "Reach out to 3 women ERG leaders at target companies", completed: false },
        { id: "w6-t3", text: "Celebrate completing your 6-Week Relaunch Sprint!", completed: false }
      ]
    }
  ]
};
