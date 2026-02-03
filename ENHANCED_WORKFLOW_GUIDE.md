# Phase 1 Enhanced Workflow - with GLB & Power Budget

**Workflow File:** `Phase1_Enhanced_With_GLB_PowerBudget.json`
**Version:** 2.1
**Created:** February 3, 2026

---

## What's New in Enhanced Version?

### Original Workflow (17 nodes)
- ✅ Requirements parsing
- ✅ Block diagram generation
- ✅ Approval gate
- ✅ Component search (DigiKey/Mouser)
- ✅ BOM generation

### Enhanced Workflow (25 nodes) - NEW!

**Additional Features:**

1. **🔬 GLB (Gain Loss Budget)** - For RF Systems
   - Automatically detects RF/Wireless projects
   - Calculates TX chain (PA, filters, etc.)
   - Calculates RX chain (LNA, mixer, etc.)
   - Link budget analysis with margin calculation
   - Stage-by-stage gain/loss/noise figure

2. **⚡ Power Consumption Budget** - Universal (ALL Systems)
   - Per-component power dissipation analysis
   - Voltage rail current/power calculation
   - Regulator efficiency losses
   - Thermal analysis (heat sink requirements)
   - Battery life estimation
   - Cooling method recommendations

3. **🤖 4 Claude AI Models**
   - Model 1: Requirements parsing
   - Model 2: Component recommendations
   - Model 3: GLB generation (RF only)
   - Model 4: Power budget (universal)

---

## Architecture

### Enhanced Flow Diagram

```
User Requirements
    ↓
Parse Requirements (AI)
    ↓
Generate Block Diagram
    ↓
[GATE 1: User Approval]
    ↓
Component Search (Playwright)
    ↓
AI Component Recommendation
    ↓
Generate BOM
    ↓
Is RF System? [CONDITIONAL]
    │
    ├─ YES → Generate GLB (AI) ──┐
    │                             ↓
    └─ NO ────────────────────────┤
                                  ↓
         Generate Power Budget (AI) [UNIVERSAL]
                                  ↓
          Show Enhanced Results (BOM + GLB + Power)
```

### Node Count Comparison

| Feature | Original | Enhanced |
|---------|----------|----------|
| Total Nodes | 17 | 25 |
| AI Agent Nodes | 2 | 4 |
| Conditional Nodes | 1 | 2 |
| AI Models | 2 | 4 |
| Output Documents | 1 (BOM) | 3 (BOM + GLB + Power) |

---

## New Nodes Explained

### Node 18: Is RF System?

**Type:** `n8n-nodes-base.if`
**Purpose:** Routes to GLB generation for RF systems only

**Condition:**
```javascript
$json.is_rf_system === true
```

**Branches:**
- **TRUE (RF System):** → Build GLB Prompt
- **FALSE (Non-RF):** → Build Power Budget Prompt (skips GLB)

### Node 19: Build GLB Prompt (RF Only)

**Type:** `n8n-nodes-base.code`
**Purpose:** Constructs AI prompt for Gain Loss Budget calculation

**Inputs:**
- RF specifications (frequency, TX power, RX sensitivity, modulation)
- Block diagram structure
- Selected components

**Prompt Template:**
```
You are an RF systems engineer. Generate a Gain Loss Budget (GLB) for this RF system.

SYSTEM SPECIFICATIONS:
- Frequency: 2.4GHz
- TX Power: +20dBm
- RX Sensitivity: -95dBm
- Modulation: FSK

Generate detailed GLB with TX chain, RX chain, and link budget analysis.
```

**Output:**
- GLB AI prompt (ready for Claude)
- Max tokens: 3000

### Node 20: AI: Generate GLB

**Type:** `@n8n/n8n-nodes-langchain.agent`
**AI Model:** Claude Sonnet 4.5
**Purpose:** Generates GLB using AI reasoning

