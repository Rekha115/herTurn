"""
HerTurn Returnship Opportunity Matching Engine.
Calculates explainable match scores using skills overlap, role relevance, and work arrangement alignment.
Enforces strict factual criteria: missing requirements are treated as unknown, not automatically satisfied.
Career breaks are never penalized.
"""

import re
from typing import List, Optional, Union, Dict, Any, Tuple
from app.models import ReturnshipItem, MatchedReturnshipItem
from app.returnships.catalog import get_all_returnships


def _normalize_skill(skill: str) -> str:
    """Normalize skill name for fuzzy matching."""
    s = skill.lower().strip()
    s = re.sub(r"[^\w\s]", " ", s)
    return " ".join(s.split())


def _skills_match(cand_skill: str, opp_skill: str) -> bool:
    """Check if candidate skill aligns with opportunity required skill."""
    c_norm = _normalize_skill(cand_skill)
    o_norm = _normalize_skill(opp_skill)

    if not c_norm or not o_norm:
        return False

    if c_norm == o_norm:
        return True

    # Substring containment
    if c_norm in o_norm or o_norm in c_norm:
        return True

    # Token overlap (e.g., "agile", "cloud", "sql", "analytics")
    c_tokens = set(t for t in c_norm.split() if len(t) > 2)
    o_tokens = set(t for t in o_norm.split() if len(t) > 2)

    return len(c_tokens.intersection(o_tokens)) > 0


def _parse_duration_to_years(text: Optional[Union[str, int, float]]) -> Optional[float]:
    """Parse break or experience string into numeric years."""
    if text is None:
        return None
    if isinstance(text, (int, float)):
        return float(text)

    s = str(text).lower().strip()
    if not s or s == "null" or s == "none" or s == "unknown":
        return None

    # Check for months: e.g. "6 months", "18 months"
    match_months = re.search(r"(\d+(?:\.\d+)?)\s*(?:month|mos|mo)", s)
    if match_months:
        return float(match_months.group(1)) / 12.0

    # Check for years: e.g. "2+ years", "3.5 yrs", "1 year"
    match_years = re.search(r"(\d+(?:\.\d+)?)\s*(?:year|yr)", s)
    if match_years:
        return float(match_years.group(1))

    # Single number without units
    match_num = re.search(r"^(\d+(?:\.\d+)?)$", s)
    if match_num:
        return float(match_num.group(1))

    return None


ROLE_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "Design & UX": {
        "keywords": {"ui", "ux", "ui/ux", "designer", "design", "figma", "product designer", "user experience", "interaction", "ux researcher", "visual", "prototyping", "wireframing"},
        "synonyms": {
            "ui": ["ux", "product designer", "user experience designer", "interaction designer"],
            "ux": ["ui", "product designer", "user experience designer", "interaction designer"],
            "ui/ux": ["product designer", "ux designer", "user experience designer", "interaction designer"],
            "product designer": ["ui/ux designer", "ux designer", "user experience designer"],
            "ux designer": ["ui/ux designer", "product designer", "interaction designer"],
            "user experience": ["product designer", "ux designer"],
            "ux researcher": ["design researcher", "user researcher"],
        }
    },
    "Software Engineering": {
        "keywords": {"software", "engineer", "developer", "frontend", "backend", "full stack", "fullstack", "web", "react", "javascript", "python", "sde", "coding"},
        "synonyms": {
            "frontend": ["web developer", "react developer", "software engineer", "frontend engineer"],
            "full stack": ["software engineer", "full stack engineer", "full stack developer"],
            "software engineer": ["developer", "software development engineer", "sde"],
        }
    },
    "Data & Analytics": {
        "keywords": {"data", "analyst", "analytics", "business intelligence", "bi", "sql", "power bi", "tableau", "scientist", "reporting"},
        "synonyms": {
            "data analyst": ["business intelligence", "bi specialist", "analytics associate"],
            "business intelligence": ["data analyst", "analytics specialist"],
        }
    },
    "Product Management": {
        "keywords": {"product manager", "product management", "apm", "product owner", "product lead", "product operations", "product discovery"},
        "synonyms": {
            "product manager": ["product owner", "associate product manager", "product lead"],
            "product operations": ["product manager", "product associate"],
        }
    },
    "Operations & Strategy": {
        "keywords": {"operations", "program manager", "tpm", "project manager", "agile", "scrum", "supply chain", "strategy", "architecture", "business analyst", "process"},
        "synonyms": {
            "program manager": ["technical program manager", "operations manager"],
            "operations": ["program manager", "operations specialist"],
        }
    }
}

VALID_SHORT_TOKENS = {"ui", "ux", "ai", "ml", "bi", "pm", "qa", "it", "sql", "sde"}
STOP_TOKENS = {"and", "the", "for", "with", "lead", "associate", "specialist", "program", "cohort", "track"}


def _extract_domain_tokens(text: str) -> set:
    """Extract normalized meaningful domain tokens including valid short acronyms."""
    norm = _normalize_skill(text)
    tokens = set()
    for tok in norm.split():
        if tok in STOP_TOKENS:
            continue
        if tok in VALID_SHORT_TOKENS or len(tok) > 2:
            tokens.add(tok)
    return tokens


