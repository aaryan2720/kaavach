# Kaavach IDS - Test-Driven Development (TDD) Guide

## Overview

This document outlines the testing strategy for Kaavach IDS, organized by layer and test type. Follow TDD principles: **Red → Green → Refactor**.

---

## Test Layers & Responsibilities

### 1. Unit Tests (70%)
Test individual functions/methods in isolation with mocked dependencies.

#### Backend Unit Tests (`api/tests/`)

**File: `test_inference.py`**
```python
import pytest
from pathlib import Path
from inference import KaavachPredictor

@pytest.fixture
def predictor():
    return KaavachPredictor()

def test_predict_one_returns_valid_response(predictor):
    """Prediction should return dict with required fields."""
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
    
    assert "prediction" in result
    assert "decision" in result
    assert "confidence" in result
    assert result["decision"] in ["attack", "normal"]
    assert 0 <= result["confidence"] <= 1

def test_batch_predict_matches_individual(predictor):
    """Batch prediction should match individual predictions."""
    records = [
        {"proto": "tcp", "service": "-", "state": "INT", "dur": 0.5, 
         "spkts": 5, "dpkts": 3, "sbytes": 500, "dbytes": 1500, 
         "rate": 100, "sttl": 64, "dttl": 64},
        {"proto": "udp", "service": "-", "state": "REQ_RST", "dur": 1.0, 
         "spkts": 10, "dpkts": 5, "sbytes": 1000, "dbytes": 3000, 
         "rate": 200, "sttl": 128, "dttl": 0},
    ]
    
    batch_result = predictor.predict_batch(records)
    assert len(batch_result) == 2
    
    for i, rec in enumerate(records):
        single = predictor.predict_one(rec)
        assert batch_result[i]["decision"] == single["decision"]
        assert abs(batch_result[i]["confidence"] - single["confidence"]) < 0.001

def test_reload_restores_model_state(predictor):
    """Model reload should restore metadata and state."""
    original_threshold = predictor.threshold
    original_model_name = predictor.model_name
    
    result = predictor.reload()
    
    assert result["success"] is True
    assert predictor.threshold == original_threshold
    assert predictor.model_name == original_model_name
```

**File: `test_traffic_monitor.py`**
```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from traffic_monitor import TrafficMonitor, MonitorEvent

@pytest.fixture
def mock_predictor():
    predictor = Mock()
    predictor.predict_one.return_value = {
        "decision": "normal",
        "confidence": 0.2,
    }
    return predictor

@pytest.fixture
def monitor(mock_predictor):
    return TrafficMonitor(mock_predictor, logs_dir="/tmp/kaavach_test")

def test_monitor_start_creates_thread(monitor):
    """Starting monitor should spin up thread."""
    result = monitor.start()
    assert result["started"] is True
    assert monitor.is_running is True
    monitor.stop()

def test_monitor_stop_halts_thread(monitor):
    """Stopping monitor should halt thread and cleanup."""
    monitor.start()
    result = monitor.stop()
    assert result["stopped"] is True
    assert monitor.is_running is False

def test_ingest_records_updates_metrics(monitor):
    """Batch ingest should update per-minute metrics."""
    records = [
        {"proto": "tcp", "service": "-", "state": "INT", "dur": 0.5, 
         "spkts": 5, "dpkts": 3, "sbytes": 500, "dbytes": 1500, 
         "rate": 100, "sttl": 64, "dttl": 64},
    ]
    
    result = monitor.ingest_records(records)
    assert result["count"] == 1
    
    metrics = monitor.get_metrics(minutes=1)
    assert metrics["total_events"] > 0

def test_get_metrics_returns_expected_structure(monitor):
    """Metrics should have per_minute dict, total counts."""
    metrics = monitor.get_metrics(minutes=5)
    
    assert "per_minute" in metrics
    assert "total_events" in metrics
    assert "total_attacks" in metrics
    assert isinstance(metrics["per_minute"], dict)
    assert metrics["total_events"] >= 0
    assert metrics["total_attacks"] >= 0

def test_icmp_burst_detection(monitor):
    """3+ ICMP pings in 5s window should be marked as attack."""
    # Mock packet with ICMP type 8 (echo request)
    packet = MagicMock()
    packet[MagicMock()].src = "192.168.1.100"
    packet[MagicMock()].dst = "192.168.1.50"
    packet[MagicMock()].proto = 1  # ICMP
    packet[MagicMock()].ttl = 64
    
    # Simulate 5 ICMP packets from same source
    for _ in range(5):
        # In real scenario, _process_packet would be called
        pass
    
    # Should flag 3+ pings as attack
    # (Actual test requires network packet simulation)
```