**Example AI Output:**
```json
{
  "tx_chain": [
    {"stage": "PA", "gain_db": 30, "noise_figure_db": 1, "output_power_dbm": 20},
    {"stage": "Filter", "gain_db": -2, "noise_figure_db": 2, "output_power_dbm": 18},
    {"stage": "Antenna", "gain_db": 2, "output_power_dbm": 20}
  ],
  "rx_chain": [
    {"stage": "LNA", "gain_db": 15, "noise_figure_db": 1.5, "output_power_dbm": -70},
    {"stage": "Mixer", "gain_db": -8, "noise_figure_db": 10, "output_power_dbm": -78},
    {"stage": "IF Filter", "gain_db": -3, "output_power_dbm": -81}
  ],
  "link_budget": {
    "tx_power_dbm": 20,
    "path_loss_db": 80,
    "rx_sensitivity_dbm": -95,
    "margin_db": 15
  },
  "summary": "Link budget closes with 15dB margin. System meets requirements."
}
```

### Node 21: Extract GLB Data

**Type:** `n8n-nodes-base.code`
**Purpose:** Parses and formats GLB from AI response

**Processing:**
1. Extracts JSON from AI response
2. Validates GLB structure
3. Formats into readable summary:

```
╔════════════════════════════════════════╗
║      GAIN LOSS BUDGET (GLB)            ║
╠════════════════════════════════════════╣

TX CHAIN:
  1. PA: Gain=30dB, Output=20dBm
  2. Filter: Gain=-2dB, Output=18dBm
  3. Antenna: Gain=2dB, Output=20dBm

RX CHAIN:
  1. LNA: Gain=15dB, NF=1.5dB
  2. Mixer: Gain=-8dB, NF=10dB
  3. IF Filter: Gain=-3dB

LINK BUDGET:
  TX Power: 20 dBm
  Path Loss: 80 dB
  RX Sensitivity: -95 dBm
  Margin: 15 dB

SUMMARY:
Link budget closes with 15dB margin. System meets requirements.

╚════════════════════════════════════════╝
```

### Node 22: Build Power Budget Prompt

**Type:** `n8n-nodes-base.code`
**Purpose:** Constructs AI prompt for power consumption analysis

**Universal:** Works for ALL system types, not just RF

**Inputs:**
- Component list with part numbers
- Voltage rails needed
- Input voltage and output power specs

**Prompt Template:**
```
You are a hardware power systems engineer. Generate a Power Consumption Budget.

SYSTEM POWER SPECIFICATIONS:
- Input Voltage: 48V
- Output Power: 10kW
- Voltage Rails: 3.3V, 1.8V, 5V, 15V

COMPONENTS:
- TMS320F28379D: DSP Processor
- TPS54339E: 3.3V Regulator
- ... (up to 15 components)

Analyze power consumption with component breakdown, rail budgets,
thermal analysis, and battery life estimation.
```

### Node 23: AI: Generate Power Budget

**Type:** `@n8n/n8n-nodes-langchain.agent`
**AI Model:** Claude Sonnet 4.5
**Purpose:** Generates comprehensive power budget

**Example AI Output:**
```json
{
  "components": [
    {"part": "TMS320F28379D", "voltage_rail": "3.3V", "typical_current_ma": 250, "max_current_ma": 350, "power_mw": 825},
    {"part": "DP83867", "voltage_rail": "3.3V", "typical_current_ma": 180, "max_current_ma": 220, "power_mw": 594},
    {"part": "TPS54339E", "voltage_rail": "3.3V", "typical_current_ma": 5, "power_mw": 16}
  ],
  "rails": [
    {"voltage": "3.3V", "total_current_ma": 435, "total_power_w": 1.436, "regulator_efficiency": 0.85, "input_power_w": 1.689},
    {"voltage": "1.8V", "total_current_ma": 120, "total_power_w": 0.216, "regulator_efficiency": 0.85, "input_power_w": 0.254}
  ],
  "total_power": {
    "typical_w": 3.2,
    "max_w": 4.8,
    "thermal_dissipation_w": 1.2
  },
  "thermal_analysis": {
    "ambient_temp_c": 25,
    "max_junction_temp_c": 85,
    "heat_sink_required": false,
    "cooling_method": "natural convection",
    "note": "Ensure adequate PCB copper for heat spreading"
  },
  "battery_life": {
    "battery_capacity_mah": 2000,
    "runtime_hours": 1.5,
    "note": "For continuous full load operation"
  },
  "summary": "Total system power is 3.2W typical, 4.8W max. Natural convection sufficient."
}
```

### Node 24: Extract Power Budget

**Type:** `n8n-nodes-base.code`
**Purpose:** Parses and formats power budget from AI

