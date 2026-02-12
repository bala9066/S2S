#!/usr/bin/env python3
import sys, io
# Force UTF-8 for Windows console/redirection
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
"""
API Setup Guide — Automated Validation Script
Tests every step in API_SETUP_GUIDE.md:
  Step 3: Environment configuration (.env)
  Step 4: Python dependencies
  Step 5.1: DigiKey API connectivity
  Step 5.2: Mouser API connectivity
  Step 5.3: Combined component_api_service
"""

import os
import sys
import time
import json
import subprocess
import importlib

# ── Colours (Windows-safe via ANSI) ──────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
NC     = "\033[0m"

# ── Tracking ─────────────────────────────────────────────────────
results = []  # list of (name, passed, detail)

def log(name, passed, detail=""):
    tag = f"{GREEN}✅ PASS{NC}" if passed else f"{RED}❌ FAIL{NC}"
    print(f"  {tag}  {name}")
    if detail:
        print(f"         {detail}")
    results.append((name, passed, detail))

def banner(title):
    print()
    print(f"{CYAN}{BOLD}{'═'*60}{NC}")
    print(f"{CYAN}{BOLD}  {title}{NC}")
    print(f"{CYAN}{BOLD}{'═'*60}{NC}")

# ==================================================================
# STEP 3 — Verify .env configuration
# ==================================================================
def test_env_config():
    banner("Step 3: Environment Configuration")

    # Load .env using python-dotenv
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if not os.path.exists(env_path):
            log(".env file exists", False, f"Not found at {env_path}")
            return
        load_dotenv(env_path, override=True)
        log(".env file loaded", True, env_path)
    except ImportError:
        log("python-dotenv import", False, "pip install python-dotenv")
        return

    # Check each key
    checks = {
        "DIGIKEY_CLIENT_ID":     "your_client_id",
        "DIGIKEY_CLIENT_SECRET": "your_client_secret",
        "MOUSER_API_KEY":        "your_api_key",
    }
    for key, placeholder_fragment in checks.items():
        val = os.environ.get(key, "")
        if not val:
            log(f"{key} is set", False, "Empty or missing")
        elif placeholder_fragment in val.lower() or val.startswith("your"):
            log(f"{key} is set", False, "Still contains placeholder value")
        else:
            log(f"{key} is set", True, f"{val[:12]}…")

# ==================================================================
# STEP 4 — Verify Python dependencies
# ==================================================================
def test_dependencies():
    banner("Step 4: Python Dependencies")

    required = ["requests", "fastapi", "uvicorn", "pydantic", "dotenv"]
    pkg_names = {
        "dotenv": "python-dotenv",
    }

    for mod in required:
        try:
            importlib.import_module(mod)
            log(f"import {mod}", True)
        except ImportError:
            pip_name = pkg_names.get(mod, mod)
            log(f"import {mod}", False, f"pip install {pip_name}")

# ==================================================================
# STEP 5.1 — DigiKey API live test
# ==================================================================
def test_digikey_api():
    banner("Step 5.1: DigiKey API")

    try:
        # Import the project module
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from digikey_api import DigiKeyAPI

        api = DigiKeyAPI()

        # Verify credentials loaded
        if not api.client_id:
            log("DigiKey client_id loaded", False, "Empty — check .env")
            return
        log("DigiKey client_id loaded", True, f"{api.client_id[:12]}…")

        if not api.client_secret:
            log("DigiKey client_secret loaded", False, "Empty — check .env")
            return
        log("DigiKey client_secret loaded", True, f"{api.client_secret[:12]}…")

        # Live search
        print(f"\n  {YELLOW}⏳ Calling DigiKey API (searching 'STM32F4')…{NC}")
        start = time.time()
        result = api.search_products("STM32F4", limit=5)
        elapsed = time.time() - start

        log("DigiKey API call", result.get("success", False),
            f"{elapsed:.2f}s — "
            + (f"found {result.get('total_found', 0)} results, "
               f"returned {len(result.get('components', []))} components"
               if result.get("success")
               else result.get("error", "Unknown error")))

        # Show first component if available
        comps = result.get("components", [])
        if comps:
            c = comps[0]
            print(f"\n  {CYAN}First component:{NC}")
            print(f"    Part:         {c.get('part_number', 'N/A')}")
            print(f"    Manufacturer: {c.get('manufacturer', 'N/A')}")
            print(f"    Price:        {c.get('pricing', {}).get('unit_price', 'N/A')}")
            print(f"    Stock:        {c.get('availability', {}).get('stock', 'N/A')}")

    except Exception as e:
        log("DigiKey API test", False, str(e))

