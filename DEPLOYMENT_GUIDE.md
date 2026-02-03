# Hardware Pipeline Phase 1 - Complete Deployment Guide
## Docker Compose + PostgreSQL + Playwright + n8n

---

## 📋 Prerequisites

### System Requirements

```
Operating System: Linux (Ubuntu 22.04+), macOS, Windows 10/11 with WSL2
RAM: Minimum 8GB (16GB recommended)
Disk Space: 10GB free space
CPU: 4 cores recommended
Docker: 20.10+ with Docker Compose v2
Python: 3.10+ (for local testing)
```

### Software Installation

**Ubuntu/Debian:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

**macOS:**
```bash
# Install Docker Desktop from:
# https://docs.docker.com/desktop/install/mac-install/

# Or via Homebrew:
brew install --cask docker
```

**Windows (WSL2):**
```bash
# Install Docker Desktop for Windows from:
# https://docs.docker.com/desktop/install/windows-install/

# Enable WSL2 integration in Docker Desktop settings
```

---

## 🚀 STEP 1: Download Project Files

### File Structure

```
hardware-pipeline/
├── docker-compose.yml              # Main Docker Compose configuration
├── init-db.sql                     # PostgreSQL schema initialization
├── .env                            # Environment variables (create from .env.example)
├── component_scraper.py            # Playwright scraping script
├── Phase1_Complete_Workflow_READY_TO_IMPORT.json  # n8n workflow
├── Phase1_Workflow_Usage_Guide.md  # Usage documentation
└── playwright_scripts/             # Directory for playwright scripts
    └── component_scraper.py        # (copy from root)
```

### Create Project Directory

```bash
# Create project directory
mkdir -p hardware-pipeline
cd hardware-pipeline

# Create subdirectories
mkdir -p workflows outputs component_cache playwright_scripts

# Copy downloaded files
cp ~/Downloads/docker-compose.yml .
cp ~/Downloads/init-db.sql .
cp ~/Downloads/.env.example .env
cp ~/Downloads/component_scraper.py .
cp ~/Downloads/component_scraper.py playwright_scripts/
cp ~/Downloads/Phase1_Complete_Workflow_READY_TO_IMPORT.json workflows/
```

---

## 🔧 STEP 2: Configure Environment Variables

### Edit .env File

```bash
nano .env  # or vim, or any text editor
```

### Required Configuration

```bash
# REQUIRED: Add your Claude API key
CLAUDE_API_KEY=sk-ant-api03-YOUR-ACTUAL-KEY-HERE

# REQUIRED: Set strong passwords
POSTGRES_PASSWORD=your-secure-password-here
N8N_PASSWORD=your-n8n-password-here

# OPTIONAL: Add other AI providers
GLM_API_KEY=your-glm-key-here
GROQ_API_KEY=your-groq-key-here
```

### Get Claude API Key

```bash
1. Go to: https://console.anthropic.com/settings/keys
2. Log in or create account
3. Click "Create Key"
4. Name: "Hardware Pipeline n8n"
5. Copy the key (starts with sk-ant-api03-...)
6. Paste into .env file
```

---

## 🐳 STEP 3: Deploy with Docker Compose

### Start All Services

```bash
# From hardware-pipeline directory
docker compose up -d

# Expected output:
# ✔ Container hardware_pipeline_postgres    Started
# ✔ Container hardware_pipeline_redis       Started
# ✔ Container hardware_pipeline_playwright  Started
# ✔ Container hardware_pipeline_n8n         Started
# ✔ Container hardware_pipeline_pgadmin     Started
```

### Verify Services Are Running

```bash
docker compose ps

# Expected output:
# NAME                              STATUS    PORTS
# hardware_pipeline_postgres        Up        0.0.0.0:5432->5432/tcp
# hardware_pipeline_n8n             Up        0.0.0.0:5678->5678/tcp
# hardware_pipeline_playwright      Up
# hardware_pipeline_redis           Up        0.0.0.0:6379->6379/tcp
# hardware_pipeline_pgadmin         Up        0.0.0.0:5050->80/tcp
```

### Check Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f n8n
docker compose logs -f postgres

# Last 50 lines
docker compose logs --tail=50 n8n
```

---

## ✅ STEP 4: Verify PostgreSQL Database

### Option A: Using Docker Exec

```bash
docker exec -it hardware_pipeline_postgres psql -U postgres -d hardware_pipeline