**Formatted Output:**
```
╔════════════════════════════════════════╗
║      POWER CONSUMPTION BUDGET          ║
╠════════════════════════════════════════╣

VOLTAGE RAILS:
  1. 3.3V: 435mA (1.44W)
  2. 1.8V: 120mA (0.22W)
  3. 5V: 300mA (1.50W)

TOTAL POWER:
  Typical: 3.20 W
  Maximum: 4.80 W
  Thermal Dissipation: 1.20 W

THERMAL ANALYSIS:
  Heat Sink Required: No
  Cooling Method: natural convection

BATTERY LIFE:
  Capacity: 2000mAh
  Runtime: 1.5h

SUMMARY:
Total system power is 3.2W typical, 4.8W max.
Natural convection sufficient.

╚════════════════════════════════════════╝
```

### Node 25: Show Enhanced Results

**Type:** `n8n-nodes-base.code`
**Purpose:** Displays all results to user

**Output Includes:**
1. **BOM Summary** (always)
2. **GLB Summary** (if RF system)
3. **Power Budget Summary** (always)
4. **Next Steps** (Phase 2-4)

**Example Output:**

```
✅ **PHASE 1 COMPLETE**

╔══════════════════════════════════════╗
║         BILL OF MATERIALS            ║
╠══════════════════════════════════════╣
║  Project: Project_1738540800000      ║
║  System: RF_Wireless                 ║
║  Total Components: 45                ║
║  Estimated Cost: $127.50             ║
╚══════════════════════════════════════╝

TOP COMPONENTS:
1. nRF52840-QIAA          $3.85
2. SKY66112-11            $2.20 (PA)
3. SKY13453-460LF         $1.50 (Antenna Switch)
...


╔════════════════════════════════════════╗
║      GAIN LOSS BUDGET (GLB)            ║
╠════════════════════════════════════════╣

TX CHAIN:
  1. PA: Gain=20dB, Output=17dBm
  2. Filter: Gain=-1dB, Output=16dBm
  3. Antenna: Gain=2dB, Output=18dBm

RX CHAIN:
  1. LNA: Gain=15dB, NF=2.5dB
  2. Mixer: Gain=-7dB, NF=8dB

LINK BUDGET:
  TX Power: 18 dBm
  Path Loss: 70 dB
  RX Sensitivity: -92 dBm
  Margin: 22 dB

╚════════════════════════════════════════╝


╔════════════════════════════════════════╗
║      POWER CONSUMPTION BUDGET          ║
╠════════════════════════════════════════╣

VOLTAGE RAILS:
  1. 3.3V: 85mA (0.28W)
  2. 1.8V: 12mA (0.02W)

TOTAL POWER:
  Typical: 0.35 W
  Maximum: 0.52 W
  Thermal Dissipation: 0.08 W

BATTERY LIFE:
  Capacity: 250mAh (CR2032)
  Runtime: 48h

╚════════════════════════════════════════╝


📦 **Next Steps:**
- Phase 2: Generate HRS Document (50-70 pages)
- Phase 3: Compliance validation (RoHS, REACH, FCC, CE RED)
- Phase 4: Netlist generation

Would you like to continue to Phase 2?
```

---

## Import Instructions

### Method 1: Via n8n UI (Recommended)

1. **Start Services**
   ```bash
   cd /home/user/S2S
   docker compose up -d
   ```

2. **Open n8n**
   - Navigate to: http://localhost:5678
   - Login: admin / admin123

3. **Import Workflow**
   - Click **"+"** → **"Import from File"**
   - Or press **Ctrl+O** / **Cmd+O**
   - Select: `Phase1_Enhanced_With_GLB_PowerBudget.json`

4. **Configure Claude API**
   - Click on **"Claude Model (Parse)"** node
   - Add Anthropic API credential
   - Repeat for all 4 Claude model nodes:
     - Claude Model (Parse)
     - Claude Model (Recommend)
     - Claude Model (GLB)
     - Claude Model (Power)

5. **Save & Activate**
   - Click **"Save"**
   - Toggle **"Active"** to ON

### Method 2: Automated Script

```bash
python3 run_pipeline.py
# Select: "2. Import workflow only"
# Choose: Enhanced workflow when prompted
```

---

