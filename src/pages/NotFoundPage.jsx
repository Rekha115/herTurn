import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Compass, Home } from 'lucide-react';
import Button from '../components/Button';

export default function NotFoundPage() {
  return (
    <div className="min-h-[70vh] flex items-center justify-center py-20 px-4 text-center">
      <div className="max-w-md w-full bg-white rounded-3xl border border-[#EAE3F1] shadow-sm p-8 sm:p-10 space-y-5">
        <div className="w-16 h-16 rounded-2xl bg-[#EAE3F1] text-[#3E1E43] mx-auto flex items-center justify-center font-serif text-2xl font-bold">
          404
        </div>
        <h1 className="font-serif text-2xl font-bold text-[#3E1E43]">
          Page Not Found
        </h1>
        <p className="text-xs text-[#6B6470] leading-relaxed">
          The page you are looking for doesn't exist or has moved. Let's get you back on track to your career roadmap.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <Link to="/">
            <Button variant="outline" size="sm" icon={Home} iconPosition="left">
              Home
            </Button>
          </Link>
          <Link to="/dashboard">
            <Button variant="primary" size="sm" icon={Compass} iconPosition="left">
              Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
