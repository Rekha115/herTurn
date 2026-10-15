"""
HerTurn Returnship Opportunity Catalog.
Contains verified enterprise return-to-work fellowships and sample partner demonstrations.
Authentic URLs are preserved; sample listings are transparently badged.
"""

from typing import List, Optional, Dict, Any
from app.models import ReturnshipItem

RAW_RETURNSHIP_CATALOG: List[Dict[str, Any]] = [
    # -------------------------------------------------------------------------
    # Design & UX Opportunities (Verified & Sample)
    # -------------------------------------------------------------------------
    {
        "id": "ret-8",
        "company": "IBM",
        "logoInitial": "IBM",
        "logoBg": "bg-blue-100 text-blue-900 border-blue-200",
        "roleTitle": "Product Experience & UI/UX Designer — Re-Entry Program",
        "roleCategory": "Design & UX",
        "industry": "Technology & Enterprise Cloud",
        "location": "Bengaluru / Kochi (Hybrid)",
        "workArrangement": "Hybrid",
        "type": "verified",
        "verificationStatus": "Verified IBM Re-Entry Track",
        "duration": "6 Months (Convertible to Full-Time)",
        "stipend": "Competitive Full Fellowship + Health Benefits",
        "minBreakRequired": "1+ year career pause",
        "minExperience": "3+ years design experience",
        "experienceLevel": "Mid-Senior (3-6 yrs)",
        "verificationDate": "Verified Cohort 2026",
        "skills": ["UI/UX Design", "Figma", "User Research", "Wireframing", "Design Systems"],
        "description": "IBM Re-Entry Program is designed for talented women designers returning after a career break. Offers full integration with the IBM Carbon Design team, executive mentorship, and direct transition to full-time design leadership.",
        "sourceUrl": "https://www.ibm.com/employment/re-entry/",
        "isLive": True,
        "badgeColor": "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    {
        "id": "ret-9",
        "company": "Microsoft",
        "logoInitial": "MS",
        "logoBg": "bg-indigo-100 text-indigo-900 border-indigo-200",
        "roleTitle": "UX Designer & Design Technologist (Leap Returnship)",
        "roleCategory": "Design & UX",
        "industry": "Technology",
        "location": "Hyderabad / Bengaluru (Hybrid)",
        "workArrangement": "Hybrid",
        "type": "verified",
        "verificationStatus": "Verified Leap Cohort 2026",
        "duration": "16 Weeks",
        "stipend": "Premier Industry Stipend + Equipment",
        "minBreakRequired": "6+ months break",
        "minExperience": "2+ years relevant experience",
        "experienceLevel": "Associate to Mid (2-5 yrs)",
        "verificationDate": "Verified Cohort 2026",
        "skills": ["Figma", "Design Systems", "Prototyping", "User Testing", "Accessibility (a11y)"],
        "description": "Microsoft Leap provides an immersive classroom and hands-on product apprenticeship for returning talent into modern UX engineering and design ecosystems across Azure and Microsoft 365 teams.",
        "sourceUrl": "https://www.microsoft.com/en-us/leap/",
        "isLive": True,
        "badgeColor": "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    {
        "id": "ret-10",
        "company": "PayPal",
        "logoInitial": "PP",
        "logoBg": "bg-sky-100 text-sky-900 border-sky-200",
        "roleTitle": "Lead Product Designer — PayPal Recharge Program",
        "roleCategory": "Design & UX",
        "industry": "Fintech & Payments",
        "location": "Chennai / Bengaluru (Hybrid)",
        "workArrangement": "Hybrid",
        "type": "verified",
        "verificationStatus": "Verified Recharge Program",
        "duration": "16 Weeks",
        "stipend": "Executive Returnee Compensation",
        "minBreakRequired": "1.5+ years break",
        "minExperience": "4+ years design experience",
        "experienceLevel": "Senior / Lead (4-8 yrs)",
        "verificationDate": "Verified Cohort 2026",
        "skills": ["Product Design", "User Journeys", "Figma", "Interaction Design", "Usability Testing"],
        "description": "PayPal Recharge empowers experienced women technologists and product designers to reignite their careers. Includes leadership bootcamps, real-world payments design projects, and dedicated executive sponsor coaching.",
        "sourceUrl": "https://www.paypal.com/us/webapps/mpp/jobs/recharge",
        "isLive": True,
        "badgeColor": "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    # -------------------------------------------------------------------------
    # Software & Full Stack Engineering Opportunities (Verified)
    # -------------------------------------------------------------------------
    {
        "id": "ret-11",
        "company": "Morgan Stanley",
        "logoInitial": "MS",
        "logoBg": "bg-slate-100 text-slate-900 border-slate-300",
        "roleTitle": "Frontend & Web Applications Engineer (Return to Work)",
        "roleCategory": "Software Engineering",
        "industry": "Financial Technology",
        "location": "Bengaluru / Mumbai (Hybrid)",
        "workArrangement": "Hybrid",
        "type": "verified",
        "verificationStatus": "Verified Return to Work Track",
        "duration": "12 Weeks (Convertible to Full-Time)",
        "stipend": "Full Institutional Pro-rated Compensation",
        "minBreakRequired": "2+ years career break",
        "minExperience": "3+ years software development",
        "experienceLevel": "Mid-Senior (3-7 yrs)",
        "verificationDate": "Verified Cohort 2026",
        "skills": ["React", "JavaScript", "HTML/CSS", "Web Performance", "Git Workflow"],
        "description": "Morgan Stanley's Return to Work is an established pathway back to institutional technology. Candidates build high-scale wealth management web applications alongside dedicated technical mentors.",
        "sourceUrl": "https://www.morganstanley.com/people/experienced-professionals/return-to-work-program",
        "isLive": True,
        "badgeColor": "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    {
        "id": "ret-12",
        "company": "JPMorgan Chase & Co.",
        "logoInitial": "JPM",
        "logoBg": "bg-amber-100 text-amber-950 border-amber-300",
        "roleTitle": "Full Stack Software Engineer (ReEntry Program)",
        "roleCategory": "Software Engineering",
        "industry": "Financial Services",
        "location": "Bengaluru / Hyderabad (Hybrid)",
        "workArrangement": "Hybrid",
        "type": "verified",
        "verificationStatus": "Verified Global ReEntry",
        "duration": "14 Weeks",
        "stipend": "Executive Pro-rated Fellowship",
        "minBreakRequired": "2+ years career hiatus",
        "minExperience": "4+ years software engineering",
        "experienceLevel": "Mid-Senior (4-8 yrs)",
        "verificationDate": "Verified Cohort 2026",
        "skills": ["React", "Python", "REST APIs", "SQL", "Cloud Fundamentals"],
        "description": "JPMorgan Chase ReEntry offers experienced software engineers a structured runway back to technology leadership with individualized coaching and live systems development.",
        "sourceUrl": "https://careers.jpmorgan.com/global/en/home/programs/re-entry-program",
        "isLive": True,
        "badgeColor": "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    # -------------------------------------------------------------------------
    # Operations, Cloud & Strategy Opportunities (Verified)
    # -------------------------------------------------------------------------
    {
        "id": "ret-1",
        "company": "Amazon Web Services (AWS)",
        "logoInitial": "A",
        "logoBg": "bg-amber-100 text-amber-900 border-amber-200",
        "roleTitle": "Cloud Operations & Technical Program Manager — Returnship",
        "roleCategory": "Operations & Strategy",
        "industry": "Cloud & Infrastructure",
        "location": "Bengaluru, India (Hybrid)",
        "workArrangement": "Hybrid",
        "type": "verified",
        "verificationStatus": "Verified Cohort 2026",
        "duration": "16 Weeks (Convertible to Full-Time)",
        "stipend": "Competitive Industry Fellowship + Healthcare",
        "minBreakRequired": "2+ years career hiatus",
        "minExperience": "4+ years prior professional experience",
        "experienceLevel": "Mid-Senior (4-7 yrs)",
        "verificationDate": "Verified Cohort 2026",
        "skills": ["Technical Program Management", "Cloud Fundamentals", "Agile", "Cross-Functional Ops"],
        "description": "AWS Return to Work is an established 16-week paid fellowship dedicated to professionals who stepped away from the workforce for caregiving, family, or health reasons. Includes dedicated mentorship, technical refresher cohorts, and an established conversion track.",
        "sourceUrl": "https://amazon.jobs",
        "isLive": True,
        "badgeColor": "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    {
        "id": "ret-2",
        "company": "Goldman Sachs",
        "logoInitial": "GS",
        "logoBg": "bg-blue-100 text-blue-900 border-blue-200",
        "roleTitle": "Operations & Business Architecture Associate (Returnship)",
        "roleCategory": "Operations & Strategy",
        "industry": "Financial Services",
        "location": "Bengaluru / Hyderabad (Hybrid)",
        "workArrangement": "Hybrid",
        "type": "verified",
        "verificationStatus": "Verified Global Returnship",
        "duration": "12 Weeks (Convertible)",
        "stipend": "Full Pro-rated Executive Compensation",
        "minBreakRequired": "2+ years career hiatus",
        "minExperience": "5+ years financial / ops background",
        "experienceLevel": "Senior / Lead (5+ yrs)",
        "verificationDate": "Verified Cohort 2026",
        "skills": ["Business Architecture", "SQL / Data Modeling", "Process Engineering", "Risk Management"],
        "description": "Goldman Sachs Returnship is a pioneer program designed to guide experienced candidates back into the financial services sector with bespoke skills refreshers, executive sponsor coaching, and peer group support.",
        "sourceUrl": "https://www.goldmansachs.com/careers/our-firm/returnship",
        "isLive": True,
        "badgeColor": "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    {
        "id": "ret-3",
        "company": "Intuit India",
        "logoInitial": "IN",
        "logoBg": "bg-indigo-100 text-indigo-900 border-indigo-200",
        "roleTitle": "Product Operations Specialist — Intuit Again Program",
        "roleCategory": "Product Management",
        "industry": "Fintech & Business Software",
        "location": "Bengaluru (Hybrid / Remote Flex)",
        "workArrangement": "Remote",
        "type": "verified",
        "verificationStatus": "Verified Corporate Initiative",
        "duration": "6 Months",
        "stipend": "Competitive Paid Fellowship + Wellness benefits",
        "minBreakRequired": "1.5+ years career break",
        "minExperience": "3+ years prior product/ops experience",
        "experienceLevel": "Mid-Level (3-6 yrs)",
        "verificationDate": "Verified Cohort 2026",
        "skills": ["Product Analytics", "Customer Journey Mapping", "Jira", "Stakeholder Communication"],
        "description": "Intuit Again is focused on inspiring technologists and business professionals to return to their passion after a career pause. Offers structured learning bootcamps, executive allies, and seamless reintegration into top-tier fintech teams.",
        "sourceUrl": "https://www.intuit.com/careers",
        "isLive": True,
        "badgeColor": "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    {
        "id": "ret-4",
        "company": "Dell Technologies",
        "logoInitial": "D",
        "logoBg": "bg-sky-100 text-sky-900 border-sky-200",
        "roleTitle": "Strategy & Supply Chain Program Lead — Dell ReStart",
        "roleCategory": "Operations & Strategy",
        "industry": "Technology & Hardware",
        "location": "Pune, India (Hybrid)",
        "workArrangement": "Hybrid",
        "type": "verified",
        "verificationStatus": "Verified ReStart Track",
        "duration": "16 Weeks",
        "stipend": "Standard Industry Stipend",
        "minBreakRequired": "1+ year break",
        "minExperience": "4+ years experience",
        "experienceLevel": "Mid-Senior (4-7 yrs)",
        "verificationDate": "Verified Cohort 2026",
        "skills": ["Supply Chain Analytics", "Strategic Sourcing", "Data Visualization", "Process Excellence"],
        "description": "Dell ReStart provides progressive pathways for women resuming corporate life. Candidates work on high-visibility global strategic projects with customized upskilling modules and career counselors.",
        "sourceUrl": "https://jobs.dell.com",
        "isLive": True,
        "badgeColor": "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    {
        "id": "ret-5",
        "company": "Accenture India",
        "logoInitial": "AC",
        "logoBg": "bg-purple-100 text-purple-900 border-purple-200",
        "roleTitle": "Enterprise Agility & Change Management Lead (Career Reboot)",
        "roleCategory": "Operations & Strategy",
        "industry": "Consulting & Digital Transformation",
        "location": "Mumbai / Bengaluru / Gurugram (Hybrid)",
        "workArrangement": "Hybrid",
        "type": "verified",
        "verificationStatus": "Verified Accenture Reboot",
        "duration": "Direct Cohort Placement",
        "stipend": "Full-Time Tier 1 Compensation",
        "minBreakRequired": "6+ months break",
        "minExperience": "3+ years relevant domain expertise",
        "experienceLevel": "Mid-Senior (3-6 yrs)",
        "verificationDate": "Verified Cohort 2026",
        "skills": ["Change Management", "Enterprise Agile", "Process Automation", "Team Facilitation"],
        "description": "Accenture's Career Reboot program is open to all qualified women seeking to re-enter professional consulting and tech management. Provides flexible working arrangements and child-care assistance allowances.",
        "sourceUrl": "https://www.accenture.com/in-en/careers",
        "isLive": True,
        "badgeColor": "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    # -------------------------------------------------------------------------
    # Data & Analytics Opportunities (Verified)
    # -------------------------------------------------------------------------
    {
        "id": "ret-13",
        "company": "Schneider Electric",
        "logoInitial": "SE",
        "logoBg": "bg-green-100 text-green-900 border-green-200",
        "roleTitle": "Business Intelligence & Data Analytics Specialist (Re-Act)",
        "roleCategory": "Data & Analytics",
        "industry": "Energy Management & Industrial Automation",
        "location": "Bengaluru (Hybrid)",
        "workArrangement": "Hybrid",
        "type": "verified",
        "verificationStatus": "Verified Re-Act Program",
        "duration": "6 Months",
        "stipend": "Competitive Paid Returnship",
        "minBreakRequired": "1+ year break",
        "minExperience": "3+ years data or business analytics",
        "experienceLevel": "Associate to Mid (3-6 yrs)",
        "verificationDate": "Verified Cohort 2026",
        "skills": ["SQL / Data Modeling", "Power BI", "Data Analytics", "Python", "Data Visualization"],
        "description": "Schneider Electric's Re-Act program brings back professionals to drive energy analytics and sustainability intelligence with flexible hybrid scheduling and transition mentorship.",
        "sourceUrl": "https://www.se.com/in/en/about-us/careers/",
        "isLive": True,
        "badgeColor": "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    # -------------------------------------------------------------------------
    # Sample / Demonstration Listings (Transparently Labeled)
    # -------------------------------------------------------------------------
    {
        "id": "ret-6",
        "company": "NovaScale Labs (Demo Partner)",
        "logoInitial": "NS",
        "logoBg": "bg-rose-100 text-rose-900 border-rose-200",
        "roleTitle": "Associate Product Designer — Returnee Pilot Cohort",
        "roleCategory": "Design & UX",
        "industry": "Software Startups",
        "location": "Remote (All India)",
        "workArrangement": "Remote",
        "type": "sample",
        "verificationStatus": "Sample Listing — Not a Live Opportunity",
        "duration": "12 Weeks Simulation",
        "stipend": "Simulated Demonstration Listing",
        "minBreakRequired": "2+ years break",
        "minExperience": "2+ years experience",
        "experienceLevel": "Associate (2-4 yrs)",
        "verificationDate": "Sample Demonstration",
        "skills": ["UI/UX Design", "Figma", "User Interviews", "Design Systems"],
        "description": "This is a demonstration listing illustrating how high-growth tech startups and scale-ups configure their bespoke returnee fellowship programs on the HerTurn platform.",
        "sourceUrl": None,
        "isLive": False,
        "badgeColor": "bg-stone-100 text-stone-600 border-stone-200",
    },
    {
        "id": "ret-7",
        "company": "Aether HealthTech (Demo Partner)",
        "logoInitial": "AH",
        "logoBg": "bg-teal-100 text-teal-900 border-teal-200",
        "roleTitle": "Digital Health Operations Manager — Second Horizon Fellowship",
        "roleCategory": "Operations & Strategy",
        "industry": "Healthcare & Life Sciences",
        "location": "Delhi NCR (On-site)",
        "workArrangement": "On-site",
        "type": "sample",
        "verificationStatus": "Sample Listing — Not a Live Opportunity",
        "duration": "14 Weeks Simulation",
        "stipend": "Simulated Demonstration Listing",
        "minBreakRequired": "1+ year break",
        "minExperience": "4+ years healthcare/ops background",
        "experienceLevel": "Mid-Senior (4-7 yrs)",
        "verificationDate": "Sample Demonstration",
        "skills": ["Healthcare Compliance", "Operational Metrics", "Team Mentorship", "SOP Optimization"],
        "description": "This simulated opportunity showcases how healthcare enterprise partners can advertise on-site and clinical-adjacent returnee positions with dedicated transition support.",
        "sourceUrl": None,
        "isLive": False,
        "badgeColor": "bg-stone-100 text-stone-600 border-stone-200",
    },
]

# Pre-parsed Pydantic objects
CATALOG_ITEMS: List[ReturnshipItem] = [ReturnshipItem(**item) for item in RAW_RETURNSHIP_CATALOG]
CATALOG_BY_ID: Dict[str, ReturnshipItem] = {item.id: item for item in CATALOG_ITEMS}


def get_all_returnships() -> List[ReturnshipItem]:
    """Return all catalog opportunities."""
    return list(CATALOG_ITEMS)


def get_returnship_by_id(returnship_id: str) -> Optional[ReturnshipItem]:
    """Retrieve returnship item by unique ID."""
    return CATALOG_BY_ID.get(returnship_id)


def get_distinct_skills() -> List[str]:
    """Return unique skills required across all catalog opportunities."""
    skills_set = set()
    for item in CATALOG_ITEMS:
        for skill in item.skills:
            skills_set.add(skill)
    return sorted(list(skills_set))


def get_distinct_categories() -> List[str]:
    """Return unique role categories across all catalog opportunities."""
    cat_set = set()
    for item in CATALOG_ITEMS:
        if item.roleCategory:
            cat_set.add(item.roleCategory)
    return sorted(list(cat_set))


def filter_returnships(
    search: Optional[str] = None,
    work_arrangement: Optional[str] = None,
    type_: Optional[str] = None,
    skill: Optional[str] = None,
    category: Optional[str] = None,
) -> List[ReturnshipItem]:
    """
    Filter returnships based on query parameters.
    """
    results = CATALOG_ITEMS

    # Filter by role category
    if category and category.lower() != "all":
        target_cat = category.lower().strip()
        results = [
            item for item in results
            if item.roleCategory and item.roleCategory.lower() == target_cat
        ]

    # Filter by work arrangement
    if work_arrangement and work_arrangement.lower() != "all":
        results = [
            item for item in results
            if item.workArrangement.lower() == work_arrangement.lower()
        ]

    # Filter by verified vs sample type
    if type_ and type_.lower() != "all":
        results = [
            item for item in results
            if item.type.lower() == type_.lower()
        ]

    # Filter by skill
    if skill and skill.lower() != "all":
        target_skill = skill.lower()
        results = [
            item for item in results
            if any(s.lower() == target_skill or target_skill in s.lower() for s in item.skills)
        ]

    # Free text search across company, roleTitle, roleCategory, location, and skills
    if search and search.strip():
        q = search.strip().lower()
        filtered = []
        for item in results:
            matches_company = q in item.company.lower()
            matches_role = q in item.roleTitle.lower()
            matches_cat = bool(item.roleCategory and q in item.roleCategory.lower())
            matches_loc = q in item.location.lower()
            matches_skills = any(q in s.lower() for s in item.skills)
            if matches_company or matches_role or matches_cat or matches_loc or matches_skills:
                filtered.append(item)
        results = filtered

    return results
