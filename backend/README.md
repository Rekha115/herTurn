# HerTurn Backend — FastAPI, Gemini & Local RAG Service

Phase 2 backend service for **HerTurn**, handling resume ingestion, document parsing, **live factual resume analysis**, **curated vector-search RAG retrieval**, and **personalized career relaunch roadmaps**.

---

## 1. Features & Architecture

### API Endpoints
- **`GET /api/health`**: Health status endpoint confirming service operational status.
- **`POST /api/resume/parse`**:
  - Multipart upload for `.pdf` and `.docx` files.
  - 5 MB file size limit enforcement.
  - PDF text extraction using **PyMuPDF** (`fitz`).
  - Scanned PDF detection (notifies user when image-only/OCR is needed).
  - DOCX text extraction using **python-docx**.
- **`POST /api/resume/analyze`**:
  - Powered by the official Google GenAI Python SDK (`google-genai`).
  - Strict factual grounding: never hallucinates dates, qualifications, or unstated roles.
  - Anti-bias guidelines: never penalizes candidates for career pauses; highlights caregiver transferable adaptability.
  - Strict Pydantic output validation (`StructuredLLMAnalysis`).
  - Extracts verified skills with supporting citations, target role competency gaps, and recommended actions.
- **`POST /api/resources/retrieve` (Phase 2 RAG)**:
  - Retrieves verified learning resources from the local ChromaDB vector store matching candidate's target role and identified skill gaps.
  - Returns canonical URLs, provider, difficulty, resource type, and relevance scores.
- **`POST /api/roadmap/generate` (Phase 2 RAG Integrated)**:
  - Generates personalized 4-week or 6-week career relaunch curriculum.
  - Queries local ChromaDB knowledge base first; passes verified learning resources into Gemini context.
  - Enforces strict anti-hallucination citation rules: only verified resources from knowledge base are cited with exact canonical URLs.
  - Transparent fallback: if vector DB is unavailable or returns no matches, marks `isRagUsed: false` and never falsely claims RAG was used.
- **`POST /api/auth/register` (Phase 3 Step 2 Auth)**:
  - Registers candidate with email, password (min 8 chars), full name, and target role.
  - Hashes passwords securely with **bcrypt** (12 rounds salt). Plaintext passwords are never stored.
  - Automatically initializes candidate profile linked to the new user.
  - Rejects duplicate emails with `409 Conflict`.
  - Issues signed JWT access token (`HS256`).
- **`POST /api/auth/login` (Phase 3 Step 2 Auth)**:
  - Authenticates credentials timing-safely via bcrypt.
  - Verifies account active status (`is_active = True`).
  - Returns signed JWT access token, expiration, and serialized user profile.
- **`GET /api/auth/me` (Phase 3 Step 2 Auth)**:
  - Verifies JWT Bearer token signature, expiration (`exp`), and subject (`sub`).
  - Returns verified user profile and candidate settings.
- **CORS Configured**: Permits requests from the local Vite frontend (`http://localhost:5173`).

---

## 2. Curated RAG Knowledge Base

The platform maintains a curated, version-controlled knowledge base of verified learning resources (`backend/app/rag/knowledge_base.json`).

### Verified Curriculum Domains
1. **Frontend & Full Stack Development**: MDN Web Docs, React.dev, freeCodeCamp.
2. **Backend & Python Engineering**: FastAPI Official Tutorial, Python.org, PostgreSQL Tutorial.
3. **Cloud & DevOps**: Docker Getting Started, AWS Cloud Practitioner, GitHub Actions CI/CD, Azure Fundamentals.
4. **Data Analytics & BI**: Mode Analytics SQL Tutorial, Kaggle Pandas, Microsoft Power BI, Tableau Public.
5. **Product Management & Operations**: Atlassian Agile Coach, Reforge Growth Loops, Lenny's Newsletter 1-Page PRD, Mixpanel Academy, Figma Community.
6. **Career Relaunch & Hiatus Storytelling**: Harvard Business Review (HBR) Career Gap Guide.

> **Canonical URL Guarantee:** 100% of URLs in the knowledge base have been checked and verified. Unverified or fabricated URLs are never marked as verified.

---

## 3. Environment Configuration

1. In the `backend/` directory, create a `.env` file from `.env.example`:
   ```powershell
   cd c:\Users\0116TU\OneDrive\Desktop\slaystack\backend
   Copy-Item .env.example .env
   ```