## Testing the Enhanced Workflow

### Test Case 1: RF Wireless System

**Input Requirements:**
```
Design a 2.4GHz Bluetooth Low Energy beacon using Nordic nRF52840 SoC,
+4dBm TX power, -95dBm RX sensitivity, coin cell battery (CR2032),
temperature sensor, accelerometer, USB-C programming interface.
```

**Expected Output:**
- System Type: **RF_Wireless**
- Components: ~30-40 found
- **GLB Generated:** ✅ (TX/RX chains, link budget)
- **Power Budget:** ✅ (battery life ~48h)
- BOM Cost: ~$18-25

**Execution Time:** ~3-4 minutes

### Test Case 2: Motor Controller (Non-RF)

**Input Requirements:**
```
Design a 3-phase motor controller with TMS320F28379D DSP,
10kW output power, 48V DC input, 0-400Hz output frequency,
Ethernet interface for monitoring, current sensing, and
temperature protection.
```

**Expected Output:**
- System Type: **Motor_Control**
- Components: ~60-80 found
- **GLB Generated:** ❌ (skipped - not RF)
- **Power Budget:** ✅ (typical 3.2W)
- BOM Cost: ~$150-200

**Execution Time:** ~3.5-5 minutes

### Test Case 3: Power Supply (Non-RF)

**Input Requirements:**
```
Design a 48V to 12V DC-DC buck converter, 5A output current,
synchronous rectification, enable pin, overcurrent protection,
thermal shutdown, -40 to 85C operation.
```

**Expected Output:**
- System Type: **Power_Electronics**
- Components: ~20-30 found
- **GLB Generated:** ❌ (not RF)
- **Power Budget:** ✅ (efficiency 92%, thermal analysis)
- BOM Cost: ~$25-35

**Execution Time:** ~2-3 minutes

---

## Comparison: Original vs Enhanced

| Feature | Original Workflow | Enhanced Workflow |
|---------|------------------|-------------------|
| **Nodes** | 17 | 25 (+8 nodes) |
| **AI Calls** | 2 | 2-4 (conditional) |
| **Documents Generated** | 1 (BOM) | 2-3 (BOM + Power + GLB if RF) |
| **RF Detection** | Yes | Yes (enhanced) |
| **GLB Generation** | ❌ No | ✅ Yes (RF only) |
| **Power Budget** | ❌ No | ✅ Yes (universal) |
| **Thermal Analysis** | ❌ No | ✅ Yes |
| **Battery Life Calc** | ❌ No | ✅ Yes |
| **Execution Time** | 2-4 min | 3-5 min |
| **API Cost/Project** | $0.047 | $0.08-0.12 |

---

## API Cost Analysis

### Per Project Execution

**Original Workflow:**
- Requirements parsing: ~2,000 tokens
- Component recommendation: ~3,000 tokens
- **Total:** ~5,000 tokens = **$0.047**

**Enhanced Workflow (Non-RF):**
- Requirements parsing: ~2,000 tokens
- Component recommendation: ~3,000 tokens
- Power budget: ~4,000 tokens
- **Total:** ~9,000 tokens = **$0.085**

**Enhanced Workflow (RF System):**
- Requirements parsing: ~2,000 tokens
- Component recommendation: ~3,000 tokens
- GLB generation: ~5,000 tokens
- Power budget: ~4,000 tokens
- **Total:** ~14,000 tokens = **$0.125**

### Annual Cost (100 Projects)

**Scenario 1: All Non-RF**
- 100 projects × $0.085 = **$8.50/year**

**Scenario 2: 50% RF, 50% Non-RF**
- 50 × $0.125 + 50 × $0.085 = **$10.50/year**

**Scenario 3: All RF**
- 100 projects × $0.125 = **$12.50/year**

**Verdict:** Still within budget (₹2.5L/year = $3,000/year)

---

## Technical Details

### GLB Calculation Algorithm

The AI performs these steps:

1. **TX Chain Analysis**
   - Start with desired output power
   - Work backwards through: Antenna → Filter → PA → Driver
   - Calculate gain/loss at each stage
   - Verify PA output capability

2. **RX Chain Analysis**
   - Start with antenna input
   - Calculate through: LNA → Mixer → IF Filter → ADC
   - Cascaded noise figure calculation (Friis formula)
   - Verify sensitivity meets requirements

