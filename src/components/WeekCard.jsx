import React, { useState, useEffect } from 'react';
import { 
  ChevronDown, 
  ChevronUp, 
  CheckCircle2, 
  Circle, 
  Clock, 
  BookOpen, 
  ExternalLink,
  Target,
  Sparkles,
  ArrowRight,
  Flag
} from 'lucide-react';

export default function WeekCard({ 
  week, 
  onToggleTask,
  progressionStatus = 'upcoming', // 'completed' | 'current' | 'upcoming'
  defaultExpanded = true 
}) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  // Sync expanded state if progression becomes 'current'
  useEffect(() => {
    if (progressionStatus === 'current') {
      setExpanded(true);
    }
  }, [progressionStatus]);

  const tasks = week.tasks || [];
  const completedCount = tasks.filter((t) => t.completed).length;
  const totalCount = tasks.length;
  const isAllComplete = totalCount > 0 && completedCount === totalCount;
  const progressPct = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  const isCurrent = progressionStatus === 'current';
  const isCompleted = progressionStatus === 'completed' || isAllComplete;

  return (
    <div className={`rounded-2xl border transition-all duration-200 overflow-hidden ${
      isCompleted
        ? 'border-emerald-300 bg-emerald-50/15 border-l-4 border-l-emerald-600 shadow-xs'
        : isCurrent
        ? 'border-[#3E1E43] ring-1 ring-[#3E1E43]/20 border-l-4 border-l-[#3E1E43] bg-white shadow-md'
        : 'border-[#EAE3F1] bg-[#FAF7F2]/40 hover:border-[#D5C2E2] shadow-xs'
    }`}>
      {/* Week Header */}
      <div 
        onClick={() => setExpanded(!expanded)}
        className="p-5 sm:p-6 flex items-start sm:items-center justify-between gap-4 cursor-pointer select-none bg-gradient-to-r from-white via-white to-[#FAF7F2]"
      >
        <div className="flex items-start sm:items-center gap-4 min-w-0">
          {/* Week number badge */}
          <div className={`w-12 h-12 rounded-2xl flex flex-col items-center justify-center shrink-0 border font-serif font-bold ${
            isCompleted
              ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
              : isCurrent
              ? 'bg-[#3E1E43] text-white border-[#3E1E43] shadow-xs'
              : 'bg-[#EAE3F1] text-[#3E1E43] border-[#DFD5E7]'
          }`}>
            <span className={`text-[10px] uppercase tracking-wider font-sans font-bold -mb-1 ${
              isCurrent ? 'text-purple-200' : 'text-[#6E4F74]'
            }`}>
              Week
            </span>
            <span className="text-lg leading-tight">{week.weekNumber}</span>
          </div>

          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-serif font-bold text-lg text-[#3E1E43] truncate">
                Week {week.weekNumber}: {week.title}
              </h3>
              
              {/* Progression Status Badges */}
              {isCompleted ? (
                <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
                  Completed
                </span>
              ) : isCurrent ? (
                <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-purple-100 text-[#3E1E43] border border-purple-300 flex items-center gap-1 animate-pulse">
                  <Sparkles className="w-3.5 h-3.5 text-[#5C2B64]" />
                  Current Active Week
                </span>
              ) : (
                <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-[#EAE3F1] text-[#6B6470] border border-[#DFD5E7]">
                  Upcoming Milestone
                </span>
              )}
            </div>

            <p className="text-xs text-[#6B6470] mt-0.5 max-w-xl truncate sm:whitespace-normal">
              {week.theme}
            </p>
          </div>
        </div>

        {/* Right side status & expand indicator */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="hidden sm:flex flex-col items-end text-right">
            <span className={`text-xs font-semibold ${isCompleted ? 'text-emerald-700' : 'text-[#3E1E43]'}`}>
              {completedCount} of {totalCount} Tasks Done ({progressPct}%)
            </span>
            <span className="text-[11px] text-[#8C7A93] flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {week.commitment || '6–8 hours'}
            </span>
          </div>
          <div className="w-8 h-8 rounded-full bg-[#FAF7F2] border border-[#EAE3F1] flex items-center justify-center text-[#3E1E43]">
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </div>
      </div>

      {/* Week Progress Bar inside Card */}
      <div className="h-1.5 w-full bg-[#FAF7F2] border-y border-[#EAE3F1]/60">
        <div 
          className={`h-full transition-all duration-300 ${
            isCompleted 
              ? 'bg-emerald-500' 
              : isCurrent
              ? 'bg-[#3E1E43]'
              : 'bg-[#B0A3B6]'
          }`}
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Expandable Body */}
      {expanded && (
        <div className="p-5 sm:p-6 border-t border-[#EAE3F1] space-y-6 bg-white">
          
          {/* Goal & Skill Gap Statement */}
          <div className="space-y-3">
            {week.skillGapAddressed && (
              <div className="flex items-center gap-2 text-xs flex-wrap">
                <span className="font-bold text-[#7D6B82] uppercase text-[10px] tracking-wider">Target Gap Addressed:</span>
                <span className="px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-900 border border-amber-200 font-medium">
                  {week.skillGapAddressed}
                </span>
              </div>
            )}

            <div className="p-4 rounded-xl bg-[#FAF7F2] border border-[#EAE3F1] flex items-start gap-3">
              <Target className="w-5 h-5 text-[#3E1E43] shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#3E1E43]">Weekly Goal</h4>
                <p className="text-xs text-[#5C5560] mt-0.5 leading-relaxed">
                  {week.weeklyGoal}
                </p>
              </div>
            </div>

            {week.expectedDeliverable && (
              <div className="p-3.5 rounded-xl bg-purple-50/70 border border-purple-200/80 flex items-start gap-3">
                <Sparkles className="w-4 h-4 text-[#5C2B64] shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-[#5C2B64]">Expected Outcome / Deliverable</h4>
                  <p className="text-xs text-[#4A454D] mt-0.5 font-medium leading-relaxed">
                    {week.expectedDeliverable}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Topics Grid */}
          {week.topics && week.topics.length > 0 && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-[#6B6470] mb-2.5">
                Core Concepts & Topics
              </h4>
              <div className="flex flex-wrap gap-2">
                {week.topics.map((topic, i) => (
                  <div 
                    key={i}
                    className="text-xs px-3 py-1.5 rounded-lg bg-[#F5F0F9] text-[#3E1E43] border border-[#EAE3F1] font-medium"
                  >
                    {topic}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Interactive Tasks Checklist with immediate progress feedback */}
          <div>
            <div className="flex items-center justify-between mb-2.5">
              <h4 className="text-xs font-bold uppercase tracking-wider text-[#6B6470]">
                Weekly Action Checklist & Deliverables
              </h4>
              <span className="text-xs text-[#8C7A93]">Check tasks to unlock progress</span>
            </div>

            <div className="space-y-2">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  onClick={() => onToggleTask(week.weekNumber, task.id)}
                  className={`p-3.5 rounded-xl border flex items-start gap-3 cursor-pointer transition-all ${
                    task.completed
                      ? 'bg-emerald-50/40 border-emerald-200 text-[#4A454D]'
                      : 'bg-white border-[#EAE3F1] hover:border-[#D5C2E2] hover:bg-[#FAF7F2]'
                  }`}
                >
                  <button 
                    type="button" 
                    className="mt-0.5 shrink-0 text-[#3E1E43] focus:outline-none"
                    aria-label={task.completed ? "Mark incomplete" : "Mark complete"}
                  >
                    {task.completed ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-600 fill-emerald-100" />
                    ) : (
                      <Circle className="w-5 h-5 text-[#8C7A93] hover:text-[#3E1E43]" />
                    )}
                  </button>
                  <div className="flex-1">
                    <p className={`text-xs sm:text-sm font-medium ${task.completed ? 'line-through text-[#7A747F]' : 'text-[#2B282C]'}`}>
                      {task.text}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Curated Educational Resources */}
          {week.resources && week.resources.length > 0 && (
            <div className="pt-2 border-t border-[#EAE3F1]">
              <div className="flex items-center justify-between mb-2.5 flex-wrap gap-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#6B6470] flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5 text-[#3E1E43]" />
                  Recommended Educational Resources
                </h4>
                {week.resources.some((r) => r.isVerified) ? (
                  <span className="text-[10px] text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 font-semibold flex items-center gap-1">
                    <Sparkles className="w-2.5 h-2.5 text-emerald-600" />
                    Verified Curriculum Resource (RAG)
                  </span>
                ) : (
                  <span className="text-[10px] text-[#7D6B82] bg-[#FAF7F2] px-2 py-0.5 rounded border border-[#EAE3F1]">
                    Generic reference
                  </span>
                )}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {week.resources.map((res, i) => (
                  <a
                    key={i}
                    href={res.url && res.url !== '#' ? res.url : undefined}
                    target={res.isExternal ? "_blank" : "_self"}
                    rel="noopener noreferrer"
                    className={`p-3 rounded-xl border transition-all flex items-center justify-between group ${
                      res.isVerified
                        ? 'border-emerald-200 bg-emerald-50/20 hover:border-emerald-400 hover:bg-white'
                        : 'border-[#EAE3F1] bg-[#FAF7F2] hover:bg-white hover:border-[#3E1E43]/40'
                    } ${res.url && res.url !== '#' ? 'cursor-pointer' : 'cursor-default'}`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <BookOpen className={`w-4 h-4 shrink-0 ${res.isVerified ? 'text-emerald-700' : 'text-[#3E1E43]'}`} />
                      <div className="truncate">
                        <span className="text-xs font-medium text-[#2B282C] group-hover:text-[#3E1E43] block truncate">
                          {res.title}
                        </span>
                        <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
                          {res.provider && (
                            <span className="text-[10px] font-semibold text-[#5C2B64]">
                              {res.provider}
                            </span>
                          )}
                          <span className="text-[10px] text-[#8C7A93]">
                            {res.type || 'Guide'}
                          </span>
                          {res.difficulty && (
                            <span className="text-[9px] px-1.5 py-0.2 rounded bg-purple-100/60 text-purple-900 font-medium">
                              {res.difficulty}
                            </span>
                          )}
                          {res.isVerified ? (
                            <span className="text-[9px] text-emerald-700 font-bold">
                              • Verified
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </div>
                    {res.url && res.url !== '#' && (
                      <ExternalLink className="w-3.5 h-3.5 text-[#8C7A93] group-hover:text-[#3E1E43] shrink-0 ml-2" />
                    )}
                  </a>
                ))}
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  );
}
