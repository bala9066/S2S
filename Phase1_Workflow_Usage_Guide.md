# Phase 1 Workflow - Usage Guide
## Complete Instructions for Import, Setup, and Testing

---

## 📥 STEP 1: IMPORT WORKFLOW TO N8N

### Method 1: Via n8n UI (Recommended)

```bash
1. Open n8n in browser: http://localhost:5678
2. Click "Workflows" in left sidebar
3. Click "+ Add workflow" button
4. Click "Import from File" (or press Ctrl+I)
5. Select file: Phase1_Complete_Workflow_READY_TO_IMPORT.json
6. Click "Import"
7. Workflow will open automatically
```

### Method 2: Via n8n CLI

```bash
# Copy file to n8n workflows directory
cp Phase1_Complete_Workflow_READY_TO_IMPORT.json ~/.n8n/workflows/

# Or use n8n API
curl -X POST http://localhost:5678/rest/workflows \
  -H "Content-Type: application/json" \
  -H "X-N8N-API-KEY: your-api-key" \
  -d @Phase1_Complete_Workflow_READY_TO_IMPORT.json
```

---

## 🔧 STEP 2: CONFIGURE CREDENTIALS

### Required: Claude API Credentials

```bash
1. In n8n, go to: Settings → Credentials
2. Click "+ Add Credential"
3. Search for "Claude" or "Anthropic"
4. Add these details:
   - Name: Claude_API
   - API Key: your-claude-api-key (get from https://console.anthropic.com)
5. Click "Save"
```

### Get Claude API Key:
```bash
1. Go to: https://console.anthropic.com/settings/keys
2. Click "Create Key"
3. Name: "Hardware Pipeline n8n"
4. Copy the key (starts with sk-ant-...)
5. Paste into n8n credentials
```

---

## 🚀 STEP 3: ACTIVATE WORKFLOW

```bash
1. Open the imported workflow in n8n
2. Click "Active" toggle in top-right (should turn green)
3. Workflow is now listening for chat input
```

---

## 💬 STEP 4: TEST WITH CHAT INTERFACE

### Test Case 1: Motor Controller

**Chat with n8n:**

```
User: Design a 3-phase motor controller with TMS320F28379D DSP, 10kW output power, 48V DC input, 0-400Hz output frequency, Ethernet interface for monitoring, current sensing, and temperature protection.
```

**Expected Response:**
```
📋 **BLOCK DIAGRAM GENERATED**

╔════════════════════════════════════════╗
║  BLOCK DIAGRAM: Project_1738454400000  ║
╠════════════════════════════════════════╣
║  System Type: Motor_Control            ║
║  Total Blocks: 12                      ║
║  Connections: 11                       ║
╚════════════════════════════════════════╝

MAIN COMPONENTS:
  1. TMS320F28379D (processor)
  2. Input 48V (power_input)
  3. Regulator 3.3V (power_regulator)
  4. Regulator 1.8V (power_regulator)
  5. Ethernet (interface)
  6. Gate Driver (driver)
  7. Inverter (MOSFETs) (power_stage)
  8. 3-Phase Motor (load)

✅ **Please review the block diagram above.**

**Options:**
- Type **"APPROVE"** to continue to component selection
- Type **"REJECT: <reason>"** to request changes
- Type **"MODIFY: <changes>"** to update requirements

Waiting for your approval...
```

**User Approves:**
```
User: APPROVE
```

**Expected Response:**
```
✅ **PHASE 1 COMPLETE**

╔══════════════════════════════════════╗
║         BILL OF MATERIALS            ║
╠══════════════════════════════════════╣
║  Project: Project_1738454400000      ║
║  Total Components: 24                ║
║  Estimated Cost: $384.75             ║
╚══════════════════════════════════════╝

TOP COMPONENTS:
1. MOCK-PROCESSOR-001     $23.45
2. MOCK-POWER_REGULATOR-001 $12.34
3. MOCK-INTERFACE-001      $8.90
4. MOCK-GATE_DRIVER-001    $15.67
5. MOCK-POWER_MOSFET-001   $4.56
... and 19 more components

📦 **Next Steps:**
- Phase 2: Generate HRS Document (50-70 pages)
- Phase 3: Compliance validation
- Phase 4: Netlist generation

Would you like to continue to Phase 2?
```

---

### Test Case 2: RF/Wireless System

**Chat Input:**
```
User: Design RF system with Xilinx Artix-7 FPGA, 5-18GHz frequency range, 40dBm output power, return loss > 10dB, GaN power amplifier, buck-boost converters for multiple power rails
```