# Inside PostgreSQL shell:
# List tables
\dt

# Should show:
# component_cache
# projects
# phase_outputs
# compliance_records
# api_usage
# component_recommendations
# block_diagrams
# bom_items
# scraping_queue
# system_logs

# View table structure
\d component_cache

# Exit
\q
```

### Option B: Using pgAdmin

```bash
1. Open browser: http://localhost:5050
2. Login:
   - Email: admin@hardwarepipeline.com
   - Password: admin123 (or value from .env)
3. Click "Add New Server"
4. Connection settings:
   - Name: Hardware Pipeline
   - Host: postgres
   - Port: 5432
   - Database: hardware_pipeline
   - Username: postgres
   - Password: (value from .env)
5. Click "Save"
6. Browse: Servers → Hardware Pipeline → Databases → hardware_pipeline → Schemas → public → Tables
```

### Test Database Connection from Command Line

```bash
# Install psql client (if not already installed)
# Ubuntu/Debian:
sudo apt-get install postgresql-client

# macOS:
brew install postgresql

# Test connection
psql -h localhost -p 5432 -U postgres -d hardware_pipeline

# Run test query
SELECT COUNT(*) FROM component_cache;
```

---

## 🔌 STEP 5: Access n8n and Import Workflow

### Open n8n Web Interface

```bash
1. Open browser: http://localhost:5678
2. Login:
   - Username: admin
   - Password: admin123 (or value from .env)
```

### Import Phase 1 Workflow

```bash
# Method 1: Via n8n UI
1. Click "Workflows" in left sidebar
2. Click "+ Add workflow"
3. Click the three dots (⋮) → "Import from File"
4. Select: Phase1_Complete_Workflow_READY_TO_IMPORT.json
5. Click "Import"
6. Workflow opens automatically

# Method 2: Via File System (Already copied)
# If you copied to workflows/ directory, it should auto-appear in n8n
```

### Configure Claude API Credentials in n8n

```bash
1. In n8n, click "Settings" (gear icon) → "Credentials"
2. Click "+ Add Credential"
3. Search for "Claude" or scroll to "Anthropic"
4. Select "Anthropic API"
5. Fill in:
   - Credential Name: Claude_API
   - API Key: (paste your Claude API key)
6. Click "Test connection" → Should show ✅
7. Click "Save"
```

### Activate Workflow

```bash
1. Open the imported workflow
2. Toggle "Active" switch in top-right (should turn green)
3. Workflow is now live and ready to receive chat input
```

---

## 🧪 STEP 6: Install Playwright Dependencies

### Enter Playwright Container

```bash
docker exec -it hardware_pipeline_playwright bash
```

### Install Python Dependencies

```bash
# Inside container
pip install playwright psycopg2-binary

# Install Playwright browsers
playwright install chromium

# Verify installation
python3 --version
playwright --version
```

### Test Component Scraper

```bash
# Still inside container
cd /app

# Test scraping (uses mock data if websites unreachable)
python3 component_scraper.py "STM32F4" "processor"

# Expected output:
# {
#   "cache_hit": false,
#   "components": [...],
#   "total_found": 5,
#   "sources": {
#     "digikey": 3,
#     "mouser": 2
#   }
# }

# Exit container
exit
```

---

## 🎯 STEP 7: Test Complete Phase 1 Workflow

### Test Case 1: Motor Controller

```bash
1. Open n8n: http://localhost:5678
2. Open Phase 1 workflow
3. Click "Test workflow" button (play icon)
4. In chat interface, type:

Design a 3-phase motor controller with TMS320F28379D DSP, 10kW output power, 48V DC input, 0-400Hz output frequency, Ethernet interface for monitoring, current sensing with hall sensors, and temperature protection with NTC thermistors.

5. Wait for response (15-20 seconds)
6. Review generated block diagram
7. Type: APPROVE
8. Wait for component search and BOM (30-60 seconds)
9. Review final BOM
```

### Expected Results

```
Step 1: Requirements Received
✅ System Type Detected: Motor_Control

Step 2: Block Diagram Generated
✅ 12 blocks created
✅ 11 connections established

Step 3: User Approval
⏸️ Waiting for "APPROVE" command