def _detect_role_category(role_text: Optional[str]) -> Optional[str]:
    """Identify the dominant role category from role text."""
    if not role_text:
        return None
    tokens = _extract_domain_tokens(role_text)
    best_cat = None
    best_overlap = 0
    for cat, data in ROLE_TAXONOMY.items():
        overlap = len(tokens.intersection(data["keywords"]))
        if overlap > best_overlap:
            best_overlap = overlap
            best_cat = cat
    return best_cat if best_overlap > 0 else None


def _calculate_role_relevance(target_role: Optional[str], opp: ReturnshipItem) -> float:
    """
    Calculate semantic role relevance between candidate target role and opportunity.
    Incorporates category alignment, title overlap, and domain synonyms.
    """
    if not target_role or not target_role.strip():
        return 0.5  # Neutral default when target role is unspecified

    t_tokens = _extract_domain_tokens(target_role)
    r_tokens = _extract_domain_tokens(opp.roleTitle)
    d_tokens = _extract_domain_tokens(opp.description)

    if not t_tokens:
        return 0.5

    # 1. Category comparison
    cand_cat = _detect_role_category(target_role)
    opp_cat = opp.roleCategory or _detect_role_category(opp.roleTitle)

    category_bonus = 0.0
    category_mismatch_penalty = False
    if cand_cat and opp_cat:
        if cand_cat == opp_cat:
            category_bonus = 0.35
        else:
            category_mismatch_penalty = True

    # 2. Direct & Synonym Overlap with Title
    direct_overlap = len(t_tokens.intersection(r_tokens)) / len(t_tokens)
    
    # Check synonym expansions
    synonym_overlap = 0.0
    if cand_cat and cand_cat in ROLE_TAXONOMY:
        synonyms = ROLE_TAXONOMY[cand_cat].get("synonyms", {})
        for t_word in t_tokens:
            if t_word in synonyms:
                for syn in synonyms[t_word]:
                    syn_tokens = _extract_domain_tokens(syn)
                    if syn_tokens and syn_tokens.intersection(r_tokens):
                        synonym_overlap = max(synonym_overlap, 0.45)

    effective_title_overlap = max(direct_overlap, synonym_overlap)
    desc_overlap = len(t_tokens.intersection(d_tokens)) / len(t_tokens)

    raw_score = (effective_title_overlap * 0.6) + (desc_overlap * 0.2) + category_bonus

    if category_mismatch_penalty and effective_title_overlap < 0.2:
        return max(0.15, min(0.35, raw_score * 0.5))

    return max(0.2, min(1.0, raw_score))


def _calculate_work_arrangement_score(
    preferred_mode: Optional[str],
    opp_mode: str,
    preferred_loc: Optional[str],
    opp_loc: str,
) -> float:
    """Calculate work arrangement compatibility."""
    if not preferred_mode or preferred_mode.lower() == "all" or not preferred_mode.strip():
        mode_score = 1.0
    else:
        p = preferred_mode.lower().strip()
        o = opp_mode.lower().strip()
        if p == o:
            mode_score = 1.0
        elif p == "hybrid" and o == "remote":
            mode_score = 0.95
        elif p == "remote" and o == "hybrid":
            mode_score = 0.45
        elif p == "remote" and o == "on-site":
            mode_score = 0.15
        elif p == "on-site" and o == "hybrid":
            mode_score = 0.85
        elif p == "hybrid" and o == "on-site":
            mode_score = 0.60
        else:
            mode_score = 0.60

    # Optional location bonus
    if preferred_loc and preferred_loc.strip() and opp_mode.lower() != "remote":
        loc_cand = _normalize_skill(preferred_loc)
        loc_opp = _normalize_skill(opp_loc)
        if any(tok in loc_opp for tok in loc_cand.split() if len(tok) > 3):
            mode_score = min(1.0, mode_score + 0.1)

    return mode_score


def _determine_eligibility(
    opp: ReturnshipItem,
    cand_break_years: Optional[float],
    cand_exp_years: Optional[float],
    skill_ratio: float,
) -> str:
    """
    Determine eligibility status factually.
    Treats missing/unverified values as unknown, rather than automatically satisfied.
    Never penalizes career breaks.
    """
    if opp.type == "sample":
        return "Sample Demonstration Listing"

    # 1. Break Requirement
    min_break = _parse_duration_to_years(opp.minBreakRequired) or 0.0

    if cand_break_years is None:
        return f"Review Requirements ({opp.minBreakRequired} required; break duration unknown)"

    if cand_break_years < min_break:
        return f"Review Requirements (Career break is below stated {opp.minBreakRequired})"

    # 2. Experience Requirement
    min_exp = _parse_duration_to_years(opp.minExperience) or 0.0

    if cand_exp_years is None:
        return f"Review Requirements ({opp.minExperience} required; prior experience unverified)"

    if cand_exp_years < min_exp:
        return f"Review Requirements (Experience is below stated {opp.minExperience})"

    # 3. Both break and experience criteria are met!
    if skill_ratio >= 0.5:
        return "Eligible"
    else:
        return "Likely Eligible (Upskilling Recommended)"


