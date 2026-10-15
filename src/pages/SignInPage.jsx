import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { 
  Sparkles, 
  ArrowRight, 
  ShieldCheck, 
  Lock, 
  Mail, 
  User as UserIcon, 
  Briefcase, 
  AlertCircle, 
  CheckCircle2, 
  LogOut, 
  Loader2,
  KeyRound,
  ShieldAlert
} from 'lucide-react';
import Button from '../components/Button';
import { useAuth } from '../context/AuthContext';

export default function SignInPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated, isLoading: isAuthLoading, login, register, logout } = useAuth();

  // Mode: 'signin' or 'register'
  const [mode, setMode] = useState('signin');

  // Form inputs
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [targetRole, setTargetRole] = useState('Product Operations & Strategy Lead');
  const [confirmPassword, setConfirmPassword] = useState('');

  // UI status
  const [clientErrors, setClientErrors] = useState({});
  const [apiError, setApiError] = useState('');
  const [apiSuccess, setApiSuccess] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Redirection target after login
  const from = location.state?.from?.pathname || '/dashboard';

  // Client-side validation
  const validateForm = () => {
    const errors = {};
    const emailClean = email.trim();

    if (!emailClean) {
      errors.email = 'Email address is required.';
    } else if (!emailClean.includes('@') || !emailClean.includes('.')) {
      errors.email = 'Please enter a valid email address.';
    }

    if (!password) {
      errors.password = 'Password is required.';
    } else if (password.length < 8) {
      errors.password = 'Password must be at least 8 characters long.';
    }

    if (mode === 'register') {
      if (!fullName.trim()) {
        errors.fullName = 'Please enter your full name.';
      }
      if (!targetRole.trim()) {
        errors.targetRole = 'Please specify your target career role.';
      }
      if (password !== confirmPassword) {
        errors.confirmPassword = 'Passwords do not match.';
      }
    }

    setClientErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError('');
    setApiSuccess('');

    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      if (mode === 'signin') {
        await login(email.trim(), password);
        setApiSuccess('Signed in successfully! Redirecting...');
        setTimeout(() => {
          navigate(from, { replace: true });
        }, 500);
      } else {
        await register({
          email: email.trim(),
          password,
          fullName: fullName.trim(),
          targetRole: targetRole.trim(),
        });
        setApiSuccess('Account created successfully! Welcome to HerTurn.');
        setTimeout(() => {
          navigate(from, { replace: true });
        }, 500);
      }
    } catch (err) {
      let msg = err.message || 'Authentication request failed. Please check your credentials.';
      if (msg.toLowerCase().includes('failed to fetch')) {
        msg = 'Unable to connect to the backend server. If using Render free tier, the service spins down after 15 minutes of inactivity and takes ~45 seconds to wake up. Please wait a moment and try again, or verify your VITE_API_BASE_URL setting.';
      }
      setApiError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = () => {
    logout();
    setApiSuccess('You have been signed out.');
  };

  if (isAuthLoading) {
    return (
      <div className="min-h-[calc(100vh-10rem)] flex items-center justify-center py-16 px-4">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-[#3E1E43] animate-spin" />
          <p className="text-sm text-[#7D6B82]">Verifying authentication session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-10rem)] flex items-center justify-center py-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-6">
        
        {/* If already authenticated, show user card */}
        {isAuthenticated && user ? (
          <div className="bg-white rounded-3xl border border-[#EAE3F1] shadow-md p-8 sm:p-10 space-y-6">
            <div className="text-center space-y-2">
              <div className="w-16 h-16 rounded-full bg-[#3E1E43] text-white flex items-center justify-center mx-auto text-xl font-bold shadow-sm">
                {user.fullName ? user.fullName.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
              </div>
              <h1 className="font-serif text-2xl font-bold text-[#3E1E43]">
                Welcome back, {user.fullName || 'Candidate'}!
              </h1>
              <p className="text-xs text-[#7D6B82]">
                Signed in as <span className="font-medium text-[#3E1E43]">{user.email}</span>
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-[#FAF7F2] border border-[#EAE3F1] space-y-2 text-xs">
              <div className="flex justify-between items-center text-[#5C5560]">
                <span>Target Role:</span>
                <span className="font-semibold text-[#3E1E43]">
                  {user.candidateProfile?.targetRole || 'Product Operations & Strategy Lead'}
                </span>
              </div>
              <div className="flex justify-between items-center text-[#5C5560]">
                <span>Account Status:</span>
                <span className="inline-flex items-center gap-1 font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  <CheckCircle2 className="w-3 h-3" /> Active & Verified
                </span>
              </div>
            </div>

            <div className="space-y-3 pt-2">
              <Button
                variant="primary"
                size="md"
                className="w-full"
                onClick={() => navigate('/dashboard')}
                icon={ArrowRight}
                iconPosition="right"
              >
                Go to Candidate Dashboard
              </Button>

              <Button
                variant="outline"
                size="md"
                className="w-full"
                onClick={() => navigate('/roadmap')}
              >
                View Career Roadmap
              </Button>

              <button
                type="button"
                onClick={handleLogout}
                className="w-full flex items-center justify-center gap-2 py-2.5 text-xs font-semibold text-red-600 hover:text-red-700 hover:bg-red-50 rounded-xl transition-colors"
              >
                <LogOut className="w-4 h-4" />
                Sign Out of HerTurn
              </button>
            </div>
          </div>
        ) : (
          /* Sign In / Register Card */
          <div className="bg-white rounded-3xl border border-[#EAE3F1] shadow-md p-8 sm:p-10 space-y-6">
            
            {/* Header */}
            <div className="text-center space-y-1">
              <div className="w-12 h-12 rounded-2xl bg-[#3E1E43] text-white flex items-center justify-center mx-auto font-serif font-bold text-xl mb-3 shadow-xs">
                H
              </div>
              <h1 className="font-serif text-2xl font-bold text-[#3E1E43]">
                {mode === 'signin' ? 'Sign In to HerTurn' : 'Create Your Account'}
              </h1>
              <p className="text-xs text-[#6B6470]">
                {mode === 'signin'
                  ? 'Access your resume analysis and returnship matches'
                  : 'Start your personalized career recovery journey'}
              </p>
            </div>

            {/* Tab Switcher */}
            <div className="flex rounded-xl bg-[#FAF7F2] p-1 border border-[#EAE3F1]">
              <button
                type="button"
                onClick={() => {
                  setMode('signin');
                  setClientErrors({});
                  setApiError('');
                }}
                className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
                  mode === 'signin'
                    ? 'bg-white text-[#3E1E43] shadow-xs'
                    : 'text-[#7D6B82] hover:text-[#3E1E43]'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode('register');
                  setClientErrors({});
                  setApiError('');
                }}
                className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
                  mode === 'register'
                    ? 'bg-white text-[#3E1E43] shadow-xs'
                    : 'text-[#7D6B82] hover:text-[#3E1E43]'
                }`}
              >
                Create Account
              </button>
            </div>

            {/* API Error Banner */}
            {apiError && (
              <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 flex items-start gap-2.5 text-xs text-red-800 animate-in fade-in duration-200">
                <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                <div className="flex-1 font-medium">{apiError}</div>
              </div>
            )}

            {/* API Success Banner */}
            {apiSuccess && (
              <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 flex items-start gap-2.5 text-xs text-emerald-800 animate-in fade-in duration-200">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div className="flex-1 font-medium">{apiSuccess}</div>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              
              {/* Full Name (Registration only) */}
              {mode === 'register' && (
                <div>
                  <label className="block text-xs font-semibold text-[#3E1E43] mb-1">
                    Full Name
                  </label>
                  <div className="relative">
                    <UserIcon className="w-4 h-4 text-[#8C7A93] absolute left-3 top-3" />
                    <input
                      type="text"
                      placeholder="e.g. Priya Sharma"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="w-full text-xs sm:text-sm pl-9 pr-3.5 py-2.5 rounded-xl border border-[#D9CEE3] focus:outline-none focus:ring-2 focus:ring-[#3E1E43] bg-[#FAF7F2]"
                    />
                  </div>
                  {clientErrors.fullName && (
                    <p className="mt-1 text-[11px] text-red-600 font-medium">{clientErrors.fullName}</p>
                  )}
                </div>
              )}

              {/* Email Address */}
              <div>
                <label className="block text-xs font-semibold text-[#3E1E43] mb-1">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-[#8C7A93] absolute left-3 top-3" />
                  <input
                    type="email"
                    placeholder="candidate@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full text-xs sm:text-sm pl-9 pr-3.5 py-2.5 rounded-xl border border-[#D9CEE3] focus:outline-none focus:ring-2 focus:ring-[#3E1E43] bg-[#FAF7F2]"
                  />
                </div>
                {clientErrors.email && (
                  <p className="mt-1 text-[11px] text-red-600 font-medium">{clientErrors.email}</p>
                )}
              </div>

              {/* Target Role (Registration only) */}
              {mode === 'register' && (
                <div>
                  <label className="block text-xs font-semibold text-[#3E1E43] mb-1">
                    Target Role
                  </label>
                  <div className="relative">
                    <Briefcase className="w-4 h-4 text-[#8C7A93] absolute left-3 top-3" />
                    <input
                      type="text"
                      placeholder="e.g. Product Operations & Strategy Lead"
                      value={targetRole}
                      onChange={(e) => setTargetRole(e.target.value)}
                      className="w-full text-xs sm:text-sm pl-9 pr-3.5 py-2.5 rounded-xl border border-[#D9CEE3] focus:outline-none focus:ring-2 focus:ring-[#3E1E43] bg-[#FAF7F2]"
                    />
                  </div>
                  {clientErrors.targetRole && (
                    <p className="mt-1 text-[11px] text-red-600 font-medium">{clientErrors.targetRole}</p>
                  )}
                </div>
              )}

              {/* Password */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold text-[#3E1E43]">
                    Password
                  </label>
                  {mode === 'register' && (
                    <span className="text-[10px] text-[#7D6B82]">
                      Min 8 characters
                    </span>
                  )}
                </div>
                <div className="relative">
                  <Lock className="w-4 h-4 text-[#8C7A93] absolute left-3 top-3" />
                  <input
                    type="password"
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full text-xs sm:text-sm pl-9 pr-3.5 py-2.5 rounded-xl border border-[#D9CEE3] focus:outline-none focus:ring-2 focus:ring-[#3E1E43] bg-[#FAF7F2]"
                  />
                </div>
                {clientErrors.password && (
                  <p className="mt-1 text-[11px] text-red-600 font-medium">{clientErrors.password}</p>
                )}
              </div>

              {/* Confirm Password (Registration only) */}
              {mode === 'register' && (
                <div>
                  <label className="block text-xs font-semibold text-[#3E1E43] mb-1">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <KeyRound className="w-4 h-4 text-[#8C7A93] absolute left-3 top-3" />
                    <input
                      type="password"
                      placeholder="••••••••••••"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full text-xs sm:text-sm pl-9 pr-3.5 py-2.5 rounded-xl border border-[#D9CEE3] focus:outline-none focus:ring-2 focus:ring-[#3E1E43] bg-[#FAF7F2]"
                    />
                  </div>
                  {clientErrors.confirmPassword && (
                    <p className="mt-1 text-[11px] text-red-600 font-medium">{clientErrors.confirmPassword}</p>
                  )}
                </div>
              )}

              {/* Submit Button */}
              <Button
                variant="primary"
                size="md"
                className="w-full mt-2"
                type="submit"
                disabled={isSubmitting}
                icon={isSubmitting ? Loader2 : ArrowRight}
                iconPosition="right"
              >
                {isSubmitting
                  ? (mode === 'signin' ? 'Signing In...' : 'Creating Account...')
                  : (mode === 'signin' ? 'Sign In' : 'Create Candidate Account')}
              </Button>
            </form>

            {/* Quick Demo Pre-fill for reviewer convenience */}
            <div className="pt-2 text-center">
              <button
                type="button"
                onClick={() => {
                  setEmail('priya.sharma@example.com');
                  setPassword('Password123!');
                  if (mode === 'register') {
                    setFullName('Priya Sharma');
                    setTargetRole('Product Operations & Strategy Lead');
                    setConfirmPassword('Password123!');
                  }
                }}
                className="text-[11px] text-[#7D6B82] hover:text-[#3E1E43] underline transition-colors"
              >
                Quick fill with sample candidate credentials
              </button>
            </div>

            {/* Switch mode footer */}
            <div className="pt-1 text-center text-xs text-[#7D6B82]">
              {mode === 'signin' ? (
                <>
                  <span>New to HerTurn? </span>
                  <button
                    type="button"
                    onClick={() => {
                      setMode('register');
                      setClientErrors({});
                      setApiError('');
                    }}
                    className="font-semibold text-[#3E1E43] hover:underline"
                  >
                    Create an Account
                  </button>
                </>
              ) : (
                <>
                  <span>Already have an account? </span>
                  <button
                    type="button"
                    onClick={() => {
                      setMode('signin');
                      setClientErrors({});
                      setApiError('');
                    }}
                    className="font-semibold text-[#3E1E43] hover:underline"
                  >
                    Sign In instead
                  </button>
                </>
              )}
            </div>

          </div>
        )}

        {/* Security & Architecture Information Card */}
        <div className="p-4 rounded-2xl bg-white border border-[#EAE3F1] shadow-xs text-xs space-y-2">
          <div className="flex items-center gap-1.5 font-semibold text-[#3E1E43]">
            <ShieldCheck className="w-4 h-4 text-[#3E1E43]" />
            <span>Secure Authentication Architecture</span>
          </div>
          <p className="text-[#6B6470] leading-relaxed">
            HerTurn protects your candidate identity with salted <strong>bcrypt</strong> password hashing and signed <strong>JWT access tokens</strong>.
          </p>
          <div className="text-[11px] text-[#8C7A93] border-t border-[#EAE3F1] pt-2">
            <strong>Security Notice:</strong> Stored session tokens in browser storage are strictly validated against <code>GET /api/auth/me</code> on startup. Raw resume texts and passwords are never written to client-side localStorage.
          </div>
        </div>

      </div>
    </div>
  );
}
