# API Directory

## Purpose
This directory contains the REST API server implementation for the UNSW-NB15 network intrusion detection system. The API provides real-time predictions and batch inference capabilities for integration with production systems.

## Directory Structure
```
api/
├── requirements.txt               # Python dependencies
├── main.py                        # FastAPI application entry point
├── config.py                      # Configuration management
├── models.py                      # Pydantic data models
├── inference.py                   # Model loading & prediction logic
├── routes/
│   ├── health.py                 # Health check endpoints
│   ├── predict.py                # Single prediction endpoint
│   ├── batch_predict.py          # Batch inference endpoint
│   └── model_info.py             # Model metadata endpoint
├── middleware/
│   ├── auth.py                   # Authentication & authorization
│   ├── logging.py                # Request/response logging
│   └── rate_limit.py             # Rate limiting
├── utils/
│   ├── validators.py             # Input validation
│   ├── formatters.py             # Response formatting
│   └── error_handlers.py         # Custom error handling
├── tests/
│   ├── test_predict.py           # Prediction endpoint tests
│   ├── test_batch.py             # Batch inference tests
│   └── test_integration.py       # End-to-end API tests
├── docker/
│   ├── Dockerfile                # Docker image definition
│   └── .dockerignore
└── k8s/
    ├── deployment.yaml           # Kubernetes deployment manifest
    ├── service.yaml              # Kubernetes service config
    └── ingress.yaml              # Kubernetes ingress config
```

## API Endpoints

### Health Check
- **GET** `/health` - Server health status
  - Returns: `{ "status": "healthy", "model_loaded": true, "version": "1.0" }`

### Single Prediction
- **POST** `/predict` - Classify single network flow
  - Input: Flow features (40 numeric + 4 categorical)
  - Output: `{ "prediction": 0|1, "confidence": 0.95, "processing_time_ms": 5 }`

### Batch Prediction
- **POST** `/batch/predict` - Classify multiple flows
  - Input: Array of flows (up to 1000 per request)
  - Output: Array of predictions

### Model Information
- **GET** `/model/info` - Model metadata and specs
  - Returns: Model version, features, training date, performance metrics

### Model Metadata
- **GET** `/model/metrics` - Current model performance
  - Returns: Precision, Recall, F1-Score, ROC-AUC, Latency

## API Features

### Authentication & Security
- API key authentication (header-based)
- HTTPS enforcement in production
- Input validation and sanitization
- Rate limiting (5000 requests/minute per API key)
- Request/response logging

### Performance
- **Prediction Latency**: < 50ms per request (Phase 3 target)
- **Throughput**: 8,500+ flows/second (on 4-core CPU)
- **Model Loading Time**: < 2 seconds on startup
- **Memory Footprint**: < 500MB total

### Reliability
- Health checks (Kubernetes readiness/liveness probes)
- Graceful shutdown (in-flight requests completed)
- Model versioning (supports multiple model versions)
- Error handling with detailed status codes
- Request tracing (correlation IDs)

### Monitoring
- Prometheus metrics exposure (`/metrics`)
- Request duration histograms
- Prediction distribution tracking
- Model inference latency percentiles (p50, p95, p99)

## Configuration

### Environment Variables
```env
MODEL_PATH=../models/best_model.pkl
SCALER_PATH=../models/feature_scaler.pkl
API_KEY_SECRET=your_secret_key_here
MAX_BATCH_SIZE=1000
REQUEST_TIMEOUT=30
LOG_LEVEL=INFO
DEBUG_MODE=false
```

### Deployment Options

#### 1. Local Development
```bash
python main.py --reload --port 8000
```

#### 2. Production (Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

#### 3. Docker Container
```bash
docker build -t ids-api:latest .
docker run -p 8000:8000 ids-api:latest
```

#### 4. Kubernetes Cluster
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

## Development Workflow

### 1. Setup
```bash
pip install -r requirements.txt
python main.py --reload
```

### 2. Testing
```bash
pytest tests/
```

### 3. API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 4. Deployment
- Build: `docker build -t ids-api:latest .`
- Push: `docker push your_registry/ids-api:latest`
- Deploy: `kubectl apply -f k8s/deployment.yaml`

## Request/Response Examples

### Single Prediction
```json
POST /predict
{
  "protocol": 6,
  "duration": 45.23,
  "src_bytes": 1024,
  "dst_bytes": 2048,
  "flags": "PA",
  ...
}

Response:
{
  "prediction": 1,
  "confidence": 0.92,
  "processing_time_ms": 3.5,
  "model_version": "phase2_xgboost_v1"
}
```

### Batch Prediction
```json
POST /batch/predict
{
  "flows": [
    { "protocol": 6, "duration": 45.23, ... },
    { "protocol": 17, "duration": 12.5, ... }
  ]
}

Response:
{
  "predictions": [
    { "prediction": 1, "confidence": 0.92 },
    { "prediction": 0, "confidence": 0.88 }
  ],
  "batch_processing_time_ms": 8.3,
  "success_count": 2,
  "error_count": 0
}
```

## Integration Patterns

### Pattern 1: REST API (HTTP)
- Client calls `/predict` endpoint
- Synchronous request/response
- Best for: Web apps, dashboards, single predictions

### Pattern 2: Batch Processing
- Client sends bulk flows to `/batch/predict`
- Process multiple predictions efficiently
- Best for: Offline analysis, SIEM integration

### Pattern 3: Streaming Integration
- API consumes from Kafka/Event Hub
- Predicts and publishes results to output topic
- Best for: Real-time flow processing (Phase 4)

### Pattern 4: Embedded Model
- Load model directly in Python application
- No HTTP overhead
- Best for: High-throughput edge deployments

## Monitoring & Observability

### Prometheus Metrics
```
ids_api_request_duration_seconds (histogram)
ids_api_requests_total (counter)
ids_api_prediction_latency_ms (histogram)
ids_api_model_predictions_total (counter)
ids_api_errors_total (counter)
```

### Health Checks
- Readiness: `/health/ready` (can accept requests?)
- Liveness: `/health/live` (process alive?)
- Startup: `/health/startup` (model loaded?)

## Security Considerations

### API Key Management
- Rotate keys regularly
- Store in environment variables or Key Vault
- Never commit secrets to version control

### Input Validation
- Validate all input types and ranges
- Reject malformed requests
- Log suspicious patterns

### Output Security
- Sanitize error messages (don't leak internals)
- Rate limit to prevent brute force
- Use CORS headers appropriately

## Phase Roadmap

### Phase 1: MVP (Current)
- [ ] Create main.py (FastAPI app)
- [ ] Implement /predict endpoint
- [ ] Add health checks
- [ ] Write unit tests

### Phase 2: Production Ready
- [ ] Add authentication (API keys)
- [ ] Implement batch prediction
- [ ] Add rate limiting
- [ ] Create Dockerfile + docker-compose

### Phase 3: Advanced Features
- [ ] Kubernetes deployment manifests
- [ ] Prometheus metrics export
- [ ] Model versioning support
- [ ] Integration tests with real models

### Phase 4: Scalability
- [ ] Kubernetes auto-scaling
- [ ] Streaming integration (Kafka)
- [ ] Multi-model serving
- [ ] Performance optimization

## Next Steps
- [ ] Create requirements.txt with FastAPI dependencies
- [ ] Create main.py with basic endpoints
- [ ] Create models.py with Pydantic schemas
- [ ] Create inference.py for model loading
- [ ] Create test suite
- [ ] Create Dockerfile
- [ ] Create Kubernetes manifests
