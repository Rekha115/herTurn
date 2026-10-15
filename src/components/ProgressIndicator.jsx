import React from 'react';
import { Check } from 'lucide-react';

export default function ProgressIndicator({ steps, currentStep }) {
  return (
    <div className="w-full max-w-2xl mx-auto mb-10">
      <div className="flex items-center justify-between relative">
        
        {/* Background track */}
        <div className="absolute top-1/2 left-0 right-0 -translate-y-1/2 h-1 bg-[#EAE3F1] -z-0" />
        
        {/* Active track bar */}
        <div 
          className="absolute top-1/2 left-0 -translate-y-1/2 h-1 bg-[#3E1E43] -z-0 transition-all duration-300"
          style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
        />

        {steps.map((step, idx) => {
          const stepNumber = idx + 1;
          const isCompleted = stepNumber < currentStep;
          const isCurrent = stepNumber === currentStep;

          return (
            <div key={step.title} className="flex flex-col items-center relative z-10">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm transition-all duration-300 ${
                  isCompleted
                    ? 'bg-[#3E1E43] text-white shadow-xs'
                    : isCurrent
                    ? 'bg-[#3E1E43] text-white ring-4 ring-[#EAE3F1] shadow-sm'
                    : 'bg-white text-[#7D6B82] border-2 border-[#D9CEE3]'
                }`}
              >
                {isCompleted ? <Check className="w-5 h-5 text-white" /> : stepNumber}
              </div>
              <div className="mt-2 text-center">
                <span
                  className={`text-xs font-medium block whitespace-nowrap ${
                    isCurrent ? 'text-[#3E1E43] font-bold' : isCompleted ? 'text-[#4A454D]' : 'text-[#8C7A93]'
                  }`}
                >
                  {step.title}
                </span>
                {step.subtitle && (
                  <span className="text-[10px] text-[#8C7A93] hidden sm:block">
                    {step.subtitle}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