**System will detect:** RF_Wireless  
**Block diagram will include:** FPGA, RF PA, Antenna, Matching Networks  

---

### Test Case 3: Digital Controller

**Chat Input:**
```
User: Design digital controller with Zynq UltraScale+ MPSoC, DDR4 memory, Gigabit Ethernet, USB 3.0, PCIe Gen3, operating temperature -40 to 85°C
```

**System will detect:** Digital_Controller  
**Block diagram will include:** Zynq, DDR4, Ethernet PHY, USB Controller  

---

### Test Case 4: Power Electronics

**Chat Input:**
```
User: Design 300W AC-DC power supply with PFC, 90-264VAC input, 48V DC output, 85% efficiency, active cooling, meets IEC 62368-1
```

**System will detect:** Power_Electronics  
**Block diagram will include:** Rectifier, PFC Controller, DC-DC Converter, Output Filter  

---

## 🔍 STEP 5: VERIFY WORKFLOW EXECUTION

### Check Execution in n8n:

```bash
1. In n8n, click "Executions" in left sidebar
2. You should see executions with status "Success"
3. Click on an execution to see detailed flow
4. Each node shows:
   - Input data (what it received)
   - Output data (what it produced)
   - Execution time
```

### Expected Node Execution Times:

```
Node                              | Time    | Output
----------------------------------|---------|---------------------------
Chat Trigger                      | <1s     | User message
Validate Input & Detect Type      | <1s     | Validated requirements
Build AI Prompt                   | <1s     | Prompt text
AI: Parse Requirements (Claude)   | 3-5s    | Parsed JSON
Extract Parsed Data               | <1s     | Structured data
Generate Block Diagram            | 1-2s    | Block diagram JSON
Show Diagram & Wait Approval      | (waits) | ASCII diagram
Handle Approval                   | <1s     | Approval confirmation
Build Component Searches          | <1s     | Search queries
Split Searches (3 per batch)      | <1s     | Batched queries
Search Components (Mock)          | 1-2s    | Mock components
Aggregate All Components          | <1s     | All components
Prepare Component Recommendations | <1s     | Recommendation prompt
AI: Recommend Components          | 2-4s    | AI recommendations
Generate BOM                      | <1s     | BOM summary
Show BOM & Complete               | <1s     | Final output
----------------------------------|---------|---------------------------
TOTAL (excluding wait)            | 10-20s  |
```

---

## 🐛 STEP 6: TROUBLESHOOTING

### Issue 1: "Chat Trigger not found"

**Solution:**
```bash
1. Check n8n version: n8n --version
2. Minimum version required: 1.20.0+
3. Update n8n: npm update -g n8n
4. Restart n8n: systemctl restart n8n
```

### Issue 2: "Claude API credentials missing"

**Solution:**
```bash
1. Go to Settings → Credentials
2. Click "+ Add Credential"
3. Search "Claude" or "Anthropic"
4. Add API key from https://console.anthropic.com
5. Test connection
6. Save
```

### Issue 3: "Workflow stays at 'Waiting for approval'"

**Explanation:**  
This is EXPECTED behavior. The workflow pauses at the approval checkpoint.

**Solution:**
```bash
1. User must type "APPROVE" in chat
2. Or restart workflow with new requirements
```

### Issue 4: "AI Parse Requirements fails"

**Possible causes:**
- Claude API rate limit exceeded
- Invalid API key
- Network timeout

**Solution:**
```bash
1. Check Claude API dashboard for rate limits
2. Verify API key is active
3. Check node timeout settings (default 90s)
4. Retry execution
```

### Issue 5: "Node 'Aggregate All Components' takes too long"

**Solution:**
```bash
1. This is normal for large component searches
2. Reduce batch size in "Split Searches" node
3. Current: 3 per batch
4. Recommended: 2 per batch for faster execution
```

---

## 📊 STEP 7: MONITOR WORKFLOW PERFORMANCE

### Key Metrics to Track:

```
Metric                    | Target      | Action if Exceeded
--------------------------|-------------|--------------------
Total execution time      | < 30s       | Optimize AI prompts
Claude API calls          | 2-3 per run | Check for loops
Component searches        | 5-10        | Reduce categories
Failed executions         | < 5%        | Review error logs
User approval wait time   | N/A         | User-dependent
```

### View Metrics in n8n:

```bash
1. Click "Executions" → "Statistics"
2. View:
   - Success rate
   - Average execution time
   - Error distribution
   - Node performance
```

