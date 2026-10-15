import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Sparkles, 
  ArrowRight, 
  FileText, 
  Compass, 
  Briefcase, 
  ShieldCheck, 
  CheckCircle2, 
  HeartHandshake, 
  TrendingUp, 
  Users, 
  Award,
  ChevronRight,
  BookOpen
} from 'lucide-react';
import Button from '../components/Button';

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      
      {/* 1. HERO SECTION */}
      <section className="relative overflow-hidden pt-12 pb-20 lg:pt-20 lg:pb-28 bg-gradient-to-b from-[#FAF7F2] via-[#FAF7F2] to-[#F5F0F9]">
        {/* Subtle decorative background blur shapes */}
        <div className="absolute top-10 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-[#EAE3F1]/70 to-[#F6D6C6]/40 blur-3xl -z-10 rounded-full pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            
            {/* Left Column: Value Messaging */}
            <div className="lg:col-span-7 space-y-6 text-center lg:text-left">
              
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#EAE3F1] border border-[#DFD5E7] text-[#3E1E43] text-xs font-semibold shadow-2xs">
                <Sparkles className="w-3.5 h-3.5 text-[#3E1E43]" />
                <span>Empowering Career Comebacks for Women</span>
              </div>

              {/* Main Headline */}
              <h1 className="font-serif text-4xl sm:text-5xl lg:text-6xl font-bold text-[#3E1E43] tracking-tight leading-[1.15]">
                Your experience still matters. <br />
                <span className="italic font-normal text-[#5C2B64]">Your next chapter starts here.</span>
              </h1>

              {/* Supporting Text */}
              <p className="text-base sm:text-lg text-[#554E59] leading-relaxed max-w-2xl mx-auto lg:mx-0">
                Career breaks don't erase your potential. HerTurn helps you identify your strengths, rebuild in-demand skills, and find opportunities designed for your comeback.
              </p>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4 pt-2">
                <Link to="/onboarding" className="w-full sm:w-auto">
                  <Button variant="primary" size="lg" className="w-full sm:w-auto" icon={ArrowRight} iconPosition="right">
                    Get Started
                  </Button>
                </Link>
                <a href="#how-it-works" className="w-full sm:w-auto">
                  <Button variant="outline" size="lg" className="w-full sm:w-auto">
                    See How It Works
                  </Button>
                </a>
              </div>

              {/* Micro Social Proof / Reassurance */}
              <div className="pt-6 border-t border-[#EAE3F1]/80 flex flex-wrap items-center justify-center lg:justify-start gap-6 text-xs text-[#6B6470]">
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Confidential resume parsing</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Curated returnship cohorts</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Personalized 4–6 week plans</span>
                </div>
              </div>
            </div>

            {/* Right Column: Hero Visual Card */}
            <div className="lg:col-span-5 relative">
              <div className="relative mx-auto max-w-md lg:max-w-none">
                
                {/* Decorative border frame */}
                <div className="absolute -inset-2 bg-gradient-to-r from-[#F6D6C6] via-[#EAE3F1] to-[#3E1E43]/20 rounded-3xl blur-md opacity-60" />

                {/* Main Card */}
                <div className="relative bg-white rounded-3xl border border-[#EAE3F1] shadow-xl p-6 sm:p-7 space-y-6">
                  
                  {/* Persona Header */}
                  <div className="flex items-center justify-between pb-4 border-b border-[#EAE3F1]">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-2xl bg-[#3E1E43] text-white flex items-center justify-center font-serif text-lg font-bold shadow-xs">
                        PS
                      </div>
                      <div>
                        <h2 className="text-sm font-bold text-[#2B282C]">Priya Sharma</h2>
                        <p className="text-xs text-[#7D6B82]">Senior Business Analyst → Product Operations</p>
                      </div>
                    </div>
                    <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      Relaunch Ready
                    </span>
                  </div>

                  {/* Career Break Badge */}
                  <div className="bg-[#FAF7F2] p-3.5 rounded-xl border border-[#EAE3F1] flex items-center justify-between text-xs">
                    <span className="text-[#6B6470]">Career Hiatus:</span>
                    <span className="font-semibold text-[#3E1E43]">3.5 Years (Maternity & Eldercare)</span>
                  </div>

                  {/* Skills radar simulation snippet */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-[#554E59] font-medium">Core Transferable Strengths</span>
                      <span className="text-[#3E1E43] font-bold">Verified</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      <span className="text-[11px] px-2.5 py-1 rounded-lg bg-[#EAE3F1] text-[#3E1E43] font-medium">
                        Stakeholder Leadership
                      </span>
                      <span className="text-[11px] px-2.5 py-1 rounded-lg bg-[#EAE3F1] text-[#3E1E43] font-medium">
                        SQL & Process Flow
                      </span>
                      <span className="text-[11px] px-2.5 py-1 rounded-lg bg-[#F6D6C6]/60 text-[#3E1E43] font-medium">
                        Mixpanel (+2 Wk Sprint)
                      </span>
                    </div>
                  </div>

                  {/* Matched Returnship preview card */}
                  <div className="p-3.5 rounded-xl bg-gradient-to-r from-[#FAF7F2] to-[#F5F0F9] border border-[#EAE3F1] space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#8C7A93]">Matched Program</span>
                      <span className="text-[10px] font-bold text-emerald-700">92% Skill Fit</span>
                    </div>
                    <div className="font-medium text-xs text-[#2B282C]">
                      AWS Technical Program Manager — Return to Work
                    </div>
                    <div className="text-[11px] text-[#7D6B82]">
                      16-Week Paid Fellowship • Hybrid Cohort 2026
                    </div>
                  </div>

                  <Link to="/onboarding" className="block">
                    <Button variant="secondary" size="md" className="w-full text-xs">
                      Preview Your Own Relaunch Plan
                    </Button>
                  </Link>

                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* 2. TRUST / VALUE SECTION (3 Concis Value Propositions) */}
      <section className="py-16 bg-white border-y border-[#EAE3F1]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="font-serif text-3xl font-bold text-[#3E1E43]">
              A Dignified, Skills-First Relaunch
            </h2>
            <p className="text-sm text-[#6B6470] mt-2">
              We replace self-doubt with evidence-based career roadmaps and return-friendly employers.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            {/* Value 1 */}
            <div className="p-7 rounded-2xl bg-[#FAF7F2] border border-[#EAE3F1] hover:border-[#D5C2E2] transition-all hover:shadow-sm space-y-3">
              <div className="w-12 h-12 rounded-xl bg-[#EAE3F1] text-[#3E1E43] flex items-center justify-center">
                <Award className="w-6 h-6" />
              </div>
              <h3 className="font-serif font-bold text-xl text-[#3E1E43]">
                1. Understand Your Strengths
              </h3>
              <p className="text-sm text-[#5C5560] leading-relaxed">
                Your prior work experience doesn't vanish. Our resume parser highlights your foundational expertise and extracts valuable transferable skills gained over your break.
              </p>
            </div>

            {/* Value 2 */}
            <div className="p-7 rounded-2xl bg-[#FAF7F2] border border-[#EAE3F1] hover:border-[#D5C2E2] transition-all hover:shadow-sm space-y-3">
              <div className="w-12 h-12 rounded-xl bg-[#F6D6C6] text-[#3E1E43] flex items-center justify-center">
                <Compass className="w-6 h-6" />
              </div>
              <h3 className="font-serif font-bold text-xl text-[#3E1E43]">
                2. Build a Personalized Roadmap
              </h3>
              <p className="text-sm text-[#5C5560] leading-relaxed">
                Skip generic 6-month courses. Receive a hyper-targeted 4–6 week weekly learning sprint that bridges modern tool gaps and polishes your interview narrative.
              </p>
            </div>

            {/* Value 3 */}
            <div className="p-7 rounded-2xl bg-[#FAF7F2] border border-[#EAE3F1] hover:border-[#D5C2E2] transition-all hover:shadow-sm space-y-3">
              <div className="w-12 h-12 rounded-xl bg-[#3E1E43] text-white flex items-center justify-center">
                <Briefcase className="w-6 h-6" />
              </div>
              <h3 className="font-serif font-bold text-xl text-[#3E1E43]">
                3. Find Your Next Opportunity
              </h3>
              <p className="text-sm text-[#5C5560] leading-relaxed">
                Connect directly with corporate returnships and return-to-work fellowships that value life perspective, offering dedicated transition support and mentors.
              </p>
            </div>

          </div>
        </div>
      </section>

      {/* 3. HOW IT WORKS (Four-Step Visual Flow) */}
      <section id="how-it-works" className="py-20 bg-[#FAF7F2]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-xs uppercase font-bold tracking-widest text-[#7D6B82]">
              Simple & Structured Path
            </span>
            <h2 className="font-serif text-3xl sm:text-4xl font-bold text-[#3E1E43] mt-1">
              How HerTurn Works
            </h2>
            <p className="text-sm text-[#6B6470] mt-2">
              Four guided milestones designed to take you from uncertain pause to career readiness.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 relative">
            
            {/* Step 1 */}
            <div className="bg-white p-6 rounded-2xl border border-[#EAE3F1] shadow-xs relative flex flex-col justify-between group hover:border-[#3E1E43]/40 transition-all">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="font-serif font-bold text-2xl text-[#8C7A93] group-hover:text-[#3E1E43] transition-colors">
                    01
                  </span>
                  <div className="w-10 h-10 rounded-xl bg-[#FAF7F2] border border-[#EAE3F1] flex items-center justify-center text-[#3E1E43]">
                    <FileText className="w-5 h-5" />
                  </div>
                </div>
                <h3 className="font-serif font-bold text-lg text-[#3E1E43] mb-2">
                  Upload Your Resume
                </h3>
                <p className="text-xs text-[#5C5560] leading-relaxed">
                  Submit your previous resume and share your career preferences. We preserve your privacy and analyze without judgment.
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="bg-white p-6 rounded-2xl border border-[#EAE3F1] shadow-xs relative flex flex-col justify-between group hover:border-[#3E1E43]/40 transition-all">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="font-serif font-bold text-2xl text-[#8C7A93] group-hover:text-[#3E1E43] transition-colors">
                    02
                  </span>
                  <div className="w-10 h-10 rounded-xl bg-[#FAF7F2] border border-[#EAE3F1] flex items-center justify-center text-[#3E1E43]">
                    <TrendingUp className="w-5 h-5" />
                  </div>
                </div>
                <h3 className="font-serif font-bold text-lg text-[#3E1E43] mb-2">
                  Discover Skill Gaps
                </h3>
                <p className="text-xs text-[#5C5560] leading-relaxed">
                  Compare your historical skillset with today's industry expectations. See what you already have and what tools need a quick refresh.
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="bg-white p-6 rounded-2xl border border-[#EAE3F1] shadow-xs relative flex flex-col justify-between group hover:border-[#3E1E43]/40 transition-all">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="font-serif font-bold text-2xl text-[#8C7A93] group-hover:text-[#3E1E43] transition-colors">
                    03
                  </span>
                  <div className="w-10 h-10 rounded-xl bg-[#FAF7F2] border border-[#EAE3F1] flex items-center justify-center text-[#3E1E43]">
                    <Compass className="w-5 h-5" />
                  </div>
                </div>
                <h3 className="font-serif font-bold text-lg text-[#3E1E43] mb-2">
                  Follow Your Roadmap
                </h3>
                <p className="text-xs text-[#5C5560] leading-relaxed">
                  Tackle week-by-week goals with verified reading materials, hands-on mini-projects, and returnee interview prep scripts.
                </p>
              </div>
            </div>

            {/* Step 4 */}
            <div className="bg-white p-6 rounded-2xl border border-[#EAE3F1] shadow-xs relative flex flex-col justify-between group hover:border-[#3E1E43]/40 transition-all">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="font-serif font-bold text-2xl text-[#8C7A93] group-hover:text-[#3E1E43] transition-colors">
                    04
                  </span>
                  <div className="w-10 h-10 rounded-xl bg-[#FAF7F2] border border-[#EAE3F1] flex items-center justify-center text-[#3E1E43]">
                    <Briefcase className="w-5 h-5" />
                  </div>
                </div>
                <h3 className="font-serif font-bold text-lg text-[#3E1E43] mb-2">
                  Explore Returnships
                </h3>
                <p className="text-xs text-[#5C5560] leading-relaxed">
                  Discover verified fellowships with supportive company culture, competitive stipends, and pathways to permanent full-time roles.
                </p>
              </div>
            </div>

          </div>

          <div className="mt-12 text-center">
            <Link to="/onboarding">
              <Button variant="primary" size="md" icon={ArrowRight} iconPosition="right">
                Start Your Career Analysis Now
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* 4. WHY HERTURN SECTION */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            
            <div className="space-y-6">
              <span className="text-xs uppercase font-bold tracking-widest text-[#7D6B82]">
                Our Philosophy
              </span>
              <h2 className="font-serif text-3xl sm:text-4xl font-bold text-[#3E1E43] leading-tight">
                Career breaks are chapters, not full stops.
              </h2>
              <p className="text-sm sm:text-base text-[#554E59] leading-relaxed">
                Millions of talented women step away from corporate roles to care for children, aging parents, or navigate life milestones. When they are ready to return, they often face algorithmic resume filters, self-doubt, and the misconception that their skills are obsolete.
              </p>
              <p className="text-sm sm:text-base text-[#554E59] leading-relaxed">
                HerTurn treats lived experience as an asset. Caregiving builds crisis management, negotiation, and resilience. Combined with focused upskilling, returnees bring mature judgment that high-performing teams desperately need.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-[#EAE3F1] flex items-center justify-center shrink-0 mt-0.5">
                    <CheckCircle2 className="w-4 h-4 text-[#3E1E43]" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-[#2B282C]">Confidence-First Approach</h4>
                    <p className="text-[11px] text-[#6B6470] mt-0.5">Reframing hiatuses without apology.</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-[#EAE3F1] flex items-center justify-center shrink-0 mt-0.5">
                    <CheckCircle2 className="w-4 h-4 text-[#3E1E43]" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-[#2B282C]">Skills-Based Matching</h4>
                    <p className="text-[11px] text-[#6B6470] mt-0.5">Matching on capability, not gap duration.</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Testimonial / Inspiration Quote Box */}
            <div className="bg-[#FAF7F2] p-8 sm:p-10 rounded-3xl border border-[#EAE3F1] relative">
              <span className="font-serif text-6xl text-[#D9CEE3] absolute top-4 left-6 select-none">“</span>
              <div className="relative z-10 space-y-4">
                <p className="font-serif italic text-lg sm:text-xl text-[#3E1E43] leading-relaxed">
                  Returning after 4 years of maternity felt daunting until I saw my skills mapped systematically. Having a 4-week structured sprint and knowing which companies had returnship cohorts gave me back my identity as a professional.
                </p>
                <div className="pt-4 border-t border-[#EAE3F1] flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-[#3E1E43] text-white flex items-center justify-center font-bold text-sm">
                    AK
                  </div>
                  <div>
                    <div className="text-xs font-bold text-[#2B282C]">Ananya Kulkarni</div>
                    <div className="text-[11px] text-[#7D6B82]">Returned as Senior Operations Manager • Cohort 2025</div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* 5. CLOSING CTA BANNER */}
      <section className="py-16 bg-[#3E1E43] text-white relative overflow-hidden">
        <div className="absolute -right-20 -bottom-20 w-80 h-80 rounded-full bg-[#5C2B64] blur-2xl opacity-60" />
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10 space-y-6">
          <span className="text-xs uppercase font-bold tracking-widest text-[#F6D6C6]">
            Start Your Comeback
          </span>
          <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-bold leading-tight">
            Your next chapter starts with one step.
          </h2>
          <p className="text-sm sm:text-base text-[#E8DDF2] max-w-xl mx-auto leading-relaxed">
            Upload your resume, analyze your transferable strengths, and receive your personalized career roadmap in under two minutes.
          </p>
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/onboarding">
              <Button variant="secondary" size="lg" icon={Sparkles} iconPosition="left">
                Get Started Free
              </Button>
            </Link>
            <Link to="/returnships">
              <Button variant="outline" size="lg" className="text-white border-white/40 hover:bg-white/10 hover:border-white">
                Browse Returnships
              </Button>
            </Link>
          </div>
        </div>
      </section>

    </div>
  );
}
