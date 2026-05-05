# Kaavach Network Traffic Logging

## Overview
The traffic monitor automatically saves all detected network events to local disk as JSON Lines (JSONL) files. Each line is a complete JSON event record for easy parsing and analysis.

## Log Location
```
api/logs/YYYY-MM-DD_traffic.jsonl
```
- One file per day
- Files created automatically when first event occurs
- Located in `api/logs/` directory

## Log File Format
Each line is a complete JSON object:
```json
{"timestamp": "2026-05-05T12:34:56.789123+00:00", "src_ip": "192.168.1.100", "dst_ip": "192.168.1.50", "protocol": "icmp", "decision": "attack", "confidence": 0.99, "reason": "icmp_echo_burst"}
```

### Event Fields
| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string (ISO 8601) | When packet was captured (UTC) |
| `src_ip` | string | Source IP address |
| `dst_ip` | string | Destination IP address |
| `protocol` | string | Protocol (icmp, tcp, udp, etc.) |
| `decision` | string | Model classification: "attack" or "normal" |
| `confidence` | float | Confidence score (0.0 - 1.0) |
| `reason` | string | Why this decision (e.g., "icmp_echo_burst", "model_inference") |

## API Endpoints for Logs

### List All Logs
```
GET /logs
```
Returns available log files and their location.

**Example Response:**
```json
{
  "logs": ["2026-05-05_traffic.jsonl", "2026-05-04_traffic.jsonl"],
  "logs_dir": "d:\\Documents\\ML model\\api\\logs"
}
```

### Get Today's Logs
```
GET /logs/today
```
Returns all events from today's log file.

**Example Response:**
```json
{
  "events": [
    {"timestamp": "2026-05-05T12:34:56.789123+00:00", "src_ip": "192.168.1.100", ...},
    {"timestamp": "2026-05-05T12:34:57.123456+00:00", "src_ip": "192.168.1.101", ...}
  ],
  "file": "2026-05-05_traffic.jsonl",
  "count": 2
}
```

### Export All Logs
```
GET /logs/export?filename=my_logs.jsonl
```
Downloads all logs as a single JSONL file.

**Query Parameters:**
- `filename` (optional): Custom download filename (default: "traffic_logs.jsonl")

## Local Database Usage

### Reading Logs with Python
```python
import json
from pathlib import Path

log_file = Path("api/logs/2026-05-05_traffic.jsonl")

events = []
with open(log_file) as f:
    for line in f:
        if line.strip():
            event = json.loads(line)
            events.append(event)

# Filter attacks only
attacks = [e for e in events if e["decision"] == "attack"]
print(f"Found {len(attacks)} attack events")
```

### Reading Logs with CLI (PowerShell)
```powershell
# Count total events
$events = Get-Content "api\logs\2026-05-05_traffic.jsonl" | Measure-Object -Line

# Filter attacks
$attacks = Get-Content "api\logs\2026-05-05_traffic.jsonl" | ConvertFrom-Json | Where-Object { $_.decision -eq "attack" }
$attacks | Format-Table timestamp, src_ip, decision, reason
```

### Reading Logs with CLI (Bash/Git Bash)
```bash
# Count total events
wc -l api/logs/2026-05-05_traffic.jsonl

# Filter attacks only
cat api/logs/2026-05-05_traffic.jsonl | jq 'select(.decision == "attack")'

# Count attacks by source IP
cat api/logs/2026-05-05_traffic.jsonl | jq -r 'select(.decision == "attack") | .src_ip' | sort | uniq -c
```

## Backup & Archival

Log files persist automatically and accumulate by date. To archive old logs:

```powershell
# Compress logs older than 30 days
$thirtyDaysAgo = (Get-Date).AddDays(-30)
Get-ChildItem "api\logs\*.jsonl" | Where-Object { $_.LastWriteTime -lt $thirtyDaysAgo } | Compress-Archive -DestinationPath "api\logs\archive.zip"
```

## Notes
- Events are appended to disk immediately as they arrive (no buffering delay)
- If log write fails, a warning is printed but monitor continues running
- Maximum 500 events kept in memory; disk has no limit
- Frontend can query logs via `/logs` and `/logs/today` endpoints
- All timestamps in UTC (ISO 8601 format)
