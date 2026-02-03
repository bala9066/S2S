# 🚀 Hardware Pipeline - Complete Quick Start Guide

**Everything You Need in ONE File!**

**Project**: DATA PATTERNS GREAT AI HACK-A-THON 2026
**Team**: S2S (Specification to Silicon)
**Goal**: Automate hardware design from requirements to production-ready files

---

## ⚡ QUICK START (10 Minutes)

### Prerequisites Checklist
- [ ] Docker Desktop installed ([Download here](https://www.docker.com/products/docker-desktop))
- [ ] Claude API key ([Get here](https://console.anthropic.com/))
- [ ] At least 8GB RAM available
- [ ] Internet connection active

### Step 1: Clone Repository (1 min)
```bash
git clone https://github.com/bala9066/S2S.git
cd S2S
```

### Step 2: Configure API Keys (2 min)
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file and add your API keys
nano .env   # or use any text editor
```

**Required API Keys:**
```bash
# Claude API (REQUIRED)
CLAUDE_API_KEY=sk-ant-your-key-here

# Optional (for enhanced features)
GLM_API_KEY=your-glm-key
GROQ_API_KEY=your-groq-key
DIGIKEY_API_KEY=your-digikey-key
MOUSER_API_KEY=your-mouser-key
```

### Step 3: Start Docker Containers (3 min)
```bash
# Start all services
docker-compose up -d

# Verify containers are running
docker-compose ps
```

You should see:
- ✅ **n8n** - Workflow orchestrator (port 5678)
- ✅ **postgres** - Database (port 5432)
- ✅ **redis** - Cache (port 6379)
- ✅ **scraper-api** - Component scraper (port 8000)

### Step 4: Access n8n Interface (1 min)
Open your browser:
```
http://localhost:5678
```

**Login Credentials:**
- Username: `admin`
- Password: `admin123`

### Step 5: Import Workflow (3 min)
1. In n8n UI: Click **Workflows** → **Import from File**
2. Choose workflow file:
   - **Original Workflow**: `AI_Hardware_Pipeline_Workflow.json` (17 nodes)
   - **Enhanced Workflow**: `Phase1_Enhanced_With_GLB_PowerBudget.json` (25 nodes)
3. Click **Import**
4. Configure Claude API credential:
   - Click any **Claude** node
   - Add credential → Paste your API key
   - Save
5. Toggle **Activate** to ON

### Step 6: Test the System (Optional)
```bash
# Test component scraper
python3 test_component_search.py

# Test full pipeline with example
curl -X POST http://localhost:5678/webhook/ai-hardware-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "Design IoT sensor with ESP32, DHT22 temperature sensor, battery powered, WiFi enabled"
  }'
```

**✅ DONE! You're ready to design hardware!**

---

## 📋 File Structure Explained

### 🔴 MUST USE FILES

| File | What It Does |
|------|--------------|
| **`.env`** | API keys configuration - EDIT THIS FIRST |
| **`docker-compose.yml`** | Orchestrates all services (n8n, PostgreSQL, Redis, Scraper API) |
| **`AI_Hardware_Pipeline_Workflow.json`** | Original 8-phase workflow (17 nodes) |
| **`Phase1_Enhanced_With_GLB_PowerBudget.json`** | Enhanced Phase 1 with GLB + Power Budget (25 nodes) |

### 📖 DOCUMENTATION

| File | Purpose |
|------|---------|
| **`START_HERE.md`** | THIS FILE - Quick start guide |
| **`REPOSITORY_ANALYSIS.md`** | Complete technical analysis (948 lines) |
| **`ENHANCED_WORKFLOW_GUIDE.md`** | Enhanced workflow node-by-node guide |
| **`WORKFLOW_COMPARISON.md`** | Original vs Enhanced comparison |
| **`N8N_IMPORT_GUIDE.md`** | Workflow import instructions |
| **`README.md`** | Project overview |
| **`Hackathon_Registration_Final.md`** | Problem statement & ROI analysis |

### ⚙️ CORE FILES

| File | Purpose |
|------|---------|
| **`component_scraper.py`** | Scrapes DigiKey, Mouser, LCSC (Playwright) |
| **`scraper_api.py`** | FastAPI wrapper for component scraper |
| **`run_pipeline.py`** | Pipeline orchestrator (calls n8n workflow) |
| **`init-db.sql`** | PostgreSQL schema (10 tables, 30-day cache) |

### 🧪 TEST FILES

| File | Purpose |
|------|---------|
| **`test_component_search.py`** | Tests all 3 suppliers (DigiKey, Mouser, LCSC) |

### 📁 DIRECTORIES

| Folder | Contents |
|--------|----------|
| **`workflows/`** | Additional workflow JSON files |
| **`output/`** | Generated design files (BOM, HRS, netlists, etc.) |

---

## 🎯 What This System Does

**Input:** Hardware design requirements (plain English)

**Example Input:**
```
Design RF transmitter with Xilinx Artix-7 FPGA (XC7A100T-2CSG324C),
GaN power amplifier with 40dBm output power, 5-18GHz frequency range,
buck-boost converters for 1.0V/1.8V/3.3V/28V rails, return loss > 10dB,
SPI/I2C interfaces, RoHS compliant
```

**Output (in ~4 minutes):**
- ✅ **Block Diagram** (PNG/draw.io format)
- ✅ **Component BOM** with DigiKey/Mouser/LCSC pricing (~$850 for RF system)
- ✅ **70-page Hardware Requirements Specification (HRS.docx)**
- ✅ **Compliance Report** (RoHS/REACH/FCC/CE/ITAR)
- ✅ **PCB Netlist** (EDIF + Excel)
- ✅ **Power Budget** (thermal analysis, efficiency)
- ✅ **GLB/Link Budget** (for RF systems)
- ✅ **Gate-Level Requirements (GLR)** (for FPGA systems)
- ✅ **Software Requirements (SRS.docx)** (40 pages)
- ✅ **Software Design (SDD.docx)** (50 pages)
- ✅ **Complete C/C++/Qt code** with unit tests

**Total:** 35+ professional files ready for production!

---

## 🏗️ The 8-Phase Workflow

| Phase | Description | Time | Manual? | Output Files |
|-------|-------------|------|---------|--------------|
| **1** | **Requirements & Component Selection** | 90s | ❌ Auto | Block diagram (PNG), BOM.xlsx, Power Budget |
|       | - Claude parses requirements | | | GLB (RF only) |
|       | - Generates block diagram (approval gate) | | | |
|       | - Searches DigiKey/Mouser/LCSC | | | |
|       | - Calculates power budget (all systems) | | | |
|       | - Calculates GLB (RF systems only) | | | |
| **2** | **HRS Document Generation** | 30s | ❌ Auto | HRS.docx (70 pages) |
|       | - Hardware Requirements Specification | | | |
|       | - Interface definitions, timing diagrams | | | |
| **3** | **Design Constraints & Compliance** | 30s | ❌ Auto | Compliance_Report.pdf |
|       | - RoHS/REACH/FCC/CE/ITAR checks | | | design_constraints.json |
|       | - PCB layout rules | | | |
| **4** | **Netlist Generation** | 40s | ❌ Auto | netlist.edif, netlist.xlsx |
|       | - EDIF for PCB tools (Xpedition/Altium) | | | |
|       | - Excel for human review | | | |
| **5** | **PCB Design (Manual)** | 8-20h | ✅ Manual | Gerber files |
|       | - User designs PCB in their tool | | | Manufacturing files |
|       | - Imports netlist.edif | | | |
| **6** | **GLR Generation** | 40s | ❌ Auto | GLR.xlsx |
|       | - Gate-Level Requirements for FPGA I/O | | | (FPGA pin assignments) |
| **7** | **FPGA Implementation (Optional)** | Hours | ✅ Manual | RDT.xlsx, PSQ.xlsx |
|       | - FPGA team implements logic | | | HDL files |
|       | - Register Description Table (RDT) | | | Bitstream |
|       | - Programming Sequence (PSQ) | | | |
| **8** | **Software Development** | 60s | ❌ Auto | SRS.docx, SDD.docx |
|       | - Generates SRS based on RDT/PSQ/HRS | | | C/C++/Qt code |
|       | - Generates SDD | | | Unit tests |
|       | - Generates complete C/C++/Qt code | | | |

**Automated Time:** ~4 minutes
**Manual Time:** 10-30 hours (PCB + FPGA design)

### Approval Gates (Human-in-the-Loop)

| Gate | When | What to Approve |
|------|------|-----------------|
| **1. Block Diagram** | After Phase 1 | Review block diagram (PNG/draw.io) before component selection |
| **2. Compliance** | After Phase 3 | Approve compliance strategy (RoHS/FCC/CE/ITAR) |
| **3. MR Review** | Before git push | Review all changes before committing to git |

---

## 🆕 Enhanced Workflow Features

The **Enhanced Workflow** (Phase1_Enhanced_With_GLB_PowerBudget.json) adds:

### 1. Power Budget (Universal - ALL Systems)
- Power consumption per rail (1.0V, 1.8V, 3.3V, 28V, etc.)
- Efficiency calculations
- Thermal analysis (junction temperature, power dissipation)
- Regulator selection recommendations

**Output:** `Power_Budget.xlsx`

### 2. GLB/Link Budget (RF Systems Only)
- **TX Chain:** PA output power, cable losses, antenna gain, EIRP
- **RX Chain:** Antenna gain, LNA noise figure, cable losses, sensitivity
- **Link Budget:** Free space path loss, margin calculations

**Output:** `RF_LinkBudget.xlsx`

**Automatic RF Detection:**
- Keywords: FPGA, GaN, power amplifier, RF, transmitter, receiver, antenna, dBm
- If detected: Generates GLB + Power Budget
- If not detected: Power Budget only

---

## 🔧 Component Scraper Features

### Supported Suppliers (3 sources)
1. **DigiKey** - US distributor, wide selection
2. **Mouser** - US distributor, competitive pricing
3. **LCSC** - Chinese distributor, 30-50% cheaper

### API Endpoints

#### 1. Single Component Search
```bash
POST http://localhost:8000/api/scrape
{
  "search_term": "STM32F4",
  "category": "processor",
  "use_cache": true
}
```

#### 2. Multi-Component Search (NEW - Perfect Listing)
```bash
POST http://localhost:8000/api/scrape/all
{
  "components": [
    {"search_term": "STM32F4", "category": "processor"},
    {"search_term": "buck converter 3.3V", "category": "power_regulator"},
    {"search_term": "SPI ADC 16-bit", "category": "interface"}
  ],
  "use_cache": true
}
```

**Benefits:**
- Searches all 3 suppliers in parallel
- Perfect component listing (no missing parts)
- 30-day PostgreSQL cache
- Automatic price comparison

#### 3. Cache Status
```bash
GET http://localhost:8000/api/cache/status
```

#### 4. Health Check
```bash
GET http://localhost:8000/api/health
```

### Cache Strategy
- **Duration:** 30 days
- **Database:** PostgreSQL (component_cache table)
- **Expiry:** Automatic cleanup of expired entries
- **Bypass:** Set `use_cache: false` to force fresh scrape

---

## 📊 Expected Outputs

### Documents (4 files)
- **HRS.docx** (70 pages) - Hardware Requirements Specification
  - System architecture, block diagrams, interface definitions
  - Electrical specifications, timing diagrams
  - Power requirements, thermal requirements
- **SRS.docx** (40 pages) - Software Requirements Specification
  - Functional requirements, API definitions
  - Based on RDT, PSQ, HRS
- **SDD.docx** (50 pages) - Software Design Document
  - Architecture, class diagrams, sequence diagrams
- **Compliance_Report.pdf** - RoHS/REACH/FCC/CE/ITAR compliance

### Spreadsheets (7+ files)
- **BOM.xlsx** - Bill of Materials
  - Part numbers, manufacturers, descriptions
  - DigiKey/Mouser/LCSC pricing (lowest price highlighted)
  - Stock availability, datasheets
- **Power_Budget.xlsx** - Power consumption analysis
  - Per-rail power (1.0V, 1.8V, 3.3V, 28V, etc.)
  - Efficiency, thermal analysis
  - Regulator recommendations
- **RF_LinkBudget.xlsx** - RF link budget (RF systems only)
  - TX chain: PA power, cable loss, antenna gain, EIRP
  - RX chain: Antenna gain, LNA NF, cable loss, sensitivity
  - Link budget: FSPL, margin
- **netlist.xlsx** - Human-readable netlist
  - Net names, connected pins
- **GLR.xlsx** - Gate-Level Requirements (FPGA systems)
  - FPGA I/O pin assignments
  - Voltage levels, drive strength
- **RDT.xlsx** - Register Description Table (FPGA implementation)
  - Created by FPGA team during Phase 7
- **PSQ.xlsx** - Programming Sequence (FPGA implementation)
  - Created by FPGA team during Phase 7

### Design Files (3+ files)
- **block_diagram.png** - System architecture (PNG format)
- **block_diagram.drawio** - Editable diagram (draw.io format)
- **netlist.edif** - For PCB tool import (Xpedition/Altium/KiCad)
- **design_constraints.json** - PCB layout rules

### Code Files (10+ files)
- **driver.c/h** - C driver implementation
- **Driver.cpp/hpp** - C++ driver implementation
- **ControlApp/** - Qt GUI application
- **test_driver.c** - Unit tests
- Qt library files

---

## 💡 Example Inputs

### 1. Simple IoT Device
```
Design IoT temperature sensor with ESP32, DHT22 sensor,
battery powered (Li-Ion 3.7V), WiFi enabled, MQTT protocol,
low power sleep mode
```

**Expected Output:**
- BOM: ~$50 (ESP32-WROOM-32, DHT22, battery management IC, voltage regulator)
- Power Budget: Active mode 160mA, sleep mode 10μA
- No GLB (not RF system)

### 2. RF Transmitter System
```
Design RF transmitter with Xilinx Artix-7 FPGA (XC7A100T-2CSG324C),
GaN power amplifier with 40dBm output power, 5-18GHz frequency range,
buck-boost converters for 1.0V/1.8V/3.3V/28V rails, return loss > 10dB,
SPI/I2C interfaces, RoHS compliant
```

**Expected Output:**
- BOM: ~$850 (FPGA $120, GaN PA $350, power supplies $200, passives $180)
- Power Budget: 1.0V@10A, 1.8V@2A, 3.3V@1A, 28V@5A (total ~160W)
- GLB: TX chain analysis, 40dBm EIRP, link budget
- GLR: FPGA I/O assignments (SPI, I2C, control signals)

### 3. Industrial Controller
```
Design industrial PLC with ARM Cortex-M7 (STM32H7),
24V industrial power supply, RS-485 Modbus,
8 digital inputs (24V), 4 relay outputs (250VAC/5A),
isolated I/O, EMC compliant
```

**Expected Output:**
- BOM: ~$200 (STM32H7 $15, isolated I/O $80, relays $40, power supply $50)
- Power Budget: 24V input, 3.3V@500mA, 5V@200mA for I/O
- No GLB (not RF system)
- Compliance: CE, RoHS, industrial EMC

---

## 🐛 Troubleshooting

### Docker Won't Start
```bash
# Check Docker Desktop is running
docker --version

# Check container logs
docker-compose logs -f n8n

# Restart containers
docker-compose restart

# Full restart
docker-compose down
docker-compose up -d
```

### Can't Access n8n
- **URL:** http://localhost:5678
- **Login:** admin / admin123
- **Port conflict?** Edit `docker-compose.yml` and change port:
  ```yaml
  ports:
    - "8080:5678"  # Change to 8080 or any free port
  ```

### API Errors
- **Claude API:** Verify key in `.env` file starts with `sk-ant-`
- **Check credits:** https://console.anthropic.com/
- **Rate limit:** Wait 60 seconds and retry

### Component Scraper Issues
```bash
# Test scraper directly
python3 test_component_search.py

# Check scraper API health
curl http://localhost:8000/api/health

# Check logs
docker-compose logs -f scraper-api
```

### Database Issues
```bash
# Connect to PostgreSQL
docker exec -it S2S-postgres psql -U postgres -d hardware_pipeline

# Check component cache
SELECT COUNT(*) FROM component_cache;
SELECT source, COUNT(*) FROM component_cache GROUP BY source;

# Clear expired cache
curl -X POST http://localhost:8000/api/cache/clear
```

### Workflow Errors
1. **"Claude API Error"** - Check API key in n8n credentials
2. **"Timeout"** - Increase timeout in node settings (60s → 120s)
3. **"Out of tokens"** - Reduce maxTokens parameter or upgrade Claude plan
4. **"Component search failed"** - Check scraper-api is running: `docker-compose ps`

---

## 💰 Cost Estimates

### API Costs (per workflow run)
- **Claude Sonnet 4.5:** ~$1.50 per complete workflow
  - Phase 1: $0.30 (requirements parsing, component recommendation, GLB, power budget)
  - Phase 2: $0.40 (HRS generation)
  - Phase 3: $0.20 (compliance)
  - Phase 4: $0.15 (netlist)
  - Phase 6: $0.15 (GLR)
  - Phase 8: $0.30 (software generation)

### Component Costs (examples)
- **Simple IoT:** ~$50 (ESP32, sensors, power)
- **RF System:** ~$850 (FPGA $120, GaN PA $350, power $200, passives $180)
- **Industrial PLC:** ~$200-$400 (MCU, isolated I/O, relays, power)

### PCB Costs
- **2-layer (IoT):** $50-$100 (fabrication) + $100-$200 (assembly)
- **4-layer (Industrial):** $150-$300 (fabrication) + $200-$400 (assembly)
- **6-layer (RF):** $200-$500 (fabrication) + $300-$800 (assembly)

### Certification Costs (optional)
- **FCC Part 15:** ~$15,000
- **CE RED:** ~$20,000
- **RoHS/REACH:** ~$5,000
- **Military (MIL-STD):** $50,000+

---

## 🔒 Security

### Production Deployment

1. **Change default passwords** in `docker-compose.yml`:
```yaml
environment:
  - N8N_BASIC_AUTH_USER=your_secure_username
  - N8N_BASIC_AUTH_PASSWORD=your_secure_password
  - POSTGRES_PASSWORD=your_secure_db_password
```

2. **Use HTTPS** with reverse proxy (nginx/Traefik)

3. **Restrict network access**:
```yaml
# Only expose n8n, not database
ports:
  - "127.0.0.1:5678:5678"  # Only accessible from localhost
```

4. **Secure API keys**:
- Never commit `.env` to git (already in `.gitignore`)
- Use secrets manager in production (AWS Secrets Manager, HashiCorp Vault)

---

## 📚 Additional Resources

### Documentation
- [n8n Documentation](https://docs.n8n.io/)
- [Claude API Reference](https://docs.anthropic.com/)
- [Playwright Docs](https://playwright.dev/python/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)

### Supplier APIs
- [DigiKey API](https://developer.digikey.com/)
- [Mouser API](https://www.mouser.com/api-hub/)
- [LCSC](https://www.lcsc.com/)

### PCB Design Tools
- [Altium Designer](https://www.altium.com/)
- [Mentor Graphics Xpedition](https://www.mentor.com/)
- [KiCad](https://www.kicad.org/) (Free)

---

## 🎯 Your Checklist

### Initial Setup (Do Once)
- [ ] Install Docker Desktop
- [ ] Clone repository
- [ ] Get Claude API key
- [ ] Edit `.env` file with API keys
- [ ] Run `docker-compose up -d`
- [ ] Access n8n at http://localhost:5678
- [ ] Import workflow JSON
- [ ] Add Claude credential in n8n
- [ ] Activate workflow
- [ ] Test with example input

### Daily Use
- [ ] Ensure Docker is running
- [ ] Access n8n (http://localhost:5678)
- [ ] Submit requirements via webhook
- [ ] Review block diagram (Approval Gate 1)
- [ ] Review compliance report (Approval Gate 2)
- [ ] Download generated files from `output/`
- [ ] Design PCB (Phase 5 - manual)
- [ ] Implement FPGA (Phase 7 - optional, manual)

### When Done
- [ ] Review all files (MR Review - Approval Gate 3)
- [ ] Commit to git
- [ ] Stop containers: `docker-compose down`

---

## 🎉 Success Tips

### For Best Results
- **Be specific** with requirements
- **Use technical terms** (FPGA model, frequencies, power levels)
- **Mention compliance** needs upfront (RoHS, FCC, CE, ITAR)
- **Specify interfaces** (SPI, I2C, UART, Ethernet)

### Common Mistakes
- ❌ Vague requirements ("design a circuit")
- ❌ Missing critical specs (voltage, current, frequency)
- ❌ Not specifying FPGA package (CSG324, FBG484, etc.)
- ✅ Better: "Design 5V 2A buck converter, automotive grade (AEC-Q100), CISPR 25 compliant, 2MHz switching frequency"

### Iteration
- Run workflow multiple times
- Refine requirements based on output
- Typical: 3-5 iterations to perfect design

---

## 📞 Support

### Quick Help
```bash
# Check system status
docker-compose ps

# View logs
docker-compose logs -f n8n
docker-compose logs -f scraper-api

# Restart everything
docker-compose restart

# Full reset
docker-compose down -v
docker-compose up -d
```

### Documentation
- **This file** - Quick start & reference
- **REPOSITORY_ANALYSIS.md** - Complete technical analysis
- **ENHANCED_WORKFLOW_GUIDE.md** - Enhanced workflow details
- **WORKFLOW_COMPARISON.md** - Original vs Enhanced comparison

---

## 📝 Quick Command Reference

```bash
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# Restart
docker-compose restart

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f n8n
docker-compose logs -f scraper-api

# Check status
docker-compose ps

# Test scraper
python3 test_component_search.py

# Access n8n
http://localhost:5678

# API docs
http://localhost:8000/docs
```

---

## 🏆 Hackathon Success

**Problem:** 35 engineers spend 10-30 hours per design → ₹43L/year cost
**Solution:** S2S automates 90% → 4 minutes automated + 10-20 hours manual
**ROI:** 59% first year, 860% ongoing

**What You Get:**
- Automated requirements parsing
- Perfect component listing (DigiKey, Mouser, LCSC)
- Professional documentation (HRS, SRS, SDD)
- Production-ready files (BOM, netlist, code)
- Compliance reports (RoHS, FCC, CE, ITAR)

**Good luck! 🚀⚡**

---

**Last Updated:** 2026-02-03
**Version:** 2.0 - Enhanced with LCSC, search_all, Power Budget, GLB