# ==================================================================
# STEP 5.2 — Mouser API live test
# ==================================================================
def test_mouser_api():
    banner("Step 5.2: Mouser API")

    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from mouser_api import MouserAPI

        api = MouserAPI()

        if not api.api_key:
            log("Mouser api_key loaded", False, "Empty — check .env")
            return
        log("Mouser api_key loaded", True, f"{api.api_key[:12]}…")

        # Live search
        print(f"\n  {YELLOW}⏳ Calling Mouser API (searching 'STM32F4')…{NC}")
        start = time.time()
        result = api.search_products("STM32F4", limit=5)
        elapsed = time.time() - start

        log("Mouser API call", result.get("success", False),
            f"{elapsed:.2f}s — "
            + (f"found {result.get('total_found', 0)} results, "
               f"returned {len(result.get('components', []))} components"
               if result.get("success")
               else result.get("error", "Unknown error")))

        comps = result.get("components", [])
        if comps:
            c = comps[0]
            print(f"\n  {CYAN}First component:{NC}")
            print(f"    Part:         {c.get('part_number', 'N/A')}")
            print(f"    Manufacturer: {c.get('manufacturer', 'N/A')}")
            print(f"    Price:        {c.get('pricing', {}).get('unit_price', 'N/A')}")
            print(f"    Stock:        {c.get('availability', {}).get('stock', 'N/A')}")

    except Exception as e:
        log("Mouser API test", False, str(e))

# ==================================================================
# STEP 5.3 — Combined service test
# ==================================================================
def test_combined_service():
    banner("Step 5.3: Combined Component API Service")

    script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "component_api_service.py")
    if not os.path.exists(script):
        log("component_api_service.py exists", False)
        return
    log("component_api_service.py exists", True)

    port = int(os.environ.get("API_SERVICE_PORT", 8001))
    base = f"http://localhost:{port}"
    proc = None

    try:
        # Start the service as a subprocess, passing current env
        env = os.environ.copy()
        proc = subprocess.Popen(
            [sys.executable, script],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Wait for service to be ready (poll /api/health)
        print(f"\n  {YELLOW}⏳ Starting service on port {port}…{NC}")
        import requests as req
        ready = False
        for i in range(15):  # up to 15 seconds
            time.sleep(1)
            try:
                r = req.get(f"{base}/api/health", timeout=2)
                if r.status_code == 200:
                    ready = True
                    break
            except Exception:
                pass

        if not ready:
            log("Service started", False, f"Not reachable after 15 s on {base}")
            return

        log("Service started", True, f"Listening on {base}")

        # Health check
        r = req.get(f"{base}/api/health", timeout=5)
        health = r.json()
        dk_ok = health.get("digikey_configured", False)
        mo_ok = health.get("mouser_configured", False)
        log("Health — DigiKey configured", dk_ok)
        log("Health — Mouser configured", mo_ok)

        # Search test
        print(f"\n  {YELLOW}⏳ Searching 'STM32F4' via combined service…{NC}")
        start = time.time()
        r = req.post(
            f"{base}/api/search",
            json={
                "search_term": "STM32F4",
                "category": "processor",
                "limit_per_source": 5,
            },
            timeout=30,
        )
        elapsed = time.time() - start
        data = r.json()

        success = data.get("success", False)
        total = data.get("total_found", 0)
        comps = data.get("components", [])
        sources = data.get("sources", {})

        log("Combined search", success,
            f"{elapsed:.2f}s — {total} found, {len(comps)} returned, "
            f"sources: {json.dumps(sources)}")

        if comps:
            c = comps[0]
            print(f"\n  {CYAN}First component:{NC}")
            print(f"    Part:         {c.get('part_number', 'N/A')}")
            print(f"    Manufacturer: {c.get('manufacturer', 'N/A')}")
            print(f"    Source:       {c.get('source', 'N/A')}")

        errs = data.get("errors", [])
        if errs:
            print(f"\n  {YELLOW}Warnings/Errors from service:{NC}")
            for e in errs:
                print(f"    ⚠ {e}")

    except Exception as e:
        log("Combined service test", False, str(e))
    finally:
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
            log("Service stopped", True)

# ==================================================================
# MAIN
# ==================================================================
if __name__ == "__main__":
    banner("API SETUP GUIDE — VALIDATION")
    print(f"  Running on Python {sys.version.split()[0]}")
    print(f"  Working dir: {os.getcwd()}")

    test_env_config()
    test_dependencies()
    test_digikey_api()
    test_mouser_api()
    test_combined_service()

    # ── Summary ──────────────────────────────────────────────────
    banner("SUMMARY")
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    total  = len(results)

    print(f"  {GREEN}{passed} passed{NC}  |  {RED if failed else GREEN}{failed} failed{NC}  |  {total} total")
    print()

    if failed:
        print(f"  {RED}Failed tests:{NC}")
        for name, p, detail in results:
            if not p:
                print(f"    ❌ {name}: {detail}")
        print()

    sys.exit(0 if failed == 0 else 1)
