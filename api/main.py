from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from inference import KaavachPredictor
from schemas import (
    BatchPredictRequest,
    BatchPredictResponse,
    PredictRequest,
    PredictResponse,
)
from traffic_monitor import TrafficMonitor
from fastapi.concurrency import run_in_threadpool
from typing import Optional
import logging


app = FastAPI(title="kaavach-ids-api", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
FRONTEND_URL = "http://localhost:8080"

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
# In-memory debug store for the last predict call (helps frontend/backend mismatch debugging)
last_predict_features: dict | None = None
last_predict_result: dict | None = None


@app.on_event("startup")
def load_model() -> None:
    global predictor, monitor
    predictor = KaavachPredictor()
    # logs_dir will default to "logs/" in current directory
    monitor = TrafficMonitor(predictor, logs_dir=BASE_DIR / "logs")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "kaavach-ids-api"}


@app.get("/")
def home() -> RedirectResponse:
    return RedirectResponse(url=FRONTEND_URL)


@app.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest) -> PredictResponse:
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Debug: log incoming features and prediction result for UI troubleshooting
        logger = logging.getLogger("kaavach")
        logger.info("/predict incoming features: %s", req.features)
        result = await run_in_threadpool(predictor.predict_one, req.features)
        logger.info("/predict result: %s", result)
        # store raw dict for quick debug inspection
        global last_predict_features, last_predict_result
        last_predict_features = dict(req.features)
        last_predict_result = dict(result)
        return PredictResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {exc}") from exc


@app.post("/predict/batch", response_model=BatchPredictResponse)
async def predict_batch(req: BatchPredictRequest) -> BatchPredictResponse:
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        preds = await run_in_threadpool(predictor.predict_batch, req.records)
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


@app.get("/debug/last_predict")
def debug_last_predict() -> dict[str, object]:
    """Return the last /predict features and server-side result for debugging UI/backend mismatch."""
    return {"features": last_predict_features, "result": last_predict_result}


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


@app.post("/ingest")
async def ingest(req: BatchPredictRequest) -> dict[str, object]:
    """High-throughput batch ingest: accepts a list of flow records, runs predictions, stores events and updates metrics."""
    if monitor is None:
        raise HTTPException(status_code=503, detail="Monitor not initialized")

    try:
        result = await run_in_threadpool(monitor.ingest_records, req.records)
        return {"ok": True, "result": result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Ingest failed: {exc}") from exc


@app.get("/metrics")
def metrics(minutes: Optional[int] = 60) -> dict[str, object]:
    """Return lightweight in-memory metrics (per-minute counts and totals)."""
    if monitor is None:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    try:
        return monitor.get_metrics(minutes=minutes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Metrics error: {exc}") from exc


@app.post("/model/reload")
async def model_reload() -> dict[str, object]:
    """Reload model artifact and metadata from disk without restarting the server."""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        result = await run_in_threadpool(predictor.reload)
        return {"ok": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Model reload failed: {exc}") from exc


@app.get("/logs")
def list_logs() -> dict[str, object]:
    """List all available log files."""
    if monitor is None:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    
    logs_dir = monitor.logs_dir
    if not logs_dir.exists():
        return {"logs": []}
    
    log_files = sorted([f.name for f in logs_dir.glob("*.jsonl")], reverse=True)
    return {"logs": log_files, "logs_dir": str(logs_dir)}


@app.get("/logs/today")
def get_today_logs() -> dict[str, object]:
    """Get today's log file contents."""
    if monitor is None:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    
    log_file = monitor._get_log_file_path()
    if not log_file.exists():
        return {"events": [], "file": log_file.name, "count": 0}
    
    try:
        events = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        return {"events": events, "file": log_file.name, "count": len(events)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read log: {exc}") from exc


@app.get("/logs/export")
def export_logs(filename: str = "traffic_logs.jsonl") -> FileResponse:
    """Export all logs as JSONL file download."""
    if monitor is None:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    
    logs_dir = monitor.logs_dir
    if not logs_dir.exists():
        raise HTTPException(status_code=404, detail="No logs directory")
    
    # Create a temporary export file with all logs
    export_file = logs_dir / "_export_temp.jsonl"
    try:
        with open(export_file, "w", encoding="utf-8") as out:
            for log_file in sorted(logs_dir.glob("*.jsonl")):
                if log_file.name != "_export_temp.jsonl":
                    with open(log_file, "r", encoding="utf-8") as inp:
                        for line in inp:
                            out.write(line)
        
        return FileResponse(
            path=export_file,
            filename=filename,
            media_type="application/x-ndjson",
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Export failed: {exc}") from exc