Step 4: Component Search
✅ Processor: 5 options found
✅ Power Regulators: 8 options found
✅ Gate Driver: 3 options found
✅ Power MOSFETs: 5 options found

Step 5: BOM Generated
✅ Total Components: 24
✅ Estimated Cost: $384.75
✅ Phase 1 Complete
```

### Test Case 2: RF System

```
Chat Input:
Design RF system with Xilinx Artix-7 XC7A100T FPGA, 5-18GHz frequency range, 40dBm output power, return loss > 10dB, GaN power amplifier, buck-boost converters for 1.0V/1.8V/3.3V/28V rails, SPI interface to PA.

Expected System Type: RF_Wireless
Expected Blocks: FPGA, Power Regulators, RF PA, Antenna, Matching Networks
```

### Test Case 3: Digital Controller

```
Chat Input:
Design digital controller with Zynq UltraScale+ ZU3EG MPSoC, 2GB DDR4 memory, Gigabit Ethernet PHY, USB 3.0, PCIe Gen3 x4, SPI flash, QSPI boot, operating temperature -40 to 85°C.

Expected System Type: Digital_Controller
Expected Blocks: Zynq, DDR4, Ethernet PHY, USB Controller, Flash
```

---

## 📊 STEP 8: Monitor System Health

### Check All Container Status

```bash
docker compose ps
docker compose stats

# Expected: All containers "Up" and healthy
```

### Monitor Logs in Real-Time

```bash
# n8n workflow execution
docker compose logs -f n8n | grep "Phase 1"

# PostgreSQL queries
docker compose logs -f postgres | grep "SELECT"

# Playwright scraping
docker compose logs -f playwright
```

### Check Database Activity

```bash
# Active connections
docker exec hardware_pipeline_postgres psql -U postgres -d hardware_pipeline -c "SELECT count(*) FROM pg_stat_activity;"

# Recent projects
docker exec hardware_pipeline_postgres psql -U postgres -d hardware_pipeline -c "SELECT id, project_name, system_type, status, phase_completed FROM projects ORDER BY created_at DESC LIMIT 5;"

# Component cache statistics
docker exec hardware_pipeline_postgres psql -U postgres -d hardware_pipeline -c "SELECT * FROM component_cache_stats;"
```

---

## 🔧 STEP 9: Troubleshooting

### Issue 1: n8n Not Starting

**Symptoms:**
```
Error: Cannot connect to database
```

**Solution:**
```bash
# Check if PostgreSQL is ready
docker compose logs postgres | grep "ready to accept connections"

# Restart n8n
docker compose restart n8n

# Wait 30 seconds, then check
docker compose logs n8n
```

### Issue 2: Playwright Scraping Fails

**Symptoms:**
```
Error: Browser not found
```

**Solution:**
```bash
# Enter playwright container
docker exec -it hardware_pipeline_playwright bash

# Reinstall browsers
playwright install chromium

# Test manually
python3 /app/component_scraper.py "test" "processor"

exit
```

### Issue 3: "Cache Miss" Every Time

**Symptoms:**
```
[CACHE MISS] No cached components
```

**Explanation:**  
This is NORMAL on first run. Components are cached after first scrape.

**Verify:**
```bash
# Check cache table
docker exec hardware_pipeline_postgres psql -U postgres -d hardware_pipeline -c "SELECT COUNT(*) FROM component_cache;"

# Should increase after each scrape
```

### Issue 4: Claude API Key Invalid

**Symptoms:**
```
401 Unauthorized: Invalid API Key
```

**Solution:**
```bash
# Verify API key in .env
cat .env | grep CLAUDE_API_KEY

# Verify n8n credential
# Open n8n → Settings → Credentials → Claude_API
# Click "Test connection"

# If failed, get new key from:
# https://console.anthropic.com/settings/keys
```

### Issue 5: Out of Memory

**Symptoms:**
```
docker compose logs shows "Killed"
```

**Solution:**
```bash
# Check Docker memory limit
docker info | grep Memory

# Increase Docker memory limit
# Docker Desktop → Settings → Resources → Memory → 8GB

# Or edit docker-compose.yml and add:
services:
  n8n:
    deploy:
      resources:
        limits:
          memory: 2G
