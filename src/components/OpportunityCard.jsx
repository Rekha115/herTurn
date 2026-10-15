import React from 'react';
import { 
  Building2, 
  MapPin, 
  Clock, 
  Bookmark, 
  ExternalLink, 
  Sparkles, 
  ShieldCheck, 
  AlertCircle,
  Briefcase
} from 'lucide-react';
import Button from './Button';

export default function OpportunityCard({ 
  opportunity, 
  isBookmarked = false, 
  onToggleBookmark 
}) {
  const isVerified = opportunity.type === 'verified';

  return (
    <div className="bg-white rounded-2xl border border-[#EAE3F1] p-6 hover:shadow-md hover:border-[#D5C2E2] transition-all duration-200 flex flex-col justify-between group">
      <div>
        {/* Top Header: Company initial + Verification Tag + Bookmark Button */}
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center font-bold text-base border shrink-0 ${opportunity.logoBg || 'bg-[#EAE3F1] text-[#3E1E43] border-[#DFD5E7]'}`}>
              {opportunity.logoInitial}
            </div>
            <div>
              <h4 className="font-semibold text-base text-[#2B282C] group-hover:text-[#3E1E43] transition-colors leading-snug">
                {opportunity.company}
              </h4>
              <div className="flex items-center gap-2 text-xs text-[#6B6470] mt-0.5 flex-wrap">
                <span className="flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-[#8C7A93]" />
                  {opportunity.location}
                </span>
                <span>•</span>
                <span className="px-2 py-0.5 rounded-full bg-[#FAF7F2] font-medium border border-[#EAE3F1]">
                  {opportunity.workArrangement}
                </span>
                {opportunity.roleCategory && (
                  <>
                    <span>•</span>
                    <span className="px-2 py-0.5 rounded-full bg-[#F3EEF7] text-[#3E1E43] font-semibold border border-[#E1D4E8]">
                      {opportunity.roleCategory}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={() => onToggleBookmark?.(opportunity.id)}
            className={`p-2.5 rounded-xl border transition-all cursor-pointer ${
              isBookmarked
                ? 'bg-[#3E1E43] text-white border-[#3E1E43]'
                : 'bg-[#FAF7F2] text-[#6B6470] border-[#EAE3F1] hover:text-[#3E1E43] hover:border-[#3E1E43]'
            }`}
            title={isBookmarked ? 'Remove bookmark' : 'Save opportunity'}
            aria-label="Bookmark Opportunity"
          >
            <Bookmark className={`w-4 h-4 ${isBookmarked ? 'fill-current' : ''}`} />
          </button>
        </div>

        {/* Role Title */}
        <h3 className="font-serif font-bold text-lg text-[#3E1E43] mb-2 leading-tight">
          {opportunity.roleTitle}
        </h3>

        {/* Match Score Badge (When Matching Active) */}
        {opportunity.matchScore !== undefined && opportunity.matchScore !== null && (
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${
              opportunity.matchScore >= 75
                ? 'bg-purple-100 text-[#3E1E43] border-purple-300'
                : opportunity.matchScore >= 50
                ? 'bg-amber-50 text-amber-900 border-amber-300'
                : 'bg-stone-100 text-stone-700 border-stone-200'
            }`}>
              <Sparkles className="w-3.5 h-3.5 text-[#3E1E43]" />
              <span>{opportunity.matchScore}% Role Match</span>
            </div>
            {opportunity.eligibilityStatus && (
              <span className="text-[11px] font-medium text-[#7D6B82] truncate max-w-[240px]" title={opportunity.eligibilityStatus}>
                • {opportunity.eligibilityStatus}
              </span>
            )}
          </div>
        )}

        {/* Verification / Sample Banner */}
        <div className="mb-4 flex items-center gap-2 flex-wrap">
          {isVerified ? (
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>{opportunity.verificationStatus}</span>
              {opportunity.verificationDate && (
                <span className="text-emerald-700/80 text-[11px]">({opportunity.verificationDate})</span>
              )}
            </div>
          ) : (
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-stone-100 text-stone-700 border border-stone-200">
              <AlertCircle className="w-3.5 h-3.5 text-stone-500" />
              <span>{opportunity.verificationStatus}</span>
            </div>
          )}
        </div>

        {/* Match Rationale Snippet (When Matching Active) */}
        {opportunity.matchRationale && (
          <div className="p-3 rounded-xl bg-purple-50/60 border border-purple-100 text-xs text-[#5C5560] mb-4">
            <strong className="text-[#3E1E43] block mb-0.5">Why this matches your profile:</strong>
            <p className="leading-relaxed">{opportunity.matchRationale}</p>
          </div>
        )}

        {/* Eligibility Details Pill Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-[#5C5560] bg-[#FAF7F2] p-3 rounded-xl mb-4 border border-[#EAE3F1]/80">
          <div>
            <span className="text-[#8C7A93] block text-[10px] uppercase font-bold tracking-wider">Duration</span>
            <span className="font-semibold text-[#2B282C]">{opportunity.duration}</span>
          </div>
          <div>
            <span className="text-[#8C7A93] block text-[10px] uppercase font-bold tracking-wider">Break Requirement</span>
            <span className="font-semibold text-[#2B282C]">{opportunity.minBreakRequired}</span>
          </div>
          <div className="sm:col-span-2 pt-1 border-t border-[#EAE3F1] flex justify-between flex-wrap gap-2">
            <div>
              <span className="text-[#8C7A93] block text-[10px] uppercase font-bold tracking-wider">Prior Experience</span>
              <span className="font-medium text-[#2B282C]">{opportunity.minExperience}</span>
            </div>
            {opportunity.experienceLevel && (
              <div>
                <span className="text-[#8C7A93] block text-[10px] uppercase font-bold tracking-wider">Level</span>
                <span className="font-medium text-[#3E1E43]">{opportunity.experienceLevel}</span>
              </div>
            )}
          </div>
        </div>

        {/* Description snippet */}
        <p className="text-xs text-[#5C5560] leading-relaxed mb-4 line-clamp-3">
          {opportunity.description}
        </p>

        {/* Skills Tag list */}
        <div className="flex flex-wrap gap-1.5 mb-5">
          {opportunity.skills.map((skill) => {
            const isMatched = opportunity.matchedSkills?.includes(skill);
            return (
              <span
                key={skill}
                className={`text-[11px] px-2.5 py-1 rounded-lg font-medium border flex items-center gap-1 ${
                  isMatched
                    ? 'bg-emerald-50 text-emerald-900 border-emerald-300'
                    : 'bg-[#EAE3F1]/60 text-[#3E1E43] border-[#DFD5E7]'
                }`}
              >
                {isMatched && <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 inline-block" />}
                {skill}
              </span>
            );
          })}
        </div>
      </div>

      {/* Card Action footer */}
      <div className="pt-4 border-t border-[#EAE3F1] flex items-center justify-between gap-3">
        {opportunity.stipend && (
          <div className="text-xs text-[#6B6470] truncate">
            <span className="font-medium text-[#2B282C]">{opportunity.stipend}</span>
          </div>
        )}

        {isVerified && opportunity.sourceUrl ? (
          <a
            href={opportunity.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0"
          >
            <Button variant="primary" size="sm" icon={ExternalLink} iconPosition="right">
              Apply via Program
            </Button>
          </a>
        ) : (
          <Button
            variant="outline"
            size="sm"
            disabled={true}
            className="shrink-0 text-xs opacity-70"
            title="Demo sample opportunity only"
          >
            Sample Listing Only
          </Button>
        )}
      </div>
    </div>
  );
}