3. **Link Budget**
   ```
   Margin = TX Power + TX Antenna Gain - Path Loss + RX Antenna Gain - RX Sensitivity
   ```
   - Target margin: 15-20 dB
   - Warn if < 10 dB

### Power Budget Calculation

1. **Component-Level Analysis**
   - Extract typical/max current from datasheets
   - Multiply by voltage rail: `P = V × I`

2. **Rail-Level Aggregation**
   - Sum all components on each rail
   - Calculate regulator input power: `P_in = P_out / efficiency`

3. **Total System Power**
   - Sum all rail input powers
   - Add switching regulator losses
   - Calculate thermal dissipation

4. **Thermal Analysis**
   - Estimate junction-to-ambient thermal resistance
   - Calculate temperature rise: `ΔT = P × Rθja`
   - Determine if heat sink needed

5. **Battery Life**
   - If battery-powered: `Runtime = Capacity / Avg Current`
   - Account for battery voltage curve
   - Provide conservative estimate

---

## Troubleshooting

### Issue 1: GLB Not Generated (RF System)

**Symptoms:** RF system detected but no GLB in output

**Causes:**
1. `is_rf_system` flag not set correctly
2. RF specifications not parsed by AI
3. GLB AI call failed

**Solutions:**
1. Check Node 2 detection logic
2. Verify AI parsing includes `rf_specifications`
3. Check Claude API logs for errors

### Issue 2: Power Budget Shows Default Values

**Symptoms:** Power budget always shows same generic values

**Causes:**
1. AI failed to parse component list
2. JSON extraction error
3. Timeout on AI call

**Solutions:**
1. Increase max_tokens to 4000
2. Check AI response format
3. Increase timeout to 120 seconds

### Issue 3: Workflow Too Slow

**Symptoms:** Execution takes > 5 minutes

**Causes:**
1. Too many component searches
2. Slow Claude API response
3. Network latency

**Solutions:**
1. Reduce component categories in Node 10
2. Use cached components (use_cache: true)
3. Limit to top 3 categories only

---

## Customization

### Disable GLB Generation

Edit Node 18 "Is RF System?" condition to always FALSE:

```javascript
// Change this:
$json.is_rf_system === true

// To this:
false  // GLB disabled
```

### Disable Power Budget

Delete or disconnect Nodes 22-24:
- Build Power Budget Prompt
- AI: Generate Power Budget
- Extract Power Budget

Connect "Generate BOM" directly to "Show Enhanced Results"

### Change AI Models

**Switch to GPT-4:**

1. Replace Claude model nodes with OpenAI nodes
2. Change model to: `gpt-4-turbo-preview`
3. Update credentials to OpenAI API key

**Switch to GLM:**

1. Keep OpenAI node type
2. Change base URL: `https://api.z.ai/api/paas/v4`
3. Change model: `glm-4-plus`

---

## Future Enhancements

### Planned for Phase 2

1. **HRS Document Generation**
   - 50-70 page Hardware Requirements Specification
   - Based on BOM, GLB, Power Budget
   - Compliance requirements included

2. **Compliance Validation**
   - RoHS substance check
   - REACH compliance
   - FCC Part 15/18 (RF only)
   - CE marking requirements

3. **Gate 2: HRS/BOM Approval**
   - User reviews complete documentation
   - Can request changes
   - Proceeds to netlist after approval

### Planned for Phase 3-4

4. **Netlist Generation**
   - Connectivity graph from block diagram
   - Component pin assignments
   - Export to JSON/CSV

5. **GLR Generation**
   - Glue Logic Requirements for FPGA
   - I/O specifications
   - Timing constraints

---

## Summary

The **Enhanced Workflow** adds critical engineering analysis documents:

✅ **GLB (Gain Loss Budget)** - RF system performance validation
✅ **Power Budget** - Power consumption and thermal analysis
✅ **4 AI Models** - Specialized for each task
✅ **Conditional Logic** - GLB only for RF systems
✅ **Universal Power Analysis** - For all system types

**Ready to import and use in production!**

---

**Document Version:** 1.0
**Workflow Version:** 2.1
**Created:** February 3, 2026
**Author:** Hardware Pipeline Team
**Repository:** bala9066/S2S