#### Frontend Unit Tests (`src/components/__tests__/`)

**File: `MonitorControls.test.tsx`**
```typescript
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MonitorControls } from "../MonitorControls";
import * as api from "@/lib/api";

jest.mock("@/lib/api");
jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    message: jest.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: any) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe("MonitorControls", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders start and stop buttons", async () => {
    (api.api.status as jest.Mock).mockResolvedValue({
      running: false,
      backend: "scapy",
      events_buffered: 0,
    });

    render(<MonitorControls />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/Stopped/i)).toBeInTheDocument();
    });
  });

  test("calls api.start when start button clicked", async () => {
    const user = userEvent.setup();
    (api.api.status as jest.Mock).mockResolvedValue({
      running: false,
      backend: "scapy",
      events_buffered: 0,
    });
    (api.api.start as jest.Mock).mockResolvedValue({
      started: true,
      message: "Monitor started",
    });

    render(<MonitorControls />, { wrapper: createWrapper() });

    const startBtn = await screen.findByRole("button", { name: /Start/i });
    await user.click(startBtn);

    await waitFor(() => {
      expect(api.api.start).toHaveBeenCalled();
    });
  });

  test("displays running status when monitor is active", async () => {
    (api.api.status as jest.Mock).mockResolvedValue({
      running: true,
      backend: "scapy",
      events_buffered: 42,
    });

    render(<MonitorControls />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/Running/i)).toBeInTheDocument();
    });
  });
});
```

**File: `ManualPredictForm.test.tsx`**
```typescript
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { ManualPredictForm } from "../ManualPredictForm";
import * as api from "@/lib/api";

jest.mock("@/lib/api");
jest.mock("sonner");

test("form submits correct features to api.predict", async () => {
  const user = userEvent.setup();
  (api.api.predict as jest.Mock).mockResolvedValue({
    decision: "normal",
    confidence: 0.15,
  });

  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  render(
    <QueryClientProvider client={qc}>
      <ManualPredictForm />
    </QueryClientProvider>
  );

  const button = screen.getByRole("button", { name: /Run Prediction/i });
  await user.click(button);

  await waitFor(() => {
    expect(api.api.predict).toHaveBeenCalledWith(
      expect.objectContaining({
        features: expect.objectContaining({
          proto: "tcp",
          dur: 0.5,
          spkts: 5,
        }),
      })
    );
  });
});
```

---

### 2. Integration Tests (25%)
Test API contracts and multi-component workflows.

**File: `api/tests/test_api_integration.py`**
```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestPredictEndpoint:
    def test_predict_accepts_valid_features(self):
        """POST /predict should accept feature dict and return prediction."""
        response = client.post("/predict", json={
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
                "dttl": 64,
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert "decision" in data
        assert "confidence" in data

    def test_predict_batch_endpoint(self):
        """POST /predict/batch should handle multiple records."""
        response = client.post("/predict/batch", json={
            "records": [
                {"proto": "tcp", "service": "-", "state": "INT", "dur": 0.5, 
                 "spkts": 5, "dpkts": 3, "sbytes": 500, "dbytes": 1500, 
                 "rate": 100, "sttl": 64, "dttl": 64},
                {"proto": "udp", "service": "-", "state": "INT", "dur": 1.0, 
                 "spkts": 10, "dpkts": 5, "sbytes": 1000, "dbytes": 3000, 
                 "rate": 200, "sttl": 128, "dttl": 0},
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["predictions"]) == 2

class TestMonitorFlow:
    def test_start_stop_monitor_lifecycle(self):
        """Monitor should start, stop, and report status correctly."""
        # Start
        resp = client.post("/monitor/start")
        assert resp.status_code == 200
        
        # Status
        resp = client.get("/monitor/status")
        status = resp.json()
        # Might not be running immediately due to scapy availability
        
        # Stop
        resp = client.post("/monitor/stop")
        assert resp.status_code == 200

    def test_ingest_and_metrics_flow(self):
        """Ingest should create events and update metrics."""
        # Ingest
        resp = client.post("/ingest", json={
            "records": [
                {"proto": "tcp", "service": "-", "state": "INT", "dur": 0.5, 
                 "spkts": 5, "dpkts": 3, "sbytes": 500, "dbytes": 1500, 
                 "rate": 100, "sttl": 64, "dttl": 64},
            ]
        })
        assert resp.status_code == 200
        assert resp.json()["result"]["count"] == 1
        
        # Metrics
        resp = client.get("/metrics?minutes=1")
        assert resp.status_code == 200
        metrics = resp.json()
        assert metrics["total_events"] > 0

class TestLogsEndpoints:
    def test_logs_list_returns_files(self):
        """GET /logs should return list of log files."""
        resp = client.get("/logs")
        assert resp.status_code == 200
        data = resp.json()
        assert "logs" in data or "files" in data

    def test_logs_today_returns_events(self):
        """GET /logs/today should return today's events."""
        resp = client.get("/logs/today")
        assert resp.status_code in [200, 404]  # 404 if no logs yet
```

