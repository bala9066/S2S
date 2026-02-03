# n8n Workflow Import Guide

**Workflow File:** `Phase1_Complete_Workflow_READY_TO_IMPORT.json`
**Workflow Name:** Phase_1_Requirements_Components_Universal
**Version:** 2.0
**Last Updated:** February 3, 2026

---

## Quick Import Methods

### Method 1: Automatic Import Script (Recommended)

**Prerequisites:**
- Docker services running (`docker compose up -d`)
- n8n accessible at http://localhost:5678

**Steps:**

```bash
# Start all services if not running
docker compose up -d

# Wait for services to be ready (2-3 minutes)
sleep 120

# Run the automated import script
python3 run_pipeline.py
# Select option: "2. Import workflow only"
```

**Or use the direct import script:**

```bash
python3 n8n_workflow_import.py
```

The script will:
- ✅ Check if n8n is accessible
- ✅ Authenticate automatically (using .env credentials)
- ✅ Import the workflow via API or UI automation
- ✅ Confirm successful import

---

### Method 2: Manual Import via n8n UI

**Steps:**

1. **Open n8n**
   ```
   http://localhost:5678
   ```

2. **Login**
   - Username: `admin` (from .env)
   - Password: `admin123` (from .env)

3. **Import Workflow**
   - Click **"+" (Create Workflow)** in top right
   - Click **"..." menu** → **"Import from File"**
   - Or use keyboard shortcut: **Ctrl+O** (Windows/Linux) or **Cmd+O** (Mac)

4. **Select File**
   - Navigate to: `/path/to/S2S/Phase1_Complete_Workflow_READY_TO_IMPORT.json`
   - Click **"Open"**

5. **Verify Import**
   - You should see 17 nodes arranged on canvas
   - Workflow name: **"Phase_1_Requirements_Components_Universal"**
   - Tags: hardware-pipeline, phase-1, universal

6. **Configure Credentials**
   - Click on **"OpenAI Chat Model (Parse)"** node
   - Add your API credentials:
     - For Claude API: Anthropic API key
     - For GLM: Zhipu AI key
     - For Groq: Groq API key

7. **Save Workflow**
   - Click **"Save"** button (top right)
   - Or press **Ctrl+S** / **Cmd+S**

8. **Activate Workflow**
   - Toggle **"Active"** switch to ON
   - Workflow is now ready to receive chat requests

---

### Method 3: Import via n8n API (Advanced)

**Prerequisites:**
- n8n running
- API credentials configured

**Steps:**

```bash
# Get n8n credentials from .env
N8N_USER="admin"
N8N_PASSWORD="admin123"
N8N_HOST="localhost"
N8N_PORT="5678"

# Read the workflow JSON
WORKFLOW_JSON=$(cat Phase1_Complete_Workflow_READY_TO_IMPORT.json)

# Import via API
curl -X POST "http://${N8N_HOST}:${N8N_PORT}/api/v1/workflows" \
  -H "Content-Type: application/json" \
  -u "${N8N_USER}:${N8N_PASSWORD}" \
  -d "${WORKFLOW_JSON}"
```

**Response:**
```json
{
  "id": "abc123",
  "name": "Phase_1_Requirements_Components_Universal",
  "active": false,
  "createdAt": "2026-02-03T...",
  "updatedAt": "2026-02-03T..."
}
```

---

## Workflow Structure

### 17 Nodes Included

