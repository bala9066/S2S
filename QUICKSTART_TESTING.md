# 🚀 Quick Start: Phase 1 Testing (5 Minutes)

## Step 1: Start Services (1 minute)

```bash
cd /home/user/S2S

# Start all services
docker compose up -d

# Wait for services to initialize
sleep 30

# Verify services are running
docker ps
```

**Expected:** You should see 3+ containers running:
- `hardware_pipeline_postgres`
- `hardware_pipeline_n8n`
- `hardware_pipeline_component_api`

---

## Step 2: Run Automated Tests (30 seconds)

```bash
# Make executable
chmod +x test_phase1_e2e.py

# Run tests
python3 test_phase1_e2e.py
```

**Expected output:**
```
======================================================================
  PHASE 1 END-TO-END AUTOMATED TESTS
======================================================================

✅ PASS: Docker Services
   Running: 3/3 - hardware_pipeline_postgres, hardware_pipeline_n8n, hardware_pipeline_component_api

✅ PASS: Component API Health
   Status: healthy, DigiKey: True, Mouser: True

✅ PASS: Component Search
   Found: 18 components, Time: 850ms, Sources: {'digikey': 10, 'mouser': 8}

✅ PASS: n8n Connectivity
   n8n accessible at http://localhost:5678

✅ PASS: Workflow File Validation
   Nodes: 19, Connections: 18

✅ PASS: Mermaid Diagram Generator
   Mermaid converter working correctly

✅ PASS: API Modules
   DigiKey module: OK, Mouser module: OK

======================================================================
  TEST SUMMARY
======================================================================

Total Tests: 7
Passed: 7
Failed: 0
Success Rate: 100.0%

✅ All tests passed! Phase 1 is ready for end-to-end testing.
```

---

## Step 3: Open n8n and Import Workflow (1 minute)

```bash
# Open n8n in browser
# URL: http://localhost:5678

# Login (if prompted):
# Username: admin
# Password: admin123
```

**In n8n:**
1. Click **"Workflows"** in sidebar
2. Click **"Import from File"**
3. Select: `Phase1_Complete_Workflow_READY_TO_IMPORT.json`
4. Click **"Import"**
5. Workflow opens automatically

---

## Step 4: Run First Test (3 minutes)

### Test Case: Motor Controller (Simple)

**In n8n workflow, find the chat interface and paste this:**

```
Design a 3-phase motor controller with TMS320F28379D DSP, 10kW output power, 48V DC input, 0-400Hz output frequency, Ethernet interface, current sensing with hall sensors, and temperature protection with NTC thermistors.
```

**Click Send and watch the workflow execute:**

### Expected Flow:

**Step 1: Requirements Parsing (5s)**
```
✅ Input validated
✅ System type detected: Motor_Control
✅ Requirements parsed by AI
```

**Step 2: Block Diagram Generation (3s)**
```
📋 BLOCK DIAGRAM GENERATED

╔════════════════════════════════════════╗
║  BLOCK DIAGRAM: Motor_Controller      ║
╠════════════════════════════════════════╣
║  System Type: Motor_Control            ║
║  Total Blocks: 28                      ║
║  Connections: 35                       ║
╚════════════════════════════════════════╝

🎨 VISUAL PREVIEW AVAILABLE
Open: /mnt/data/outputs/Project_xxx_block_diagram.html

Type "APPROVE" to continue
```

**Step 3: Approve Diagram**
- Type: `APPROVE`
- Press Send

**Step 4: Component Search (10-30s)**
```
🔍 Searching DigiKey + Mouser...
[BATCH 1/3] Processing...
[BATCH 2/3] Processing...
[BATCH 3/3] Processing...
```

**Step 5: BOM Generation (2s)**
```
✅ PHASE 1 COMPLETE

╔══════════════════════════════════════╗
║         BILL OF MATERIALS            ║
╠══════════════════════════════════════╣
║  Project: Project_1707523456789      ║
║  Total Components: 47                ║
║  Estimated Cost: $387.50             ║
╚══════════════════════════════════════╝

TOP COMPONENTS:
1. TMS320F28379DZWTT        $15.50
2. ACPL-P346                 $8.20
3. LAN8720A-CP              $3.90
...and 44 more components

📦 Next Steps:
- Phase 2: Generate HRS Document
- Phase 3: Compliance validation
- Phase 4: Netlist generation
```

