import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Sparkles, 
  ArrowRight, 
  CheckCircle2, 
  AlertTriangle, 
  TrendingUp, 
  FileText, 
  Compass, 
  Briefcase, 
  User, 
  Clock, 
  MapPin, 
  Calendar,
  Layers,
  ChevronRight,
  Info,
  ShieldCheck,
  BookOpen,
  GraduationCap,
  Database,
  History,
  RotateCcw
} from 'lucide-react';
import Button from '../components/Button';
import { sampleAnalysisData } from '../data/demoAnalysis';
import { useAuth } from '../context/AuthContext';
import { fetchCandidateAnalyses } from '../services/api';

export default function AnalysisDashboard() {
  const location = useLocation();
  const { isAuthenticated, user } = useAuth();

  // Retrieve stored session from sessionStorage if available
  let storedSession = null;
  try {
    const raw = sessionStorage.getItem('herturn_session');
    if (raw) storedSession = JSON.parse(raw);
  } catch (_) {}

  // USER ISOLATION GUARD:
  // If user is authenticated, ensure storedSession strictly belongs to this user!
  // If it belongs to a previous user (or different email), PURGE IT IMMEDIATELY!
  if (isAuthenticated && user && storedSession) {
    const sessionEmail = storedSession.candidate?.email;
    const sessionUserId = storedSession.userId || storedSession.candidate?.userId;
    const isOwner = (sessionEmail && sessionEmail.toLowerCase() === user.email.toLowerCase()) ||
                    (sessionUserId && sessionUserId === user.id);
    if (!isOwner) {
      try {
        sessionStorage.removeItem('herturn_session');
        Object.keys(sessionStorage).forEach((k) => {
          if (k.startsWith('herturn_roadmap_')) sessionStorage.removeItem(k);
        });
      } catch (_) {}
      storedSession = null;
    }
  }

  // Navigation state ownership guard
  const isNavValid = !isAuthenticated || !user || !location.state?.candidate?.email ||
                     (location.state.candidate.email.toLowerCase() === user.email.toLowerCase());
  const effectiveNavState = isNavValid ? location.state : null;

  const initialCandidate = effectiveNavState?.candidate || storedSession?.candidate || (isAuthenticated && user ? {
    fullName: user.fullName || 'Candidate',
    email: user.email,
    targetRole: user.candidateProfile?.targetRole || 'Technology Professional',
    previousRole: 'Tech Professional',
    breakDuration: 'Career Pause',
    preferredWorkMode: user.candidateProfile?.workMode || 'Hybrid',
    resumeFileName: null,
    resumeAnalysisId: null,
    resumeId: null,
  } : null);

  const initialLiveParsed = effectiveNavState?.isLiveParsed ?? storedSession?.isLiveParsed ?? false;
  const initialLiveAnalyzed = effectiveNavState?.isLiveAnalyzed ?? storedSession?.isLiveAnalyzed ?? false;
  const initialWordCount = effectiveNavState?.extractedWordCount ?? storedSession?.extractedWordCount ?? 0;
  const initialModel = effectiveNavState?.modelUsed || storedSession?.modelUsed || 'gemini-2.5-flash';
  const initialLlmAnalysis = effectiveNavState?.llmAnalysis || storedSession?.llmAnalysis || null;

  // Saved analyses from database
  const [savedAnalyses, setSavedAnalyses] = useState([]);
  const [selectedRecordId, setSelectedRecordId] = useState(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  // Active state for analysis details (allows restoring from backend or switching history items)
  const [activeAnalysis, setActiveAnalysis] = useState(initialLlmAnalysis);
  const [activeCandidateMeta, setActiveCandidateMeta] = useState(initialCandidate);
  const [activeModel, setActiveModel] = useState(initialModel);
  const [activeWordCount, setActiveWordCount] = useState(initialWordCount);
  const [isLiveActive, setIsLiveActive] = useState(initialLiveAnalyzed);

  // Helper to apply a saved record from the database
  const applyRecord = (record) => {
    if (!record) return;
    const raw = record.structuredAnalysis || {};
    const normalized = {
      ...raw,
      verifiedSkills: raw.verifiedSkills || raw.verified_skills || [],
      skillGaps: raw.skillGaps || raw.skill_gaps || [],
      transferableStrengths: raw.transferableStrengths || raw.transferable_strengths || [],
      suggestedNextSteps: raw.suggestedNextSteps || raw.suggested_next_steps || [],
      extractedExperience: raw.extractedExperience || raw.extracted_experience || [],
      extractedEducation: raw.extractedEducation || raw.extracted_education || [],
      resumeSummary: raw.resumeSummary || raw.resume_summary || '',
      evidenceNotes: raw.evidenceNotes || raw.evidence_notes || '',
    };
    setActiveAnalysis(normalized);
    setActiveModel(record.modelUsed || 'gemini-2.5-flash');
    setActiveWordCount(record.wordCount || 0);
    setIsLiveActive(true);
    setSelectedRecordId(record.id);

    const updatedCandidate = {
      fullName: user?.fullName || normalized.candidateName || activeCandidateMeta?.fullName || sampleAnalysisData.candidate.fullName,
      email: user?.email || activeCandidateMeta?.email || sampleAnalysisData.candidate.email,
      targetRole: record.targetRole || normalized.targetRole || activeCandidateMeta?.targetRole || sampleAnalysisData.candidate.targetRole,
      previousRole: activeCandidateMeta?.previousRole || 'Software Engineering / Tech Professional',
      breakDuration: normalized.careerBreakDuration || activeCandidateMeta?.breakDuration || 'Prior Career Break',
      preferredWorkMode: activeCandidateMeta?.preferredWorkMode || 'Hybrid / Flexible',
      resumeFileName: record.fileName || activeCandidateMeta?.resumeFileName || 'Saved_Resume.pdf',
      resumeAnalysisId: record.id,
      resumeId: `analysis_${record.id}`,
    };
    setActiveCandidateMeta(updatedCandidate);

    try {
      sessionStorage.setItem('herturn_session', JSON.stringify({
        userId: user?.id,
        candidate: updatedCandidate,
        llmAnalysis: normalized,
        resumeAnalysisId: record.id,
        resumeId: `analysis_${record.id}`,
        isLiveAnalyzed: true,
        modelUsed: record.modelUsed || 'gemini-2.5-flash',
        extractedWordCount: record.wordCount || 0,
        isLiveParsed: true
      }));
    } catch (_) {}
  };

  // Fetch candidate's saved analyses from backend when authenticated
  useEffect(() => {
    if (!isAuthenticated || !user) return;
    let isMounted = true;
    setIsLoadingHistory(true);

    fetchCandidateAnalyses()
      .then(res => {
        if (!isMounted) return;
        const items = res?.analyses || res?.items || [];
        setSavedAnalyses(items);

        if (items.length > 0) {
          // If the active analysis doesn't belong to the current user or is not set, apply the latest saved analysis for this user!
          const currentBelongsToUser = activeAnalysis && activeCandidateMeta?.email && 
                                       (activeCandidateMeta.email.toLowerCase() === user.email.toLowerCase());
          if (!currentBelongsToUser) {
            applyRecord(items[0]);
          } else {
            const matched = items.find(it => it.id === selectedRecordId) || items[0];
            setSelectedRecordId(matched.id);
          }
        } else {
          // Authenticated user has NO saved analyses yet!
          // Clear activeAnalysis so NO prior user's resume is displayed!
          setActiveAnalysis(null);
          setIsLiveActive(false);
          setSelectedRecordId(null);
          setActiveCandidateMeta({
            fullName: user.fullName || 'Candidate',
            email: user.email,
            targetRole: user.candidateProfile?.targetRole || 'Technology Professional',
            previousRole: 'Tech Professional',
            breakDuration: 'Career Pause',
            preferredWorkMode: user.candidateProfile?.workMode || 'Hybrid',
            resumeFileName: null,
            resumeAnalysisId: null,
            resumeId: null,
          });
        }
      })
      .catch(err => {
        console.warn('Could not fetch saved analyses history:', err);
      })
      .finally(() => {
        if (isMounted) setIsLoadingHistory(false);
      });

    return () => { isMounted = false; };
  }, [isAuthenticated, user?.id, user?.email]);

  // Merge candidate metadata
  const candidate = (isAuthenticated && user) ? {
    ...sampleAnalysisData.candidate,
    ...(activeCandidateMeta || {}),
    fullName: user.fullName || activeCandidateMeta?.fullName || 'Candidate',
    email: user.email,
    targetRole: activeCandidateMeta?.targetRole || user.candidateProfile?.targetRole || 'Technology Professional',
    preferredWorkMode: activeCandidateMeta?.preferredWorkMode || user.candidateProfile?.workMode || 'Hybrid',
    resumeFileName: activeCandidateMeta?.resumeFileName || (selectedRecordId ? 'Saved_Resume.pdf' : null),
    resumeAnalysisId: activeCandidateMeta?.resumeAnalysisId || selectedRecordId || null,
    resumeId: activeCandidateMeta?.resumeId || (selectedRecordId ? `analysis_${selectedRecordId}` : null),
  } : (activeCandidateMeta ? {
    ...sampleAnalysisData.candidate,
    ...activeCandidateMeta,
    resumeAnalysisId: activeCandidateMeta.resumeAnalysisId || selectedRecordId || location.state?.resumeAnalysisId || storedSession?.resumeAnalysisId || null,
    resumeId: activeCandidateMeta.resumeId || location.state?.resumeId || storedSession?.resumeId || (selectedRecordId ? `analysis_${selectedRecordId}` : null),
    fullName: activeCandidateMeta.fullName || sampleAnalysisData.candidate.fullName,
    email: activeCandidateMeta.email || sampleAnalysisData.candidate.email,
    resumeFileName: activeCandidateMeta.resumeFileName || sampleAnalysisData.candidate.resumeFileName,
  } : sampleAnalysisData.candidate);

  // Adapt data: use live LLM fields if available, otherwise fallback cleanly to demoAnalysis
  const isUsingRealAI = Boolean(isLiveActive && activeAnalysis);
  const isLiveAnalyzed = isLiveActive;
  const llmAnalysis = activeAnalysis;
  const modelUsed = activeModel;
  const extractedWordCount = activeWordCount;
  const isLiveParsed = initialLiveParsed || isUsingRealAI;

  // Safe candidate metadata accessors
  const candidateName = candidate?.fullName || 'Candidate';
  const candidateFirstName = candidateName.split(' ')[0] || 'Candidate';
  const candidateInitials = candidateName.split(' ').filter(Boolean).map(n => n[0]).join('').slice(0, 2) || 'HT';
  const targetRole = candidate?.targetRole || 'Technology Professional';
  const previousRole = candidate?.previousRole || 'Tech Professional';
  const breakDuration = candidate?.breakDuration || 'Prior Career Pause';
  const preferredWorkMode = candidate?.preferredWorkMode || candidate?.workMode || 'Hybrid / Remote';
  const resumeFileName = candidate?.resumeFileName || 'Resume.pdf';
  const candidateEmail = candidate?.email || '';

  const existingSkills = isUsingRealAI && llmAnalysis.verifiedSkills?.length > 0
    ? llmAnalysis.verifiedSkills.map(s => ({
        name: s.name,
        category: s.category || 'Verified',
        evidence: s.evidence,
        strength: 'Documented'
      }))
    : sampleAnalysisData.skillBreakdown.existing;

  const skillsToStrengthen = isUsingRealAI && llmAnalysis.skillGaps?.length > 0
    ? llmAnalysis.skillGaps.map(g => ({
        name: g.name,
        category: g.category || 'Target Competency',
        importance: g.importance || 'High',
        gapDescription: g.explanation,
        action: g.recommendedAction
      }))
    : sampleAnalysisData.skillBreakdown.toStrengthen;

  const nextSteps = isUsingRealAI && llmAnalysis.suggestedNextSteps?.length > 0
    ? llmAnalysis.suggestedNextSteps.map((s, idx) => ({
        action: s.action,
        link: idx === 1 ? '/returnships' : '/roadmap',
        detail: s.detail
      }))
    : sampleAnalysisData.recommendedNextSteps;

  return (
    <div className="space-y-8 pb-12">
      
      {/* 1. STATUS BANNER: HONEST LIVE VS DEMO TRANSPARENCY */}
      {isUsingRealAI ? (
        <div className="p-4 sm:p-5 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-start gap-3.5 text-xs text-emerald-950 animate-in fade-in shadow-xs">
          <div className="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center shrink-0 mt-0.5">
            <Sparkles className="w-4 h-4 text-emerald-700" />
          </div>
          <div className="space-y-1.5 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-bold text-sm text-emerald-900">
                Live Google Gemini Analysis Active
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
                Model: {modelUsed || 'gemini-2.5-flash'}
              </span>
              <span className="text-emerald-700 text-[11px]">
                • {extractedWordCount || 0} words parsed from resume
              </span>
            </div>
            <p className="text-emerald-800 leading-relaxed">
              {llmAnalysis.resumeSummary || "All verified skills and gaps below were extracted factually from your uploaded resume without bias or gap penalties."}
            </p>
            {llmAnalysis.evidenceNotes && (
              <div className="pt-1.5 text-[11px] text-emerald-900 border-t border-emerald-200/80 font-medium">
                <strong>Evidence & Objectivity Note:</strong> {llmAnalysis.evidenceNotes}
              </div>
            )}
          </div>
        </div>
      ) : isLiveParsed ? (
        <div className="p-4 rounded-2xl bg-sky-50 border border-sky-200 flex items-start gap-3 text-xs text-sky-950 animate-in fade-in">
          <CheckCircle2 className="w-5 h-5 text-sky-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold text-sm block">
              Resume Document Ingested via FastAPI ({extractedWordCount || 0} words extracted)
            </span>
            <p className="text-sky-800 leading-relaxed">
              Your resume text was extracted using PyMuPDF/python-docx. Configure <code>GEMINI_API_KEY</code> in <code>backend/.env</code> to unlock live LLM analysis. The cards below currently showcase the baseline demonstration profile.
            </p>
          </div>
        </div>
      ) : (
        <div className="p-3.5 rounded-2xl bg-[#FAF7F2] border border-[#EAE3F1] flex items-center justify-between text-xs text-[#6B6470]">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-[#3E1E43]" />
            <span>Demonstration mode active. Showing curated sample candidate profile and recommendations.</span>
          </div>
          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-[#EAE3F1] text-[#3E1E43]">
            Sample Mode
          </span>
        </div>
      )}

      {/* 1b. SAVED ANALYSES HISTORY BAR (WHEN AUTHENTICATED WITH PERSISTENT RECORDS) */}
      {isAuthenticated && savedAnalyses.length > 0 && (
        <div className="p-3.5 bg-white rounded-2xl border border-[#EAE3F1] shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs animate-in fade-in">
          <div className="flex items-center gap-2.5 text-[#3E1E43]">
            <div className="w-7 h-7 rounded-lg bg-[#FAF7F2] border border-[#EAE3F1] flex items-center justify-center text-[#7D6B82]">
              <History className="w-4 h-4 text-[#3E1E43]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm text-[#2B282C]">
                  Saved Resume Evaluations ({savedAnalyses.length})
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-50 text-purple-900 border border-purple-200">
                  Account Synced
                </span>
              </div>
              <span className="text-[11px] text-[#7D6B82]">
                Switch between your previously analyzed resumes to inspect specific competency gaps
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <label htmlFor="history-select" className="text-[11px] text-[#7D6B82] font-medium shrink-0">
              Active Evaluation:
            </label>
            <select
              id="history-select"
              value={selectedRecordId || ''}
              onChange={(e) => {
                const recId = Number(e.target.value);
                const rec = savedAnalyses.find(r => r.id === recId);
                if (rec) applyRecord(rec);
              }}
              className="text-xs bg-[#FAF7F2] border border-[#EAE3F1] text-[#3E1E43] font-medium rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#3E1E43]"
            >
              {savedAnalyses.map((rec) => (
                <option key={rec.id} value={rec.id}>
                  #{rec.id} — {rec.targetRole} ({rec.fileName || 'Resume'}) • {new Date(rec.createdAt).toLocaleDateString()}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* 2. WELCOME HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#EAE3F1] pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase font-bold tracking-widest text-[#7D6B82]">
              Resume Analysis & Profile
            </span>
            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
              isUsingRealAI
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-[#EAE3F1] text-[#3E1E43] border-[#DFD5E7]'
            }`}>
              {isUsingRealAI ? 'Live AI Analysis' : 'Sample Candidate View'}
            </span>
            {selectedRecordId && (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold border bg-purple-50 text-purple-900 border-purple-200 flex items-center gap-1">
                <Database className="w-3 h-3 text-purple-700" />
                Record #{selectedRecordId}
              </span>
            )}
          </div>
          <h1 className="font-serif text-2xl sm:text-3xl font-bold text-[#3E1E43] mt-1">
            Welcome back, {candidateFirstName}!
          </h1>
          <p className="text-xs sm:text-sm text-[#6B6470] mt-0.5">
            Your career relaunch plan for <span className="font-semibold text-[#3E1E43]">{targetRole}</span> is taking shape.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/roadmap" state={{ candidate, llmAnalysis, isLiveAnalyzed, targetRole, resumeAnalysisId: candidate?.resumeAnalysisId || selectedRecordId, resumeId: candidate?.resumeId }}>
            <Button variant="primary" size="sm" icon={Compass} iconPosition="left">
              View Learning Roadmap
            </Button>
          </Link>
          <Link to="/returnships">
            <Button variant="outline" size="sm" icon={Briefcase} iconPosition="left">
              Returnships
            </Button>
          </Link>
        </div>
      </div>

      {/* 3. PROFILE SUMMARY CARD */}
      <div className="bg-white rounded-2xl border border-[#EAE3F1] p-6 shadow-xs">
        <div className="flex items-center justify-between pb-4 border-b border-[#EAE3F1] mb-5">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#3E1E43] to-[#5C2B64] text-white flex items-center justify-center font-serif text-lg font-bold shadow-xs">
              {candidateInitials}
            </div>
            <div>
              <h2 className="font-serif font-bold text-lg text-[#2B282C] leading-tight">
                {candidateName}
              </h2>
              <div className="text-xs text-[#7D6B82] flex items-center gap-2 mt-0.5">
                <span>{candidateEmail}</span>
                {candidateEmail && <span>•</span>}
                <span className="flex items-center gap-1 text-[#3E1E43] font-medium">
                  <FileText className="w-3.5 h-3.5" />
                  {resumeFileName}
                </span>
              </div>
            </div>
          </div>

          <Link to="/onboarding">
            <span className="text-xs font-semibold text-[#3E1E43] hover:underline cursor-pointer">
              Edit Preferences
            </span>
          </Link>
        </div>

        {/* Profile Attributes Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div className="bg-[#FAF7F2] p-3 rounded-xl border border-[#EAE3F1]">
            <span className="text-[#8C7A93] block text-[10px] uppercase font-bold tracking-wider">Target Direction</span>
            <span className="font-semibold text-[#3E1E43] mt-0.5 block truncate">{targetRole}</span>
          </div>

          <div className="bg-[#FAF7F2] p-3 rounded-xl border border-[#EAE3F1]">
            <span className="text-[#8C7A93] block text-[10px] uppercase font-bold tracking-wider">Previous Background</span>
            <span className="font-semibold text-[#2B282C] mt-0.5 block truncate">{previousRole}</span>
          </div>

          <div className="bg-[#FAF7F2] p-3 rounded-xl border border-[#EAE3F1]">
            <span className="text-[#8C7A93] block text-[10px] uppercase font-bold tracking-wider">Career Pause</span>
            <span className="font-semibold text-[#2B282C] mt-0.5 block truncate">{breakDuration}</span>
          </div>

          <div className="bg-[#FAF7F2] p-3 rounded-xl border border-[#EAE3F1]">
            <span className="text-[#8C7A93] block text-[10px] uppercase font-bold tracking-wider">Preferred Setup</span>
            <span className="font-semibold text-[#2B282C] mt-0.5 block truncate">{preferredWorkMode}</span>
          </div>
        </div>
      </div>

      {/* 4. EXTRACTED WORK HISTORY & EDUCATION (WHEN AVAILABLE VIA LLM) */}
      {isUsingRealAI && (llmAnalysis.extractedExperience?.length > 0 || llmAnalysis.extractedEducation?.length > 0) && (
        <div className="bg-white rounded-2xl border border-[#EAE3F1] p-6 shadow-xs space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-[#EAE3F1]">
            <div className="flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-[#3E1E43]" />
              <h3 className="font-serif font-bold text-lg text-[#2B282C]">
                Extracted Career & Academic Baseline
              </h3>
            </div>
            <span className="text-[11px] font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
              Extracted from Resume
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
            {/* Experience list */}
            {llmAnalysis.extractedExperience?.length > 0 && (
              <div className="space-y-3">
                <h4 className="font-bold uppercase tracking-wider text-[#7D6B82] text-[10px]">
                  Documented Employment History
                </h4>
                {llmAnalysis.extractedExperience.map((exp, i) => (
                  <div key={i} className="p-3.5 rounded-xl bg-[#FAF7F2] border border-[#EAE3F1] space-y-1">
                    <div className="flex items-center justify-between font-bold text-[#2B282C]">
                      <span>{exp.title}</span>
                      {exp.duration && <span className="text-[11px] font-normal text-[#7D6B82]">{exp.duration}</span>}
                    </div>
                    <div className="text-[#3E1E43] font-medium">{exp.organization}</div>
                    {exp.highlights?.length > 0 && (
                      <ul className="list-disc list-inside text-[#554E59] text-[11px] pt-1 space-y-0.5">
                        {exp.highlights.slice(0, 2).map((h, hi) => (
                          <li key={hi} className="truncate">{h}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Education list */}
            {llmAnalysis.extractedEducation?.length > 0 && (
              <div className="space-y-3">
                <h4 className="font-bold uppercase tracking-wider text-[#7D6B82] text-[10px]">
                  Credentials & Education
                </h4>
                {llmAnalysis.extractedEducation.map((edu, i) => (
                  <div key={i} className="p-3.5 rounded-xl bg-[#FAF7F2] border border-[#EAE3F1] space-y-1">
                    <div className="flex items-center gap-2 font-bold text-[#2B282C]">
                      <GraduationCap className="w-4 h-4 text-[#3E1E43]" />
                      <span>{edu.degree}</span>
                    </div>
                    <div className="text-[#554E59]">{edu.institution} {edu.year ? `(${edu.year})` : ''}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 5. SKILLS & GAP CATEGORIES */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Left Column: Verified Skills Explicitly Found */}
        <div className="bg-white rounded-2xl border border-[#EAE3F1] p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#EAE3F1]">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-serif font-bold text-base text-[#2B282C]">
                    Skills Explicitly in Resume
                  </h3>
                  <span className="text-[11px] text-[#7D6B82]">
                    {isUsingRealAI ? 'Verified by Gemini from resume text' : 'Verified from prior experience'}
                  </span>
                </div>
              </div>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
                {existingSkills.length} Identified
              </span>
            </div>

            <p className="text-xs text-[#6B6470] mb-4">
              These capabilities are factually verified from your documented work history:
            </p>

            <div className="space-y-2.5">
              {existingSkills.map((skill, idx) => (
                <div 
                  key={idx}
                  className="p-3 rounded-xl bg-[#FAF7F2] border border-[#EAE3F1] text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span className="font-semibold text-[#2B282C]">{skill.name}</span>
                    </div>
                    <span className="text-[11px] px-2 py-0.5 rounded-md bg-white border border-[#EAE3F1] text-[#7D6B82] font-medium">
                      {skill.category}
                    </span>
                  </div>
                  {skill.evidence && (
                    <p className="text-[11px] text-[#6B6470] pl-6 italic">
                      "{skill.evidence}"
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-[#EAE3F1] text-[11px] text-[#7D6B82] flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Factual grounding: Skills not found in the resume are marked absent rather than assumed.</span>
          </div>
        </div>

        {/* Right Column: Skill Gaps To Strengthen */}
        <div className="bg-white rounded-2xl border border-[#EAE3F1] p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#EAE3F1]">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-700 border border-amber-200 flex items-center justify-center">
                  <TrendingUp className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-serif font-bold text-base text-[#2B282C]">
                    Skills to Strengthen for Target Role
                  </h3>
                  <span className="text-[11px] text-[#7D6B82]">
                    High-impact tools to brush up for {targetRole}
                  </span>
                </div>
              </div>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                {skillsToStrengthen.length} Recommendations
              </span>
            </div>

            <p className="text-xs text-[#6B6470] mb-4">
              Bridging these competencies in your weekly learning sprint will ensure full alignment with modern hiring standards:
            </p>

            <div className="space-y-3">
              {skillsToStrengthen.map((gap, idx) => (
                <div 
                  key={idx}
                  className="p-3.5 rounded-xl border border-amber-200/80 bg-amber-50/20 space-y-1.5"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-[#3E1E43]">{gap.name}</span>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-white text-amber-800 border border-amber-200">
                      {gap.importance}
                    </span>
                  </div>
                  <p className="text-xs text-[#5C5560]">
                    {gap.gapDescription}
                  </p>
                  {gap.action && (
                    <p className="text-[11px] font-medium text-[#3E1E43] pt-0.5">
                      → Action: {gap.action}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-[#EAE3F1]">
            <Link to="/roadmap" state={{ candidate, llmAnalysis, isLiveAnalyzed, targetRole, resumeAnalysisId: candidate?.resumeAnalysisId || selectedRecordId, resumeId: candidate?.resumeId }}>
              <Button variant="secondary" size="sm" className="w-full text-xs" icon={ArrowRight} iconPosition="right">
                Practice These in Your Learning Roadmap
              </Button>
            </Link>
          </div>
        </div>

      </div>

      {/* 6. RECOMMENDED ACTIONS / NEXT STEPS */}
      <div className="bg-[#3E1E43] rounded-2xl text-white p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <span className="text-xs uppercase font-bold tracking-wider text-[#F6D6C6]">
              Action Plan
            </span>
            <h3 className="font-serif font-bold text-xl sm:text-2xl mt-0.5">
              Recommended Next Actions
            </h3>
          </div>
          <span className="text-xs text-[#E8DDF2]">
            Keep your momentum rolling
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {nextSteps.map((rec, idx) => (
            <Link 
              key={idx}
              to={rec.link}
              state={rec.link === '/roadmap' ? { candidate, llmAnalysis, isLiveAnalyzed, targetRole, resumeAnalysisId: candidate?.resumeAnalysisId || selectedRecordId, resumeId: candidate?.resumeId } : undefined}
              className="bg-white/10 hover:bg-white/15 border border-white/20 rounded-xl p-4 transition-all flex flex-col justify-between group"
            >
              <div className="space-y-1.5">
                <h4 className="text-sm font-semibold text-white group-hover:text-[#F6D6C6] transition-colors flex items-center justify-between">
                  <span>{rec.action}</span>
                  <ChevronRight className="w-4 h-4 text-white/60 group-hover:translate-x-1 transition-transform" />
                </h4>
                <p className="text-xs text-[#E8DDF2] leading-relaxed">
                  {rec.detail}
                </p>
              </div>
            </Link>
          ))}
        </div>
      </div>

    </div>
  );
}
