import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileSearch, 
  MapPin, 
  Briefcase, 
  User, 
  Sparkles,
  ArrowUpRight,
  ShieldAlert
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Sidebar({ mobileOpen, onClose }) {
  const { user, isAuthenticated } = useAuth();
  const location = useLocation();
  const currentPath = location.pathname;

  // Determine active item strictly so exactly ONE item is active at any time
  const getIsActive = (itemId) => {
    switch (itemId) {
      case 'overview':
        return currentPath === '/dashboard';
      case 'analysis':
        return currentPath === '/analysis' || currentPath === '/resume-analysis' || currentPath === '/onboarding';
      case 'roadmap':
        return currentPath === '/roadmap';
      case 'returnships':
        return currentPath === '/returnships';
      case 'auth':
        return currentPath === '/signin';
      default:
        return false;
    }
  };

  const navItems = [
    { id: 'overview', label: 'Overview', to: '/dashboard', icon: LayoutDashboard },
    { id: 'analysis', label: 'Resume Analysis', to: '/analysis', icon: FileSearch },
    { id: 'roadmap', label: 'My Roadmap', to: '/roadmap', icon: MapPin },
    { id: 'returnships', label: 'Returnships', to: '/returnships', icon: Briefcase },
    { id: 'auth', label: isAuthenticated ? (user?.fullName || 'My Account') : 'Sign In', to: '/signin', icon: User },
  ];

  const content = (
    <div className="flex flex-col h-full bg-white border-r border-[#EAE3F1] py-6 px-4">
      {/* Brand in sidebar */}
      <div className="px-3 pb-6 border-b border-[#EAE3F1]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#3E1E43] flex items-center justify-center text-white font-serif font-bold text-base shadow-xs">
            H
          </div>
          <div>
            <div className="font-serif font-bold text-lg text-[#3E1E43] leading-none">HerTurn</div>
            <div className="text-[10px] text-[#7D6B82] font-semibold tracking-wider uppercase mt-0.5">Career Hub</div>
          </div>
        </div>
      </div>

      {/* Nav list */}
      <div className="flex-1 py-6 space-y-1">
        <div className="text-[11px] font-bold text-[#8C7A93] uppercase tracking-wider px-3 mb-2">Navigation</div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = getIsActive(item.id);
          return (
            <Link
              key={item.id}
              to={item.to}
              onClick={onClose}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-[#3E1E43] text-white shadow-sm font-semibold'
                  : 'text-[#5C5560] hover:bg-[#F5F0F9] hover:text-[#3E1E43]'
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>

      {/* Candidate status / roadmap progress tag */}
      <div className="p-3.5 rounded-xl bg-[#FAF7F2] border border-[#EAE3F1] space-y-2">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-[#3E1E43]">
          <Sparkles className="w-3.5 h-3.5 text-[#3E1E43]" />
          <span className="line-clamp-1">
            {isAuthenticated ? (user?.fullName || 'Active Candidate') : 'Relaunch Sprint'}
          </span>
        </div>
        <p className="text-xs text-[#6B6470] leading-relaxed line-clamp-2">
          {isAuthenticated && user?.candidateProfile?.targetRole
            ? `Target: ${user.candidateProfile.targetRole}`
            : '4-Week Roadmap in progress: Week 2 of 4.'}
        </p>
        <div className="w-full bg-[#EAE3F1] h-1.5 rounded-full overflow-hidden">
          <div className="bg-[#3E1E43] h-full rounded-full" style={{ width: isAuthenticated ? '65%' : '42%' }}></div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden lg:block w-64 shrink-0 sticky top-20 h-[calc(100vh-5rem)]">
        {content}
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div className="fixed inset-0 bg-black/30 backdrop-blur-xs" onClick={onClose} />
          <div className="relative w-72 max-w-[85vw] h-full z-10 animate-in slide-in-from-left duration-200">
            {content}
          </div>
        </div>
      )}
    </>
  );
}
