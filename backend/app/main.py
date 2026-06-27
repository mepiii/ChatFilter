"""FastAPI application routes.

Purpose: Expose spam detection, batch detection, metrics, and history APIs.
Callers: ASGI servers and API tests.
Deps: FastAPI, SQLAlchemy, app settings, schemas, models, security, predictor.
API: FastAPI app with /api routes.
Side effects: Creates database tables and loads model at import time.
"""

import json
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, engine, get_db
from app.ml.predictor import SpamScamPredictor
from app.ml.train import download_public_dataset, train
from app.models import AnalysisHistory
from app.schemas import BatchDetectRequest, BatchDetectionResponse, DetectionResult, DetectRequest, Explanation, HistoryItem, ModelMetrics, RetrainRequest, RetrainResponse
from app.security import RateLimiter

settings = get_settings()
BACKEND_DIR = Path(__file__).resolve().parents[1]
Base.metadata.create_all(bind=engine)
predictor = SpamScamPredictor(settings.model_path)
rate_limiter = RateLimiter(settings.rate_limit_per_minute)

app = FastAPI(title='ChatFilter API')
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def _validate_messages(messages: list[str]) -> None:
    if len(messages) > settings.max_batch_size:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='Batch size exceeds configured limit')
    if any(len(message) > settings.max_message_length for message in messages):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='Message length exceeds configured limit')


def _result_for_message(message: str) -> DetectionResult:
    raw = predictor.predict(message)
    return DetectionResult(message=message, **raw)


def _store_history(db: Session, result: DetectionResult) -> None:
    db.add(AnalysisHistory(
        message=result.message or '',
        label=result.label,
        spam_probability=result.spam_probability,
        risk_level=result.risk_level,
        explanation_json=result.explanation.model_dump_json(),
    ))
    db.commit()


@app.post('/api/detect-spam', response_model=DetectionResult)
def detect_spam(payload: DetectRequest, request: Request, db: Session = Depends(get_db)) -> DetectionResult:
    rate_limiter.check(request)
    _validate_messages([payload.message])
    result = _result_for_message(payload.message)
    _store_history(db, result)
    return result


@app.post('/api/detect-batch', response_model=BatchDetectionResponse)
def detect_batch(payload: BatchDetectRequest, request: Request, db: Session = Depends(get_db)) -> BatchDetectionResponse:
    rate_limiter.check(request)
    _validate_messages(payload.messages)
    results = [_result_for_message(message) for message in payload.messages]
    for result in results:
        _store_history(db, result)
    return BatchDetectionResponse(results=results)


@app.get('/api/model-metrics', response_model=ModelMetrics)
def model_metrics() -> ModelMetrics:
    path: Path = settings.metrics_path
    if not path.exists():
        return ModelMetrics(accuracy=0.0, precision=0.0, recall=0.0, f1=0.0)
    return ModelMetrics(**json.loads(path.read_text()))


@app.post('/api/retrain', response_model=RetrainResponse)
def retrain_model(payload: RetrainRequest) -> RetrainResponse:
    data_path = BACKEND_DIR / ('data/public_messages.csv' if payload.use_public_dataset else 'data/seed_messages.csv')
    source = 'public dataset' if payload.use_public_dataset else 'seed dataset'
    if payload.use_public_dataset:
        download_public_dataset(data_path)
    metrics = ModelMetrics(**train(data_path, settings.model_path, settings.metrics_path))
    global predictor
    predictor = SpamScamPredictor(settings.model_path)
    return RetrainResponse(metrics=metrics, source=source)


@app.get('/api/history', response_model=list[HistoryItem])
def history(db: Session = Depends(get_db)) -> list[HistoryItem]:
    rows = db.query(AnalysisHistory).order_by(AnalysisHistory.created_at.desc()).limit(50).all()
    return [
        HistoryItem(
            id=row.id,
            message=row.message,
            label=row.label,
            spam_probability=row.spam_probability,
            risk_level=row.risk_level,
            explanation=Explanation(**json.loads(row.explanation_json)),
            created_at=row.created_at,
        )
        for row in rows
    ]


@app.delete('/api/history/{item_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_history(item_id: int, db: Session = Depends(get_db)) -> Response:
    row = db.get(AnalysisHistory, item_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='History item not found')
    db.delete(row)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