---

## 🔄 STEP 8: WORKFLOW VARIATIONS

### Variation 1: Skip Component Search (Faster Testing)

```javascript
// In "Handle Approval" node, add:
return {
  json: {
    ...($json),
    skip_component_search: true  // Add this line
  }
};
```

### Variation 2: Auto-Approve (No User Input)

```javascript
// Replace "Show Diagram & Wait Approval" node with:
{
  "parameters": {
    "jsCode": "return {json: {approved: true}};"
  },
  "name": "Auto-Approve"
}
```

### Variation 3: Custom System Type

```javascript
// In "Validate Input & Detect Type", add:
const systemType = input.force_system_type || autoDetectedType;
```

---

## 📝 STEP 9: EXTEND WORKFLOW

### Add Real Playwright Scraping:

Replace "Search Components (Mock)" node with:

```python
# Node: Search Components (Playwright)
import asyncio
from playwright.async_api import async_playwright

async def scrape_digikey(search_term):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto('https://www.digikey.com')
        await page.fill('input[name="keywords"]', search_term)
        await page.press('input[name="keywords"]', 'Enter')
        await page.wait_for_selector('.product-table')
        
        # Extract products...
        
        await browser.close()
    return results

# Execute
results = await scrape_digikey(_input.item.json['search_term'])
return {'json': {'components': results}}
```

### Add PostgreSQL Caching:

Insert before "Search Components (Mock)":

```javascript
// Node: Check Cache
const { Client } = require('pg');
const client = new Client({
  host: 'localhost',
  database: 'hardware_pipeline',
  user: 'postgres',
  password: 'password'
});

await client.connect();

const result = await client.query(
  'SELECT * FROM component_cache WHERE search_term = $1 AND expires_at > NOW()',
  [$json.search_term]
);

await client.end();

if (result.rows.length > 0) {
  return {json: {cache_hit: true, components: result.rows}};
} else {
  return {json: {cache_hit: false}};
}
```

---

## ✅ STEP 10: VERIFY COMPLETE FUNCTIONALITY

### Checklist:

- [ ] Workflow imports without errors
- [ ] Chat trigger activates
- [ ] System type detection works (test 6 types)
- [ ] Block diagram generates correctly
- [ ] Approval checkpoint pauses workflow
- [ ] User can approve/reject
- [ ] Component search executes
- [ ] AI recommendations work
- [ ] BOM generates
- [ ] Execution completes successfully

### Test All 6 System Types:

```bash
1. RF/Wireless: ✓ Test with "RF amplifier 5GHz"
2. Motor Control: ✓ Test with "3-phase motor controller"
3. Digital Controller: ✓ Test with "FPGA with DDR"
4. Power Electronics: ✓ Test with "AC-DC power supply"
5. Industrial Control: ✓ Test with "PLC with Modbus"
6. Sensor System: ✓ Test with "temperature sensor with ADC"
```

---

## 🎯 SUMMARY

### What This Workflow Does:

1. ✅ Receives hardware requirements via **chat interface**
2. ✅ Auto-detects system type (6 types supported)
3. ✅ Parses requirements with Claude AI
4. ✅ Generates **universal block diagram** (adapts to system type)
5. ✅ **Pauses for user approval** of block diagram
6. ✅ Searches for components (currently mock data)
7. ✅ AI recommends best components
8. ✅ Generates BOM with cost estimate
9. ✅ Displays results in chat

### Execution Time:
- **Without user wait:** 10-20 seconds
- **With approval wait:** User-dependent (can be minutes/hours)

### Next Steps:
1. Replace mock component search with real Playwright scraping
2. Add PostgreSQL caching
3. Implement real BOM Excel generation (openpyxl)
4. Add Phase 2 trigger (HRS document generation)
5. Add error handling and retry logic

---

## 📞 SUPPORT

**If you encounter issues:**

1. Check n8n logs: `docker logs n8n` or `~/.n8n/logs/`
2. Verify Claude API key is valid
3. Test with minimal requirements (50 chars)
4. Check execution history in n8n UI
5. Review this guide's Troubleshooting section

**File Location:**
- Workflow JSON: `/mnt/user-data/outputs/Phase1_Complete_Workflow_READY_TO_IMPORT.json`
- Usage Guide: This file

---

🎉 **WORKFLOW READY TO USE!**

Import the JSON file, configure Claude API credentials, and start chatting with your Hardware Pipeline assistant!
