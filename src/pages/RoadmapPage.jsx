import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Sparkles, 
  ArrowLeft, 
  RotateCcw,
  Briefcase, 
  Loader2, 
  AlertCircle, 
  FileText, 
  RefreshCw, 
  BookOpen, 
  Cloud, 
  CheckCircle2,
  Trophy,
  ArrowRight
} from 'lucide-react';
import Button from '../components/Button';
import WeekCard from '../components/WeekCard';
import { sampleRoadmapData } from '../data/demoRoadmap';
import { 
  generatePersonalizedRoadmap, 
  fetchCandidateRoadmap, 
  updateRoadmapTaskProgress, 
  USE_MOCK_DATA 
} from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function RoadmapPage() {
  const location = useLocation();
  const { user, isAuthenticated } = useAuth();

  // Track database record ID and sync state
  const [persistedRoadmapId, setPersistedRoadmapId] = useState(null);
  const [isSyncingTask, setIsSyncingTask] = useState(false);
  const [syncNotice, setSyncNotice] = useState('');

  // Retrieve stored session from location.state or sessionStorage fallback
  const sessionData = useMemo(() => {
    let stored = null;
    try {
      const raw = sessionStorage.getItem('herturn_session');
      if (raw) stored = JSON.parse(raw);
    } catch (_) {}

    // If authenticated, ensure stored session strictly belongs to current user
    if (isAuthenticated && user && stored) {
      const sessionEmail = stored.candidate?.email;
      const sessionUserId = stored.userId || stored.candidate?.userId;
      const isOwner = (sessionEmail && sessionEmail.toLowerCase() === user.email.toLowerCase()) ||
                      (sessionUserId && sessionUserId === user.id);
      if (!isOwner) {
        stored = null;
      }
    }

    const navCandidate = location.state?.candidate;
    const isNavValid = !isAuthenticated || !user || !navCandidate?.email ||
                       (navCandidate.email.toLowerCase() === user.email.toLowerCase());
    const validNavState = isNavValid ? location.state : null;

    const rawCandidate = validNavState?.candidate || stored?.candidate || null;
    const resolvedCandidate = rawCandidate ? {
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

    return {
      candidate: resolvedCandidate,
      llmAnalysis: validNavState?.llmAnalysis || stored?.llmAnalysis || null,
      isLiveAnalyzed: validNavState?.isLiveAnalyzed ?? stored?.isLiveAnalyzed ?? false,
      modelUsed: validNavState?.modelUsed || stored?.modelUsed || 'gemini-3.1-flash-lite-preview',
      resumeAnalysisId: validNavState?.resumeAnalysisId || stored?.resumeAnalysisId || null,
      resumeId: validNavState?.resumeId || stored?.resumeId || null
    };
  }, [location.state, isAuthenticated, user]);

  const { candidate, llmAnalysis, isLiveAnalyzed } = sessionData;

  // Stable identifier for active resume
  const activeResumeAnalysisId = useMemo(() => {
    return sessionData.resumeAnalysisId || candidate?.resumeAnalysisId || null;
  }, [sessionData.resumeAnalysisId, candidate?.resumeAnalysisId]);

  const activeResumeId = useMemo(() => {
    if (activeResumeAnalysisId) return `analysis_${activeResumeAnalysisId}`;
    if (sessionData.resumeId) return sessionData.resumeId;
    if (candidate?.resumeId) return candidate.resumeId;
    const file = candidate?.resumeFileName || 'resume_default';
    const role = candidate?.targetRole || 'tech_role';
    return `ref_${file}_${role}`.replace(/[^a-zA-Z0-9_-]/g, '_');
  }, [activeResumeAnalysisId, sessionData.resumeId, candidate?.resumeId, candidate?.resumeFileName, candidate?.targetRole]);

  // Duration selector: 4 weeks or 6 weeks
  const [selectedDuration, setSelectedDuration] = useState(4);

  // Allow user in live mode without analysis to voluntarily view sample demo roadmap
  const [showDemoFallback, setShowDemoFallback] = useState(false);

  // Scoped cache key helpers
  const getCacheKey = useCallback((resumeId, duration) => {
    return `herturn_roadmap_cache_${resumeId}_${duration}`;
  }, []);

  const getMetaCacheKey = useCallback((resumeId) => {
    return `herturn_roadmap_meta_${resumeId}`;
  }, []);

  // Helper to read cached roadmap from sessionStorage for instant 0ms load strictly for active resume
  const getCachedPlan = useCallback((resumeId, duration) => {
    if (USE_MOCK_DATA) {
      return duration === 6 ? sampleRoadmapData.sixWeekPlan : sampleRoadmapData.fourWeekPlan;
    }
    if (!resumeId) return null;
    try {
      const cacheKey = getCacheKey(resumeId, duration);
      const raw = sessionStorage.getItem(cacheKey);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed?.weeks && parsed.weeks.length > 0) {
          return parsed.weeks;
        }
      }
    } catch (_) {}
    return null;
  }, [getCacheKey]);

  const getCachedMeta = useCallback((resumeId) => {
    if (!resumeId) return null;
    try {
      const raw = sessionStorage.getItem(getMetaCacheKey(resumeId));
      if (raw) return JSON.parse(raw);
    } catch (_) {}
    return null;
  }, [getMetaCacheKey]);

  // Plans state: initialized strictly from activeResumeId's cache (null if new resume)
  const [plans, setPlans] = useState(() => ({
    4: getCachedPlan(activeResumeId, 4),
    6: getCachedPlan(activeResumeId, 6),
  }));

  // Metadata for the active roadmap
  const [roadmapMetadata, setRoadmapMetadata] = useState(() => {
    const cachedMeta = getCachedMeta(activeResumeId);
    if (cachedMeta) return cachedMeta;
    return {
      targetRole: candidate?.targetRole || sampleRoadmapData.targetRole,
      personalizedSummary: sampleRoadmapData.personalizedSummary,
      modelUsed: sessionData.modelUsed,
      isPersonalized: Boolean(getCachedPlan(activeResumeId, 4)),
      isRagUsed: false,
      ragStatus: 'unavailable',
      ragSourceCount: 0,
    };
  });

  // Track active resume changes to invalidate/switch in-memory state immediately
  const prevResumeIdRef = useRef(activeResumeId);
  useEffect(() => {
    if (prevResumeIdRef.current !== activeResumeId) {
      prevResumeIdRef.current = activeResumeId;
      const cached4 = getCachedPlan(activeResumeId, 4);
      const cached6 = getCachedPlan(activeResumeId, 6);
      const cachedMeta = getCachedMeta(activeResumeId);

      setPlans({
        4: cached4,
        6: cached6,
      });

      if (cachedMeta) {
        setRoadmapMetadata(cachedMeta);
      } else {
        setRoadmapMetadata({
          targetRole: candidate?.targetRole || sampleRoadmapData.targetRole,
          personalizedSummary: sampleRoadmapData.personalizedSummary,
          modelUsed: sessionData.modelUsed,
          isPersonalized: Boolean(cached4),
          isRagUsed: false,
          ragStatus: 'unavailable',
          ragSourceCount: 0,
        });
      }
      setPersistedRoadmapId(null);
      setApiError('');
    }
  }, [activeResumeId, getCachedPlan, getCachedMeta, candidate?.targetRole, sessionData.modelUsed]);

  // Loading & Error States
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState('');
  
  // Guard to prevent concurrent duplicate generation requests
  const isGeneratingRef = useRef(false);
  const generationSeqRef = useRef(0);
  const activeResumeIdRef = useRef(activeResumeId);
  activeResumeIdRef.current = activeResumeId;

  // Determine if candidate has live analysis available
  const hasAnalysis = Boolean(isLiveAnalyzed && llmAnalysis);

  // 1. Restore persisted roadmap and progress from SQLite database on mount / resume switch
  useEffect(() => {
    let isMounted = true;
    async function loadSavedRoadmap() {
      if (!isAuthenticated || USE_MOCK_DATA) return;
      try {
        const saved = await fetchCandidateRoadmap({
          resumeAnalysisId: activeResumeAnalysisId,
          durationWeeks: selectedDuration
        });
        if (!isMounted) return;
        if (saved?.hasRoadmap && saved.roadmap?.weeks) {
          // Verify that retrieved roadmap corresponds to active resume analysis if specified
          if (activeResumeAnalysisId && saved.resumeAnalysisId && saved.resumeAnalysisId !== activeResumeAnalysisId) {
            return;
          }

          const duration = saved.durationWeeks || 4;
          const progressMap = saved.tasksProgress || {};
          const syncedWeeks = saved.roadmap.weeks.map((w) => ({
            ...w,
            tasks: (w.tasks || []).map((t) => ({
              ...t,
              completed: Boolean(progressMap[t.id]),
            })),
          }));

          setPlans((prev) => ({
            ...prev,
            [duration]: syncedWeeks,
          }));
          setSelectedDuration(duration);
          setPersistedRoadmapId(saved.roadmapId);

          const meta = {
            targetRole: saved.targetRole || saved.roadmap.targetRole,
            personalizedSummary: saved.roadmap.personalizedSummary || 'Restored from your candidate profile.',
            modelUsed: saved.modelUsed || 'gemini-3.1-flash-lite-preview',
            isPersonalized: true,
            isRagUsed: Boolean(saved.isRagUsed),
            ragStatus: saved.isRagUsed ? 'verified_rag_used' : 'unavailable',
            ragSourceCount: saved.ragSourceCount || 0,
          };
          setRoadmapMetadata(meta);

          // Cache in sessionStorage for fast back/forward navigation strictly under active resume ID
          try {
            sessionStorage.setItem(getCacheKey(activeResumeId, duration), JSON.stringify({ weeks: syncedWeeks }));
            sessionStorage.setItem(getMetaCacheKey(activeResumeId), JSON.stringify(meta));
          } catch (_) {}
        }
      } catch (err) {
        console.warn('Failed to load saved candidate roadmap:', err.message);
      }
    }

    loadSavedRoadmap();
    return () => {
      isMounted = false;
    };
  }, [isAuthenticated, activeResumeAnalysisId, activeResumeId, selectedDuration, getCacheKey, getMetaCacheKey]);

  // 2. Fetch or generate personalized roadmap (with deduplication, caching & race condition guard)
  const loadPersonalizedRoadmap = useCallback(async (duration, forceRegenerate = false) => {
    if (USE_MOCK_DATA) return;
    if (!hasAnalysis && !candidate) return;

    // Check if already cached for active resume and not forced
    if (!forceRegenerate && plans[duration] && plans[duration].length > 0) {
      return;
    }

    // Check if already generating to prevent duplicate requests
    if (isGeneratingRef.current) return;

    const currentSeq = ++generationSeqRef.current;
    const targetResumeId = activeResumeId;
    const targetAnalysisId = activeResumeAnalysisId;

    isGeneratingRef.current = true;
    setIsLoading(true);
    setApiError('');

    try {
      const targetRole = candidate?.targetRole || 'Technology Professional';
      const verifiedSkills = llmAnalysis?.verifiedSkills?.map(s => s.name) || [];
      const skillGaps = llmAnalysis?.skillGaps?.map(g => g.name) || [];

      const result = await generatePersonalizedRoadmap({
        targetRole,
        durationWeeks: duration,
        analysis: llmAnalysis,
        verifiedSkills,
        skillGaps,
        preferences: candidate,
        resumeAnalysisId: targetAnalysisId,
        generationId: `gen_${targetResumeId}_${duration}_${currentSeq}`
      });

      // Guard: Discard stale response if another generation was launched or resume changed
      if (currentSeq !== generationSeqRef.current || targetResumeId !== activeResumeIdRef.current) {
        console.warn('Discarding stale roadmap response for prior resume/request.');
        return;
      }

      if (result.success && result.roadmap?.weeks) {
        const weeks = result.roadmap.weeks;
        
        // Immediate UI update without full page refresh!
        setPlans(prev => ({
          ...prev,
          [duration]: weeks
        }));
        if (result.recordId) {
          setPersistedRoadmapId(result.recordId);
        }

        const meta = {
          targetRole: result.roadmap.targetRole || targetRole,
          personalizedSummary: result.roadmap.personalizedSummary,
          modelUsed: result.modelUsed || sessionData.modelUsed,
          isPersonalized: true,
          isRagUsed: result.isRagUsed ?? false,
          ragStatus: result.ragStatus || 'unavailable',
          ragSourceCount: result.ragSourceCount || 0,
        };
        setRoadmapMetadata(meta);

        // Store in sessionStorage scoped strictly by targetResumeId
        try {
          sessionStorage.setItem(getCacheKey(targetResumeId, duration), JSON.stringify({ weeks }));
          sessionStorage.setItem(getMetaCacheKey(targetResumeId), JSON.stringify(meta));
        } catch (_) {}

      } else {
        throw new Error('Invalid roadmap payload received from backend.');
      }
    } catch (err) {
      if (currentSeq === generationSeqRef.current) {
        console.error('Roadmap generation error:', err);
        setApiError(err.message || 'Failed to generate personalized roadmap. Please try again.');
      }
    } finally {
      if (currentSeq === generationSeqRef.current) {
        setIsLoading(false);
        isGeneratingRef.current = false;
      }
    }
  }, [hasAnalysis, candidate, llmAnalysis, sessionData.modelUsed, plans, activeResumeId, activeResumeAnalysisId, getCacheKey, getMetaCacheKey]);

  // Effect: Trigger generation only when needed for active resume
  useEffect(() => {
    if (!USE_MOCK_DATA && hasAnalysis) {
      if (!plans[selectedDuration] || plans[selectedDuration].length === 0) {
        loadPersonalizedRoadmap(selectedDuration);
      }
    }
  }, [selectedDuration, hasAnalysis, activeResumeId, plans, loadPersonalizedRoadmap]);

  // Active Plan determination
  const activePlan = useMemo(() => {
    if (plans[selectedDuration] && plans[selectedDuration].length > 0) {
      return plans[selectedDuration];
    }
    // If user requested demo fallback or in mock mode
    if (USE_MOCK_DATA || showDemoFallback) {
      return selectedDuration === 6 ? sampleRoadmapData.sixWeekPlan : sampleRoadmapData.fourWeekPlan;
    }
    return [];
  }, [plans, selectedDuration, showDemoFallback]);

  // Progression Logic: Compute exact status for each week
  // A week is completed ONLY if all its tasks are completed.
  // The first incomplete week is highlighted as 'current'. All subsequent are 'upcoming'.
  const weekProgressionStatuses = useMemo(() => {
    if (!activePlan || activePlan.length === 0) return {};

    const completionMap = {};
    activePlan.forEach((week) => {
      const tasks = week.tasks || [];
      const isComplete = tasks.length > 0 && tasks.every((t) => t.completed);
      completionMap[week.weekNumber] = isComplete;
    });

    let firstIncompleteWeekNum = null;
    for (const week of activePlan) {
      if (!completionMap[week.weekNumber]) {
        firstIncompleteWeekNum = week.weekNumber;
        break;
      }
    }

    const statuses = {};
    activePlan.forEach((week) => {
      if (completionMap[week.weekNumber]) {
        statuses[week.weekNumber] = 'completed';
      } else if (week.weekNumber === firstIncompleteWeekNum) {
        statuses[week.weekNumber] = 'current';
      } else {
        statuses[week.weekNumber] = 'upcoming';
      }
    });

    return statuses;
  }, [activePlan]);

  // Calculate overall progress across all tasks
  const allTasks = useMemo(() => activePlan.flatMap((w) => w.tasks || []), [activePlan]);
  const totalTasks = allTasks.length;
  const completedTasks = allTasks.filter((t) => t.completed).length;
  const overallProgressPct = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
  const isEntireRoadmapCompleted = totalTasks > 0 && completedTasks === totalTasks;

  // Toggle task completion with background SQLite persistence
  const handleToggleTask = async (weekNumber, taskId) => {
    let nextCompleted = false;

    // 1. Optimistic UI update
    setPlans((prev) => {
      const currentList = prev[selectedDuration] || activePlan;
      const updatedList = currentList.map((week) => {
        if (week.weekNumber !== weekNumber) return week;
        return {
          ...week,
          tasks: (week.tasks || []).map((task) => {
            if (task.id !== taskId) return task;
            nextCompleted = !task.completed;
            return { ...task, completed: nextCompleted };
          }),
        };
      });

      // Update cache in sessionStorage scoped to activeResumeId
      try {
        sessionStorage.setItem(getCacheKey(activeResumeId, selectedDuration), JSON.stringify({ weeks: updatedList }));
      } catch (_) {}

      return { ...prev, [selectedDuration]: updatedList };
    });

    // 2. Persist to backend if authenticated
    if (isAuthenticated && persistedRoadmapId) {
      setIsSyncingTask(true);
      setSyncNotice('Saving checklist progress...');
      try {
        await updateRoadmapTaskProgress({
          roadmapId: persistedRoadmapId,
          taskId,
          completed: nextCompleted,
        });
        setSyncNotice('Progress saved to database');
        setTimeout(() => setSyncNotice(''), 2000);
      } catch (err) {
        console.error('Failed to sync task progress to backend:', err);
        setSyncNotice('Sync failed. Changes stored locally.');
        setTimeout(() => setSyncNotice(''), 3000);
      } finally {
        setIsSyncingTask(false);
      }
    }
  };

  // Reset checklist state
  const handleResetProgress = async () => {
    setPlans((prev) => {
      const currentList = prev[selectedDuration] || activePlan;
      const updatedList = currentList.map((week) => ({
        ...week,
        tasks: (week.tasks || []).map((task) => ({ ...task, completed: false })),
      }));

      try {
        sessionStorage.setItem(getCacheKey(activeResumeId, selectedDuration), JSON.stringify({ weeks: updatedList }));
      } catch (_) {}

      return { ...prev, [selectedDuration]: updatedList };
    });

    if (isAuthenticated && persistedRoadmapId) {
      const resetMap = {};
      allTasks.forEach((t) => {
        resetMap[t.id] = false;
      });
      try {
        await updateRoadmapTaskProgress({
          roadmapId: persistedRoadmapId,
          tasksProgress: resetMap,
        });
        setSyncNotice('Checklist reset saved');
        setTimeout(() => setSyncNotice(''), 2000);
      } catch (err) {
        console.warn('Failed to reset task progress in backend:', err);
      }
    }
  };

  return (
    <div className="space-y-8 pb-16">
      
      {/* 1. TOP HEADER & BREADCRUMB */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#EAE3F1] pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <Link to="/dashboard" className="text-xs text-[#7D6B82] hover:text-[#3E1E43] flex items-center gap-1 font-medium">
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Overview</span>
            </Link>
            <span className="text-[#8C7A93]">•</span>
            
            {roadmapMetadata.isPersonalized ? (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-emerald-700" />
                Live AI-Personalized Roadmap ({roadmapMetadata.modelUsed})
              </span>
            ) : (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#EAE3F1] text-[#3E1E43] border border-[#DFD5E7]">
                Sample Demo Roadmap
              </span>
            )}

            {isAuthenticated && persistedRoadmapId ? (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#F3EEF7] text-[#3E1E43] border border-[#DFD0E7] flex items-center gap-1">
                <Cloud className="w-3 h-3 text-[#5C2B64]" />
                Database Synced
              </span>
            ) : null}

            {roadmapMetadata.isRagUsed && (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#F5EDF8] text-[#5C2B64] border border-[#DFD0E7] flex items-center gap-1">
                <BookOpen className="w-3 h-3 text-[#5C2B64]" />
                RAG-Verified ({roadmapMetadata.ragSourceCount} Sources)
              </span>
            )}

          </div>

          <h1 className="font-serif text-2xl sm:text-3xl font-bold text-[#3E1E43]">
            Personalized Career Relaunch Roadmap
          </h1>
          <p className="text-xs sm:text-sm text-[#6B6470] mt-0.5 max-w-2xl leading-relaxed">
            Target Role: <strong className="text-[#3E1E43] font-semibold">{roadmapMetadata.targetRole}</strong>. 
            {" "}{roadmapMetadata.personalizedSummary}
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          {hasAnalysis && (
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => loadPersonalizedRoadmap(selectedDuration, true)}
              disabled={isLoading}
              icon={RefreshCw}
              iconPosition="left"
              title="Regenerate this curriculum with Gemini"
            >
              Regenerate Plan
            </Button>
          )}
          <Link to="/returnships">
            <Button variant="primary" size="sm" icon={Briefcase} iconPosition="left">
              Matched Returnships
            </Button>
          </Link>
        </div>
      </div>

      {/* 2. CELEBRATION BANNER WHEN ALL TASKS COMPLETED */}
      {isEntireRoadmapCompleted && (
        <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-300 flex items-start gap-4 text-emerald-950 animate-in fade-in shadow-xs">
          <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center shrink-0">
            <Trophy className="w-5 h-5 text-emerald-700" />
          </div>
          <div className="space-y-1">
            <h3 className="font-serif font-bold text-base text-emerald-900">
              Curriculum Milestone Completed!
            </h3>
            <p className="text-xs text-emerald-800 leading-relaxed">
              Congratulations! You have completed all checklist actions across every week in this roadmap. Your verified competencies are aligned and you are fully prepared to apply for returnship cohorts.
            </p>
            <div className="pt-2">
              <Link to="/returnships">
                <Button variant="primary" size="sm" icon={ArrowRight} iconPosition="right">
                  Explore Returnship Opportunities Now
                </Button>
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* 3. LIVE MODE NOTICE WHEN NO RESUME HAS BEEN ANALYZED */}
      {!USE_MOCK_DATA && !hasAnalysis && !showDemoFallback && (
        <div className="p-6 rounded-3xl bg-amber-50/80 border border-amber-200 space-y-4 text-amber-950">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h3 className="font-semibold text-sm text-amber-900">
                No Resume Analysis Found for Live Mode
              </h3>
              <p className="text-xs text-amber-800 leading-relaxed max-w-2xl">
                HerTurn designs a personalized curriculum based directly on your documented career history and verified competencies. You can upload your resume to generate your custom roadmap or preview the sample demonstration plan.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link to="/analysis">
              <Button variant="primary" size="sm" icon={FileText} iconPosition="left">
                Start Resume Analysis
              </Button>
            </Link>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setShowDemoFallback(true)}
              className="bg-white"
            >
              Preview Sample Demo Roadmap
            </Button>
          </div>
        </div>
      )}

      {/* 4. API ERROR BANNER WITH RETRY */}
      {apiError && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-950 flex items-start justify-between gap-4 text-xs">
          <div className="flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-rose-900">Failed to Generate Personalized Roadmap</p>
              <p className="text-rose-800 mt-0.5">{apiError}</p>
            </div>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => loadPersonalizedRoadmap(selectedDuration, true)}
            icon={RefreshCw}
            iconPosition="left"
            className="shrink-0 bg-white text-rose-900 border-rose-300"
          >
            Retry
          </Button>
        </div>
      )}

      {/* 5. PROGRESS BANNER & DURATION SELECTOR */}
      <div className="bg-white rounded-2xl border border-[#EAE3F1] p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          
          {/* Left: Overall Completion stats */}
          <div className="space-y-2 flex-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[#3E1E43] flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                Overall Roadmap Progress
              </span>
              <span className="text-sm font-bold text-[#3E1E43]">
                {completedTasks} of {totalTasks} Tasks Completed ({overallProgressPct}%)
              </span>
            </div>

            <div className="w-full bg-[#FAF7F2] h-2.5 rounded-full overflow-hidden border border-[#EAE3F1]">
              <div 
                className="bg-gradient-to-r from-[#3E1E43] to-[#5C2B64] h-full rounded-full transition-all duration-300"
                style={{ width: `${overallProgressPct}%` }}
              />
            </div>

            <div className="flex items-center justify-between text-xs text-[#6B6470] pt-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span>Interactive checklist: Mark tasks completed to advance through the weekly sprint</span>
                {syncNotice && (
                  <span className="text-[11px] text-[#5C2B64] font-medium animate-pulse flex items-center gap-1 bg-[#F5EDF8] px-2 py-0.5 rounded-full border border-[#EAE3F1]">
                    <Cloud className="w-3 h-3 text-[#5C2B64]" /> {syncNotice}
                  </span>
                )}
              </div>
              <button 
                type="button" 
                onClick={handleResetProgress}
                className="text-[11px] text-[#8C7A93] hover:text-[#3E1E43] flex items-center gap-1 cursor-pointer"
              >
                <RotateCcw className="w-3 h-3" />
                Reset Progress
              </button>
            </div>
          </div>

          {/* Right: Duration toggle (4 Weeks or 6 Weeks) */}
          <div className="bg-[#FAF7F2] p-3 rounded-2xl border border-[#EAE3F1] shrink-0">
            <span className="block text-[11px] font-bold text-[#7D6B82] uppercase tracking-wider mb-2 text-center">
              Pacing Duration
            </span>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => setSelectedDuration(4)}
                disabled={isLoading}
                className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
                  selectedDuration === 4
                    ? 'bg-[#3E1E43] text-white shadow-xs'
                    : 'bg-white text-[#5C5560] border border-[#EAE3F1] hover:border-[#3E1E43]'
                } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                4-Week Sprint (Intensive)
              </button>
              <button
                type="button"
                onClick={() => setSelectedDuration(6)}
                disabled={isLoading}
                className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
                  selectedDuration === 6
                    ? 'bg-[#3E1E43] text-white shadow-xs'
                    : 'bg-white text-[#5C5560] border border-[#EAE3F1] hover:border-[#3E1E43]'
                } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                6-Week Flexible (Balanced)
              </button>
            </div>
          </div>

        </div>
      </div>

      {/* 6. SKELETON LOADING UI (FAST FEEDBACK WHILE GENERATING) */}
      {(isLoading || (!showDemoFallback && hasAnalysis && (!activePlan || activePlan.length === 0))) ? (
        <div className="space-y-4">
          <div className="p-4 rounded-2xl bg-purple-50/80 border border-purple-200 flex items-center gap-3 text-xs text-[#3E1E43] animate-pulse shadow-xs">
            <Loader2 className="w-4 h-4 animate-spin text-[#3E1E43]" />
            <span className="font-medium">
              Creating your personalized career roadmap for <strong className="text-[#3E1E43] font-bold">{roadmapMetadata.targetRole || candidate?.targetRole || 'your target role'}</strong>...
            </span>
          </div>

          {/* 4/6 Skeleton Cards */}
          {Array.from({ length: selectedDuration }).map((_, i) => (
            <div key={i} className="bg-white rounded-2xl border border-[#EAE3F1] p-6 space-y-4 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-[#EAE3F1]" />
                  <div className="space-y-2">
                    <div className="h-4 w-48 bg-[#EAE3F1] rounded-md" />
                    <div className="h-3 w-64 bg-[#FAF7F2] rounded-md" />
                  </div>
                </div>
                <div className="h-4 w-20 bg-[#EAE3F1] rounded-md" />
              </div>
              <div className="space-y-2 pt-2 border-t border-[#EAE3F1]">
                <div className="h-8 bg-[#FAF7F2] rounded-xl" />
                <div className="h-8 bg-[#FAF7F2] rounded-xl" />
              </div>
            </div>
          ))}
        </div>
      ) : activePlan.length > 0 ? (
        /* 7. WEEK-BY-WEEK ACCORDION TIMELINE WITH PROGRESSION STATUS */
        <div className="space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="font-serif font-bold text-xl text-[#3E1E43]">
              {selectedDuration}-Week Step-by-Step Curriculum
            </h2>
            <span className="text-xs text-[#7D6B82]">
              {activePlan.length} Structured Modules
            </span>
          </div>

          <div className="space-y-4">
            {activePlan.map((week, idx) => {
              const status = weekProgressionStatuses[week.weekNumber] || (idx === 0 ? 'current' : 'upcoming');
              return (
                <WeekCard
                  key={`${selectedDuration}-${week.weekNumber}`}
                  week={week}
                  onToggleTask={handleToggleTask}
                  progressionStatus={status}
                  defaultExpanded={status === 'current' || idx === 0}
                />
              );
            })}
          </div>
        </div>
      ) : null}

      {/* 8. MENTORSHIP & INTERVIEW READINESS CALLOUT */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-[#FAF7F2] via-white to-[#F5F0F9] border border-[#EAE3F1] flex flex-col sm:flex-row items-center justify-between gap-6">
        <div className="space-y-1">
          <h3 className="font-serif font-bold text-lg text-[#3E1E43]">
            Ready to test your answers in mock interviews?
          </h3>
          <p className="text-xs text-[#5C5560] max-w-xl">
            Our returnee playbook helps you explain career breaks with confidence. Discover supportive partner employers actively hiring returnees right now.
          </p>
        </div>

        <Link to="/returnships" className="shrink-0">
          <Button variant="secondary" size="md">
            Browse Fellowship Openings
          </Button>
        </Link>
      </div>

    </div>
  );
}