def match_opportunity(
    opp: ReturnshipItem,
    candidate_skills: List[str],
    target_role: Optional[str] = None,
    experience_years: Optional[Union[int, float, str]] = None,
    break_duration: Optional[str] = None,
    preferred_work_mode: Optional[str] = None,
    location: Optional[str] = None,
    transferable_skills: Optional[List[str]] = None,
) -> MatchedReturnshipItem:
    """
    Match a single returnship opportunity against candidate parameters.
    """
    # 1. Skills overlap (combining verified skills and any relevant transferable competencies)
    all_cand_skills = list(candidate_skills)
    if transferable_skills:
        for ts in transferable_skills:
            if ts not in all_cand_skills:
                all_cand_skills.append(ts)

    matched_skills: List[str] = []
    skills_to_bridge: List[str] = []

    for opp_skill in opp.skills:
        if any(_skills_match(c_skill, opp_skill) for c_skill in all_cand_skills):
            matched_skills.append(opp_skill)
        else:
            skills_to_bridge.append(opp_skill)

    skill_ratio = len(matched_skills) / len(opp.skills) if opp.skills else 0.5

    # 2. Role relevance
    role_relevance = _calculate_role_relevance(target_role, opp)

    # 3. Work mode alignment
    arrangement_score = _calculate_work_arrangement_score(
        preferred_work_mode,
        opp.workArrangement,
        location,
        opp.location,
    )

    # 4. Composite Match Score (0 to 100)
    # Weights: Skills (50%), Role Relevance (35%), Work Arrangement (15%)
    raw_score = (skill_ratio * 50.0) + (role_relevance * 35.0) + (arrangement_score * 15.0)
    match_score = int(round(max(5.0, min(98.0, raw_score))))

    # 5. Factual Eligibility
    cand_break_years = _parse_duration_to_years(break_duration)
    cand_exp_years = _parse_duration_to_years(experience_years)
    eligibility_status = _determine_eligibility(opp, cand_break_years, cand_exp_years, skill_ratio)

    # 6. Explainable Rationale
    rationale_parts = []
    if role_relevance >= 0.75:
        role_label = target_role or opp.roleCategory or "target role"
        rationale_parts.append(f"Direct alignment with your {role_label} focus")
    elif role_relevance >= 0.5:
        rationale_parts.append(f"Relevant domain transition path in {opp.roleCategory or 'Technology'}")

    if matched_skills:
        rationale_parts.append(
            f"Matched {len(matched_skills)} of {len(opp.skills)} core skills ({', '.join(matched_skills[:2])})"
        )
    else:
        rationale_parts.append("Found opportunity to bridge core cohort competencies")

    if preferred_work_mode and preferred_work_mode.lower() != "all":
        if arrangement_score >= 0.8:
            rationale_parts.append(f"aligns with your {opp.workArrangement} preference")
        else:
            rationale_parts.append(f"offers {opp.workArrangement} arrangement")

    if skills_to_bridge:
        rationale_parts.append(f"Bridge target: {skills_to_bridge[0]}")

    match_rationale = ". ".join(rationale_parts) + "."

    return MatchedReturnshipItem(
        **opp.model_dump(),
        matchScore=match_score,
        matchedSkills=matched_skills,
        skillsToBridge=skills_to_bridge,
        eligibilityStatus=eligibility_status,
        matchRationale=match_rationale,
    )


def match_all_returnships(
    candidate_skills: List[str],
    target_role: Optional[str] = None,
    experience_years: Optional[Union[int, float, str]] = None,
    break_duration: Optional[str] = None,
    preferred_work_mode: Optional[str] = None,
    location: Optional[str] = None,
    role_category: Optional[str] = None,
    search: Optional[str] = None,
    transferable_skills: Optional[List[str]] = None,
) -> List[MatchedReturnshipItem]:
    """
    Match all catalog opportunities and return sorted by matchScore descending.
    Applies optional category and search filters.
    """
    opportunities = get_all_returnships()

    # Filter by category if requested
    if role_category and role_category.lower() != "all":
        cat_lower = role_category.lower().strip()
        opportunities = [
            opp for opp in opportunities
            if opp.roleCategory and opp.roleCategory.lower() == cat_lower
        ]

    # Filter by search keyword if requested
    if search and search.strip():
        q = search.strip().lower()
        opportunities = [
            opp for opp in opportunities
            if q in opp.company.lower()
            or q in opp.roleTitle.lower()
            or (opp.roleCategory and q in opp.roleCategory.lower())
            or q in opp.location.lower()
            or any(q in s.lower() for s in opp.skills)
        ]

    matched = [
        match_opportunity(
            opp=opp,
            candidate_skills=candidate_skills,
            target_role=target_role,
            experience_years=experience_years,
            break_duration=break_duration,
            preferred_work_mode=preferred_work_mode,
            location=location,
            transferable_skills=transferable_skills,
        )
        for opp in opportunities
    ]
    # Sort primarily by matchScore desc, then by verified first
    matched.sort(key=lambda m: (m.matchScore, 1 if m.type == "verified" else 0), reverse=True)
    return matched
