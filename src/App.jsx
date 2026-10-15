import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

// Layouts & Nav
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import DashboardLayout from './layouts/DashboardLayout';

// Pages
import LandingPage from './pages/LandingPage';
import OnboardingPage from './pages/OnboardingPage';
import AnalysisDashboard from './pages/AnalysisDashboard';
import RoadmapPage from './pages/RoadmapPage';
import ReturnshipsPage from './pages/ReturnshipsPage';
import SignInPage from './pages/SignInPage';
import NotFoundPage from './pages/NotFoundPage';
import { AuthProvider } from './context/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
        {/* Public Marketing & Onboarding Pages with standard Navbar/Footer */}
        <Route
          path="/"
          element={
            <div className="min-h-screen flex flex-col bg-[#FAF7F2]">
              <Navbar />
              <main className="flex-1">
                <LandingPage />
              </main>
              <Footer />
            </div>
          }
        />

        <Route
          path="/onboarding"
          element={
            <div className="min-h-screen flex flex-col bg-[#FAF7F2]">
              <Navbar />
              <main className="flex-1">
                <OnboardingPage />
              </main>
              <Footer />
            </div>
          }
        />

        <Route
          path="/signin"
          element={
            <div className="min-h-screen flex flex-col bg-[#FAF7F2]">
              <Navbar />
              <main className="flex-1">
                <SignInPage />
              </main>
              <Footer />
            </div>
          }
        />

        {/* Dashboard & Returnship Hub Pages with DashboardLayout */}
        <Route element={<DashboardLayout />}>
          <Route path="/dashboard" element={<AnalysisDashboard />} />
          <Route path="/analysis" element={<OnboardingPage />} />
          <Route path="/resume-analysis" element={<OnboardingPage />} />
          <Route path="/roadmap" element={<RoadmapPage />} />
          <Route path="/returnships" element={<ReturnshipsPage />} />
        </Route>

        {/* Catch-all 404 */}
        <Route
          path="*"
          element={
            <div className="min-h-screen flex flex-col bg-[#FAF7F2]">
              <Navbar />
              <main className="flex-1">
                <NotFoundPage />
              </main>
              <Footer />
            </div>
          }
        />
      </Routes>
    </BrowserRouter>
  </AuthProvider>
</ErrorBoundary>
  );
}

