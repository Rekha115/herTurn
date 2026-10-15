# 🚀 HerTurn Deployment Guide

This guide provides step-by-step instructions for deploying both the **FastAPI Backend** and the **React + Vite Frontend** to the cloud.

---

## 📋 Recommended Deployment Strategy

| Component | Recommended Platform | Cost | Setup Time |
| :--- | :--- | :--- | :--- |
| **Frontend (React/Vite)** | **Vercel** or **Netlify** | Free | ~2 minutes |
| **Backend (FastAPI)** | **Render** or **Railway** | Free tier available | ~5 minutes |

---

## 🔹 Part 1: Deploying the Backend (FastAPI on Render)

### Step 1: Create a Free Render Account
1. Go to [render.com](https://render.com) and sign in using your GitHub account (`Rekha115`).

### Step 2: Create a New Web Service
1. Click **New +** > **Web Service**.
2. Select your repository: `Rekha115/herTurn`.
3. Fill in the service configuration:
   - **Name**: `herturn-backend` (or your preferred name)
   - **Region**: Choose the region closest to you (e.g., Singapore, Frankfurt, Oregon)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`

### Step 3: Add Environment Variables
Under the **Environment Variables** section on Render, add the following:

| Key | Value | Notes |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `production` | Enables production security checks |
| `GEMINI_API_KEY` | `AIzaSy...` | Your Google Gemini API Key from [AI Studio](https://aistudio.google.com/) |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Fast, high-accuracy analysis model |
| `JWT_SECRET_KEY` | *(Click "Generate" or paste a random 64-char string)* | Secures session tokens |
| `DATABASE_URL` | `sqlite:///./herturn.db` | Local SQLite database (or Postgres connection string) |
| `ALLOWED_ORIGINS` | `https://your-frontend.vercel.app` | **Note:** Set this after deploying your frontend in Part 2! |

### Step 4: Deploy
1. Click **Deploy Web Service**.
2. Render will build the environment, install packages, and launch Uvicorn.
3. Once deployed, Render will provide your public backend URL, for example:  
   `https://herturn-backend.onrender.com`
4. Test the health endpoint in your browser:  
   `https://herturn-backend.onrender.com/api/health`  
   *(Expected response: `{"status": "healthy", ...}`)*

---

## 🔹 Part 2: Deploying the Frontend (React + Vite on Vercel)

### Step 1: Create a Free Vercel Account
1. Go to [vercel.com](https://vercel.com) and log in with GitHub (`Rekha115`).

### Step 2: Import Your Repository
1. Click **Add New...** > **Project**.
2. Choose `Rekha115/herTurn` and click **Import**.

### Step 3: Configure Project Settings
- **Framework Preset**: `Vite` (automatically detected)
- **Root Directory**: `./` (leave default)
- **Build Command**: `npm run build`
- **Output Directory**: `dist`

### Step 4: Add Environment Variables
Expand the **Environment Variables** section and add:

| Key | Value | Example |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Your Render Backend URL | `https://herturn-backend.onrender.com` |
| `VITE_USE_MOCK` | `false` | Disables mock data so real backend is used |

### Step 5: Deploy
1. Click **Deploy**.
2. Vercel will install dependencies and build the app in ~30 seconds.
3. Your app is live at: `https://her-turn.vercel.app` (or similar assigned URL).

---

## 🔹 Part 3: Connect Frontend & Backend (Final CORS Step)

1. Copy your live Vercel URL (e.g. `https://her-turn.vercel.app`).
2. Go back to your **Render Dashboard** > **herturn-backend** > **Environment**.
3. Update `ALLOWED_ORIGINS`:
   ```
   https://her-turn.vercel.app
   ```
4. Click **Save Changes**. Render will automatically restart with CORS authorized for your frontend!

---

## 💡 Alternative: Deploying on Railway (All-in-One)

If you prefer deploying everything under one dashboard:
1. Sign in to [railway.app](https://railway.app).
2. Click **New Project** > **Deploy from GitHub repo** > `Rekha115/herTurn`.
3. Add service for Backend (`Root Directory: backend`) with start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
4. Add service for Frontend (`Root Directory: .`) with `npm run build`.
5. Connect environmental variables as described above.

---

## 🧪 Post-Deployment Verification Checklist

- [ ] Visit frontend URL: Landing page loads with HerTurn theme.
- [ ] Sign Up / Sign In: Register a test account (`test@herturn.org`).
- [ ] Upload Resume: Test PDF upload and confirm Gemini analysis runs live.
- [ ] Roadmap: Verify 4-week / 6-week curriculum generates with RAG citations.
- [ ] Returnships: Filter by "Remote" and bookmark an opportunity.
- [ ] Refresh check: Press F5 on `/dashboard` or `/roadmap` to confirm no 404 errors (handled by `vercel.json` / `_redirects`).