---

## ✅ Success Criteria

Your test is successful if:
- [x] Workflow completes without errors
- [x] Block diagram shows 25-35 blocks
- [x] BOM shows 40-60 components
- [x] Total cost is calculated
- [x] Execution time < 60 seconds

---

## 🐛 If Tests Fail

### Problem: Component API Health fails

**Error:** `digikey_configured: false`

**Solution:**
```bash
# Edit .env file
nano .env

# Add your API credentials:
DIGIKEY_CLIENT_ID=your_client_id_here
DIGIKEY_CLIENT_SECRET=your_client_secret_here
MOUSER_API_KEY=your_api_key_here

# Restart services
docker compose restart component_api

# Re-test
python3 test_phase1_e2e.py
```

**Get API keys:**
- DigiKey: https://developer.digikey.com/
- Mouser: https://www.mouser.com/api-hub/

See `API_SETUP_GUIDE.md` for detailed instructions.

---

### Problem: Component Search returns 0 components

**Error:** `total_found: 0`

**Solution:**
```bash
# Check API service logs
docker logs hardware_pipeline_component_api --tail 50

# Test APIs directly
curl -X POST http://localhost:8001/api/search \
  -H "Content-Type: application/json" \
  -d '{"search_term": "STM32F4", "category": "processor", "limit_per_source": 5}'

# Should return components from DigiKey + Mouser
```

If still failing, check:
1. API credentials are correct in `.env`
2. Network/firewall not blocking API calls
3. API rate limits not exceeded

---

### Problem: n8n Connectivity fails

**Error:** `Cannot connect to n8n`

**Solution:**
```bash
# Check if n8n is running
docker ps | grep n8n

# If not running, start it
docker compose up -d n8n

# Check logs
docker logs hardware_pipeline_n8n --tail 50

# Access n8n
open http://localhost:5678
```

---

### Problem: Docker Services not running

**Error:** `Running: 0/3`

**Solution:**
```bash
# Check Docker daemon
docker info

# If Docker not running, start it:
# - Windows/Mac: Open Docker Desktop
# - Linux: sudo systemctl start docker

# Start services
cd /home/user/S2S
docker compose up -d

# Wait and verify
sleep 30
docker ps
```

---

## 📊 What to Test Next

After successful quick start test:

### Test Different Hardware Types:

1. **RF System** (40s)
   ```
   Design RF transmitter 5-18 GHz, 40 dBm output, Xilinx Artix-7 FPGA, GaN PA, Ethernet interface
   ```

2. **Digital Controller** (25s)
   ```
   Design digital controller with STM32F407 MCU, USB 2.0, microSD card, 128x64 OLED display, 4 buttons
   ```

3. **Sensor System** (30s)
   ```
   Design sensor system with RP2040, BME680 sensor, MPU6050 IMU, GPS module, WiFi ESP8266, microSD storage
   ```

Each test should complete in 20-50 seconds with different BOM outputs.

---

## 📋 Complete Testing

For comprehensive testing, see:
- **PHASE1_E2E_TEST_GUIDE.md** - Complete test guide with 5 detailed test cases
- **VISUAL_DIAGRAM_SOLUTIONS.md** - Visual diagram testing
- **API_SETUP_GUIDE.md** - API configuration details

---

## 🎯 Next Steps

Once quick start testing passes:

1. **Run all 5 test cases** from PHASE1_E2E_TEST_GUIDE.md
2. **Test visual diagram approval** (Mermaid HTML)
3. **Verify DigiKey + Mouser integration**
4. **Test error handling** (invalid input, API failures)
5. **Performance testing** (measure execution times)

Then either:
- **Deploy Phase 1** for production use
- **Implement Phase 2** (HRS Document Generation)
- **Implement Phase 4** (Netlist Generation)

---

## ✅ Done!

You've successfully:
- ✅ Started all services
- ✅ Ran automated tests
- ✅ Imported workflow
- ✅ Tested with real hardware project
- ✅ Generated block diagram and BOM

**Phase 1 is working!** 🎉

**Total time:** 5 minutes
