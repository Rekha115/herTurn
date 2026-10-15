import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  UploadCloud, 
  FileCheck, 
  Trash2, 
  ArrowRight, 
  ArrowLeft, 
  ShieldCheck, 
  AlertCircle, 
  Sparkles, 
  Briefcase, 
  Clock, 
  CheckCircle2,
  Loader2,
  RefreshCw
} from 'lucide-react';
import Button from '../components/Button';
import ProgressIndicator from '../components/ProgressIndicator';
import { uploadAndAnalyzeResume, USE_MOCK_DATA } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  // Wizard state: 1: Resume Upload, 2: Career Details, 3: Review & Analyze
  const [currentStep, setCurrentStep] = useState(1);

  // Resume File State
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileError, setFileError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [uploadConfirmation, setUploadConfirmation] = useState('');

  // Form Details State - Initially EMPTY so user enters details fresh
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    targetRole: '',
    previousRole: '',
    totalExperience: '',
    breakDuration: '',
    skills: '',
    careerGoals: '',
    workMode: '',
    preferredLocation: '',
  });

  // Validation errors for step 2
  const [formErrors, setFormErrors] = useState({});

  // Loading state during analysis submission (triggered ONLY upon explicit user launch in Step 3)
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStatusText, setAnalysisStatusText] = useState('Extracting work history...');
  const [apiError, setApiError] = useState('');

  const steps = [
    { title: 'Resume Upload', subtitle: 'PDF or DOCX' },
    { title: 'Career Details', subtitle: 'Experience & Goals' },
    { title: 'Review & Analyze', subtitle: 'Launch Analysis' },
  ];

  // File Upload Handlers
  const handleFileValidation = (file) => {
    setFileError('');
    setUploadConfirmation('');
    if (!file) return;

    const validTypes = [
      'application/pdf', 
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
      'application/msword'
    ];
    const maxSizeBytes = 5 * 1024 * 1024; // 5 MB

    const extension = file.name.split('.').pop().toLowerCase();
    const isExtensionValid = ['pdf', 'docx', 'doc'].includes(extension);

    if (!validTypes.includes(file.type) && !isExtensionValid) {
      setFileError('Please select a valid PDF or DOCX resume document.');
      return;
    }

    if (file.size > maxSizeBytes) {
      setFileError('File size exceeds the 5MB limit. Please upload a smaller file.');
      return;
    }

    // Successfully validated: save file state and display confirmation without auto-navigating
    setSelectedFile(file);
    setUploadConfirmation(`${file.name} (${Math.round(file.size / 1024)} KB) validated successfully.`);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileValidation(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileValidation(e.target.files[0]);
    }
  };

  // Step 2 Form Handlers
  const handleInputChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (formErrors[field]) {
      setFormErrors((prev) => ({ ...prev, [field]: '' }));
    }
  };

  const validateStep2 = () => {
    const errors = {};
    if (!formData.fullName.trim()) errors.fullName = 'Please enter your name';
    if (!formData.email.trim() || !formData.email.includes('@')) errors.email = 'Please enter a valid email address';
    if (!formData.targetRole.trim()) errors.targetRole = 'Please enter your target role or career goals';
    if (!formData.breakDuration.trim()) errors.breakDuration = 'Please specify career break duration and context';
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Step Navigation - each transition is strictly user-initiated
  const handleNext = () => {
    if (currentStep === 1) {
      if (!selectedFile) {
        setFileError('Please select or upload a resume file (.pdf or .docx) to proceed.');
        return;
      }
      setFileError('');
      // Advance to Step 2 with clean fields
      setCurrentStep(2);
    } else if (currentStep === 2) {
      if (validateStep2()) {
        setCurrentStep(3);
      }
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  // Final Action: Launch Analysis / Parse Document (Executed ONLY from Step 3 when user clicks button)
  const handleAnalyzeResume = async () => {
    setIsAnalyzing(true);
    setApiError('');
    setAnalysisStatusText(USE_MOCK_DATA ? 'Extracting historical roles & credentials...' : 'Extracting resume text with PyMuPDF / docx...');

    try {
      if (USE_MOCK_DATA) {
        setTimeout(() => setAnalysisStatusText('Identifying core strengths & capabilities...'), 600);
        setTimeout(() => setAnalysisStatusText('Comparing with contemporary industry tool requirements...'), 1200);
        setTimeout(() => setAnalysisStatusText('Synthesizing customized 4-week roadmap & returnships...'), 1800);
      }

      const result = await uploadAndAnalyzeResume(
        selectedFile,
        formData,
        (msg) => setAnalysisStatusText(msg)
      );

      // Generate a unique resumeId for this specific upload
      const resumeAnalysisId = result.recordId || null;
      const resumeId = resumeAnalysisId
        ? `analysis_${resumeAnalysisId}`
        : `resume_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;

      const candidateProfile = {
        ...formData,
        resumeId,
        resumeAnalysisId,
        fullName: formData.fullName || user?.fullName || 'Candidate',
        email: formData.email || user?.email || '',
        targetRole: formData.targetRole || 'Technology Professional',
        previousRole: formData.previousRole || 'Professional',
        breakDuration: formData.breakDuration || 'Career Pause',
        workMode: formData.workMode || 'Hybrid',
        preferredLocation: formData.preferredLocation || 'Flexible',
        resumeFileName: selectedFile?.name || 'Uploaded_Resume.pdf',
        resumeFileSize: selectedFile?.size ? `${Math.round(selectedFile.size / 1024)} KB` : '248 KB',
      };

      try {
        // Invalidate stale roadmap caches so the new upload never displays previous resume plans
        Object.keys(sessionStorage).forEach((key) => {
          if (
            key.startsWith('herturn_roadmap_cache_') ||
            key.startsWith('herturn_roadmap_meta') ||
            key.startsWith('herturn_roadmap_tasks_')
          ) {
            sessionStorage.removeItem(key);
          }
        });

        sessionStorage.setItem('herturn_session', JSON.stringify({
          candidate: candidateProfile,
          llmAnalysis: result.llmAnalysis,
          resumeAnalysisId,
          resumeId,
          isLiveAnalyzed: !USE_MOCK_DATA && Boolean(result.llmAnalysis),
          modelUsed: result.modelUsed,
          extractedWordCount: result.wordCount,
          isLiveParsed: !USE_MOCK_DATA
        }));
      } catch (_) {}

      setTimeout(() => {
        setIsAnalyzing(false);
        navigate('/dashboard', { 
          state: { 
            fromOnboarding: true,
            isLiveParsed: !USE_MOCK_DATA,
            isLiveAnalyzed: !USE_MOCK_DATA && Boolean(result.llmAnalysis),
            extractedWordCount: result.wordCount,
            modelUsed: result.modelUsed,
            llmAnalysis: result.llmAnalysis,
            candidate: candidateProfile,
            resumeAnalysisId,
            resumeId
          } 
        });
      }, USE_MOCK_DATA ? 1800 : 400);

    } catch (err) {
      console.error(err);
      setIsAnalyzing(false);
      setApiError(err.message || 'Failed to analyze resume. Please verify the backend is running.');
    }
  };

  // Render Full Screen Analysis Loading Transition
  if (isAnalyzing) {
    return (
      <div className="min-h-screen bg-[#FAF7F2] flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-white rounded-3xl p-8 border border-[#EAE3F1] shadow-xl text-center space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-[#EAE3F1] text-[#3E1E43] mx-auto flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-[#3E1E43]" />
          </div>

          <div className="space-y-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#7D6B82] bg-[#FAF7F2] px-3 py-1 rounded-full border border-[#EAE3F1]">
              {USE_MOCK_DATA ? 'Simulating Demo Analysis' : 'Live Document Ingestion'}
            </span>
            <h2 className="font-serif text-2xl font-bold text-[#3E1E43]">
              {USE_MOCK_DATA ? 'Analyzing Your Experience' : 'Extracting Document Text'}
            </h2>
            <p className="text-xs text-[#6B6470] animate-pulse h-6">
              {analysisStatusText}
            </p>
          </div>

          <div className="w-full bg-[#FAF7F2] h-2 rounded-full overflow-hidden border border-[#EAE3F1]">
            <div className="bg-[#3E1E43] h-full rounded-full animate-[shimmer_2s_infinite]" style={{ width: '85%' }}></div>
          </div>

          <div className="text-[11px] text-[#8C7A93] bg-[#FAF7F2] p-3 rounded-xl border border-[#EAE3F1]">
            {USE_MOCK_DATA 
              ? 'Notice: In demo mode, sample heuristics showcase the end-to-end user experience.'
              : 'Notice: PyMuPDF/python-docx extracts document text, and Google Gemini synthesizes verified competencies.'}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAF7F2] py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        
        {/* Top Header */}
        <div className="text-center mb-8">
          <span className="text-xs uppercase font-bold tracking-widest text-[#7D6B82]">
            Resume Analysis & Profile Builder
          </span>
          <h1 className="font-serif text-3xl sm:text-4xl font-bold text-[#3E1E43] mt-1">
            Let's Shape Your Return
          </h1>
          <p className="text-sm text-[#6B6470] mt-1.5 max-w-lg mx-auto">
            Provide your resume and career preferences so we can map out your tailored learning roadmap and matched returnships.
          </p>
        </div>

        {/* Multi-step progress indicator */}
        <ProgressIndicator steps={steps} currentStep={currentStep} />

        {/* Card Container */}
        <div className="bg-white rounded-3xl border border-[#EAE3F1] shadow-md p-6 sm:p-10 transition-all">

          {/* ================= STEP 1: RESUME UPLOAD ================= */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="font-serif text-xl font-bold text-[#3E1E43]">
                  Step 1: Upload Your Existing Resume
                </h2>
                <p className="text-xs text-[#6B6470] mt-1">
                  Don't worry about career gaps or older formatting. We analyze your foundational expertise and skills.
                </p>
              </div>

              {/* Upload Drag & Drop Area */}
              {!selectedFile ? (
                <div
                  onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer ${
                    isDragging 
                      ? 'border-[#3E1E43] bg-[#EAE3F1]/30' 
                      : 'border-[#D9CEE3] hover:border-[#3E1E43]/60 bg-[#FAF7F2]/50'
                  }`}
                  onClick={() => document.getElementById('resume-file-input')?.click()}
                >
                  <input
                    id="resume-file-input"
                    type="file"
                    accept=".pdf,.docx,.doc"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <div className="w-14 h-14 rounded-2xl bg-[#EAE3F1] text-[#3E1E43] mx-auto flex items-center justify-center mb-4">
                    <UploadCloud className="w-7 h-7" />
                  </div>
                  <h3 className="font-semibold text-sm text-[#2B282C]">
                    Drag and drop your resume file here
                  </h3>
                  <p className="text-xs text-[#7D6B82] mt-1 mb-4">
                    Supports PDF, DOCX (Max 5MB)
                  </p>
                  <Button variant="outline" size="sm" type="button">
                    Browse Files
                  </Button>
                </div>
              ) : (
                /* Selected File Preview Box & Confirmation State */
                <div className="p-5 rounded-2xl border border-emerald-200 bg-emerald-50/40 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-11 h-11 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center shrink-0">
                        <FileCheck className="w-6 h-6 text-emerald-700" />
                      </div>
                      <div className="truncate">
                        <div className="text-sm font-semibold text-[#2B282C] truncate">
                          {selectedFile.name}
                        </div>
                        <div className="text-xs text-emerald-800 font-medium flex items-center gap-1.5 mt-0.5">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                          <span>
                            {selectedFile.size ? `${Math.round(selectedFile.size / 1024)} KB` : 'Validated'} • File Validated & Ready
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedFile(null);
                          setUploadConfirmation('');
                        }}
                        className="p-2 text-rose-600 hover:bg-rose-50 rounded-xl transition-colors"
                        title="Remove file"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <div className="p-3 bg-white/80 rounded-xl border border-emerald-100 text-xs text-emerald-950 flex items-center justify-between">
                    <span>File is confirmed. You can now proceed to Step 2 to enter your career preferences.</span>
                    <button
                      type="button"
                      onClick={() => document.getElementById('resume-file-input')?.click()}
                      className="text-xs font-semibold text-[#3E1E43] hover:underline shrink-0 ml-3"
                    >
                      Change File
                    </button>
                    <input
                      id="resume-file-input"
                      type="file"
                      accept=".pdf,.docx,.doc"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                  </div>
                </div>
              )}

              {/* Error Alert */}
              {fileError && (
                <div className="flex items-center gap-2 p-3 text-xs rounded-xl bg-rose-50 text-rose-800 border border-rose-200">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                  <span>{fileError}</span>
                </div>
              )}

              {/* Privacy Reassurance Note */}
              <div className="flex items-start gap-2.5 pt-2 text-xs text-[#7D6B82]">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <p>
                  <strong>Privacy First:</strong> Your resume is utilized exclusively to generate your personalized career insights. We do not sell or expose candidate records.
                </p>
              </div>
            </div>
          )}

          {/* ================= STEP 2: PROFESSIONAL DETAILS (ALL EDITABLE FIELDS INITIALLY EMPTY) ================= */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="font-serif text-xl font-bold text-[#3E1E43]">
                  Step 2: Career Preferences & Background
                </h2>
                <p className="text-xs text-[#6B6470] mt-1">
                  Enter your background, skills, and target goals below. All fields can be manually entered and edited.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                
                {/* Full Name */}
                <div>
                  <label className="block text-xs font-semibold text-[#3E1E43] mb-1">
                    Full Name *
                  </label>
                  <input
                    type="text"
                    value={formData.fullName}
                    onChange={(e) => handleInputChange('fullName', e.target.value)}
                    placeholder="Enter your full name"
                    className="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-[#D9CEE3] focus:outline-none focus:ring-2 focus:ring-[#3E1E43] bg-[#FAF7F2]"
                  />
                  {formErrors.fullName && <p className="text-[11px] text-rose-600 mt-1">{formErrors.fullName}</p>}
                </div>

                {/* Email Address */}
                <div>
                  <label className="block text-xs font-semibold text-[#3E1E43] mb-1">
                    Email Address *
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    placeholder="Enter your email address"
                    className="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-[#D9CEE3] focus:outline-none focus:ring-2 focus:ring-[#3E1E43] bg-[#FAF7F2]"
                  />
                  {formErrors.email && <p className="text-[11px] text-rose-600 mt-1">{formErrors.email}</p>}
                </div>

                {/* Target Role / Career Goals */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-semibold text-[#3E1E43] mb-1">
                    Target Role or Career Direction *
                  </label>
                  <input
                    type="text"
                    value={formData.targetRole}
                    onChange={(e) => handleInputChange('targetRole', e.target.value)}
                    placeholder="Enter your career goals (e.g. Frontend Developer, Product Operations Lead, Data Analyst)"
                    className="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-[#D9CEE3] focus:outline-none focus:ring-2 focus:ring-[#3E1E43] bg-[#FAF7F2]"
                  />
                  {formErrors.targetRole && <p className="text-[11px] text-rose-600 mt-1">{formErrors.targetRole}</p>}
                </div>

                {/* Previous Job Role */}
                <div>
                  <label className="block text-xs font-semibold text-[#3E1E43] mb-1">
                    Previous Role (Prior to Break)
                  </label>
                  <input
                    type="text"
                    value={formData.previousRole}
                    onChange={(e) => handleInputChange('previousRole', e.target.value)}
                    placeholder="Enter your experience (e.g. Senior Business Analyst)"
                    className="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-[#D9CEE3] focus:outline-none focus:ring-2 focus:ring-[#3E1E43] bg-[#FAF7F2]"
                  />
                </div>

                {/* Total Experience */}
                <div>
                  <label className="block text-xs font-semibold text-[#3E1E43] mb-1">
                    Total Prior Experience
                  </label>
                  <select
                    value={formData.totalExperience}
                    onChange={(e) => handleInputChange('totalExperience', e.target.value)}
                    className="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-[#D9CEE3] focus:outline-none focus:ring-2 focus:ring-[#3E1E43] bg-[#FAF7F2]"
                  >
                    <option value="">Select your prior experience</option>
                    <option value="1–2 years">1–2 years</option>
                    <option value="3–5 years">3–5 years</option>
                    <option value="5–8 years">5–8 years</option>
                    <option value="8+ years">8+ years</option>
                  </select>
                </div>

                {/* Career Break Duration */}
                <div>
                  <label className="block text-xs font-semibold text-[#3E1E43] mb-1">
                    Career Break Duration & Context *
                  </label>
                  <input
                    type="text"
                    value={formData.breakDuration}
                    onChange={(e) => handleInputChange('breakDuration', e.target.value)}
                    placeholder="Enter your career break duration and context (e.g. 3 years for parenting / caregiving)"
                    className="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-[#D9CEE3] focus:outline-none focus:ring-2 focus:ring-[#3E1E43] bg-[#FAF7F2]"
                  />
                  {formErrors.breakDuration && <p className="text-[11px] text-rose-600 mt-1">{formErrors.breakDuration}</p>}
                </div>

                {/* Core Skills Input */}
                <div>
                  <label className="block text-xs font-semibold text-[#3E1E43] mb-1">
                    Key Skills & Competencies
                  </label>
                  <input
                    type="text"
                    value={formData.skills}
                    onChange={(e) => handleInputChange('skills', e.target.value)}
                    placeholder="Enter your skills (e.g. React, Python, SQL, Project Management)"
                    className="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-[#D9CEE3] focus:outline-none focus:ring-2 focus:ring-[#3E1E43] bg-[#FAF7F2]"
                  />
                </div>

                {/* Career Goals */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-semibold text-[#3E1E43] mb-1">
                    Career Goals & Return Vision
                  </label>
                  <input
                    type="text"
                    value={formData.careerGoals}
                    onChange={(e) => handleInputChange('careerGoals', e.target.value)}
                    placeholder="Enter your career goals (e.g. Transition into technical product management)"
                    className="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-[#D9CEE3] focus:outline-none focus:ring-2 focus:ring-[#3E1E43] bg-[#FAF7F2]"
                  />
                </div>

                {/* Work Arrangement Preference */}
                <div>
                  <label className="block text-xs font-semibold text-[#3E1E43] mb-1">
                    Preferred Work Arrangement
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {['Remote', 'Hybrid', 'On-site'].map((mode) => (
                      <button
                        key={mode}
                        type="button"
                        onClick={() => handleInputChange('workMode', mode)}
                        className={`py-2 px-2 text-xs rounded-xl font-medium border text-center transition-all ${
                          formData.workMode === mode
                            ? 'bg-[#3E1E43] text-white border-[#3E1E43]'
                            : 'bg-[#FAF7F2] text-[#4A454D] border-[#D9CEE3] hover:border-[#3E1E43]'
                        }`}
                      >
                        {mode}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Preferred Location */}
                <div>
                  <label className="block text-xs font-semibold text-[#3E1E43] mb-1">
                    Preferred Location / Cities
                  </label>
                  <input
                    type="text"
                    value={formData.preferredLocation}
                    onChange={(e) => handleInputChange('preferredLocation', e.target.value)}
                    placeholder="Enter preferred location or Remote"
                    className="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-[#D9CEE3] focus:outline-none focus:ring-2 focus:ring-[#3E1E43] bg-[#FAF7F2]"
                  />
                </div>

              </div>
            </div>
          )}

          {/* ================= STEP 3: REVIEW AND ANALYZE ================= */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div>
                <h2 className="font-serif text-xl font-bold text-[#3E1E43]">
                  Step 3: Review Details & Launch Analysis
                </h2>
                <p className="text-xs text-[#6B6470] mt-1">
                  Double check your profile configuration. You can edit any parameter prior to generating your plan.
                </p>
              </div>

              {/* Review summary box */}
              <div className="bg-[#FAF7F2] p-5 rounded-2xl border border-[#EAE3F1] space-y-4">
                
                {/* File preview */}
                <div className="flex items-center justify-between pb-3 border-b border-[#EAE3F1]">
                  <div className="flex items-center gap-3">
                    <FileCheck className="w-5 h-5 text-[#3E1E43]" />
                    <div>
                      <div className="text-xs font-semibold text-[#2B282C]">{selectedFile?.name || 'Resume Document'}</div>
                      <div className="text-[11px] text-[#7D6B82]">
                        {selectedFile?.size ? `${Math.round(selectedFile.size / 1024)} KB • ` : ''}Validated for analysis
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setCurrentStep(1)}
                    className="text-xs text-[#3E1E43] font-semibold hover:underline cursor-pointer"
                  >
                    Change File
                  </button>
                </div>

                {/* Details grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-[#8C7A93] block">Candidate:</span>
                    <span className="font-semibold text-[#2B282C]">{formData.fullName || 'Not provided'} ({formData.email || 'No email'})</span>
                  </div>
                  <div>
                    <span className="text-[#8C7A93] block">Target Role:</span>
                    <span className="font-semibold text-[#3E1E43]">{formData.targetRole || 'Not specified'}</span>
                  </div>
                  <div>
                    <span className="text-[#8C7A93] block">Prior Background:</span>
                    <span className="font-semibold text-[#2B282C]">{formData.previousRole || 'Not specified'} {formData.totalExperience ? `• ${formData.totalExperience}` : ''}</span>
                  </div>
                  <div>
                    <span className="text-[#8C7A93] block">Career Hiatus:</span>
                    <span className="font-semibold text-[#2B282C]">{formData.breakDuration || 'Not specified'}</span>
                  </div>
                  {formData.skills && (
                    <div className="sm:col-span-2">
                      <span className="text-[#8C7A93] block">Skills Specified:</span>
                      <span className="font-semibold text-[#2B282C]">{formData.skills}</span>
                    </div>
                  )}
                  <div>
                    <span className="text-[#8C7A93] block">Work Mode & Location:</span>
                    <span className="font-semibold text-[#2B282C]">{(formData.workMode || 'Flexible')} {formData.preferredLocation ? `• ${formData.preferredLocation}` : ''}</span>
                  </div>
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    type="button"
                    onClick={() => setCurrentStep(2)}
                    className="text-xs text-[#3E1E43] font-semibold hover:underline cursor-pointer"
                  >
                    Edit Details
                  </button>
                </div>
              </div>

              {/* Api Error Alert with Retry button */}
              {apiError && (
                <div className="flex items-start justify-between gap-3 p-4 text-xs rounded-xl bg-rose-50 text-rose-800 border border-rose-200">
                  <div className="flex items-start gap-2.5">
                    <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
                    <div>
                      <span className="font-semibold block">Resume Processing Error</span>
                      <span>{apiError}</span>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleAnalyzeResume}
                    icon={RefreshCw}
                    iconPosition="left"
                    className="bg-white text-rose-900 border-rose-300 shrink-0"
                  >
                    Try Again
                  </Button>
                </div>
              )}

              {/* Mode Notice */}
              <div className="p-4 rounded-xl bg-purple-50/70 border border-purple-200/80 text-xs text-[#3E1E43] flex items-start gap-2.5">
                <Sparkles className="w-4 h-4 text-[#5C2B64] shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block">
                    Ready to Generate Your Personalized Insights
                  </span>
                  <span>
                    Click "Launch Analysis" below to extract your resume text and generate your verified skills, skill gaps, and custom career roadmap.
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Form Navigation Controls */}
          <div className="mt-8 pt-6 border-t border-[#EAE3F1] flex items-center justify-between">
            {currentStep > 1 ? (
              <Button
                variant="outline"
                size="md"
                onClick={handleBack}
                icon={ArrowLeft}
                iconPosition="left"
              >
                Back
              </Button>
            ) : (
              <div />
            )}

            {currentStep < 3 ? (
              <Button
                variant="primary"
                size="md"
                onClick={handleNext}
                icon={ArrowRight}
                iconPosition="right"
              >
                {currentStep === 1 ? 'Continue to Career Details' : 'Continue to Review'}
              </Button>
            ) : (
              <Button
                variant="primary"
                size="md"
                onClick={handleAnalyzeResume}
                icon={Sparkles}
                iconPosition="left"
              >
                Launch Analysis
              </Button>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
