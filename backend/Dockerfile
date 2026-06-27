# Purpose: Build ChatFilter FastAPI backend container. Callers: Render and local Docker. Deps: Python, requirements.txt, app package. API: uvicorn ASGI server. Side effects: Starts HTTP service.
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY data ./data
COPY artifacts ./artifacts
ENV PYTHONPATH=/app
ENV PORT=8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
