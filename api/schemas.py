from typing import Any

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    features: dict[str, Any] = Field(
        ..., description="Single flow feature map (column -> value)"
    )


class PredictResponse(BaseModel):
    prediction: int
    decision: str
    confidence: float
    threshold: float
    model_name: str


class BatchPredictRequest(BaseModel):
    records: list[dict[str, Any]] = Field(
        ..., description="List of flow feature maps"
    )


class BatchPredictResponse(BaseModel):
    count: int
    model_name: str
    threshold: float
    predictions: list[PredictResponse]