---

### 3. End-to-End Tests (5%)
Test full user workflows in a live environment.

**File: `e2e/monitor-capture-flow.cy.ts`** (Cypress)
```typescript
describe("Monitor Capture Flow", () => {
  beforeEach(() => {
    cy.visit("http://localhost:5173");
  });

  it("should start monitor and display events", () => {
    // Verify UI is loaded
    cy.contains("Dashboard").should("be.visible");
    
    // Click Start Monitor
    cy.contains("Start Monitor").click();
    
    // Wait for status to show Running
    cy.contains("Running", { timeout: 5000 }).should("be.visible");
    
    // Wait for buffered events count to increase
    cy.get('[aria-label="Buffered events"]', { timeout: 3000 })
      .should("contain", /\d+/);
  });

  it("should filter and export logs", () => {
    // Navigate to Logs
    cy.get('a[href="/logs"]').click();
    
    // Verify logs page loads
    cy.contains("Logs Explorer").should("be.visible");
    
    // Click export button (if logs exist)
    cy.get('button:contains("Export")').then(($btn) => {
      if ($btn.length > 0) {
        cy.wrap($btn).click();
        // Verify download
        cy.readFile("Downloads/traffic_logs.jsonl");
      }
    });
  });

  it("should predict traffic manually", () => {
    // Fill form
    cy.get('input[id="proto"]').clear().type("tcp");
    cy.get('input[id="dur"]').clear().type("0.5");
    cy.get('input[id="spkts"]').clear().type("5");
    
    // Submit
    cy.contains("Run Prediction").click();
    
    // Verify result
    cy.contains(/normal|attack/i, { timeout: 5000 }).should("be.visible");
  });
});
```

---

## Test Execution

### Run All Tests

**Backend:**
```bash
cd api
pytest tests/ -v --cov=. --cov-report=html
```

**Frontend:**
```bash
cd frontend
npm test -- --coverage
```

**E2E:**
```bash
cd frontend
npm run test:e2e
```

### Continuous Integration (GitHub Actions)

Create `.github/workflows/test.yml`:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -r api/requirements.txt
      - run: cd api && pytest tests/ -v --tb=short

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: "20"
      - run: cd frontend && npm install
      - run: npm run lint
      - run: npm test -- --coverage
      - run: npm run build
```

---

## Test Checklist

Before merging, ensure:

- [ ] All unit tests pass (`pytest tests/`)
- [ ] All component tests pass (`npm test`)
- [ ] Frontend builds without warnings (`npm run build`)
- [ ] Backend starts without errors (`python -m uvicorn main:app`)
- [ ] Frontend can connect to backend (API health check)
- [ ] Manual prediction works end-to-end
- [ ] Live monitor capture (if Admin + Npcap available)
- [ ] Logs are persisted to disk
- [ ] Model reload succeeds
- [ ] Batch ingest stores events correctly
- [ ] Metrics endpoint returns valid data
- [ ] No console errors in browser DevTools
- [ ] No Python warnings in server logs

---

## Coverage Targets

- **Backend**: ≥ 80% coverage for `inference.py` and `traffic_monitor.py`
- **Frontend**: ≥ 75% coverage for component logic (exclude styling)
- **Integration**: All API endpoints tested with happy path + error cases
- **E2E**: Critical user flows (start/stop, predict, logs export)

---

## Debugging Tips

### Backend
```bash
# Enable debug logging
RUST_LOG=debug python -m uvicorn main:app

# Run specific test with output
pytest api/tests/test_inference.py::test_predict_one_returns_valid_response -vvs
```

### Frontend
```bash
# Run tests in watch mode
npm test -- --watch

# Debug specific test
npm test -- --testNamePattern="renders start button"

# Open browser DevTools during test
npm test -- --no-coverage --detectOpenHandles
```

---

## References

- **pytest**: https://docs.pytest.org/
- **React Testing Library**: https://testing-library.com/react
- **Cypress**: https://www.cypress.io/
- **Jest**: https://jestjs.io/

---

**Summary**: Write tests first (TDD), run locally before commit, and rely on CI/CD for validation.
