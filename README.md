# HerTurn — AI-Powered Career Recovery & Returnship Platform

**HerTurn** is a specialized career relaunch platform designed for women returning to the workforce after career hiatuses (caregiving, maternity, family relocations, or professional sabbaticals).

---

## Architecture Overview

HerTurn combines a modern React 19 frontend with a robust FastAPI backend, powered by Google Gemini structured evaluation and a local ChromaDB Retrieval-Augmented Generation (RAG) pipeline:

1. **Document Extraction & Resume Ingestion**: PyMuPDF (`fitz`) and `python-docx` extract resume text from uploaded `.pdf` and `.docx` files with 5 MB validation and image-only scan detection.
2. **Factual Skill Evaluation (Google Gemini)**: Analyzes documented career history, extracts verified skills with textual citations, maps competencies against target role requirements, and identifies concrete skill gaps without penalizing career breaks.
3. **Verified Learning Resources RAG (ChromaDB)**: Curated, version-controlled knowledge base of verified learning materials across engineering, data analysis, product management, and career relaunch. Resources are normalized and embedded locally in ChromaDB.
4. **Personalized 4-Week / 6-Week Curriculum**: Dynamic sprint roadmaps with progressive deliverables, interactive task checklists, and verified educational citations directly retrieved via RAG.
5. **Transparency & Anti-Hallucination**:
   - Zero hallucinated URLs: Gemini is provided only verified resources from ChromaDB and may only cite checked canonical links.
   - Transparent fallbacks: If the vector database is unavailable or returns no matches, HerTurn never falsely claims RAG was used.
   - Dual-Mode Operation: Runs seamlessly in demo mode with static fixtures or live mode with the FastAPI backend.

---

## Getting Started

### Prerequisites
- **Node.js**: v18+ (tested with Node 20+)
- **Python**: 3.10+ (tested with Python 3.13)
- **Google Gemini API Key**: Optional for demo mode; required for live analysis ([Get API Key](https://aistudio.google.com/)).

---

### Backend Setup & RAG Ingestion

1. Navigate to the `backend/` directory:
   ```powershell
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Install backend dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

4. Configure environment variables in `backend/.env`:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-3.1-flash-lite-preview
   ```

5. **Ingest the Curated Knowledge Base (Idempotent)**:
   ```powershell
   python scripts/ingest_knowledge_base.py
   ```
   *Indexes 20 verified curriculum resources into local ChromaDB storage at `backend/chroma_db`.*

6. Start the FastAPI backend server:
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   - API Documentation (Swagger): `http://127.0.0.1:8000/docs`

---

### Frontend Setup

1. In the project root directory, install dependencies:
   ```powershell
   npm install
   ```

2. Configure environment variables in root `.env`:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_USE_MOCK=false
   ```
   *(To run in offline demo mode without the backend, set `VITE_USE_MOCK=true`)*

3. Start the Vite development server:
   ```powershell
   npm run dev
   ```
   - Frontend Application: `http://localhost:5173`

4. Build production bundle:
   ```powershell
   npm run build
   ```

---

## Testing

Run the complete backend test suite (24 tests covering parser, analyzer, RAG ingestion, retrieval relevance, anti-hallucination, and transparent fallbacks):

```powershell
$env:PYTHONPATH="backend"
.\backend\venv\Scripts\pytest backend\tests -v
```

All external LLM calls are mocked in automated tests to ensure repeatable, deterministic execution without consuming API quota.

---

## Privacy & Security

- `backend/.env`, `.env`, and vector database files (`backend/chroma_db/`) are excluded from Git via `.gitignore`.
- Resume text and candidate data are processed strictly in memory and are never written to disk or logged.
- API keys are never exposed in logs or transmitted to the client.
