import React, { useState, useMemo, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Search, 
  Filter, 
  Bookmark, 
  Sparkles, 
  ShieldCheck, 
  ArrowLeft, 
  RotateCcw,
  Briefcase,
  AlertCircle,
  Database,
  CheckCircle2,
  RefreshCw,
  Info
} from 'lucide-react';
import Button from '../components/Button';
import OpportunityCard from '../components/OpportunityCard';
import { sampleReturnships } from '../data/sampleReturnships';
import { useAuth } from '../context/AuthContext';
import { 
  fetchReturnships, 
  matchReturnships, 
  fetchSavedReturnships, 
  saveReturnship, 
  removeSavedReturnship 
} from '../services/api';

export default function ReturnshipsPage() {
  const location = useLocation();
  const { isAuthenticated, user } = useAuth();

  // Search query & filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All'); // All, Design & UX, Software Engineering, etc.
  const [selectedArrangement, setSelectedArrangement] = useState('All'); // All, Remote, Hybrid, On-site
  const [selectedType, setSelectedType] = useState('All'); // All, verified, sample
  const [selectedSkill, setSelectedSkill] = useState('All');

  // Bookmarks state (restored from backend when authenticated)
  const [bookmarkedIds, setBookmarkedIds] = useState(new Set(['ret-1', 'ret-3']));
  const [showBookmarksOnly, setShowBookmarksOnly] = useState(false);

  // Live API data state
  const [opportunities, setOpportunities] = useState(sampleReturnships);
  const [isLoading, setIsLoading] = useState(false);
  const [isMatchingActive, setIsMatchingActive] = useState(false);
  const [isLiveBackend, setIsLiveBackend] = useState(false);
  const [recommendationNotice, setRecommendationNotice] = useState('');
  const [syncFeedback, setSyncFeedback] = useState(null);

  // Retrieve candidate context from session or location state
  let storedSession = null;
  try {
    const raw = sessionStorage.getItem('herturn_session');
    if (raw) storedSession = JSON.parse(raw);
  } catch (_) {}

  if (isAuthenticated && user && storedSession) {
    const sessionEmail = storedSession.candidate?.email;
    const sessionUserId = storedSession.userId || storedSession.candidate?.userId;
    const isOwner = (sessionEmail && sessionEmail.toLowerCase() === user.email.toLowerCase()) ||
                    (sessionUserId && sessionUserId === user.id);
    if (!isOwner) {
      storedSession = null;
    }
  }

  const navCandidate = location.state?.candidate;
  const isNavValid = !isAuthenticated || !user || !navCandidate?.email ||
                     (navCandidate.email.toLowerCase() === user.email.toLowerCase());
  const validNavState = isNavValid ? location.state : null;

  const rawCandidate = validNavState?.candidate || storedSession?.candidate || null;
  const candidate = rawCandidate ? {
    ...rawCandidate,
    fullName: (isAuthenticated && user?.fullName) ? user.fullName : (rawCandidate.fullName || 'Candidate'),
    email: (isAuthenticated && user?.email) ? user.email : (rawCandidate.email || '')
  } : (isAuthenticated && user ? {
    fullName: user.fullName || 'Candidate',
    email: user.email,
    targetRole: user.candidateProfile?.targetRole || 'Technology Professional',
    previousRole: 'Tech Professional',
    breakDuration: 'Career Pause',
    preferredWorkMode: user.candidateProfile?.workMode || 'Hybrid'
  } : null);

  const llmAnalysis = validNavState?.llmAnalysis || storedSession?.llmAnalysis || null;

  // 1. Restore bookmarks from backend when authenticated
  useEffect(() => {
    if (!isAuthenticated) return;
    let isMounted = true;

    fetchSavedReturnships()
      .then((res) => {
        if (!isMounted) return;
        if (res?.savedIds) {
          setBookmarkedIds(new Set(res.savedIds));
        }
      })
      .catch((err) => {
        console.warn('Could not restore saved returnships from backend:', err);
      });

    return () => { isMounted = false; };
  }, [isAuthenticated]);

  // 2. Fetch live opportunities & calculate candidate matching if available
  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);

    const hasCandidateCriteria = Boolean(
      candidate?.targetRole || 
      (llmAnalysis?.verifiedSkills && llmAnalysis.verifiedSkills.length > 0) ||
      isAuthenticated
    );

    if (hasCandidateCriteria) {
      // Extract verified skills from LLM analysis
      const extractedSkills = [];
      if (llmAnalysis?.verifiedSkills) {
        llmAnalysis.verifiedSkills.forEach((s) => {
          if (typeof s === 'string') extractedSkills.push(s);
          else if (s?.name) extractedSkills.push(s.name);
        });
      }

      matchReturnships({
        targetRole: candidate?.targetRole || null,
        verifiedSkills: extractedSkills,
        experienceYears: candidate?.totalExperience || candidate?.yearsOfExperience || null,
        breakDuration: candidate?.breakDuration || candidate?.careerBreakDuration || null,
        preferredWorkMode: candidate?.preferredWorkMode || candidate?.workMode || null,
        location: candidate?.preferredLocation || null,
        roleCategory: selectedCategory !== 'All' ? selectedCategory : null,
        search: searchQuery.trim() || null,
        transferableSkills: candidate?.areasOfInterest || []
      })
        .then((res) => {
          if (!isMounted) return;
          if (res?.items && res.items.length > 0) {
            setOpportunities(res.items);
            setIsMatchingActive(true);
            setIsLiveBackend(true);
            if (res.recommendationNotice) {
              setRecommendationNotice(res.recommendationNotice);
            }
          }
        })
        .catch((err) => {
          console.warn('Matching service unavailable, loading catalog directly:', err);
          fetchCatalogFallback(isMounted);
        })
        .finally(() => {
          if (isMounted) setIsLoading(false);
        });
    } else {
      fetchCatalogFallback(isMounted);
    }

    return () => { isMounted = false; };
  }, [isAuthenticated, candidate?.targetRole, candidate?.resumeAnalysisId, candidate?.resumeId]);

  const fetchCatalogFallback = (isMounted) => {
    fetchReturnships()
      .then((res) => {
        if (!isMounted) return;
        if (res?.items && res.items.length > 0) {
          setOpportunities(res.items);
          setIsLiveBackend(true);
        }
      })
      .catch((err) => {
        console.warn('Backend returnships endpoint unavailable, using demo catalog:', err);
        if (isMounted) {
          setOpportunities(sampleReturnships);
          setIsLiveBackend(false);
        }
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });
  };

  // Toggle bookmark with backend persistence
  const toggleBookmark = async (id) => {
    const isCurrentlySaved = bookmarkedIds.has(id);

    // Optimistic UI toggle
    setBookmarkedIds((prev) => {
      const next = new Set(prev);
      if (isCurrentlySaved) next.delete(id);
      else next.add(id);
      return next;
    });

    if (isAuthenticated) {
      try {
        if (isCurrentlySaved) {
          await removeSavedReturnship(id);
          setSyncFeedback('Removed from saved bookmarks');
        } else {
          await saveReturnship(id);
          setSyncFeedback('Saved to your profile');
        }
        setTimeout(() => setSyncFeedback(null), 2500);
      } catch (err) {
        console.error('Bookmark sync error:', err);
        // Rollback on failure
        setBookmarkedIds((prev) => {
          const next = new Set(prev);
          if (isCurrentlySaved) next.add(id);
          else next.delete(id);
          return next;
        });
        setSyncFeedback('Could not update bookmark');
        setTimeout(() => setSyncFeedback(null), 3000);
      }
    } else {
      setSyncFeedback('Saved in demo mode (Sign in to sync across devices)');
      setTimeout(() => setSyncFeedback(null), 3000);
    }
  };

  // Extract all distinct skills across active opportunities
  const allSkills = useMemo(() => {
    const set = new Set();
    opportunities.forEach((item) => {
      item.skills.forEach((s) => set.add(s));
    });
    return Array.from(set).sort();
  }, [opportunities]);

  // Extract all distinct role categories
  const allCategories = useMemo(() => {
    const defaultCategories = [
      'Design & UX',
      'Software Engineering',
      'Data & Analytics',
      'Product Management',
      'Operations & Strategy'
    ];
    const found = new Set(defaultCategories);
    opportunities.forEach((item) => {
      if (item.roleCategory) found.add(item.roleCategory);
    });
    return ['All', ...Array.from(found).sort()];
  }, [opportunities]);

  // Filtered dataset
  const filteredReturnships = useMemo(() => {
    return opportunities.filter((item) => {
      // Bookmark filter
      if (showBookmarksOnly && !bookmarkedIds.has(item.id)) {
        return false;
      }

      // Role Category filter
      if (selectedCategory !== 'All' && item.roleCategory !== selectedCategory) {
        return false;
      }

      // Work arrangement
      if (selectedArrangement !== 'All' && item.workArrangement !== selectedArrangement) {
        return false;
      }

      // Type (verified vs sample)
      if (selectedType !== 'All' && item.type !== selectedType) {
        return false;
      }

      // Skill filter
      if (selectedSkill !== 'All' && !item.skills.includes(selectedSkill)) {
        return false;
      }

      // Search query (matches company, role title, skills, or location)
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesCompany = item.company.toLowerCase().includes(query);
        const matchesRole = item.roleTitle.toLowerCase().includes(query);
        const matchesLocation = item.location.toLowerCase().includes(query);
        const matchesCategory = item.roleCategory?.toLowerCase().includes(query);
        const matchesSkills = item.skills.some((s) => s.toLowerCase().includes(query));
        if (!matchesCompany && !matchesRole && !matchesLocation && !matchesCategory && !matchesSkills) {
          return false;
        }
      }

      return true;
    });
  }, [opportunities, searchQuery, selectedCategory, selectedArrangement, selectedType, selectedSkill, bookmarkedIds, showBookmarksOnly]);

  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedCategory('All');
    setSelectedArrangement('All');
    setSelectedType('All');
    setSelectedSkill('All');
    setShowBookmarksOnly(false);
  };

  return (
    <div className="space-y-8 pb-16">
      
      {/* 1. TOP HEADER & INTRO */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#EAE3F1] pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link to="/dashboard" className="text-xs text-[#7D6B82] hover:text-[#3E1E43] flex items-center gap-1 font-medium">
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Overview</span>
            </Link>
            <span className="text-[#8C7A93]">•</span>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#EAE3F1] text-[#3E1E43] border border-[#DFD5E7]">
              Career Marketplace
            </span>
            {isAuthenticated ? (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 text-purple-900 border border-purple-200 flex items-center gap-1">
                <Database className="w-3 h-3 text-purple-700" />
                Account Synced
              </span>
            ) : (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FAF7F2] text-[#6B6470] border border-[#EAE3F1] flex items-center gap-1">
                <Info className="w-3 h-3 text-[#7D6B82]" />
                Demo Mode
              </span>
            )}
          </div>

          <h1 className="font-serif text-2xl sm:text-3xl font-bold text-[#3E1E43]">
            Curated Returnship Opportunities
          </h1>
          <p className="text-xs sm:text-sm text-[#6B6470] mt-0.5 max-w-2xl">
            Explore dedicated return-to-work fellowships, corporate cohort programs, and returnship pilots designed for women relaunching their careers.
          </p>
        </div>

        {/* Bookmark toggle pill */}
        <button
          type="button"
          onClick={() => setShowBookmarksOnly(!showBookmarksOnly)}
          className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold border transition-all cursor-pointer ${
            showBookmarksOnly
              ? 'bg-[#3E1E43] text-white border-[#3E1E43] shadow-xs'
              : 'bg-white text-[#3E1E43] border-[#EAE3F1] hover:border-[#3E1E43]'
          }`}
        >
          <Bookmark className={`w-3.5 h-3.5 ${showBookmarksOnly ? 'fill-current' : ''}`} />
          <span>Saved ({bookmarkedIds.size})</span>
        </button>
      </div>

      {/* Sync Notification Toast */}
      {syncFeedback && (
        <div className="p-3 bg-purple-50 border border-purple-200 text-xs text-[#3E1E43] rounded-xl flex items-center justify-between animate-in fade-in shadow-xs">
          <div className="flex items-center gap-2 font-medium">
            <CheckCircle2 className="w-4 h-4 text-purple-700" />
            <span>{syncFeedback}</span>
          </div>
        </div>
      )}

      {/* AI Matching Status Banner */}
      {isMatchingActive && (
        <div className="p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-purple-50/80 via-white to-pink-50/40 border border-[#EAE3F1] flex items-start gap-3.5 text-xs shadow-xs animate-in fade-in">
          <div className="w-8 h-8 rounded-xl bg-[#3E1E43] text-white flex items-center justify-center shrink-0 mt-0.5">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div className="space-y-1 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-bold text-sm text-[#3E1E43]">
                AI Match Recommendation Active
              </span>
              {candidate?.targetRole && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-100 text-[#3E1E43] border border-purple-200">
                  Target: {candidate.targetRole}
                </span>
              )}
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                Skills Overlap Ranked
              </span>
            </div>
            <p className="text-[#6B6470] leading-relaxed">
              Opportunities below are ranked based on factual skills overlap, role relevance, and work arrangement preferences without career-break bias.
            </p>
            {recommendationNotice && (
              <p className="text-[11px] text-[#8C7A93] italic pt-0.5 border-t border-[#EAE3F1]/80">
                Notice: {recommendationNotice}
              </p>
            )}
          </div>
        </div>
      )}

      {/* 2. SEARCH & FILTER CONTROLS BAR */}
      <div className="bg-white rounded-2xl border border-[#EAE3F1] p-5 shadow-xs space-y-4">
        
        {/* Search input */}
        <div className="relative">
          <Search className="w-4 h-4 text-[#8C7A93] absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by role title, company name, skills, or city..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#D9CEE3] focus:outline-none focus:ring-2 focus:ring-[#3E1E43] text-xs sm:text-sm bg-[#FAF7F2]"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery('')}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-xs text-[#8C7A93] hover:text-[#3E1E43]"
            >
              Clear
            </button>
          )}
        </div>

        {/* Category Quick Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs no-scrollbar">
          {allCategories.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-full font-medium transition-all cursor-pointer shrink-0 border ${
                selectedCategory === cat
                  ? 'bg-[#3E1E43] text-white border-[#3E1E43] shadow-xs'
                  : 'bg-[#FAF7F2] text-[#5C5560] border-[#EAE3F1] hover:border-[#3E1E43]'
              }`}
            >
              {cat === 'All' ? 'All Roles' : cat}
            </button>
          ))}
        </div>

        {/* Filter chips row */}
        <div className="flex flex-wrap items-center gap-3 pt-1 text-xs">
          
          {/* Category Dropdown */}
          <div className="flex items-center gap-1.5">
            <span className="text-[#8C7A93] font-medium">Category:</span>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg border border-[#D9CEE3] bg-[#FAF7F2] text-[#2B282C] focus:outline-none font-medium"
            >
              {allCategories.map((cat) => (
                <option key={cat} value={cat}>{cat === 'All' ? 'All Role Categories' : cat}</option>
              ))}
            </select>
          </div>

          {/* Work Mode */}
          <div className="flex items-center gap-1.5">
            <span className="text-[#8C7A93] font-medium">Work Mode:</span>
            <select
              value={selectedArrangement}
              onChange={(e) => setSelectedArrangement(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg border border-[#D9CEE3] bg-[#FAF7F2] text-[#2B282C] focus:outline-none font-medium"
            >
              <option value="All">All Arrangements</option>
              <option value="Remote">Remote</option>
              <option value="Hybrid">Hybrid</option>
              <option value="On-site">On-site</option>
            </select>
          </div>

          {/* Verification Status */}
          <div className="flex items-center gap-1.5">
            <span className="text-[#8C7A93] font-medium">Status:</span>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg border border-[#D9CEE3] bg-[#FAF7F2] text-[#2B282C] focus:outline-none font-medium"
            >
              <option value="All">All Listings</option>
              <option value="verified">Verified Cohorts</option>
              <option value="sample">Sample Demonstrations</option>
            </select>
          </div>

          {/* Filter by skill */}
          <div className="flex items-center gap-1.5">
            <span className="text-[#8C7A93] font-medium">Skill:</span>
            <select
              value={selectedSkill}
              onChange={(e) => setSelectedSkill(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg border border-[#D9CEE3] bg-[#FAF7F2] text-[#2B282C] focus:outline-none font-medium max-w-[180px] truncate"
            >
              <option value="All">All Required Skills</option>
              {allSkills.map((sk) => (
                <option key={sk} value={sk}>{sk}</option>
              ))}
            </select>
          </div>

          {/* Reset button */}
          {(searchQuery || selectedCategory !== 'All' || selectedArrangement !== 'All' || selectedType !== 'All' || selectedSkill !== 'All' || showBookmarksOnly) && (
            <button
              type="button"
              onClick={handleResetFilters}
              className="ml-auto text-xs text-[#8C7A93] hover:text-[#3E1E43] flex items-center gap-1 underline cursor-pointer"
            >
              <RotateCcw className="w-3 h-3" />
              Reset All
            </button>
          )}

        </div>

      </div>

      {/* 3. TRANSPARENCY NOTICE */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-[#FAF7F2] to-[#F5F0F9] border border-[#EAE3F1] flex items-start gap-3 text-xs text-[#5C5560]">
        <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
        <div>
          <strong className="text-[#3E1E43] font-semibold">Integrity Commitment:</strong> Verified listings link to actual official returnship career portals (Amazon Return to Work, Goldman Sachs Returnship, Intuit Again, Dell ReStart, Accenture Reboot). Sample listings are transparently badged to show how new corporate partners will register their cohorts.
        </div>
      </div>

      {/* 4. OPPORTUNITIES GRID */}
      {filteredReturnships.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredReturnships.map((opportunity) => (
            <OpportunityCard
              key={opportunity.id}
              opportunity={opportunity}
              isBookmarked={bookmarkedIds.has(opportunity.id)}
              onToggleBookmark={toggleBookmark}
            />
          ))}
        </div>
      ) : (
        /* Empty State */
        <div className="bg-white rounded-3xl border border-[#EAE3F1] p-12 text-center max-w-md mx-auto space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-[#EAE3F1] text-[#3E1E43] mx-auto flex items-center justify-center">
            <AlertCircle className="w-7 h-7" />
          </div>
          <h3 className="font-serif font-bold text-lg text-[#3E1E43]">
            No matching returnships found
          </h3>
          <p className="text-xs text-[#6B6470] leading-relaxed">
            {selectedCategory !== 'All'
              ? `No opportunities match the "${selectedCategory}" category under your active filters. Try clearing category filters or adjusting search keywords.`
              : 'Try adjusting your search criteria, switching your work arrangement filter, or clearing your active filters.'}
          </p>
          <Button variant="outline" size="sm" onClick={handleResetFilters}>
            Clear All Filters
          </Button>
        </div>
      )}

    </div>
  );
}
