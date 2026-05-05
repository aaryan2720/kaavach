import json
import time
import urllib.request

def send_to_dashboard(records):
    url = "http://localhost:8000/ingest"
    data = json.dumps({"records": records}).encode("utf-8")
    
    print(f"📡 Sending {len(records)} test events to Dashboard...")
    try:
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as f:
            res = json.loads(f.read().decode("utf-8"))
            print(f"✅ Success: {res.get('result', {}).get('count', 0)} events injected.")
    except Exception as e:
        print(f"❌ Failed to connect to Dashboard: {e}")
        print("   Make sure your backend (main.py) is running on port 8000!")

def run_demo():
    # Scenario 1: Normal Web Traffic
    normal_flow = {
        "src_ip": "192.168.1.5",
        "dst_ip": "93.184.216.34",
        "proto": "tcp",
        "state": "FIN",
        "dur": 0.5,
        "spkts": 4,
        "dpkts": 4,
        "sbytes": 500,
        "dbytes": 1200,
        "rate": 10,
        "sttl": 64,
        "dttl": 64
    }

    # Scenario 2: Risk (Suspicious)
    risk_flow = {
        "src_ip": "45.12.33.10",
        "dst_ip": "192.168.1.100",
        "proto": "tcp",
        "state": "REQ_RST",
        "dur": 0.1,
        "spkts": 20,
        "dpkts": 0,
        "sbytes": 2000,
        "dbytes": 0,
        "rate": 200,
        "sttl": 254,
        "dttl": 0
    }

    # Scenario 3: Critical (Attack)
    critical_flow = {
        "src_ip": "103.44.22.1",
        "dst_ip": "192.168.1.100",
        "proto": "udp",
        "state": "INT",
        "dur": 0.001,
        "spkts": 500,
        "dpkts": 0,
        "sbytes": 50000,
        "dbytes": 0,
        "rate": 5000,
        "sttl": 255,
        "dttl": 0
    }

    print("=== Kaavach Dashboard Injection Test ===")
    
    # Inject one by one with a delay so you can see them pop up
    send_to_dashboard([normal_flow])
    time.sleep(2)
    send_to_dashboard([risk_flow])
    time.sleep(2)
    send_to_dashboard([critical_flow])
    
    print("\nCheck your dashboard now! You should see:")
    print("1. A Green 'NORMAL' event.")
    print("2. A Yellow 'RISK' event.")
    print("3. A Red 'CRITICAL' event.")

if __name__ == "__main__":
    run_demo()