| # | Node Name | Type | Purpose |
|---|-----------|------|---------|
| 1 | Chat Trigger | Trigger | Entry point for user input |
| 2 | Validate Input & Detect Type | Code | Input validation, system type detection |
| 3 | Is This Approval? | If | Routes to requirements or approval path |
| 4 | Build AI Prompt | Code | Constructs AI prompt for parsing |
| 5 | AI: Parse Requirements | Agent | AI extracts structured data |
| 6 | Extract Parsed Data | Code | Validates and merges AI output |
| 7 | Generate Block Diagram | Code | Creates hardware block diagram |
| 8 | Show Diagram & Wait Approval | Code | Displays diagram, requests approval |
| 9 | Handle Approval | Code | Processes user approval |
| 10 | Build Component Searches | Code | Generates search queries |
| 11 | Split Searches (3 per batch) | Split | Batches searches |
| 12 | Search Components (Real) | HTTP | Calls Playwright scraper API |
| 13 | Aggregate All Components | Aggregate | Combines all results |
| 14 | Prepare Component Recommendations | Code | Builds recommendation prompt |
| 15 | AI: Recommend Components | Agent | AI selects best components |
| 16 | Generate BOM | Code | Creates Bill of Materials |
| 17 | Show BOM & Complete | Code | Final output display |

### 2 AI Model Nodes

| Node Name | Model | Purpose |
|-----------|-------|---------|
| OpenAI Chat Model (Parse) | glm-4.7 | Requirements parsing |
| OpenAI Chat Model (Recommend) | glm-4.7 | Component recommendation |

**Note:** You can change these to Claude API by editing the node configuration.

---

## Post-Import Configuration

### 1. Configure AI API Keys

**Option A: Claude API (Recommended)**

1. Get API key from: https://console.anthropic.com/settings/keys
2. In n8n, click **"OpenAI Chat Model (Parse)"** node
3. Click **"Credentials"** dropdown
4. Click **"+ Create New Credential"**
5. Select **"Anthropic API"** (not OpenAI)
6. Paste your Claude API key
7. Save credential
8. Repeat for **"OpenAI Chat Model (Recommend)"** node
9. Change model to: `claude-sonnet-4-5-20250929`

**Option B: GLM API (Current Default)**

1. Get API key from: https://open.bigmodel.cn/
2. Add to `.env` file:
   ```bash
   GLM_API_KEY=your-glm-key-here
   ```
3. In n8n, the nodes are already configured for GLM
4. Just add the credential when prompted

**Option C: Groq API (Fast, Free Tier)**

1. Get API key from: https://console.groq.com/keys
2. Add to `.env` file:
   ```bash
   GROQ_API_KEY=your-groq-key-here
   ```
3. Change model in both nodes to: `llama-3.1-70b-versatile`

### 2. Verify Playwright Scraper Service

The workflow depends on the Playwright scraper API running at `http://playwright:8000`.

**Check if service is running:**

```bash
docker ps | grep playwright

# Or check the API health endpoint
curl http://localhost:8000/api/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "hardware_pipeline_scraper",
  "database": "connected",
  "version": "1.0"
}
```

**If not running:**

```bash
docker compose up -d playwright
```

### 3. Test the Workflow

**Method 1: Via n8n Chat Interface**

1. Open the workflow in n8n
2. Click **"Chat"** button (if available in n8n UI)
3. Enter test requirements:
   ```
   Design a 3-phase motor controller with TMS320F28379D DSP,
   10kW output power, 48V DC input, 0-400Hz output frequency,
   Ethernet interface for monitoring, current sensing, and
   temperature protection.
   ```

**Method 2: Via Webhook**

```bash
WEBHOOK_URL="http://localhost:5678/webhook/phase1-chat-hardware-pipeline"

curl -X POST "${WEBHOOK_URL}" \
  -H "Content-Type: application/json" \
  -d '{
    "chatInput": "Design a 3-phase motor controller with TMS320F28379D DSP, 10kW output, 48V input, Ethernet interface"
  }'
```

**Method 3: Via Test Execution**

1. In n8n workflow editor
2. Click **"Execute Workflow"** button (top right)
3. Or press **Ctrl+Enter** / **Cmd+Enter**
4. Enter test data in the trigger node

---

## Expected Workflow Execution

### Execution Time

**Total:** 2-4 minutes (depending on component searches)

