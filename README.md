# HerTurn — AI-Powered Career Recovery & Returnship Platform

> **Empowering women to return to the workforce with confidence, verified skill roadmaps, and bias-free AI evaluation.**

**HerTurn** is a full-stack career relaunch platform tailored specifically for women and caregivers re-entering the workforce after career breaks (caregiving, maternity leave, family relocation, or professional sabbaticals). By eliminating the traditional "career gap penalty," HerTurn objectively evaluates historical professional strengths, identifies modern tool requirements, and generates personalized, sprint-based learning roadmaps backed by verified educational resources.

---

## 🌟 How It Works

```
 ┌──────────────────────┐      ┌────────────────────────┐      ┌─────────────────────────┐
 │ 1. Profile & Target  │ ───► │  2. Resume Ingestion   │ ───► │  3. Bias-Free AI Eval   │
 │   Role & Hiatus Info │      │   PyMuPDF / docx Parse │      │  Google Gemini Factual  │
 └──────────────────────┘      └────────────────────────┘      └─────────────────────────┘
                                                                            │
 ┌──────────────────────┐      ┌────────────────────────┐                   ▼
 │ 6. Persistent Hub    │ ◄─── │ 5. Returnship Match    │ ◄─── ┌─────────────────────────┐
 │   JWT & SQLite Sync  │      │   Role & Remote Filter │      │  4. RAG-Verified Sprint │
 └──────────────────────┘      └────────────────────────┘      │   ChromaDB Curricula    │
                                                               └─────────────────────────┘
```

### 1. Guided Candidate Onboarding
Candidates begin by specifying their target career direction (e.g., Software Engineer, Product Operations, Data Analyst), hiatus context (family, caregiving, relocation), preferred work mode (Remote, Hybrid, In-Office), and career background.

### 2. Fast, Secure Document Ingestion
- Upload `.pdf` or `.docx` resume files (up to 5 MB).
- High-fidelity in-memory text extraction using **PyMuPDF** (`fitz`) and **python-docx**.
- Built-in scanned document detection that alerts users if an image-only PDF requires OCR.
- **Privacy First**: Documents and extracted texts are processed in memory and never stored as raw personal documents.

### 3. Factual, Bias-Free AI Evaluation (Google Gemini)
- Analyzes candidate background against contemporary industry requirements for the target role.
- **Zero Career Gap Penalty**: Career pauses are never framed as negative deficits or penalized.
- **Evidence-Based Extraction**: Every verified skill is linked to textual evidence and citations from the uploaded resume.
- **Actionable Gap Analysis**: Identifies high-priority competencies to modernize without generic boilerplate advice.

### 4. RAG-Verified Personalized Learning Roadmaps (ChromaDB)
- Automatically queries a local, version-controlled vector store (**ChromaDB**) indexed with vetted curriculum resources (MDN, React.dev, FastAPI, Docker, Kaggle, Atlassian, HBR).
- Generates structured **4-week** or **6-week** relaunch sprints with progressive weekly milestones and concrete deliverables.
- **Anti-Hallucination Guarantee**: Gemini is strictly bounded to cite canonical, verified links from the curated knowledge base. If RAG resources are unavailable, HerTurn transparently reports status rather than fabricating URLs.

### 5. Role-Aligned Returnship Matching & Bookmarking
- Connects candidates with supportive return-to-work opportunities and fellowships.
- Filter returnships by role category, work arrangement (Remote, Hybrid, Onsite), and required skills.
- One-click bookmarking synchronized with candidate accounts.

### 6. Secure Authentication & Profile Isolation
- Fully authenticated session management via **JWT Bearer tokens** and **bcrypt** password hashing.
- **Strict Multi-User Isolation**: Each user's evaluations, roadmaps, task checklists, and bookmarks are isolated in SQLite (`backend/herturn.db`), ensuring switching accounts never leaks previous candidate data.

---

## 🛠️ Architecture & Tech Stack

