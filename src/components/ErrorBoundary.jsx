import React from 'react';
import { AlertTriangle, RotateCcw, Home } from 'lucide-react';
import Button from './Button';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('HerTurn ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#FAF7F2] flex items-center justify-center p-6">
          <div className="max-w-lg w-full bg-white rounded-3xl p-8 border border-[#EAE3F1] shadow-xl text-center space-y-6">
            <div className="w-16 h-16 rounded-2xl bg-amber-50 text-amber-700 mx-auto flex items-center justify-center border border-amber-200">
              <AlertTriangle className="w-8 h-8" />
            </div>

            <div className="space-y-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-amber-800 bg-amber-50 px-3 py-1 rounded-full border border-amber-200">
                Application Rendering Notice
              </span>
              <h2 className="font-serif text-2xl font-bold text-[#3E1E43]">
                Something went wrong
              </h2>
              <p className="text-xs text-[#6B6470] leading-relaxed">
                HerTurn encountered an unexpected display issue while rendering this page. You can refresh the view or return to the main portal.
              </p>
            </div>

            {this.state.error && (
              <div className="p-3 bg-red-50/60 border border-red-200 rounded-xl text-left">
                <span className="text-[10px] uppercase font-bold text-red-800 block mb-1">
                  Diagnostics
                </span>
                <p className="text-xs font-mono text-red-900 break-words">
                  {this.state.error.message || String(this.state.error)}
                </p>
              </div>
            )}

            <div className="flex items-center justify-center gap-3 pt-2">
              <Button
                variant="primary"
                size="sm"
                icon={RotateCcw}
                iconPosition="left"
                onClick={this.handleReload}
              >
                Reload Page
              </Button>
              <Button
                variant="outline"
                size="sm"
                icon={Home}
                iconPosition="left"
                onClick={this.handleGoHome}
              >
                Go to Homepage
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