| Step | Time | Description |
|------|------|-------------|
| Requirements parsing | 10-15s | AI extracts structured data |
| Block diagram generation | 5-10s | Creates visual representation |
| **User approval** | Variable | Human review (pauses workflow) |
| Component scraping | 60-120s | Searches 3-10 components |
| AI recommendation | 10-20s | Selects best components |
| BOM generation | 5s | Creates bill of materials |

### Execution Flow

```
[1] User sends requirements
     ↓ (10s)
[2] AI parses requirements
     ↓ (5s)
[3] Block diagram generated
     ↓ (shows to user)
[4] WORKFLOW PAUSES - Waiting for "APPROVE"
     ↓ (user responds)
[5] User types "APPROVE"
     ↓ (60-120s)
[6] Scrapes 3-10 components in parallel
     ↓ (10s)
[7] AI recommends best components
     ↓ (5s)
[8] BOM generated and displayed
```

### Success Indicators

✅ **Workflow executed successfully**
✅ **Block diagram displayed** (ASCII format with boxes)
✅ **Approval request shown** ("Type APPROVE to continue")
✅ **Component search logs** (shows "Searching DigiKey/Mouser...")
✅ **BOM displayed** (with pricing and component count)

### Common Issues

**Issue 1: "Node 'OpenAI Chat Model' has no credentials"**
- **Fix:** Configure AI API credentials (see Configuration section above)

**Issue 2: "Cannot connect to http://playwright:8000"**
- **Fix:** Start playwright service: `docker compose up -d playwright`

**Issue 3: "Workflow execution timed out"**
- **Fix:** Increase timeout in n8n settings or reduce component search count

**Issue 4: "AI returned invalid JSON"**
- **Fix:** Check AI model configuration, try Claude API instead of GLM

---

## Workflow Customization

### Change System Type Detection

Edit **"Validate Input & Detect Type"** node (Node 2):

```javascript
// Add new system type detection
if (reqLower.includes('automotive') || reqLower.includes('can bus')) {
  systemType = 'Automotive';
}
```

### Adjust Component Search Count

Edit **"Build Component Searches"** node (Node 10):

```javascript
// Limit to top 3 component categories only
const searches = [];

// Processor only
if (parsed.primary_components?.processor) {
  searches.push({...});
}

// Power regulator (first rail only)
if (parsed.primary_components?.power) {
  const firstRail = parsed.primary_components.power.rails_needed[0];
  searches.push({...});
}

// Skip interface searches for faster execution
```

### Change Scraper Timeout

Edit **"Search Components (Real)"** node (Node 12):

```json
{
  "options": {
    "timeout": 90000  // Increase to 90 seconds
  }
}
```

### Disable Cache (Force Fresh Scraping)

Edit **"Search Components (Real)"** node (Node 12):

```json
{
  "jsonBody": {
    "search_term": "{{ $json.search_term }}",
    "use_cache": false  // Change to false
  }
}
```

---

## Database Setup (If Not Auto-Created)

The workflow uses PostgreSQL tables. If they don't exist:

```bash
# Connect to PostgreSQL container
docker exec -it postgres psql -U postgres -d hardware_pipeline

# Run the init script
\i /docker-entrypoint-initdb.d/init-db.sql

# Or manually from host
docker exec -i postgres psql -U postgres -d hardware_pipeline < init-db.sql
```

**Required tables:**
- `component_cache` - Component search cache
- `projects` - Project tracking
- `block_diagrams` - Block diagram storage
- `bom_items` - Bill of materials
- `component_recommendations` - AI recommendations

---

## Monitoring Workflow Execution

### Via n8n UI

1. Open n8n: http://localhost:5678
2. Go to **"Executions"** tab (left sidebar)
3. View all workflow runs with status:
   - ✅ Success
   - ⚠️ Waiting (approval gate)
   - ❌ Error

### Via Logs

```bash
# n8n logs
docker compose logs -f n8n

# Playwright scraper logs
docker compose logs -f playwright

# Database logs
docker compose logs -f postgres
```

### Via Database