### Frontend
- **Framework**: React 19 + Vite
- **Styling**: TailwindCSS + Lucide React icons
- **State & Routing**: React Router v7, AuthContext, SessionStorage cache sync
- **Design System**: Warm Plum / Deep Purple palette (`#3E1E43`), responsive layout, accessible typography

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **ORM & Database**: SQLAlchemy with SQLite (`backend/herturn.db`)
- **Document Parsing**: PyMuPDF (`fitz`), `python-docx`
- **AI / LLM**: Google Gemini (`google-genai` SDK, `gemini-2.5-flash` / `gemini-3.1-flash-lite-preview`)
- **Vector Database (RAG)**: ChromaDB with local persistent storage
- **Authentication**: PyJWT (`HS256`), bcrypt password encryption

---

## 🚀 Getting Started

### Prerequisites
- **Node.js**: v18+ (tested on Node 20+)
- **Python**: 3.10+ (tested on Python 3.12 / 3.13)
- **Google Gemini API Key**: [Get API key from Google AI Studio](https://aistudio.google.com/) *(Optional: App supports offline mock mode)*

---

### Backend Setup

1. Open a terminal and navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows PowerShell
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables in `backend/.env` (copy from `backend/.env.example`):
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   JWT_SECRET_KEY=your_secure_random_jwt_secret_key_here
   DATABASE_URL=sqlite:///./herturn.db
   ```

5. **Ingest the Curated Knowledge Base into ChromaDB**:
   ```bash
   python scripts/ingest_knowledge_base.py
   ```
   *Indexes 20 verified curriculum resources into local vector storage (`backend/chroma_db`).*

6. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   - API Documentation (Interactive Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### Frontend Setup

1. In the project root directory, install dependencies:
   ```bash
   npm install
   ```

2. Configure environment variables in `.env` (copy from `.env.example`):
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_USE_MOCK=false
   ```
   *(Set `VITE_USE_MOCK=true` to run completely offline without the backend service)*

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   - Application URL: [http://localhost:5173](http://localhost:5173)

4. Build production bundle:
   ```bash
   npm run build
   ```

---

## 🧪 Automated Testing Suite

HerTurn includes an end-to-end backend test suite covering security, parsing, LLM evaluations, RAG ingestion, and candidate journey:

```bash
cd backend
.\venv\Scripts\python -m pytest tests -q
```

**Test Coverage Highlights (106 tests passing):**
- `test_resume_parser.py`: PDF/DOCX parsing, file size limits, corrupted file rejection.
- `test_analyzer.py`: Factual extraction, evidence citation, prompt injection resistance.
- `test_rag.py`: Knowledge base normalization, ChromaDB retrieval, canonical link enforcement.
- `test_roadmap.py`: Sprint duration generation (4 vs 6 weeks), task progress persistence.
- `test_auth.py`: JWT issuance, bcrypt hashing, invalid token rejection, profile sync.
- `test_candidate.py`: Evaluation history, roadmap synchronization, data isolation.
- `test_returnships.py`: Search, filters (remote/hybrid), bookmark persistence.
- `test_e2e_journey.py`: Complete user flow from register -> upload -> AI analysis -> roadmap -> returnship bookmarks.

---

## 🔒 Privacy & Security Standards

- **Zero Document Retention**: Raw resume binaries and unstructured resume text are never permanently written to disk or database tables. Only structured, anonymized evaluation results are stored.
- **Secrets Protection**: Secrets (`.env`, `JWT_SECRET_KEY`, `GEMINI_API_KEY`) and SQLite databases (`herturn.db`) are strictly excluded by `.gitignore`.
- **Timing-Safe Authentication**: Passwords hashed with 12-round bcrypt salt; timing-safe comparisons prevent enumeration attacks.
- **Strict Role & User Scoping**: API endpoints enforce foreign key tenancy—candidates cannot view or modify other users' analyses, roadmaps, or bookmarks.

---

## 📄 License

This project is licensed under the MIT License.
