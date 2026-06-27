# ChatFilter

ChatFilter is a full-stack spam and scam chat detector. It uses a FastAPI backend, a React frontend, and a TF-IDF + Logistic Regression model with rule-based scam hints.

## Features

- Detect spam, scam, and safe chat messages
- Analyze one or multiple messages
- Show spam probability, risk level, top model terms, and rule hints
- Store and delete analysis history
- Expose REST API endpoints for future integration
- Include backend and frontend tests

## Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite, scikit-learn
- Frontend: React, TypeScript, Vite, Vitest
- ML: TF-IDF vectorizer + Logistic Regression

## Backend Setup

```bash
cd backend
python -m venv ../.venv
../.venv/bin/python -m pip install -r requirements.txt
PYTHONPATH=. ../.venv/bin/python -m uvicorn app.main:app --reload
```

Backend runs at `http://127.0.0.1:8000`.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://127.0.0.1:5173`.

## API Endpoints

```http
POST /api/detect-spam
POST /api/detect-batch
GET /api/model-metrics
POST /api/retrain
GET /api/history
DELETE /api/history/{item_id}
```

Example request:

```bash
curl -X POST http://127.0.0.1:8000/api/detect-spam \
  -H 'Content-Type: application/json' \
  -d '{"message":"Urgent verify your bank password now"}'
```

## Tests

Backend:

```bash
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -q
```

Frontend:

```bash
npm --prefix frontend test -- --run
npm --prefix frontend run build
```

## Training Model

```bash
cd backend
PYTHONPATH=. ../.venv/bin/python -m app.ml.train \
  --data data/seed_messages.csv \
  --model artifacts/spam_model.joblib \
  --metrics artifacts/model_metrics.json
```

Download public SMS spam data before training:

```bash
cd backend
PYTHONPATH=. ../.venv/bin/python -m app.ml.train \
  --download-public \
  --data data/public_messages.csv \
  --model artifacts/spam_model.joblib \
  --metrics artifacts/model_metrics.json
```

## Deployment

Recommended split:

- Backend: Render web service from `backend/Dockerfile`
- Frontend: Vercel static build from `frontend/dist`

Set frontend env var:

```text
VITE_API_BASE_URL=https://your-render-service.onrender.com
```
