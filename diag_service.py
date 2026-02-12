"""Quick diagnostic: does uvicorn subprocess see .env values?"""
import subprocess, sys, time, json

print("Starting component_api_service.py as subprocess...")
proc = subprocess.Popen(
    [sys.executable, "component_api_service.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="replace",
)

# Wait for service
import requests as req
for i in range(10):
    time.sleep(1)
    try:
        r = req.get("http://localhost:8001/api/health", timeout=2)
        if r.status_code == 200:
            print(f"Service ready after {i+1}s")
            print("Health:", json.dumps(r.json(), indent=2))
            # Also test search
            r2 = req.post("http://localhost:8001/api/search", json={
                "search_term": "STM32F4", "category": "processor",
                "sources": ["mouser"], "limit_per_source": 3
            }, timeout=15)
            data = r2.json()
            print(f"\nSearch: success={data.get('success')}, sources={data.get('sources')}, errors={data.get('errors')}")
            if data.get("components"):
                c = data["components"][0]
                print(f"  First: {c.get('part_number')} from {c.get('source')}")
            break
    except Exception as e:
        print(f"  waiting... ({e})")

# Capture startup output
proc.terminate()
try:
    out, _ = proc.communicate(timeout=3)
    print("\n--- Service stdout ---")
    print(out[:2000])
except:
    proc.kill()