```sql
-- Connect to PostgreSQL
docker exec -it postgres psql -U postgres -d hardware_pipeline

-- View recent projects
SELECT project_name, system_type, created_at
FROM projects
ORDER BY created_at DESC
LIMIT 10;

-- View component cache stats
SELECT * FROM component_cache_stats;

-- View scraping queue
SELECT * FROM scraping_queue WHERE status = 'pending';
```

---

## Troubleshooting

### Workflow Import Fails

**Error:** "Invalid workflow JSON"

**Causes:**
1. JSON file corrupted
2. Incompatible n8n version
3. Missing node types

**Solutions:**
1. Validate JSON: `jq . Phase1_Complete_Workflow_READY_TO_IMPORT.json`
2. Update n8n to latest: `docker compose pull n8n`
3. Install missing nodes via n8n Community Nodes

### Approval Loop Doesn't Work

**Error:** User types "APPROVE" but workflow doesn't continue

**Causes:**
1. Workflow not active
2. Chat trigger not properly configured
3. Approval message not recognized

**Solutions:**
1. Activate workflow (toggle switch to ON)
2. Check webhook ID: `phase1-chat-hardware-pipeline`
3. Type exactly "APPROVE" (case-insensitive, but exact spelling)

### Component Scraping Takes Too Long

**Error:** Timeout after 60 seconds

**Causes:**
1. Slow network connection
2. Distributor websites down/slow
3. Too many component searches

**Solutions:**
1. Increase timeout to 90-120 seconds
2. Enable cache to use cached results
3. Reduce number of component categories searched

### AI Returns Invalid JSON

**Error:** "Cannot parse JSON from AI response"

**Causes:**
1. AI model hallucinating
2. Prompt too complex
3. Token limit exceeded

**Solutions:**
1. Switch to Claude API (more reliable)
2. Simplify requirements input
3. Increase max_tokens parameter

---

## Next Steps After Import

### Phase 2-4 Implementation

The current workflow covers **Phase 1** only. To add Phase 2-4:

**Phase 2: HRS Document Generation**
- Add node after "Generate BOM"
- Call Claude API to generate 50-70 page HRS
- For RF systems: Add GLB (Gain Loss Budget) calculation
- For RF systems: Add Power Consumption Analysis
- Save to PostgreSQL `phase_outputs` table

**Phase 3: Compliance Validation**
- Add compliance checking nodes
- Validate RoHS, REACH, FCC, CE
- Flag ITAR/EAR components
- Generate compliance report

**Phase 4: Netlist Generation**
- Add netlist generation nodes
- Use NetworkX for connectivity graph
- Export to JSON/CSV format
- Prepare for PCB layout tools

**Phase 6: GLR Generation**
- Add after netlist
- Generate Glue Logic Requirements
- I/O specifications for FPGA interface

**Phase 8: Software Generation**
- Add code generation nodes
- Generate C/C++ drivers based on RDT/PSQ
- Generate Qt GUI application
- Add automated code review (MISRA-C)
- Add MR review gate before git push

### Enhancement Ideas

1. **Visual Block Diagram Export**
   - Add draw.io API integration
   - Export to PNG/SVG
   - Allow user editing

2. **Real-time Cost Tracking**
   - Track API usage per project
   - Show cost breakdown
   - Alert on budget overrun

3. **Component Alternatives**
   - AI suggests 3 alternatives per category
   - Price comparison
   - Lifecycle status warning

4. **Multi-Language Support**
   - Accept requirements in multiple languages
   - Translate to English for processing
   - Return results in user's language

---

## Support

**Issues:** https://github.com/bala9066/S2S/issues

**Documentation:**
- [REPOSITORY_ANALYSIS.md](./REPOSITORY_ANALYSIS.md)
- [PHASE1_WORKFLOW_SPECIFICATION.md](./PHASE1_WORKFLOW_SPECIFICATION.md)
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

**n8n Community:** https://community.n8n.io/

---

**Document Version:** 1.0
**Created:** February 3, 2026
**Last Updated:** February 3, 2026
**Workflow Version:** 2.0