2. Add your Gemini API key from [Google AI Studio](https://aistudio.google.com/):
   ```env
   GEMINI_API_KEY=AIzaSy...your_actual_key...
   GEMINI_MODEL=gemini-3.1-flash-lite-preview
   ```

3. Database & RAG settings:
   ```env
   # Database configuration (defaults to sqlite:///./herturn.db if omitted)
   DATABASE_URL=sqlite:///./herturn.db
   
   # Vector storage directory for local ChromaDB
   CHROMA_PERSIST_DIR=backend/chroma_db
   ```

> **Privacy & Security Note:** `backend/.env`, `*.db`, and `chroma_db/` are strictly excluded in `.gitignore`. **API keys and resume contents are never logged or exposed.**

---

## 4. Database Setup & ORM Architecture (Phase 3 Foundation)

HerTurn uses **SQLAlchemy 2.x** with local SQLite by default (or any PostgreSQL instance via `DATABASE_URL`).

### Database Models (`backend/app/db/models.py`)
1. **`users`**:
   - `id` (PK, int), `email` (unique index, string), `hashed_password` (string), `full_name` (string), `is_active` (bool), `created_at`, `updated_at`.
   - Cascades deletion to candidate profile, resume analyses, roadmaps, and saved returnships.
2. **`candidate_profiles`**:
   - `id` (PK, int), `user_id` (FK -> users.id, unique index, cascade delete), `target_role` (indexed), `previous_role`, `total_experience`, `break_duration`, `work_mode`, `preferred_location`, `areas_of_interest` (JSON).
3. **`resume_analysis_records`**:
   - `id` (PK, int), `user_id` (FK -> users.id, cascade delete), `file_name`, `file_size_bytes`, `word_count`, `target_role`, `model_used`, `structured_analysis` (native JSON), `created_at`.
4. **`roadmap_records`**:
   - `id` (PK, int), `user_id` (FK -> users.id, cascade delete), `target_role`, `duration_weeks`, `model_used`, `is_rag_used`, `rag_source_count`, `structured_roadmap` (native JSON), `tasks_progress` (native JSON checklist state), `created_at`, `updated_at`.
5. **`saved_returnships`**:
   - `id` (PK, int), `user_id` (FK -> users.id, cascade delete), `returnship_id` (string), `notes` (text), `created_at`.
   - `UniqueConstraint("user_id", "returnship_id")` prevents duplicate bookmarks.

### Safe Initialization & Inspection Commands
- **Automatic Initialization**: FastAPI automatically verifies and creates all tables on application startup via its lifespan context manager.
- **Manual Initialization Command**:
  ```powershell
  python -c "from app.db import init_db; init_db(); print('HerTurn database initialized.')"
  ```
- **Inspect Tables Command**:
  ```powershell
  python -c "from sqlalchemy import inspect; from app.db import engine; print(inspect(engine).get_table_names())"
  ```

---

## 5. Setup, Ingestion & Running the Backend

### Step 1: Activate Virtual Environment
```powershell
cd c:\Users\0116TU\OneDrive\Desktop\slaystack\backend
.\venv\Scripts\Activate.ps1
```

*(If installing dependencies from scratch: `pip install -r requirements.txt`)*

### Step 2: Ingest the Curated Knowledge Base (Idempotent)
Run the repeatable ingestion script to index the curated knowledge base into ChromaDB:
```powershell
python scripts/ingest_knowledge_base.py
```
- Normalizes resource documents, extracts skills and roles.
- Embeds documents locally using ChromaDB's ONNX embedding pipeline.
- Performs idempotent `upsert`: rerunning this command updates records without creating duplicates.

### Step 3: Start the FastAPI Server
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Base: `http://127.0.0.1:8000`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`

---

## 6. Running the Frontend with RAG Integration

In the project root folder (`c:\Users\0116TU\OneDrive\Desktop\slaystack`):

1. Set `.env`:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_USE_MOCK=false
   ```
2. Start the Vite development server:
   ```powershell
   npm run dev
   ```
3. Open `http://localhost:5173/onboarding`:
   - Upload a resume (`.pdf` or `.docx`).
   - Gemini extracts verified skills and identifies role-specific skill gaps.
   - Navigate to `/roadmap` to see the personalized curriculum augmented with **RAG-Verified learning resources**.

---

## 7. Automated Test Suite

Run the complete test suite (50 passing tests):
```powershell
$env:PYTHONPATH="backend"
.\backend\venv\Scripts\pytest backend\tests -v
```

The test suite covers:
- **Authentication & JWT Security (18 tests)**: Secure bcrypt hashing, timing-safe password verification, JWT creation, claims decoding, expiration handling, malformed token rejection, production `JWT_SECRET_KEY` entropy enforcement, candidate registration with profile auto-creation, duplicate email rejection (409 Conflict), login credential verification, account deactivation handling (403 Forbidden), and `/api/auth/me` identity resolution.
- **Database & ORM Models (8 tests)**: Safe table initialization, unique email constraints, 1-to-1 candidate profile relationships, cascading deletes on all child tables, native JSON column serialization/deserialization, duplicate returnship bookmark prevention, SQLite foreign key enforcement, and independent session persistence.
- **Health & Resume Extraction (6 tests)**: Input validation, PyMuPDF parsing, DOCX extraction, 5MB limits.
- **Gemini Analysis (6 tests)**: Mocked structured output validation, error handling, quota limits, model fallbacks.
- **RAG Ingestion & Retrieval (10 tests)**: Knowledge base schema validation, document normalization, idempotent upsert (0 duplicates), semantic search relevance ranking, metadata/URL preservation, and transparent empty/uninitialized collection fallback.
- **Roadmap RAG Integration (2 tests)**: Ingestion of verified citations, anti-hallucination verification (rejecting fake URLs), and transparent fallback when ChromaDB is unavailable.

