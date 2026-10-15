// Mock / configurable API service layer for HerTurn frontend
// Seamless switching between default Mock mode and live FastAPI + Gemini backend

// Base URL normalization (handles relative /api or direct localhost:8000)
const envBaseUrl = import.meta.env.VITE_API_BASE_URL;
export const API_BASE_URL = envBaseUrl 
  ? (envBaseUrl.endsWith('/api') ? envBaseUrl : `${envBaseUrl.replace(/\/$/, '')}/api`)
  : '/api';

// Mock mode flag:
// Explicitly controlled via VITE_USE_MOCK ('false' disables mock, 'true' enables mock).
// In production builds (import.meta.env.PROD), defaults to false (live backend).
export const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK !== undefined
  ? import.meta.env.VITE_USE_MOCK !== 'false'
  : !import.meta.env.PROD;


/**
 * Health check query to backend
 */
export async function checkBackendHealth() {
  if (USE_MOCK_DATA) {
    return {
      status: 'mock',
      service: 'HerTurn Frontend Mock Service',
      version: '1.0.0',
      message: 'Running in demo mode without live backend.'
    };
  }

  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Backend health check failed: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Ingest resume file via POST /api/resume/parse
 * Extract text with PyMuPDF / python-docx
 * 
 * @param {File} file 
 */
export async function parseResumeDocument(file) {
  if (USE_MOCK_DATA) {
    await new Promise((resolve) => setTimeout(resolve, 800));
    return {
      success: true,
      filename: file?.name || 'Resume_Priya_Sharma.pdf',
      file_type: 'pdf',
      file_size_bytes: file?.size || 148200,
      word_count: 320,
      extracted_text: "Demonstration extracted resume text with verified background in business analysis and agile operations."
    };
  }

  if (!file) {
    throw new Error('Please select a resume file (.pdf or .docx).');
  }

  // If user used sample candidate button (not an actual binary File instance)
  if (!(file instanceof File) && !(file instanceof Blob)) {
    return {
      success: true,
      filename: file.name || 'Sample_Resume.pdf',
      file_type: 'pdf',
      file_size_bytes: file.size || 248000,
      word_count: 280,
      extracted_text: `Priya Sharma | renuka | rathorerekhan052@gmail.com
Target Role: Chartered Accountant / Senior Financial Analyst
Professional Summary: Experienced finance and accounting professional with 2+ years of background in auditing, statutory compliance, tax preparation, balance sheet reconciliation, and financial modeling.
Key Skills: Financial Auditing, GAAP Compliance, Balance Sheet Reconciliation, Corporate Taxation, GST Filing, Excel Financial Modeling, ERP & Tally.
Work History:
- Associate Chartered Accountant (2021 - 2023): Executed quarterly financial audit cycles for corporate clients, managed ledger reconciliations, and reduced reporting variance.
Education: Chartered Accountancy (ICAI), Bachelor of Commerce (B.Com).`
    };
  }

  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/resume/parse`, {
    method: 'POST',
    body: formData,
  });


  if (!response.ok) {
    let errorDetail = `Failed to parse document: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Perform deep factual resume analysis with Gemini via POST /api/resume/analyze
 * 
 * @param {string} resumeText 
 * @param {Object} candidatePreferences 
 * @param {string} fileName 
 */
export async function analyzeResumeWithGemini(resumeText, candidatePreferences = {}, fileName = '') {
  if (USE_MOCK_DATA) {
    await new Promise((resolve) => setTimeout(resolve, 1400));
    return {
      success: true,
      mode: 'demo',
      targetRole: candidatePreferences.targetRole || 'Product Operations & Strategy Lead',
      analysis: null // triggers demo fallback structure gracefully
    };
  }

  const payload = {
    resumeText: resumeText || '',
    preferences: {
      fullName: candidatePreferences.fullName || null,
      email: candidatePreferences.email || null,
      targetRole: candidatePreferences.targetRole,
      previousRole: candidatePreferences.previousRole || null,
      totalExperience: candidatePreferences.totalExperience || null,
      breakDuration: candidatePreferences.breakDuration || null,
      workMode: candidatePreferences.workMode || null,
      preferredLocation: candidatePreferences.preferredLocation || null,
      areasOfInterest: candidatePreferences.areasOfInterest || []
    },
    fileName: fileName || null
  };

  const response = await fetch(`${API_BASE_URL}/resume/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders()
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    let errorDetail = `Analysis failed: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * End-to-end Onboarding Orchestrator:
 * In live mode:
 *   1. Uploads file to POST /api/resume/parse (PyMuPDF/docx)
 *   2. Sends extracted text to POST /api/resume/analyze (Google Gemini)
 * In mock mode:
 *   Simulates network delay and returns mock status
 * 
 * @param {File} file 
 * @param {Object} candidateDetails 
 */
export async function uploadAndAnalyzeResume(file, candidateDetails = {}, onProgressUpdate = null) {
  if (USE_MOCK_DATA) {
    if (onProgressUpdate) onProgressUpdate('Simulating candidate strength analysis...');
    await new Promise((resolve) => setTimeout(resolve, 1400));
    return {
      success: true,
      mode: 'demo',
      status: 'demo_extracted',
      message: 'Demo resume analysis ready',
      data: {
        fileName: file?.name || 'Resume_Priya_Sharma.pdf',
        fileSize: file?.size || 148200,
        ...candidateDetails
      }
    };
  }

  // 1. Text Extraction
  if (onProgressUpdate) onProgressUpdate('Extracting text from resume file (PyMuPDF / docx)...');
  const parseResult = await parseResumeDocument(file);

  // 2. Gemini Analysis
  if (onProgressUpdate) onProgressUpdate('Analyzing career history and skill gaps with Google Gemini...');
  const analysisResult = await analyzeResumeWithGemini(
    parseResult.extracted_text,
    candidateDetails,
    parseResult.filename
  );

  return {
    success: true,
    mode: 'live',
    status: 'analyzed',
    recordId: analysisResult.recordId || null,
    isPersisted: Boolean(analysisResult.isPersisted),
    modelUsed: analysisResult.modelUsed,
    wordCount: parseResult.word_count,
    llmAnalysis: analysisResult.analysis,
    data: {
      fileName: parseResult.filename,
      fileSize: parseResult.file_size_bytes,
      fileType: parseResult.file_type,
      ...candidateDetails,
    }
  };
}

/**
 * Generate personalized roadmap via POST /api/roadmap/generate
 * @param {Object} options 
 */
export async function generatePersonalizedRoadmap({
  targetRole = 'Product Operations & Strategy Lead',
  durationWeeks = 4,
  analysis = null,
  verifiedSkills = [],
  skillGaps = [],
  preferences = null,
  resumeAnalysisId = null,
  generationId = null
}) {
  if (USE_MOCK_DATA) {
    await new Promise((resolve) => setTimeout(resolve, 600));
    return {
      success: true,
      mode: 'demo',
      targetRole: targetRole || 'Product Operations & Strategy Lead',
      durationWeeks,
      modelUsed: 'demo-mode',
      roadmap: null // tells component to use demoRoadmap in mock mode
    };
  }

  const payload = {
    targetRole,
    durationWeeks,
    analysis,
    verifiedSkills,
    skillGaps,
    preferences,
    resumeAnalysisId: resumeAnalysisId || null,
    generationId: generationId || null
  };

  const response = await fetch(`${API_BASE_URL}/roadmap/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders()
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    let errorDetail = `Failed to generate roadmap: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Fetch personalized roadmap (backwards compatible wrapper)
 * @param {string} role 
 * @param {number} weeks 
 */
export async function fetchCareerRoadmap(role = 'Product Manager', weeks = 4) {
  return generatePersonalizedRoadmap({ targetRole: role, durationWeeks: weeks });
}

/**
 * Retrieve verified learning resources via POST /api/resources/retrieve
 * @param {Object} options
 */
export async function retrieveVerifiedResources({
  targetRole = 'Product Operations & Strategy Lead',
  skillGaps = [],
  topK = 6
} = {}) {
  if (USE_MOCK_DATA) {
    await new Promise((resolve) => setTimeout(resolve, 300));
    return {
      success: true,
      status: 'mock',
      targetRole,
      totalRetrieved: 3,
      isRagUsed: false,
      ragStatus: 'demo_mode',
      resources: [
        {
          id: 'res-react-docs',
          title: 'React Official Documentation: Quick Start & Hooks',
          url: 'https://react.dev/learn',
          provider: 'React Team / Meta',
          type: 'Official Documentation',
          difficulty: 'Beginner',
          description: 'Authoritative guide to React and state architecture.',
          isVerified: true,
          skills: ['React', 'Hooks', 'State Management'],
          targetRoles: ['Frontend Engineer', 'Full Stack Engineer'],
          relevanceScore: 0.92
        }
      ],
      message: 'Demo retrieved resources.'
    };
  }

  const payload = {
    targetRole,
    skillGaps,
    topK
  };

  const response = await fetch(`${API_BASE_URL}/resources/retrieve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    let errorDetail = `Resource retrieval failed: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}


// ============================================================================
// Secure Authentication & JWT Session Management
// ============================================================================

/**
 * SECURITY NOTE ON LOCALSTORAGE TOKEN USAGE:
 * Storing JWT access tokens in browser `localStorage` allows session persistence
 * across page refreshes. However, `localStorage` is accessible to JavaScript
 * running in the same origin and is susceptible to XSS (Cross-Site Scripting).
 *
 * Security measures enforced in HerTurn:
 * 1. ONLY the signed bearer token string is stored in localStorage.
 * 2. Passwords, hashes, and raw resume contents are NEVER written to localStorage.
 * 3. A stored token alone is NEVER treated as proof of authentication; it MUST
 *    be validated against the backend (`GET /api/auth/me`) before trusting user state.
 * 4. Tokens expire automatically (ACCESS_TOKEN_EXPIRE_MINUTES) on the backend.
 * 5. In future production hardening, HttpOnly SameSite=Strict cookies can be used
 *    alongside CSRF protections for defense-in-depth against XSS token exfiltration.
 */
export const TOKEN_STORAGE_KEY = 'herturn_access_token';

export function getStoredToken() {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch (_) {
    return null;
  }
}

export function setStoredToken(token) {
  try {
    if (token) {
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  } catch (_) {}
}

export function clearStoredToken() {
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch (_) {}
}

export function getAuthHeaders() {
  const token = getStoredToken();
  if (token) {
    return {
      Authorization: `Bearer ${token}`
    };
  }
  return {};
}

/**
 * Register a new candidate account via POST /api/auth/register
 * @param {Object} params
 * @param {string} params.email
 * @param {string} params.password
 * @param {string} [params.fullName]
 * @param {string} [params.targetRole]
 */
export async function registerUser({ email, password, fullName, targetRole }) {
  if (USE_MOCK_DATA) {
    await new Promise((resolve) => setTimeout(resolve, 600));
    const mockToken = 'mock_jwt_token_herturn_session_xyz';
    setStoredToken(mockToken);
    return {
      accessToken: mockToken,
      tokenType: 'Bearer',
      expiresInMinutes: 1440,
      user: {
        id: 1,
        email,
        fullName: fullName || 'Demo Candidate',
        isActive: true,
        candidateProfile: {
          id: 1,
          targetRole: targetRole || 'Product Operations & Strategy Lead',
          workMode: 'Hybrid',
          areasOfInterest: []
        }
      },
      message: 'Account created successfully (demo mode).'
    };
  }

  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      email,
      password,
      fullName: fullName || undefined,
      targetRole: targetRole || undefined
    })
  });

  if (!response.ok) {
    let errorDetail = `Registration failed: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  const data = await response.json();
  if (data.accessToken) {
    setStoredToken(data.accessToken);
  }
  return data;
}

/**
 * Sign in existing user via POST /api/auth/login
 * @param {Object} params
 * @param {string} params.email
 * @param {string} params.password
 */
export async function loginUser({ email, password }) {
  if (USE_MOCK_DATA) {
    await new Promise((resolve) => setTimeout(resolve, 600));
    const mockToken = 'mock_jwt_token_herturn_session_xyz';
    setStoredToken(mockToken);
    return {
      accessToken: mockToken,
      tokenType: 'Bearer',
      expiresInMinutes: 1440,
      user: {
        id: 1,
        email,
        fullName: 'Priya Sharma',
        isActive: true,
        candidateProfile: {
          id: 1,
          targetRole: 'Product Operations & Strategy Lead',
          workMode: 'Hybrid',
          areasOfInterest: []
        }
      },
      message: 'Signed in successfully (demo mode).'
    };
  }

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email, password })
  });

  if (!response.ok) {
    let errorDetail = `Sign in failed: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  const data = await response.json();
  if (data.accessToken) {
    setStoredToken(data.accessToken);
  }
  return data;
}

/**
 * Validates the stored token against the backend via GET /api/auth/me
 * Returns user profile if valid; throws error and clears token if expired or invalid.
 */
export async function getCurrentUser() {
  const token = getStoredToken();
  if (!token) {
    return null;
  }

  if (USE_MOCK_DATA) {
    return {
      id: 1,
      email: 'priya.sharma@example.com',
      fullName: 'Priya Sharma',
      isActive: true,
      candidateProfile: {
        id: 1,
        targetRole: 'Product Operations & Strategy Lead',
        workMode: 'Hybrid',
        areasOfInterest: ['Product Discovery', 'Analytics', 'Agile Operations']
      }
    };
  }

  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  if (!response.ok) {
    // Stored token was rejected by backend (expired, revoked, or invalid)
    clearStoredToken();
    let errorDetail = `Session expired: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Log out current session
 */
export function logoutUser() {
  clearStoredToken();
}

/**
 * Retrieve current authenticated candidate's saved resume analyses
 */
export async function fetchCandidateAnalyses() {
  const token = getStoredToken();
  if (!token) {
    return {
      success: true,
      totalCount: 0,
      analyses: [],
      message: 'Guest session: sign in to view persistent analysis history.'
    };
  }

  if (USE_MOCK_DATA) {
    return {
      success: true,
      totalCount: 1,
      analyses: [
        {
          id: 1,
          fileName: 'Resume_Priya_Sharma.pdf',
          fileSizeBytes: 148200,
          wordCount: 320,
          targetRole: 'Product Operations & Strategy Lead',
          modelUsed: 'gemini-3.1-flash-lite-preview',
          structuredAnalysis: null,
          createdAt: new Date().toISOString()
        }
      ],
      message: 'Demo analysis records.'
    };
  }

  const response = await fetch(`${API_BASE_URL}/candidate/analyses`, {
    headers: {
      ...getAuthHeaders()
    }
  });

  if (!response.ok) {
    let errorDetail = `Failed to fetch candidate analyses: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Retrieve current candidate's active roadmap and checklist progress from backend.
 * Optionally filtered by resumeAnalysisId and durationWeeks.
 */
export async function fetchCandidateRoadmap({ resumeAnalysisId = null, durationWeeks = null } = {}) {
  const token = getStoredToken();
  if (!token) {
    return {
      success: true,
      hasRoadmap: false,
      roadmap: null,
      tasksProgress: {},
      message: 'No authenticated session.'
    };
  }

  if (USE_MOCK_DATA) {
    return {
      success: true,
      hasRoadmap: false,
      roadmap: null,
      tasksProgress: {},
      message: 'Demo mode active.'
    };
  }

  const params = new URLSearchParams();
  if (resumeAnalysisId) params.append('resumeAnalysisId', resumeAnalysisId);
  if (durationWeeks) params.append('durationWeeks', durationWeeks);
  const queryStr = params.toString() ? `?${params.toString()}` : '';

  const response = await fetch(`${API_BASE_URL}/candidate/roadmap${queryStr}`, {
    headers: {
      ...getAuthHeaders()
    }
  });

  if (!response.ok) {
    let errorDetail = `Failed to fetch candidate roadmap: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Persist roadmap task checklist changes to the backend
 * @param {Object} params
 * @param {number} [params.roadmapId]
 * @param {string} [params.taskId]
 * @param {boolean} [params.completed]
 * @param {Object} [params.tasksProgress]
 */
export async function updateRoadmapTaskProgress({ roadmapId, taskId, completed, tasksProgress }) {
  const token = getStoredToken();
  if (!token) {
    // In guest mode, checklist changes remain local without network persistence
    return {
      success: true,
      tasksProgress: taskId ? { [taskId]: completed } : tasksProgress,
      message: 'Guest checklist updated locally.'
    };
  }

  if (USE_MOCK_DATA) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return {
      success: true,
      roadmapId: roadmapId || 1,
      tasksProgress: taskId ? { [taskId]: completed } : tasksProgress,
      completedCount: completed ? 1 : 0,
      totalTasksCount: 8,
      completionPercentage: completed ? 12.5 : 0.0,
      message: 'Demo task progress updated.'
    };
  }

  const response = await fetch(`${API_BASE_URL}/candidate/roadmap/progress`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders()
    },
    body: JSON.stringify({
      roadmapId,
      taskId,
      completed,
      tasksProgress
    })
  });

  if (!response.ok) {
    let errorDetail = `Failed to update task progress: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * ============================================================================
 * Phase 3 - Step 4: Returnship Catalog, Matching & Bookmarking APIs
 * ============================================================================
 */

/**
 * Fetch returnships catalog with optional filters and search query.
 */
export async function fetchReturnships({ search, workArrangement, type, skill, category } = {}) {
  const params = new URLSearchParams();
  if (search && search.trim()) params.append('search', search.trim());
  if (workArrangement && workArrangement !== 'All') params.append('workArrangement', workArrangement);
  if (type && type !== 'All') params.append('type', type);
  if (skill && skill !== 'All') params.append('skill', skill);
  if (category && category !== 'All') params.append('category', category);

  const queryStr = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE_URL}/returnships${queryStr}`, {
    headers: {
      ...getAuthHeaders()
    }
  });

  if (!response.ok) {
    let errorDetail = `Failed to fetch returnships: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Compute candidate-specific returnship matches and explainable scores.
 */
export async function matchReturnships({
  targetRole,
  verifiedSkills = [],
  experienceYears,
  breakDuration,
  preferredWorkMode,
  location,
  roleCategory,
  search,
  transferableSkills = []
} = {}) {
  const payload = {
    targetRole: targetRole || null,
    verifiedSkills: Array.isArray(verifiedSkills) ? verifiedSkills : [],
    experienceYears: experienceYears || null,
    breakDuration: breakDuration || null,
    preferredWorkMode: preferredWorkMode || null,
    location: location || null,
    roleCategory: roleCategory || null,
    search: search || null,
    transferableSkills: Array.isArray(transferableSkills) ? transferableSkills : []
  };

  const response = await fetch(`${API_BASE_URL}/returnships/match`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders()
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    let errorDetail = `Failed to match returnships: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Retrieve saved returnship bookmarks for the authenticated candidate.
 */
export async function fetchSavedReturnships() {
  const token = getStoredToken();
  if (!token) {
    return {
      success: true,
      count: 0,
      savedIds: [],
      items: [],
      message: 'No authenticated session.'
    };
  }

  const response = await fetch(`${API_BASE_URL}/returnships/saved`, {
    headers: {
      ...getAuthHeaders()
    }
  });

  if (!response.ok) {
    let errorDetail = `Failed to fetch saved returnships: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Bookmark/save a returnship opportunity.
 */
export async function saveReturnship(returnshipId) {
  const response = await fetch(`${API_BASE_URL}/returnships/save/${encodeURIComponent(returnshipId)}`, {
    method: 'POST',
    headers: {
      ...getAuthHeaders()
    }
  });

  if (!response.ok) {
    let errorDetail = `Failed to save returnship: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Remove a bookmarked returnship opportunity.
 */
export async function removeSavedReturnship(returnshipId) {
  const response = await fetch(`${API_BASE_URL}/returnships/save/${encodeURIComponent(returnshipId)}`, {
    method: 'DELETE',
    headers: {
      ...getAuthHeaders()
    }
  });

  if (!response.ok) {
    let errorDetail = `Failed to remove bookmark: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}


