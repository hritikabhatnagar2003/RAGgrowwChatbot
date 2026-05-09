# RAGgrowwChatbot

## Deploy (Option A)

### Backend (FastAPI) → Render

- **Service root**: repo root
- **Build command**: `pip install -r phase4_backend_api/requirements.txt`
- **Start command**: `python -m uvicorn phase4_backend_api.main:app --host 0.0.0.0 --port $PORT`
- **Health check**: `/api/health`
- **Environment variables**:
  - `GROQ_API_KEY` (secret)
  - `ALLOWED_ORIGINS` = `https://<your-vercel-domain>`
  - `RATE_LIMIT_PER_MINUTE` = `30` (optional)

You can also deploy using the included `render.yaml`.

### Frontend (React/Vite) → Vercel

- **Root Directory**: `phase4_frontend_ui`
- **Build command**: `npm run build`
- **Output directory**: `dist`
- **Environment variables**:
  - `VITE_API_BASE_URL` = `https://<your-render-backend-domain>`
