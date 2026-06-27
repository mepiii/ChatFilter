"""Pydantic API schemas.

Purpose: Define request and response validation models.
Callers: FastAPI routes and tests.
Deps: datetime, pydantic.
API: Request, detection, metrics, and history schemas.
Side effects: None.
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

MessageText = Annotated[str, Field(min_length=1, max_length=2000)]


class DetectRequest(BaseModel):
    message: MessageText


class BatchDetectRequest(BaseModel):
    messages: list[MessageText] = Field(min_length=1, max_length=25)


class Explanation(BaseModel):
    top_terms: list[str]
    rule_hints: list[str]


class DetectionResult(BaseModel):
    message: str | None = None
    label: str
    spam_probability: float
    risk_level: str
    explanation: Explanation


class BatchDetectionResponse(BaseModel):
    results: list[DetectionResult]


class ModelMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float


class RetrainRequest(BaseModel):
    use_public_dataset: bool = False


class RetrainResponse(BaseModel):
    metrics: ModelMetrics
    source: str


class HistoryItem(BaseModel):
    id: int
    message: str
    label: str
    spam_probability: float
    risk_level: str
    explanation: Explanation
    created_at: datetime