```

---

## 📈 STEP 10: Performance Optimization

### PostgreSQL Tuning

```bash
# Edit PostgreSQL config (optional)
docker exec hardware_pipeline_postgres bash -c "cat >> /var/lib/postgresql/data/postgresql.conf" << EOF
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
max_connections = 50
EOF

# Restart PostgreSQL
docker compose restart postgres
```

### Component Cache Cleanup

```bash
# Run cache cleanup function
docker exec hardware_pipeline_postgres psql -U postgres -d hardware_pipeline -c "SELECT clean_expired_cache();"

# Schedule via cron (on host machine)
echo "0 2 * * * docker exec hardware_pipeline_postgres psql -U postgres -d hardware_pipeline -c 'SELECT clean_expired_cache();'" | crontab -
```

### Optimize n8n Executions

```bash
# Edit docker-compose.yml
# Add to n8n environment:
EXECUTIONS_DATA_PRUNE: "true"
EXECUTIONS_DATA_MAX_AGE: 168  # Keep 7 days

# Restart
docker compose up -d n8n
```

---

## 🛑 STEP 11: Stopping and Cleanup

### Stop All Services

```bash
# Stop containers (keep data)
docker compose stop

# Start again later
docker compose start
```

### Complete Cleanup

```bash
# Stop and remove containers (keep volumes)
docker compose down

# Remove everything including volumes (⚠️ DELETES ALL DATA)
docker compose down -v

# Remove images
docker compose down --rmi all
```

### Backup Database

```bash
# Create backup
docker exec hardware_pipeline_postgres pg_dump -U postgres hardware_pipeline > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
cat backup_20260202_120000.sql | docker exec -i hardware_pipeline_postgres psql -U postgres hardware_pipeline
```

---

## 📦 STEP 12: Update and Maintenance

### Update Docker Images

```bash
# Pull latest images
docker compose pull

# Recreate containers with new images
docker compose up -d --force-recreate
```

### Update n8n Workflow

```bash
# Export current workflow from n8n UI
# Import new version via UI
# Or replace JSON file in workflows/ directory
```

### Database Migration (if schema changes)

```bash
# Create migration SQL file
nano migration_v2.sql

# Run migration
cat migration_v2.sql | docker exec -i hardware_pipeline_postgres psql -U postgres hardware_pipeline
```

---

## 📞 Support and Next Steps

### Verify Complete Setup

**Checklist:**
- [ ] Docker Compose running
- [ ] PostgreSQL database initialized (11 tables)
- [ ] n8n accessible at http://localhost:5678
- [ ] Claude API credentials configured
- [ ] Phase 1 workflow imported and active
- [ ] Playwright scraper tested
- [ ] Test workflow completed successfully

### Next Steps

1. **Test all 6 system types:**
   - RF/Wireless ✓
   - Motor Control ✓
   - Digital Controller ✓
   - Power Electronics
   - Industrial Control
   - Sensor System

2. **Replace mock scraper with real Playwright:**
   - Update workflow node "Search Components (Mock)"
   - Replace with call to component_scraper.py

3. **Implement Phases 2-8:**
   - Phase 2: HRS Document Generation
   - Phase 3: Compliance Validation
   - Phase 4: Netlist Generation
   - Phase 5: PCB Design Helper
   - Phase 6: GLR Generation
   - Phase 7: FPGA Helper
   - Phase 8: Software Generation + AntiGravity

### Useful Commands Reference

```bash
# View all containers
docker compose ps

# View logs
docker compose logs -f [service_name]

# Restart service
docker compose restart [service_name]

# Execute command in container
docker exec -it [container_name] [command]

# Check resource usage
docker compose stats

# Backup volumes
docker run --rm -v hardware_pipeline_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

---

## 🎉 DEPLOYMENT COMPLETE!

Your Hardware Pipeline Phase 1 is now fully deployed and operational!

**Access Points:**
- n8n Workflow: http://localhost:5678
- pgAdmin: http://localhost:5050
- PostgreSQL: localhost:5432
- Redis: localhost:6379

**Credentials:**
- n8n: admin / (your N8N_PASSWORD)
- pgAdmin: admin@hardwarepipeline.com / (your PGADMIN_PASSWORD)
- PostgreSQL: postgres / (your POSTGRES_PASSWORD)

Start designing hardware! 🚀
