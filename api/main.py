from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from inference import KaavachPredictor
from schemas import (
    BatchPredictRequest,
    BatchPredictResponse,
    PredictRequest,
    PredictResponse,
)
from traffic_monitor import TrafficMonitor


app = FastAPI(title="kaavach-ids-api", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor: KaavachPredictor | None = None
monitor: TrafficMonitor | None = None


@app.on_event("startup")
def load_model() -> None:
    global predictor, monitor
    predictor = KaavachPredictor()
    monitor = TrafficMonitor(predictor)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "kaavach-ids-api"}


@app.get("/")
def home() -> FileResponse:
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index_path)


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        result = predictor.predict_one(req.features)
        return PredictResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {exc}") from exc


@app.post("/predict/batch", response_model=BatchPredictResponse)
def predict_batch(req: BatchPredictRequest) -> BatchPredictResponse:
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        preds = predictor.predict_batch(req.records)
        threshold = predictor.threshold
        model_name = predictor.model_name
        return BatchPredictResponse(
            count=len(preds),
            model_name=model_name,
            threshold=threshold,
            predictions=[PredictResponse(**p) for p in preds],
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Batch prediction failed: {exc}") from exc


@app.post("/monitor/start")
def start_monitor() -> dict[str, object]:
    if monitor is None:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    return monitor.start()


@app.post("/monitor/stop")
def stop_monitor() -> dict[str, object]:
    if monitor is None:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    return monitor.stop()


@app.get("/monitor/status")
def monitor_status() -> dict[str, object]:
    if monitor is None:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    return monitor.status()


@app.get("/monitor/events")
def monitor_events(limit: int = 50) -> dict[str, object]:
    if monitor is None:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    return {
        "events": monitor.latest_events(limit=limit),
        "status": monitor.status(),
    }
