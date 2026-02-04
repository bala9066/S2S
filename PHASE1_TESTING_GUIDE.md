# Phase 1 Workflow - Complete Testing Guide

## 🎯 Overview

This guide provides step-by-step instructions for testing the Phase 1 workflow of the Hardware Pipeline system.

**What Phase 1 Does:**
- Takes natural language hardware requirements as input
- Detects system type (RF, Motor Control, Digital, Power, Industrial, Sensor)
- Parses requirements using Claude AI (12+ component categories)
- Generates comprehensive block diagrams (20-35 blocks, 25-45 connections)
- Searches for components using Playwright (DigiKey, Mouser)
- Caches components in PostgreSQL (95% hit rate, 30-day TTL)
- Recommends best components with AI
- Generates Bill of Materials (BOM)

**Expected Duration:** ~6 minutes for complete Phase 1 execution

---

## 📋 Prerequisites

### Required Software

- **Docker:** Version 20.10+ with Docker Compose v2
- **Python:** 3.10+
- **Node.js:** 16+ (for JavaScript validation)
- **Git:** For version control
- **curl:** For API testing

### Required Accounts

- **Claude API Key:** Get from [console.anthropic.com](https://console.anthropic.com/settings/keys)
  - Model used: Claude Sonnet 4.5
  - Estimated cost: $0.10-0.20 per Phase 1 run

### System Requirements

- **RAM:** 8GB minimum (16GB recommended)
- **Disk:** 10GB free space
- **CPU:** 4 cores recommended
- **Network:** Internet connection for component scraping and Claude API

---

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Clone repository
git clone https://github.com/bala9066/S2S.git
cd S2S
git checkout claude/start-implementation-Y5bqL

# 2. Configure environment
cp .env.example .env
nano .env  # Add your CLAUDE_API_KEY=sk-ant-api03-YOUR-KEY

# 3. Run pre-flight check
chmod +x test_phase1_preflight.sh
./test_phase1_preflight.sh

# 4. Start services
docker compose up -d

# 5. Run automated tests
chmod +x test_phase1_workflow.sh
./test_phase1_workflow.sh

# 6. Access n8n
# Open: http://localhost:5678
# Login: admin / admin123 (or from .env)
```

---

## 📝 Step-by-Step Testing Guide

### Step 1: Pre-Flight Check

Run the pre-flight check script to validate your environment:

```bash
chmod +x test_phase1_preflight.sh
./test_phase1_preflight.sh
```

**What it checks:**
- ✅ Docker and Docker Compose installed
- ✅ Required files present
- ✅ .env file configured
- ✅ CLAUDE_API_KEY set
- ✅ Port availability (5432, 5678, 8000, 6379, 5050)
- ✅ Sufficient disk space
- ✅ Valid JSON/YAML/JavaScript/Python syntax

**Expected output:**
```
✅ PRE-FLIGHT CHECK PASSED

You are ready to start Phase 1 testing!
```

**If it fails:**
- Check error messages
- Fix reported issues
- Re-run pre-flight check

---

### Step 2: Start Docker Services

Start all required services:

```bash
docker compose up -d
```

**Services started:**
- `postgres` - PostgreSQL database (port 5432)
- `n8n` - Workflow orchestrator (port 5678)
- `playwright` - Component scraper with FastAPI (port 8000)
- `redis` - Session management (port 6379)
- `pgadmin` - Database admin GUI (port 5050)

**Verify services are running:**
```bash
docker compose ps
```

**Expected output:**
```
NAME                              STATUS    PORTS
hardware_pipeline_postgres        Up        0.0.0.0:5432->5432/tcp
hardware_pipeline_n8n             Up        0.0.0.0:5678->5678/tcp
hardware_pipeline_playwright      Up        0.0.0.0:8000->8000/tcp
hardware_pipeline_redis           Up        0.0.0.0:6379->6379/tcp
hardware_pipeline_pgadmin         Up        0.0.0.0:5050->80/tcp
```

**Wait for services to be ready (~30 seconds):**
```bash
# Check n8n
curl http://localhost:5678

# Check Playwright API
curl http://localhost:8000/api/health
```

---

### Step 3: Verify Database Initialization

Check that PostgreSQL database is initialized with the schema:

```bash
# Connect to database
docker exec -it hardware_pipeline_postgres psql -U postgres -d hardware_pipeline

# List tables (should show 11 tables)
\dt

# Expected tables:
# - component_cache
# - projects
# - phase_outputs
# - compliance_records
# - api_usage
# - component_recommendations
# - block_diagrams
# - bom_items
# - scraping_queue
# - system_logs
# - user_sessions (if applicable)

# Exit
\q
```

**Or check programmatically:**
```bash
docker exec hardware_pipeline_postgres psql -U postgres -d hardware_pipeline -c "\dt"
```

---

### Step 4: Run Automated Tests

Run the comprehensive test suite:

```bash
chmod +x test_phase1_workflow.sh
./test_phase1_workflow.sh
```

**Tests performed (10 test suites):**

1. **Docker Services Startup**
   - ✅ PostgreSQL starts
   - ✅ n8n starts
   - ✅ Playwright API starts

2. **Database Initialization**
   - ✅ 11 tables created
   - ✅ Python can connect

3. **Playwright Scraper API**
   - ✅ Health endpoint responds
   - ✅ Cache status endpoint works
   - ✅ Component search works

4. **Component Caching**
   - ✅ First search (cache miss)
   - ✅ Second search (cache hit, faster)

5. **Workflow Structure Validation**
   - ✅ JSON structure valid
   - ✅ All required nodes present
   - ✅ JavaScript nodes valid

6. **Component Flow Simulation**
   - ✅ System type detection works
   - ✅ Component search pipeline works

7. **Database Data Persistence**
   - ✅ Write test data
   - ✅ Read test data back

8. **Resource Usage Check**
   - ✅ All 5 containers running
   - ✅ Memory usage acceptable

9. **Error Handling**
   - ✅ Invalid API requests rejected
   - ✅ Database errors handled

10. **Service Logs Check**
    - ✅ No critical errors in logs

**Expected output:**
```
════════════════════════════════════════════════════════════
  TEST RESULTS SUMMARY
════════════════════════════════════════════════════════════

Total Tests:  25
Passed:       25
Failed:       0

✅ ALL TESTS PASSED

Phase 1 workflow is ready for use!
```

---

### Step 5: Import Workflow to n8n

Now that all tests pass, import the workflow into n8n:

#### Method A: Via n8n UI (Recommended)

1. **Open n8n:**
   ```
   http://localhost:5678
   ```

2. **Login:**
   - Username: `admin`
   - Password: `admin123` (or value from .env `N8N_PASSWORD`)

3. **Import workflow:**
   - Click "Workflows" in left sidebar
   - Click "+ Add workflow"
   - Click ⋮ (three dots) → "Import from File"
   - Select: `Phase1_Complete_Workflow_READY_TO_IMPORT.json`
   - Click "Import"

4. **Workflow opens automatically**

#### Method B: Via n8n API (Alternative)

```bash
curl -X POST http://localhost:5678/rest/workflows \
  -H "Content-Type: application/json" \
  -H "X-N8N-API-KEY: your-api-key" \
  -d @Phase1_Complete_Workflow_READY_TO_IMPORT.json
```

---

### Step 6: Update Workflow Nodes (CRITICAL!)

The imported workflow has the old restrictive prompts. Update with improved versions:

#### Update "Build AI Prompt" Node

1. Find node named **"Build AI Prompt"**
2. Double-click to open
3. **Replace the entire `jsCode` parameter** with contents of:
   ```
   improved_ai_prompt.js
   ```
4. Click "Save"

**How to copy:**
```bash
# View the code
cat improved_ai_prompt.js

# Or open in editor
nano improved_ai_prompt.js
```

#### Update "Generate Block Diagram" Node

1. Find node named **"Generate Block Diagram"**
2. Double-click to open
3. **Replace the entire `jsCode` parameter** with contents of:
   ```
   improved_block_diagram_generator.js
   ```
4. Click "Save"

**How to copy:**
```bash
# View the code
cat improved_block_diagram_generator.js
```

#### Configure Claude API Credentials

1. In n8n, click **"Settings"** (gear icon) → "Credentials"
2. Click **"+ Add Credential"**
3. Search for **"Claude"** or **"Anthropic"**
4. Fill in:
   - **Credential Name:** `Claude_API`
   - **API Key:** `sk-ant-api03-...` (your key from .env)
5. Click **"Test connection"** → Should show ✅
6. Click **"Save"**

---

### Step 7: Activate Workflow

1. In the workflow editor, click the **"Active"** toggle in top-right
2. It should turn **green**
3. Workflow is now listening for chat input

---

### Step 8: Test with Sample Requirements

Now test the workflow with real requirements:

#### Test Case 1: Motor Controller (Recommended First Test)

**In n8n chat interface, enter:**

```
Design a 3-phase motor controller with TMS320F28379D DSP, 10kW output power,
48V DC input, 0-400Hz output frequency, Ethernet interface for monitoring,
current sensing with hall sensors, and temperature protection with NTC thermistors.
```

**Expected AI response (~5-8 seconds):**

```
📋 BLOCK DIAGRAM GENERATED

╔════════════════════════════════════════════╗
║   BLOCK DIAGRAM: Project_1738454400000    ║
╠════════════════════════════════════════════╣
║   System Type: Motor_Control               ║
║   Total Blocks: 24                         ║
║   Connections: 31                          ║
║   Power Rails: 4                           ║
╚════════════════════════════════════════════╝

SYSTEM ARCHITECTURE:

1. POWER:
   a. Input 48V [power_input]
   b. Protection Circuit [protection]
   c. 5V @ 2A [power_regulator]
   d. 3.3V @ 1.5A [power_regulator]
   e. 1.8V @ 0.8A [power_regulator]
   f. 15V @ 0.5A [power_regulator]

2. PROCESSING:
   a. TMS320F28379D [processor]

3. POWER_STAGE:
   a. Gate Driver (6ch) [gate_driver]
   b. MOSFET (100V/240A) [power_switch]
   c. 3-phase inverter [output_stage]

4. SENSING:
   a. Current Sensor [sensor]
   b. Temperature Sensor [sensor]

... and more

✅ Please review the block diagram above.

Options:
- Type "APPROVE" to continue to component selection
- Type "REJECT: <reason>" to request changes

Waiting for your approval...
```

**User response:**
```
APPROVE
```

**AI continues** (~60-90 seconds):
- Searches for components (processor, regulators, gate drivers, MOSFETs, sensors)
- Caches components in PostgreSQL
- AI recommends best components
- Generates BOM

**Expected final output:**

```
✅ PHASE 1 COMPLETE

╔══════════════════════════════════════╗
║         BILL OF MATERIALS            ║
╠══════════════════════════════════════╣
║  Project: Project_1738454400000      ║
║  Total Components: 50+               ║
║  Estimated Cost: $450-550            ║
╚══════════════════════════════════════╝

TOP COMPONENTS:
1. TMS320F28379D - DSP Processor
2. UCC21520 - Isolated Gate Driver
3. CSD19536KTT - 100V N-Channel MOSFET
4. TPS54620 - 6A Buck Converter
5. ACS770 - Hall Effect Current Sensor
... and 45+ more components

📦 Next Steps:
- Phase 2: Generate HRS Document (50-70 pages)
- Phase 3: Compliance validation
- Phase 4: Netlist generation

Would you like to continue to Phase 2?
```

**✅ SUCCESS CRITERIA:**
- Block diagram shows 20-35 blocks (not just 8-12)
- Power distribution tree with 4+ voltage rails
- Power stage components (gate drivers, MOSFETs)
- Sensors (current, temperature)
- BOM with 50+ components
- Total time: ~6 minutes

---

#### Test Case 2: RF/Wireless System

```
Design RF amplifier with Xilinx Artix-7 FPGA, 40dBm output power, 5-18GHz
frequency range, GaN power amplifier, return loss > 10dB, buck-boost converters
for multiple power rails.
```

**Expected:**
- System Type: RF_Wireless
- RF components: PA, LNA, filters, matching networks, antenna
- FPGA with appropriate I/O
- Power management for multiple rails

---

#### Test Case 3: Digital Controller

```
Design digital controller with Zynq UltraScale+ MPSoC, 2GB DDR4 memory,
Gigabit Ethernet, USB 3.0, PCIe Gen3 x4, operating temperature -40 to 85°C.
```

**Expected:**
- System Type: Digital_Controller
- Zynq processor
- DDR4 memory with interface
- Ethernet PHY, USB controller, PCIe interface
- Power regulators for multiple voltage domains

---

### Step 9: Monitor Execution

During workflow execution, monitor in n8n:

1. Click **"Executions"** in left sidebar
2. See execution list with status
3. Click on an execution to see detailed flow
4. Each node shows:
   - Input data (what it received)
   - Output data (what it produced)
   - Execution time

**Check for errors:**
- Green = Success
- Red = Error (click for details)
- Yellow = Warning

---

### Step 10: Verify Database Storage

After successful execution, check data was stored:

```bash
# Connect to database
docker exec -it hardware_pipeline_postgres psql -U postgres -d hardware_pipeline

# Check projects
SELECT id, project_name, system_type, phase_completed, created_at
FROM projects
ORDER BY created_at DESC
LIMIT 5;

# Check component cache
SELECT COUNT(*) FROM component_cache;

# Check block diagrams
SELECT COUNT(*) FROM block_diagrams;

# Exit
\q
```

---

## 🐛 Troubleshooting

### Issue 1: Services Won't Start

**Symptom:**
```
Error: Cannot start service postgres
```

**Solutions:**
1. Check if ports are already in use:
   ```bash
   lsof -i :5432
   lsof -i :5678
   lsof -i :8000
   ```

2. Stop conflicting services:
   ```bash
   # Kill process on port 5432
   kill $(lsof -t -i:5432)
   ```

3. Or change ports in `docker-compose.yml`:
   ```yaml
   postgres:
     ports:
       - "5433:5432"  # Changed from 5432:5432
   ```

---

### Issue 2: n8n Won't Start

**Symptom:**
```
n8n exiting with error
```

**Solutions:**
1. Check logs:
   ```bash
   docker compose logs n8n
   ```

2. Wait for PostgreSQL:
   ```bash
   # n8n depends on postgres, give it time
   docker compose logs postgres | grep "ready to accept"
   ```

3. Restart n8n:
   ```bash
   docker compose restart n8n
   ```

---

### Issue 3: Playwright Scraping Fails

**Symptom:**
```
Component search returns empty or errors
```

**Solutions:**
1. Check Playwright container:
   ```bash
   docker compose logs playwright
   ```

2. Reinstall Chromium:
   ```bash
   docker exec -it hardware_pipeline_playwright bash
   playwright install chromium
   exit
   ```

3. Test API manually:
   ```bash
   curl -X POST http://localhost:8000/api/scrape \
     -H "Content-Type: application/json" \
     -d '{"search_term": "test", "category": "processor", "use_cache": true}'
   ```

---

### Issue 4: Claude API Errors

**Symptom:**
```
401 Unauthorized: Invalid API Key
```

**Solutions:**
1. Verify API key in .env:
   ```bash
   cat .env | grep CLAUDE_API_KEY
   ```

2. Check n8n credential:
   - Settings → Credentials → Claude_API
   - Click "Test connection"

3. Get new key:
   - Visit: https://console.anthropic.com/settings/keys
   - Create new key
   - Update .env and n8n credential

---

### Issue 5: Workflow Stops at Approval

**Symptom:**
```
Workflow stays at "Waiting for approval"
```

**Explanation:**
This is **EXPECTED** behavior. The workflow pauses for user approval.

**Solution:**
Type `APPROVE` in the chat to continue.

---

### Issue 6: Database Connection Failed

**Symptom:**
```
psycopg2.OperationalError: could not connect
```

**Solutions:**
1. Check PostgreSQL is running:
   ```bash
   docker compose ps postgres
   ```

2. Check connection string:
   ```python
   # Should be:
   host='localhost'  # or 'postgres' from inside containers
   port=5432
   database='hardware_pipeline'
   user='postgres'
   password='postgres123'  # from .env
   ```

3. Test connection:
   ```bash
   docker exec hardware_pipeline_postgres psql -U postgres -d hardware_pipeline -c "SELECT 1;"
   ```

---

### Issue 7: Out of Memory

**Symptom:**
```
Container killed (OOMKilled)
```

**Solutions:**
1. Increase Docker memory:
   - Docker Desktop → Settings → Resources → Memory → 8GB+

2. Check memory usage:
   ```bash
   docker stats
   ```

3. Restart with more resources:
   ```bash
   docker compose down
   docker compose up -d
   ```

---

## 📊 Performance Benchmarks

### Expected Timing

| Step | Duration | Notes |
|------|----------|-------|
| Requirements input | ~1s | User types |
| System type detection | <1s | JavaScript regex |
| AI prompt building | <1s | JavaScript |
| Claude API (parse) | 5-8s | 3,900 token prompt |
| Block diagram generation | 1-2s | JavaScript |
| User approval wait | Variable | User-dependent |
| Component searches (parallel) | 30-60s | Playwright scraping |
| Component aggregation | <1s | n8n |
| Claude API (recommend) | 3-5s | Component analysis |
| BOM generation | <1s | JavaScript |
| **TOTAL (excluding approval)** | **~60-90s** | Full automated flow |

### Resource Usage

| Service | CPU | Memory | Disk |
|---------|-----|--------|------|
| PostgreSQL | 5-10% | 200-300MB | 1-2GB |
| n8n | 10-20% | 300-500MB | 500MB |
| Playwright | 20-40% | 400-600MB | 1GB |
| Redis | 1-5% | 50-100MB | 100MB |
| pgAdmin | 1-5% | 100-200MB | 200MB |
| **TOTAL** | **40-80%** | **~1.5-2GB** | **~3-4GB** |

---

## ✅ Success Checklist

After completing all tests, verify:

- [ ] All services started successfully
- [ ] Database has 11 tables
- [ ] Component scraper API responds
- [ ] Cache hit rate > 90% on second search
- [ ] Workflow imports without errors
- [ ] Improved prompts integrated
- [ ] Claude API credentials configured
- [ ] Workflow activated (green toggle)
- [ ] Test case 1 (Motor Controller) succeeds
- [ ] Block diagram shows 20+ blocks
- [ ] Component search finds parts
- [ ] BOM generates with 50+ components
- [ ] Total execution time ~6 minutes
- [ ] No errors in service logs
- [ ] Database stores project data

---

## 📁 Test Artifacts

After successful testing, you'll have:

**In n8n:**
- Imported workflow (active)
- Execution history (visible in Executions tab)
- Test project data

**In PostgreSQL:**
- Cached components (component_cache table)
- Project records (projects table)
- Block diagrams (block_diagrams table)
- BOM items (bom_items table)

**In Docker:**
- 5 running containers
- Persistent volumes with data

---

## 🔄 Reset and Retry

If you need to start fresh:

```bash
# Stop all services
docker compose down

# Remove volumes (WARNING: deletes all data)
docker compose down -v

# Remove all images
docker compose down --rmi all

# Start fresh
docker compose up -d

# Re-run tests
./test_phase1_workflow.sh
```

---

## 📝 Test Report Template

After testing, document your results:

```
PHASE 1 TEST REPORT
===================

Date: [YYYY-MM-DD]
Tester: [Your Name]
Environment: [OS, Docker version]

PRE-FLIGHT CHECK:
✅ / ❌ Docker installed and running
✅ / ❌ CLAUDE_API_KEY configured
✅ / ❌ All files present
✅ / ❌ Ports available

SERVICE STARTUP:
✅ / ❌ PostgreSQL (5432)
✅ / ❌ n8n (5678)
✅ / ❌ Playwright API (8000)
✅ / ❌ Redis (6379)
✅ / ❌ pgAdmin (5050)

DATABASE:
✅ / ❌ 11 tables created
✅ / ❌ Can connect from Python
✅ / ❌ Data persistence working

WORKFLOW:
✅ / ❌ JSON imports successfully
✅ / ❌ Improved prompts integrated
✅ / ❌ Claude API connected
✅ / ❌ Workflow activated

TEST EXECUTION:
✅ / ❌ Motor Controller test passed
✅ / ❌ Block diagram: [X] blocks
✅ / ❌ Components found: [X]
✅ / ❌ BOM generated
✅ / ❌ Execution time: [X] minutes

ISSUES FOUND:
[List any issues]

OVERALL RESULT: ✅ PASS / ❌ FAIL

NOTES:
[Any additional notes]
```

---

## 🚀 Next Steps After Phase 1 Testing

Once Phase 1 is validated:

1. **Document Results:** Fill out test report
2. **Save Artifacts:** Export successful workflow execution
3. **Backup Database:** Create PostgreSQL dump
4. **Prepare Phase 2:** Review Phase 2 requirements (HRS generation)
5. **Optimize:** Fine-tune based on performance observations

---

## 📞 Support

If you encounter issues:

- **Check logs:** `docker compose logs [service_name]`
- **Review troubleshooting:** See section above
- **GitHub Issues:** https://github.com/bala9066/S2S/issues
- **Documentation:** See other .md files in repository

---

**Document Version:** 1.0
**Last Updated:** February 4, 2026
**Test Scripts:** test_phase1_preflight.sh, test_phase1_workflow.sh
**Repository:** github.com/bala9066/S2S
**Branch:** claude/start-implementation-Y5bqL
