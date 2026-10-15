import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Sparkles, ArrowRight, LogOut, User as UserIcon } from 'lucide-react';
import Button from './Button';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const { user, isAuthenticated, logout } = useAuth();

  const navLinks = [
    { name: 'How It Works', path: '/#how-it-works' },
    { name: 'Dashboard', path: '/dashboard' },
    { name: 'Career Roadmap', path: '/roadmap' },
    { name: 'Returnships', path: '/returnships' },
  ];

  const isActive = (path) => {
    if (path.startsWith('/#')) return false;
    return location.pathname === path;
  };

  const handleScrollTo = (e, hash) => {
    if (location.pathname === '/') {
      e.preventDefault();
      const el = document.getElementById(hash.replace('/#', ''));
      if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
        setMobileMenuOpen(false);
      }
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-[#FAF7F2]/90 backdrop-blur-md border-b border-[#EAE3F1]/80 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#3E1E43] to-[#5C2B64] flex items-center justify-center text-white shadow-sm group-hover:scale-105 transition-transform duration-200">
              <span className="font-serif font-bold text-xl tracking-tight">H</span>
            </div>
            <div className="flex flex-col">
              <span className="font-serif font-bold text-2xl tracking-tight text-[#3E1E43] group-hover:text-[#2C1430] transition-colors">
                HerTurn
              </span>
              <span className="text-[10px] uppercase font-semibold tracking-widest text-[#7D6B82] -mt-1">
                Career Relaunch
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.path}
                onClick={(e) => link.path.startsWith('/#') && handleScrollTo(e, link.path)}
                className={`text-sm font-medium transition-colors duration-150 relative py-1 ${
                  isActive(link.path)
                    ? 'text-[#3E1E43] font-semibold'
                    : 'text-[#5C5560] hover:text-[#3E1E43]'
                }`}
              >
                {link.name}
                {isActive(link.path) && (
                  <span className="absolute bottom-0 left-0 w-full h-0.5 bg-[#3E1E43] rounded-full" />
                )}
              </a>
            ))}
          </nav>

          {/* Action CTAs */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated && user ? (
              <div className="flex items-center gap-3">
                <Link
                  to="/signin"
                  className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white border border-[#EAE3F1] hover:border-[#3E1E43] transition-colors"
                >
                  <div className="w-7 h-7 rounded-lg bg-[#3E1E43] text-white flex items-center justify-center font-bold text-xs">
                    {user.fullName ? user.fullName.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex flex-col text-left">
                    <span className="text-xs font-semibold text-[#3E1E43] line-clamp-1 max-w-[120px]">
                      {user.fullName || user.email.split('@')[0]}
                    </span>
                    <span className="text-[10px] text-[#7D6B82] leading-none">Candidate</span>
                  </div>
                </Link>

                <button
                  type="button"
                  onClick={logout}
                  title="Sign Out"
                  className="p-2 rounded-xl text-[#7D6B82] hover:text-red-600 hover:bg-red-50 border border-transparent hover:border-red-200 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <>
                <Link to="/signin">
                  <Button variant="ghost" size="sm">
                    Sign In
                  </Button>
                </Link>
                <Link to="/onboarding">
                  <Button variant="primary" size="sm" icon={Sparkles} iconPosition="left">
                    Get Started
                  </Button>
                </Link>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="flex md:hidden">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-[#3E1E43] hover:bg-[#EAE3F1]/50 transition-colors focus:outline-none"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[#EAE3F1] bg-[#FAF7F2] px-4 pt-2 pb-6 space-y-3 shadow-lg animate-in slide-in-from-top duration-200">
          <div className="flex flex-col space-y-2 pt-2">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.path}
                onClick={(e) => {
                  if (link.path.startsWith('/#')) handleScrollTo(e, link.path);
                  else setMobileMenuOpen(false);
                }}
                className={`px-3 py-2 rounded-lg text-base font-medium transition-colors ${
                  isActive(link.path)
                    ? 'bg-[#EAE3F1] text-[#3E1E43] font-semibold'
                    : 'text-[#4A454D] hover:bg-[#F3EEF7] hover:text-[#3E1E43]'
                }`}
              >
                {link.name}
              </a>
            ))}
          </div>

          <div className="pt-4 border-t border-[#EAE3F1] flex flex-col gap-2">
            {isAuthenticated && user ? (
              <div className="space-y-2">
                <div className="px-3 py-2 rounded-xl bg-white border border-[#EAE3F1] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-[#3E1E43] text-white flex items-center justify-center font-bold text-xs">
                      {user.fullName ? user.fullName.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
                    </div>
                    <span className="text-xs font-semibold text-[#3E1E43]">
                      {user.fullName || user.email}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      logout();
                      setMobileMenuOpen(false);
                    }}
                    className="text-xs font-semibold text-red-600 flex items-center gap-1"
                  >
                    <LogOut className="w-3.5 h-3.5" /> Sign Out
                  </button>
                </div>
              </div>
            ) : (
              <>
                <Link to="/signin" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="outline" size="md" className="w-full">
                    Sign In
                  </Button>
                </Link>
                <Link to="/onboarding" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="primary" size="md" className="w-full" icon={ArrowRight} iconPosition="right">
                    Get Started Free
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
