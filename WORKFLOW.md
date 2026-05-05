# Kaavach IDS - Complete Workflow & Architecture Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Frontend-Backend Integration](#frontend-backend-integration)
4. [API Reference](#api-reference)
5. [Data Flow](#data-flow)
6. [Development Workflow](#development-workflow)
7. [Testing Strategy (TDD)](#testing-strategy-tdd)
8. [Deployment Guide](#deployment-guide)

---

## System Overview

**Kaavach** is a real-time **Intrusion Detection System (IDS)** with an ML-based network traffic classifier. It consists of:

### Stack
- **Backend**: FastAPI (Python) with async inference, packet sniffing (scapy), logging to disk
- **Frontend**: React + TypeScript with TanStack Router, React Query, Tailwind CSS + Radix UI
- **ML Model**: Logistic Regression (baseline) trained on UNSW-NB15 dataset
- **Deployment**: Vite (frontend), Uvicorn (backend), optional Docker/K8s

### Key Features
- ✅ Live packet capture and real-time attack detection
- ✅ Manual traffic classification via form
- ✅ High-throughput batch ingest (REST API)
- ✅ Per-minute metrics tracking (in-memory)
- ✅ Persistent event logging (daily JSONL files)
- ✅ Model warm-reload without server restart
- ✅ Comprehensive logs explorer & export
- ✅ Responsive web UI with keyboard shortcuts

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React/TS)                     │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │   Dashboard     │  │   Logs UI    │  │   Settings     │ │
│  │  - Monitor      │  │  - Explore   │  │  - Config      │ │
│  │  - Events Tbl   │  │  - Filter    │  │  - API URL     │ │
│  │  - Metrics      │  │  - Export    │  │  - Intervals   │ │
│  └─────────────────┘  └──────────────┘  └────────────────┘ │
│                                                               │
│  React Query (polling every 2.5s)                            │
│  Axios HTTP Client                                           │
└────────────────────────────────────────────────────────────┬─┘
                                                              │
                HTTP/JSON API (port 8000)
                ┌─────────────────────────────┐
                │                             │
┌───────────────┴─────────────────────────────┴──────────────────────┐
│                    Backend (FastAPI/Python)                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  Core API Endpoints                          │  │
│  │  GET  /health              — Service health check            │  │
│  │  GET  /monitor/status      — Running status + buffered      │  │
│  │  POST /monitor/start       — Start packet sniffing          │  │
│  │  POST /monitor/stop        — Stop packet sniffing           │  │
│  │  GET  /monitor/events      — Buffered events (polling)      │  │
│  │  POST /predict             — Single inference               │  │
│  │  POST /predict/batch       — Batch inference                │  │
│  │  POST /ingest              — High-throughput batch ingest   │  │
│  │  GET  /metrics             — Per-minute counts              │  │
│  │  POST /model/reload        — Warm-start model reload        │  │
│  │  GET  /logs                — List log files                 │  │
│  │  GET  /logs/today          — Today's JSONL logs             │  │
│  │  GET  /logs/export         — Download all logs              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │          Traffic Monitor (Packet Sniffing Thread)            │  │
│  │  - Scapy packet capture (IP filter)                          │  │
│  │  - Async inference (ThreadPoolExecutor, 4 workers)          │  │
│  │  - ICMP burst detection (3+ pings in 5s = ATTACK)           │  │
│  │  - Event buffering (max 500 in-memory)                      │  │
│  │  - Per-minute metrics tracking                              │  │
│  │  - JSONL logging to disk (daily files)                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │           ML Inference Engine (KaavachPredictor)             │  │
│  │  - Model: Logistic Regression (selected_model.joblib)       │  │
│  │  - Preprocessing: scikit-learn Pipeline                      │  │
│  │  - Memory-mapped loading for efficiency                      │  │
│  │  - Thread-safe with lock protection                         │  │
│  │  - Threshold: 0.895 (FPR-first optimization)                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Persistent Storage Layer                        │  │
│  │  - models/selected_model.joblib (trained LR pipeline)       │  │
│  │  - models/model_metadata.json (features, threshold)         │  │
│  │  - logs/YYYY-MM-DD_traffic.jsonl (daily event logs)         │  │
│  │  - performance_analysis/ (training metrics & charts)        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

---

## Frontend-Backend Integration

### Connection Points

#### 1. **Configuration Layer** (`src/context/AppConfigContext.tsx`)
- Stores API base URL (default: `http://localhost:8000`)
- Persists to `localStorage` as `kaavach.config`
- Allows runtime URL switching in Settings page
- Poll interval config (default: 2500ms)

#### 2. **API Client** (`src/lib/api.ts`)
- Axios instance with 15-second timeout
- Automatic baseURL updates when config changes
- All endpoints accept optional parameters (limits, filters, etc.)
- Resilient JSON parsing for JSONL responses

#### 3. **Types Alignment** (`src/lib/types.ts`)
- `NetworkEvent`: Flexible schema matching both backend and legacy formats
- `MonitorStatus`: Handles `running`, `backend`, `events_buffered` fields
- `MetricsData`: Per-minute buckets + total counters
- `PredictResponse`: `decision` ("attack" | "normal"), `confidence` (0–1), `reason`

#### 4. **Component Integration**

| Component | Purpose | API Calls | Polling |
|-----------|---------|-----------|---------|
| `MonitorControls` | Start/stop monitoring | `/monitor/start`, `/monitor/stop`, `/monitor/status` | 4s |
| `LiveEventsTable` | Show real-time events | `/monitor/events` | 2.5s |
| `ManualPredictForm` | Single prediction | `/predict` | Manual |
| `AggregateCards` | Stats summary | `/monitor/status`, `/metrics` | 4s |
| `LogsExplorer` | Logs management | `/logs`, `/logs/today`, `/logs/export` | Manual |

---

## API Reference

### Monitor Endpoints

#### `POST /monitor/start`
Starts the traffic monitor (packet sniffing thread).

**Response:**
```json
{
  "started": true,
  "message": "Traffic monitor started."
}
```

---

#### `POST /monitor/stop`
Stops the traffic monitor.

**Response:**
```json
{
  "stopped": true,
  "message": "Traffic monitor stopped."
}
```

---

#### `GET /monitor/status`
Returns current monitor status.

**Response:**
```json
{
  "running": true,
  "backend": "scapy",
  "events_buffered": 42
}
```

---

#### `GET /monitor/events?limit=50`
Retrieves the latest events from buffer.

**Response:**
```json
{
  "events": [
    {
      "timestamp": "2026-05-05T12:34:56.789123+00:00",
      "src_ip": "192.168.1.100",
      "dst_ip": "192.168.1.50",
      "protocol": "icmp",
      "decision": "attack",
      "confidence": 0.99,
      "reason": "icmp_echo_burst"
    }
  ],
  "status": { "running": true, ... }
}
```

---

### Prediction Endpoints

#### `POST /predict`
Single prediction.

**Request:**
```json
{
  "features": {
    "proto": "tcp",
    "service": "-",
    "state": "INT",
    "dur": 0.5,
    "spkts": 5,
    "dpkts": 3,
    "sbytes": 500,
    "dbytes": 1500,
    "rate": 100,
    "sttl": 64,
    "dttl": 64
  }
}
```

**Response:**
```json
{
  "prediction": 0,
  "decision": "normal",
  "confidence": 0.125,
  "threshold": 0.895,
  "model_name": "logistic_regression"
}
```

---

#### `POST /predict/batch`
Batch predictions (up to 1000 records recommended).

**Request:**
```json
{
  "records": [
    { "proto": "tcp", "service": "-", ... },
    { "proto": "udp", "service": "-", ... }
  ]
}
```

**Response:**
```json
{
  "count": 2,
  "model_name": "logistic_regression",
  "threshold": 0.895,
  "predictions": [
    { "prediction": 0, "decision": "normal", "confidence": 0.15, ... },
    { "prediction": 1, "decision": "attack", "confidence": 0.98, ... }
  ]
}
```

---

### Ingest Endpoint

#### `POST /ingest`
High-throughput batch ingest (stores events to disk + updates metrics).

**Request:**
```json
{
  "records": [
    {
      "src_ip": "192.168.1.100",
      "dst_ip": "10.0.0.1",
      "proto": "tcp",
      "dur": 0.5,
      "spkts": 10,
      ...
    }
  ]
}
```

**Response:**
```json
{
  "ok": true,
  "result": { "count": 1 }
}
```

---

### Metrics Endpoint

#### `GET /metrics?minutes=60`
Returns per-minute event counts for the last N minutes.

**Response:**
```json
{
  "per_minute": {
    "2026-05-05T12:34": { "total": 100, "attacks": 5 },
    "2026-05-05T12:33": { "total": 95, "attacks": 3 },
    ...
  },
  "total_events": 2500,
  "total_attacks": 120
}
```

---

### Model Management

#### `POST /model/reload`
Reloads model artifact and metadata from disk (warm-start, no restart).

**Response:**
```json
{
  "ok": {
    "success": true,
    "message": "model reloaded"
  }
}
```

---

### Logs Endpoints

#### `GET /logs`
Lists all available log files.

**Response:**
```json
{
  "logs": ["2026-05-05_traffic.jsonl", "2026-05-04_traffic.jsonl"],
  "logs_dir": "d:\\Documents\\ML model\\api\\logs"
}
```

---

#### `GET /logs/today`
Returns today's JSONL log file contents.

**Response:**
```json
{
  "events": [ ... ],
  "file": "2026-05-05_traffic.jsonl",
  "count": 234
}
```

---

#### `GET /logs/export?filename=traffic_logs.jsonl`
Downloads all logs as a single JSONL file.

---

## Data Flow

### Live Monitoring Flow

```
1. User clicks "Start Monitor"
   ↓
2. POST /monitor/start (API)
   ↓
3. Backend spins up scapy sniffing thread
   ↓
4. Packets arrive → captured & filtered (IP only)
   ↓
5. Packet handler extracts features
   ↓
6. ThreadPoolExecutor offloads inference (non-blocking sniff)
   ↓
7. Model prediction + ICMP burst detection
   ↓
8. Event created & appended to:
   - In-memory buffer (max 500)
   - Daily JSONL log file
   - Per-minute metrics dict
   ↓
9. Frontend polls GET /monitor/events every 2.5s
   ↓
10. React Query caches + renders LiveEventsTable
   ↓
11. User sees attack flagged in red if decision="attack"
```

### Batch Ingest Flow

```
1. Client prepares CSV/JSON with N flow records
   ↓
2. POST /ingest { records: [...] }
   ↓
3. Backend runs batch prediction
   ↓
4. For each record:
   - Create MonitorEvent
   - Append to buffer + JSONL log + metrics
   ↓
5. Return { ok: true, result: { count: N } }
   ↓
6. Client gets confirmation; can fetch /logs/today or /metrics
```

### Manual Prediction Flow

```
1. User fills ManualPredictForm with flow features
   ↓
2. Clicks "Run Prediction"
   ↓
3. POST /predict { features: {...} }
   ↓
4. Backend normalizes features + runs inference
   ↓
5. Returns { decision, confidence, threshold, model_name }
   ↓
6. Frontend renders decision badge (red=attack, green=normal)
   ↓
7. Displays raw JSON response for transparency
```

---

## Development Workflow

### Local Setup

#### Backend
```bash
cd "d:\Documents\ML model"

# Activate venv
.\.venv\Scripts\Activate.ps1

# Install deps
pip install -r api\requirements.txt

# Run backend (from api/ folder)
cd api
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Backend available at http://localhost:8000
```

#### Frontend
```bash
cd "d:\Documents\ML model\frontend"

# Install deps
npm install

# Run dev server
npm run dev

# Frontend available at http://localhost:5173 (or as printed)
```

### Code Organization

**Backend** (`d:\Documents\ML model\api\`)
- `main.py`: FastAPI app, route definitions
- `inference.py`: KaavachPredictor class, model loading + inference
- `traffic_monitor.py`: TrafficMonitor class, packet sniffing + events
- `schemas.py`: Pydantic request/response models
- `requirements.txt`: Python dependencies
- `logs/`: Daily JSONL log files (auto-created)
- `static/`: Legacy HTML frontend (optional)

**Frontend** (`d:\Documents\ML model\frontend\src\`)
- `routes/`: Page components (index, logs, settings, __root)
- `components/`: Reusable UI components
- `context/`: AppConfigContext for global state
- `lib/`: API client, types, utilities
- `hooks/`: Custom React hooks
- `styles.css`: Global styles

### Extending the API

To add a new endpoint:

1. **Backend** (`api/main.py`):
   ```python
   @app.get("/custom-endpoint")
   async def custom_endpoint() -> dict[str, Any]:
       # implementation
       return {"data": "..."}
   ```

2. **Frontend Types** (`src/lib/types.ts`):
   ```typescript
   export interface CustomResponse {
     data: string;
   }
   ```

3. **Frontend Client** (`src/lib/api.ts`):
   ```typescript
   export const api = {
     // ... existing
     customEndpoint: async (): Promise<CustomResponse> =>
       (await client.get("/custom-endpoint")).data,
   };
   ```

4. **Frontend Component** (`src/components/MyComponent.tsx`):
   ```typescript
   const { data } = useQuery({
     queryKey: ["custom"],
     queryFn: api.customEndpoint,
     refetchInterval: 5000,
   });
   ```

---

## Testing Strategy (TDD)

### Test Pyramid

```
        ┌────────────────────┐
        │   E2E Tests (5%)   │  Playwright/Cypress
        │  - Full workflows  │
        ├────────────────────┤
        │  Integration (25%) │  Backend + Frontend
        │  - API contract    │  - Logs persistence
        │  - Events flow     │
        ├────────────────────┤
        │   Unit Tests (70%) │  Jest + pytest
        │  - Prediction      │  - Predictor logic
        │  - Parsing         │  - Metrics tracking
        │  - Component logic │
        └────────────────────┘
```

### Unit Tests

#### Backend (pytest)
```bash
# Test predictor
pytest api/test_inference.py -v

# Test monitor events
pytest api/test_traffic_monitor.py -v
```

**Example: `api/test_inference.py`**
```python
import pytest
from inference import KaavachPredictor

def test_predict_normal():
    predictor = KaavachPredictor()
    result = predictor.predict_one({
        "proto": "tcp",
        "service": "-",
        "state": "INT",
        "dur": 0.5,
        "spkts": 5,
        "dpkts": 3,
        "sbytes": 500,
        "dbytes": 1500,
        "rate": 100,
        "sttl": 64,
        "dttl": 64,
    })
    assert result["decision"] in ["attack", "normal"]
    assert 0 <= result["confidence"] <= 1
    assert result["model_name"] == "logistic_regression"

def test_reload():
    predictor = KaavachPredictor()
    result = predictor.reload()
    assert result["success"] is True
```

#### Frontend (Jest + React Testing Library)
```bash
npm test -- src/components/MonitorControls.test.tsx
```

**Example: `src/components/__tests__/MonitorControls.test.tsx`**
```typescript
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { MonitorControls } from "../MonitorControls";

const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });

test("renders start button", () => {
  render(
    <QueryClientProvider client={qc}>
      <MonitorControls />
    </QueryClientProvider>
  );
  expect(screen.getByText(/Start/i)).toBeInTheDocument();
});
```

### Integration Tests

**Scenario: "User starts monitor → pings device → events appear in table"**

```bash
# Backend integration
pytest api/test_integration.py::test_start_and_capture -v

# Frontend integration (with backend running)
npm run test:e2e -- --spec "cypress/e2e/monitor-flow.cy.ts"
```

**Example: `api/test_integration.py`**
```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_start_and_ingest():
    # Start monitor
    resp = client.post("/monitor/start")
    assert resp.status_code == 200
    assert resp.json()["started"] is True
    
    # Ingest records
    resp = client.post("/ingest", json={
        "records": [
            {
                "proto": "tcp",
                "service": "-",
                "state": "INT",
                "dur": 0.5,
                "spkts": 5,
                "dpkts": 3,
                "sbytes": 500,
                "dbytes": 1500,
                "rate": 100,
                "sttl": 64,
                "dttl": 64,
            }
        ]
    })
    assert resp.status_code == 200
    assert resp.json()["result"]["count"] == 1
    
    # Fetch metrics
    resp = client.get("/metrics?minutes=1")
    assert resp.status_code == 200
    metrics = resp.json()
    assert metrics["total_events"] > 0
```

### Regression Tests

**When adding features, add tests to prevent breakage:**
- Prediction response format unchanged
- Monitor start/stop idempotent
- Metrics calculated correctly
- Logs persisted to disk

---

## Deployment Guide

### Quick Start (Development)

```bash
# Terminal 1: Backend
cd "d:\Documents\ML model\api"
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd "d:\Documents\ML model\frontend"
npm run dev
```

Open `http://localhost:5173` in browser.

### Production Build

#### Backend
```bash
# No special build needed; just ensure:
# - Python 3.11+
# - All deps in requirements.txt installed
# - Run with production ASGI server:
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Frontend
```bash
cd frontend
npm run build

# Output: dist/
# Serve with nginx or static host
```

### Docker Deployment (Optional)

**Backend Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY api/requirements.txt .
RUN pip install -r requirements.txt
COPY api/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:20 AS build
WORKDIR /app
COPY frontend/ .
RUN npm install && npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**docker-compose.yml:**
```yaml
version: "3.9"
services:
  backend:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

### Monitoring & Logs

- **Backend logs**: Console output from uvicorn
- **Event logs**: `api/logs/YYYY-MM-DD_traffic.jsonl` (daily)
- **Metrics**: In-memory (up to 60 minutes), no persistence
- **Frontend**: Browser console (F12)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Backend: unavailable" | Restart backend; check port 8000 is listening |
| No events appearing | Run as Administrator (scapy packet capture); install Npcap |
| Slow predictions | Check CPU usage; model inference offloaded to 4 threads |
| Log files not created | Check write permissions in `api/logs/` directory |
| "CORS error" | Frontend & backend on same origin (localhost); check proxy settings |
| Model reload fails | Verify `models/` folder exists with `selected_model.joblib` |

---

## References

- **Backend**: [FastAPI docs](https://fastapi.tiangolo.com/), [Scapy docs](https://scapy.readthedocs.io/)
- **Frontend**: [React Router TanStack](https://tanstack.com/router/latest), [React Query](https://tanstack.com/query/latest)
- **ML Model**: UNSW-NB15 dataset, Logistic Regression with threshold tuning
- **Monitoring**: Prometheus-ready `/metrics` endpoint (can add exporter)

---

## Summary

Kaavach provides a **end-to-end IDS solution** with:
- Real-time attack detection via scapy + ML
- High-throughput batch ingest for historical data
- Persistent event logging for audit trails
- Responsive React UI for operator dashboard
- Extensible FastAPI backend for custom rules/models

The **workflow** is:
1. Start backend + frontend
2. Click "Start Monitor" to begin packet capture
3. View events in real-time or ingest historical records
4. Use manual prediction for ad-hoc analysis
5. Export logs for compliance/investigation

**For questions or enhancements**, refer to individual component docstrings and API documentation above.
