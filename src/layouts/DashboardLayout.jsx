import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import Footer from '../components/Footer';
import { Menu } from 'lucide-react';

export default function DashboardLayout() {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-[#FAF7F2]">
      <Navbar />

      {/* Subheader bar for mobile to open dashboard drawer */}
      <div className="lg:hidden bg-white border-b border-[#EAE3F1] px-4 py-2.5 flex items-center justify-between">
        <button
          type="button"
          onClick={() => setMobileSidebarOpen(true)}
          className="flex items-center gap-2 text-xs font-semibold text-[#3E1E43] px-3 py-1.5 rounded-lg bg-[#FAF7F2] border border-[#EAE3F1]"
        >
          <Menu className="w-4 h-4" />
          <span>Dashboard Menu</span>
        </button>
        <span className="text-xs text-[#7D6B82] font-medium">HerTurn Portal</span>
      </div>

      <div className="flex-1 flex max-w-7xl w-full mx-auto">
        <Sidebar 
          mobileOpen={mobileSidebarOpen} 
          onClose={() => setMobileSidebarOpen(false)} 
        />
        <main className="flex-1 min-w-0 px-4 sm:px-6 lg:px-8 py-8">
          <Outlet />
        </main>
      </div>

      <Footer />
    </div>
  );
}
