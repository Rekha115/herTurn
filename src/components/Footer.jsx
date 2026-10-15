import React from 'react';
import { Link } from 'react-router-dom';
import { Heart, Sparkles, Compass, ShieldCheck, Mail, ArrowUpRight } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-[#2B1730] text-[#E8DDF2] pt-16 pb-12 border-t border-[#45274C]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10 pb-12 border-b border-[#45274C]">
          
          {/* Brand Info */}
          <div className="lg:col-span-2 space-y-4">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#F6D6C6] to-[#EAE3F1] flex items-center justify-center text-[#3E1E43] font-serif font-bold text-lg shadow-sm">
                H
              </div>
              <span className="font-serif font-bold text-2xl tracking-tight text-white">
                HerTurn
              </span>
            </Link>
            <p className="text-sm text-[#C9BFD3] leading-relaxed max-w-sm">
              Your experience still matters. Your next chapter starts here. HerTurn is an AI-powered career relaunch & returnship platform empowering women to return to work with clarity and dignity.
            </p>
          </div>


          {/* Column 1: Platform */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-white">Platform</h4>
            <ul className="space-y-2 text-sm text-[#C9BFD3]">
              <li>
                <Link to="/onboarding" className="hover:text-white transition-colors">
                  Resume Analysis
                </Link>
              </li>
              <li>
                <Link to="/roadmap" className="hover:text-white transition-colors">
                  Personalized Roadmap
                </Link>
              </li>
              <li>
                <Link to="/returnships" className="hover:text-white transition-colors">
                  Returnship Marketplace
                </Link>
              </li>
              <li>
                <Link to="/dashboard" className="hover:text-white transition-colors">
                  Career Dashboard
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 2: Resources */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-white">Resources</h4>
            <ul className="space-y-2 text-sm text-[#C9BFD3]">
              <li>
                <a href="#how-it-works" className="hover:text-white transition-colors">
                  How It Works
                </a>
              </li>
              <li>
                <span className="cursor-pointer hover:text-white transition-colors" title="Guide coming soon">
                  Break Narrative Guide
                </span>
              </li>
              <li>
                <span className="cursor-pointer hover:text-white transition-colors" title="Guide coming soon">
                  Mentorship Circles
                </span>
              </li>
              <li>
                <span className="cursor-pointer hover:text-white transition-colors" title="Partnerships">
                  Partner Companies
                </span>
              </li>
            </ul>
          </div>

          {/* Column 3: Trust & Info */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-white">Trust & Security</h4>
            <ul className="space-y-2 text-sm text-[#C9BFD3]">
              <li className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-[#F6D6C6]" />
                <span>Private Resume Parsing</span>
              </li>
              <li>
                <span className="hover:text-white transition-colors cursor-pointer">
                  Privacy Policy
                </span>
              </li>
              <li>
                <span className="hover:text-white transition-colors cursor-pointer">
                  Terms of Service
                </span>
              </li>
              <li>
                <Link to="/signin" className="hover:text-white transition-colors">
                  Account Sign In
                </Link>
              </li>
            </ul>
          </div>

        </div>

        {/* Bottom bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between text-xs text-[#A89CAE] gap-4">
          <p>© 2026 HerTurn Technologies. Built with pride for returning women everywhere.</p>
          <div className="flex items-center gap-1 text-[#C9BFD3]">
            <span>Designed with</span>
            <Heart className="w-3.5 h-3.5 text-[#F6D6C6] fill-[#F6D6C6]" />
            <span>for dignified career relaunches</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
