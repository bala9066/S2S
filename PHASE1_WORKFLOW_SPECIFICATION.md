# Phase 1 Workflow - Universal Hardware Design Automation

**Version:** 2.0
**Last Updated:** February 3, 2026
**Workflow Name:** `Phase_1_Requirements_Components_Universal`
**Type:** Universal (All Hardware Systems)

---

## Table of Contents

1. [Overview](#overview)
2. [Supported System Types](#supported-system-types)
3. [Workflow Architecture](#workflow-architecture)
4. [Node-by-Node Breakdown](#node-by-node-breakdown)
5. [User Interaction Flow](#user-interaction-flow)
6. [Data Structures](#data-structures)
7. [AI Integration](#ai-integration)
8. [Component Scraping](#component-scraping)
9. [Error Handling](#error-handling)
10. [Output Artifacts](#output-artifacts)
11. [Usage Examples](#usage-examples)

---

## Overview

### Purpose

Phase 1 automates the **Requirements-to-BOM** workflow for hardware design:
- Captures natural language requirements from user
- Auto-detects system type (RF, Motor Control, Power, Sensor, Industrial, Digital)
- Parses requirements using AI into structured data
- Generates block diagram for visual verification
- **GATE 1:** Requires user approval before proceeding
- Searches for components using Playwright scraper (DigiKey/Mouser)
- Uses AI to recommend best components
- Generates Bill of Materials (BOM) with pricing

### Execution Time

**Total:** ~2-4 minutes
- Requirements parsing: 10-15 seconds
- Block diagram generation: 5-10 seconds
- User approval: Variable (human in the loop)
- Component scraping: 60-120 seconds (3-10 searches)
- AI component recommendation: 10-20 seconds
- BOM generation: 5 seconds

### Key Features

✅ **Universal System Support** - Works for all hardware types, not just RF
✅ **Intelligent Type Detection** - Auto-classifies based on keywords
✅ **Human-in-the-Loop** - Approval gate before expensive operations
✅ **Real Component Data** - Live scraping from distributors
✅ **AI-Powered Selection** - Smart component recommendations
✅ **Cost Estimation** - BOM with real-time pricing

---

## Supported System Types

The workflow automatically detects and handles **6 system types**:

| System Type | Detection Keywords | Example Project |
|-------------|-------------------|-----------------|
| **RF_Wireless** | rf, wireless, ghz, antenna, transceiver, frequency | 2.4GHz transceiver, LoRa gateway |
| **Motor_Control** | motor, inverter, 3-phase, bldc, servo, gate driver | BLDC motor controller, VFD |
| **Power_Electronics** | power supply, ac/dc, dc/dc, rectifier, buck, boost | 48V to 12V DC-DC converter |
| **Sensor_System** | sensor, adc, measurement, amplifier, precision | Temperature sensor array, DAQ |
| **Industrial_Control** | plc, industrial, modbus, profibus, fieldbus, 24v | Modbus RTU controller, PLC |
| **Digital_Controller** | fpga, xilinx, altera, ddr, ethernet, mcu | STM32-based controller, FPGA board |

**Default:** If no keywords match, defaults to `Digital_Controller`

---

## Workflow Architecture

### High-Level Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 1 WORKFLOW                         │
│          (Universal Hardware Design Automation)             │
└─────────────────────────────────────────────────────────────┘

[1] User Input (Chat)
     │
     ▼
[2] Validate & Detect Type
     │
     ▼
[3] Is Approval? ──YES──► [9] Handle Approval
     │                           │
     NO                          ▼
     │                    [10] Build Component Searches
     ▼                           │
[4] Build AI Prompt              ▼
     │                    [11] Split Searches (batches of 3)
     ▼                           │
[5] AI: Parse Requirements       ▼
     │                    [12] Search Components (Playwright API)
     ▼                           │
[6] Extract Parsed Data          ▼
     │                    [13] Aggregate All Components
     ▼                           │
[7] Generate Block Diagram       ▼
     │                    [14] Prepare Recommendations
     ▼                           │
[8] Show Diagram & Wait          ▼
     │                    [15] AI: Recommend Components
     │                           │
     └─────► [APPROVAL LOOP] ◄───┘
                                 │
                                 ▼
                          [16] Generate BOM
                                 │
                                 ▼
                          [17] Show BOM & Complete
```

### Approval Loop

The workflow implements a **conversational approval pattern**:

1. Generate block diagram → Show to user
2. Wait for user response (loops back to Chat Trigger)
3. User types "APPROVE", "REJECT", or "MODIFY"
4. Workflow resumes from approval handler
5. Continues to component search

This creates a **human-in-the-loop** checkpoint before expensive operations.

---

## Node-by-Node Breakdown

### Node 1: Chat Trigger

**Type:** `@n8n/n8n-nodes-langchain.chatTrigger`
**Purpose:** Entry point for user interaction

**Configuration:**
```json
{
  "webhookId": "phase1-chat-hardware-pipeline",
  "options": {}
}
```

**Input:** User message (natural language)
**Output:** `chatInput` field containing user text

**Usage:**
- Initial requirements: User provides design requirements
- Approval response: User responds with "APPROVE" or "REJECT"

---

### Node 2: Validate Input & Detect Type

**Type:** `n8n-nodes-base.code` (JavaScript)
**Purpose:** Input validation and automatic system type detection

**Logic:**

1. **Approval Detection**
   - Checks if message contains "approve", "reject", or "modify"
   - If yes, returns `is_approval: true` and routes to approval handler
   - If no, continues to requirements parsing

2. **Requirements Validation**
   - Minimum length: 30 characters
   - Error if too short with helpful example

3. **Auto-Detection Algorithm**
   ```javascript
   const reqLower = requirements.toLowerCase();

   if (reqLower.includes('rf') || reqLower.includes('wireless') || ...)
     systemType = 'RF_Wireless';
   else if (reqLower.includes('motor') || reqLower.includes('inverter') || ...)
     systemType = 'Motor_Control';
   // ... etc
   ```

4. **Project Name Generation**
   - Format: `Project_<timestamp>`
   - Example: `Project_1738540800000`

**Output Data Structure:**
```json
{
  "is_approval": false,
  "requirements": "Design a 3-phase motor controller...",
  "project_name": "Project_1738540800000",
  "system_type": "Motor_Control",
  "timestamp": 1738540800000,
  "phase": 1,
  "status": "requirements_received"
}
```

---

### Node 3: Is This Approval?

**Type:** `n8n-nodes-base.if` (Conditional)
**Purpose:** Routes to either requirements path or approval path

**Condition:**
```
$json.is_approval === false
```

**Branches:**
- **TRUE (is_approval = false):** New requirements → Build AI Prompt
- **FALSE (is_approval = true):** Approval response → Handle Approval

---

### Node 4: Build AI Prompt

**Type:** `n8n-nodes-base.code`
**Purpose:** Constructs AI prompt for requirements parsing

**Prompt Template:**
```
You are a hardware design expert. Parse these requirements and extract structured data.

SYSTEM TYPE DETECTED: {systemType}
REQUIREMENTS:
{requirements}

Extract and return ONLY valid JSON (no markdown, no explanation):

{
  "system_type": "{systemType}",
  "primary_components": {
    "processor": {
      "type": "FPGA/MCU/DSP/CPU",
      "specific_part": "part number if mentioned",
      "required_features": ["features needed"],
      "package": "package type"
    },
    "power": {
      "input_voltage": "input voltage",
      "output_power": "output power",
      "rails_needed": ["3.3V", "1.8V", etc]
    },
    "interfaces": ["Ethernet", "CAN", "USB", etc]
  },
  "specifications": {},
  "key_components_needed": [
    {"category": "processor", "description": "what's needed", "quantity": 1}
  ],
  "special_requirements": ["isolation", "EMI shielding"],
  "certifications_needed": ["RoHS", "CE", "FCC"],
  "environmental": {
    "temperature_range": "range",
    "protection_rating": "IP rating"
  }
}

RULES:
1. Be specific and technical
2. Use standard units (V, A, W, Hz)
3. Return ONLY JSON, no other text
4. All fields must be present
```

**Output:**
```json
{
  "ai_prompt": "...",
  "task_complexity": "high",
  "max_tokens": 3000,
  ...previous_data
}
```

---

### Node 5: AI: Parse Requirements

**Type:** `@n8n/n8n-nodes-langchain.agent`
**Purpose:** Uses LLM to extract structured data from requirements

**Configuration:**
```json
{
  "promptType": "define",
  "text": "={{ $json.ai_prompt }}",
  "options": {}
}
```

**Connected Model:** `OpenAI Chat Model (Parse)`
- Model: `glm-4.7` (or Claude API)
- Base URL: `https://api.z.ai/api/paas/v4`
- Version: 1.7

**Input:** AI prompt from Node 4
**Output:** AI-generated JSON with parsed requirements

**Example AI Response:**
```json
{
  "system_type": "Motor_Control",
  "primary_components": {
    "processor": {
      "type": "DSP",
      "specific_part": "TMS320F28379D",
      "required_features": ["PWM", "ADC", "Ethernet"],
      "package": "LQFP"
    },
    "power": {
      "input_voltage": "48V",
      "output_power": "10kW",
      "rails_needed": ["3.3V", "1.8V", "5V"]
    },
    "interfaces": ["Ethernet", "CAN", "RS485"]
  },
  ...
}
```

---

### Node 6: Extract Parsed Data

**Type:** `n8n-nodes-base.code`
**Purpose:** Extracts and validates AI response

**Logic:**

1. **Response Extraction**
   - Tries multiple fields: `output`, `choices[0].message.content`, `text`
   - Handles both object and string responses

2. **JSON Parsing**
   - Uses regex to find JSON: `/\{[\s\S]*\}/`
   - Parses JSON from text if needed

3. **Error Handling**
   - Falls back to default structure if parsing fails
   - Default: STM32F4-based Digital Controller

4. **Data Merging**
   - Combines AI output with original metadata
   - Preserves project name, timestamp

**Output:**
```json
{
  "parsed_requirements": {...},
  "original_requirements": "Design a 3-phase...",
  "project_name": "Project_1738540800000",
  "system_type": "Motor_Control",
  "timestamp": 1738540800000
}
```

---

### Node 7: Generate Block Diagram

**Type:** `n8n-nodes-base.code`
**Purpose:** Creates hardware block diagram from parsed data

**Algorithm:**

1. **Initialize Diagram Object**
   ```javascript
   const diagram = {
     version: '1.0',
     type: 'hardware_block_diagram',
     metadata: {...},
     blocks: [],
     connections: []
   };
   ```

2. **Add Processor Block**
   - Type: `processor`
   - Label: Specific part number or generic type
   - Position: Center (500, 300)

3. **Add Power Blocks**
   - Input power block (100, 100)
   - Voltage regulator for each rail
   - Auto-connect: Input → Regulators → Processor

4. **Add Interface Blocks**
   - One block per interface (Ethernet, CAN, etc.)
   - Position: Right side (800, 150+)
   - Connect to processor

5. **Generate ASCII Diagram**
   ```
   ╔════════════════════════════════════════╗
   ║  BLOCK DIAGRAM: Project_1738540800000  ║
   ╠════════════════════════════════════════╣
   ║  System Type: Motor_Control            ║
   ║  Total Blocks: 8                       ║
   ║  Connections: 12                       ║
   ╚════════════════════════════════════════╝

   MAIN COMPONENTS:
     1. TMS320F28379D (processor)
     2. Input 48V (power_input)
     3. Regulator 3.3V (power_regulator)
     4. Regulator 1.8V (power_regulator)
     5. Ethernet (interface)
     6. CAN (interface)

   CONNECTIONS:
     1. Input 48V → Regulator 3.3V
     2. Regulator 3.3V → TMS320F28379D
     ...
   ```

**Output:**
```json
{
  "block_diagram": {
    "blocks": [...],
    "connections": [...]
  },
  "ascii_diagram": "...",
  "awaiting_approval": true,
  ...previous_data
}
```

**Future Enhancement:**
- Export to PNG using draw.io/mermaid
- Export to draw.io XML format for editing
- Interactive web visualization

---

### Node 8: Show Diagram & Wait Approval

**Type:** `n8n-nodes-base.code`
**Purpose:** Displays diagram to user and requests approval

**Output Message:**
```
📋 **BLOCK DIAGRAM GENERATED**

╔════════════════════════════════════════╗
║  BLOCK DIAGRAM: Project_1738540800000  ║
╠════════════════════════════════════════╣
║  System Type: Motor_Control            ║
║  Total Blocks: 8                       ║
║  Connections: 12                       ║
╚════════════════════════════════════════╝

MAIN COMPONENTS:
  1. TMS320F28379D (processor)
  2. Input 48V (power_input)
  ...

✅ **Please review the block diagram above.**

**Options:**
- Type **"APPROVE"** to continue to component selection
- Type **"REJECT: <reason>"** to request changes

Waiting for your approval...
```

**Critical:** This node connects back to **Chat Trigger** (Node 1), creating an approval loop.

---

### Node 9: Handle Approval

**Type:** `n8n-nodes-base.code`
**Purpose:** Processes user approval response

**Logic:**

1. **Check Approval Action**
   ```javascript
   if (approvalMsg !== 'approve') {
     throw new Error('User did not approve. Workflow stopped.');
   }
   ```

2. **Retrieve Previous Data**
   - Uses n8n's `$('Node Name').item.json` syntax
   - Fetches block diagram from Node 7
   - Fetches parsed requirements from Node 6

3. **Pass Data Forward**
   ```json
   {
     "approved": true,
     "block_diagram": {...},
     "parsed_requirements": {...},
     "project_name": "...",
     "system_type": "..."
   }
   ```

**Error Handling:**
- If user types "REJECT", throws error and stops workflow
- User must restart with modified requirements

---

### Node 10: Build Component Searches

**Type:** `n8n-nodes-base.code`
**Purpose:** Generates search queries for component scraping

**Logic:**

1. **Processor Search**
   - Priority: 1 (highest)
   - Search term: Specific part number OR generic type
   - Example: `TMS320F28379D` or `MCU`

2. **Power Regulator Searches**
   - Priority: 2
   - One search per voltage rail
   - Example: `DC-DC converter 3.3V`

3. **Interface IC Searches**
   - Priority: 3
   - One search per interface
   - Example: `Ethernet transceiver IC`, `CAN transceiver IC`

**Output (Array):**
```javascript
[
  {
    category: 'processor',
    search_term: 'TMS320F28379D',
    priority: 1,
    project_name: '...',
    system_type: 'Motor_Control'
  },
  {
    category: 'power_regulator',
    search_term: 'DC-DC converter 3.3V',
    priority: 2,
    ...
  },
  {
    category: 'interface',
    search_term: 'Ethernet transceiver IC',
    priority: 3,
    ...
  }
]
```

**Typical Search Count:** 3-10 searches depending on system complexity

---

### Node 11: Split Searches (3 per batch)

**Type:** `n8n-nodes-base.splitInBatches`
**Purpose:** Batches searches to avoid overwhelming scraper API

**Configuration:**
```json
{
  "batchSize": 3,
  "options": {}
}
```

**Why Batching?**
- Each search takes 15-30 seconds
- Running sequentially would take too long
- Batches allow parallel execution with rate limiting
- Prevents timeout errors

**Example:**
- 9 searches → 3 batches of 3
- Each batch runs in parallel
- Total time: ~30-60 seconds (vs 4.5 minutes sequential)

---

### Node 12: Search Components (Real)

**Type:** `n8n-nodes-base.httpRequest`
**Purpose:** Calls Playwright scraper API to find components

**Configuration:**
```json
{
  "method": "POST",
  "url": "http://playwright:8000/api/scrape",
  "sendBody": true,
  "specifyBody": "json",
  "jsonBody": {
    "search_term": "{{ $json.search_term }}",
    "category": "{{ $json.category }}",
    "use_cache": true
  },
  "options": {
    "timeout": 60000
  },
  "retryOnFail": true,
  "maxTries": 3,
  "waitBetweenTries": 5000
}
```

**Retry Logic:**
- Max attempts: 3
- Wait between retries: 5 seconds
- Handles transient network errors
- Graceful degradation on failure

**API Response:**
```json
{
  "success": true,
  "search_term": "TMS320F28379D",
  "components": [
    {
      "part_number": "TMS320F28379DZPZT",
      "manufacturer": "Texas Instruments",
      "description": "C2000 32-bit MCU 200MHz...",
      "price": "$22.50",
      "availability": "In Stock",
      "datasheet": "https://...",
      "lifecycle_status": "Active",
      "source": "DigiKey"
    },
    ...
  ],
  "cache_hit": false,
  "execution_time": "18.3s"
}
```

**Component Sources:**
- DigiKey (parallel scraping)
- Mouser (parallel scraping)
- Returns top 5 from each = 10 total per search

---

### Node 13: Aggregate All Components

**Type:** `n8n-nodes-base.aggregate`
**Purpose:** Combines all component search results into single array

**Configuration:**
```json
{
  "aggregate": "aggregateAllItemData",
  "options": {}
}
```

**Input:** Multiple items from Node 12 (one per search)
**Output:** Single item with all components

**Example:**
- Search 1: 10 components (processor)
- Search 2: 10 components (3.3V regulator)
- Search 3: 10 components (Ethernet IC)
- **Aggregated:** 30 components total

---

### Node 14: Prepare Component Recommendations

**Type:** `n8n-nodes-base.code`
**Purpose:** Builds AI prompt for component selection

**Logic:**

1. **Extract All Components**
   ```javascript
   const allResults = $input.all();
   const allComponents = [];
   allResults.forEach(result => {
     if (result.json.components) {
       allComponents.push(...result.json.components);
     }
   });
   ```

2. **Build Recommendation Prompt**
   ```
   Analyze these component options and recommend the best choice for each category.

   Components found: 30

   1. TMS320F28379DZPZT - C2000 32-bit MCU... - $22.50
   2. TMS320F28379DPTPT - C2000 32-bit MCU... - $24.00
   ...
   15. (truncated to 15 components for prompt)

   For each category, recommend ONE component with brief rationale (1 sentence).

   Return JSON:
   {
     "recommendations": [
       {
         "category": "processor",
         "part_number": "XXX",
         "rationale": "Best balance of features and price"
       }
     ]
   }
   ```

**Output:**
```json
{
  "all_components": [...],
  "component_count": 30,
  "ai_prompt": "...",
  "max_tokens": 2000
}
```

---

### Node 15: AI: Recommend Components

**Type:** `@n8n/n8n-nodes-langchain.agent`
**Purpose:** Uses AI to select best components

**Connected Model:** `OpenAI Chat Model (Recommend)`

**AI Selection Criteria:**
1. **Feature Match** - Does it meet requirements?
2. **Lifecycle Status** - Active > NRND > Obsolete
3. **Availability** - In stock > Lead time
4. **Price** - Best value for requirements
5. **Manufacturer** - Reputable brands preferred
6. **Package** - Suitable for application

**Example AI Response:**
```json
{
  "recommendations": [
    {
      "category": "processor",
      "part_number": "TMS320F28379DZPZT",
      "rationale": "Exact match with required PWM, ADC, and Ethernet MAC. Active lifecycle, best value."
    },
    {
      "category": "power_regulator",
      "part_number": "TPS54339EDDAR",
      "rationale": "3.3V output, 3.5A capable, high efficiency, wide input range 48V compatible."
    },
    {
      "category": "interface",
      "part_number": "DP83867IRPAP",
      "rationale": "Gigabit Ethernet PHY, low power, TI ecosystem compatible with DSP."
    }
  ]
}
```

---

### Node 16: Generate BOM

**Type:** `n8n-nodes-base.code`
**Purpose:** Creates Bill of Materials with cost estimate

**Logic:**

1. **Retrieve All Components**
   - From Node 14: `all_components` array

2. **Calculate Total Cost**
   ```javascript
   let totalCost = 0;
   components.forEach(comp => {
     const priceMatch = comp.price.match(/\$?([0-9.]+)/);
     if (priceMatch) {
       totalCost += parseFloat(priceMatch[1]);
     }
   });
   ```

3. **Generate BOM Summary**
   ```
   ╔══════════════════════════════════════╗
   ║         BILL OF MATERIALS            ║
   ╠══════════════════════════════════════╣
   ║  Project: Project_1738540800000      ║
   ║  Total Components: 30                ║
   ║  Estimated Cost: $45.75              ║
   ╚══════════════════════════════════════╝

   TOP COMPONENTS:
   1. TMS320F28379DZPZT          $22.50
   2. TPS54339EDDAR              $ 3.25
   3. DP83867IRPAP               $ 8.00
   ...
   10. (showing top 10)

   ... and 20 more components
   ```

**Output:**
```json
{
  "project_name": "...",
  "bom_summary": "...",
  "total_components": 30,
  "total_cost": 45.75,
  "components": [...],
  "phase_1_complete": true
}
```

---

### Node 17: Show BOM & Complete

**Type:** `n8n-nodes-base.code`
**Purpose:** Displays final output to user

**Output Message:**
```
✅ **PHASE 1 COMPLETE**

╔══════════════════════════════════════╗
║         BILL OF MATERIALS            ║
╠══════════════════════════════════════╣
║  Project: Project_1738540800000      ║
║  Total Components: 30                ║
║  Estimated Cost: $45.75              ║
╚══════════════════════════════════════╝

TOP COMPONENTS:
1. TMS320F28379DZPZT          $22.50
2. TPS54339EDDAR              $ 3.25
...

📦 **Next Steps:**
- Phase 2: Generate HRS Document (50-70 pages)
- Phase 3: Compliance validation
- Phase 4: Netlist generation

Would you like to continue to Phase 2?
```

---

## User Interaction Flow

### Example Session

**User Input 1:**
```
Design a 3-phase motor controller with TMS320F28379D DSP,
10kW output power, 48V DC input, 0-400Hz output frequency,
Ethernet interface for monitoring, current sensing, and
temperature protection.
```

**Workflow Response 1:**
```
📋 **BLOCK DIAGRAM GENERATED**

╔════════════════════════════════════════╗
║  BLOCK DIAGRAM: Project_1738540800000  ║
╠════════════════════════════════════════╣
║  System Type: Motor_Control            ║
║  Total Blocks: 12                      ║
║  Connections: 18                       ║
╚════════════════════════════════════════╝

MAIN COMPONENTS:
  1. TMS320F28379D (processor)
  2. Input 48V (power_input)
  3. Regulator 3.3V (power_regulator)
  4. Regulator 1.8V (power_regulator)
  5. Ethernet (interface)
  6. Current Sensor (sensor)
  7. Temperature Sensor (sensor)
  8. Gate Driver (driver)

CONNECTIONS:
  1. Input 48V → Regulator 3.3V
  2. Regulator 3.3V → TMS320F28379D
  3. TMS320F28379D → Ethernet
  4. TMS320F28379D → Gate Driver
  5. Current Sensor → TMS320F28379D
  6. Temperature Sensor → TMS320F28379D
  ...

✅ **Please review the block diagram above.**

**Options:**
- Type **"APPROVE"** to continue to component selection
- Type **"REJECT: <reason>"** to request changes

Waiting for your approval...
```

**User Input 2:**
```
APPROVE
```

**Workflow Processing:**
```
[Internal execution - not shown to user]
- Building 8 component searches...
- Searching DigiKey and Mouser...
  ✓ TMS320F28379D: 10 components found
  ✓ DC-DC 3.3V: 10 components found
  ✓ DC-DC 1.8V: 10 components found
  ✓ Ethernet PHY: 10 components found
  ✓ Current sensor: 10 components found
  ✓ Temperature sensor: 10 components found
  ✓ Gate driver: 10 components found
  ✓ Isolator: 10 components found
- Total: 80 components found
- AI analyzing options...
- Generating BOM...
```

**Workflow Response 2:**
```
✅ **PHASE 1 COMPLETE**

╔══════════════════════════════════════╗
║         BILL OF MATERIALS            ║
╠══════════════════════════════════════╣
║  Project: Project_1738540800000      ║
║  Total Components: 80                ║
║  Estimated Cost: $156.25             ║
╚══════════════════════════════════════╝

TOP COMPONENTS:
1. TMS320F28379DZPZT          $22.50  (DSP Controller)
2. TPS54339EDDAR              $ 3.25  (3.3V Regulator)
3. TPS62177DQCT               $ 2.85  (1.8V Regulator)
4. DP83867IRPAP               $ 8.00  (Ethernet PHY)
5. INA240A1PWR                $ 1.75  (Current Sensor)
6. TMP1075NDRLR               $ 1.20  (Temperature Sensor)
7. UCC21520DW                 $12.50  (Isolated Gate Driver)
8. ISO7741DW                  $ 4.80  (Digital Isolator)
... and 72 more components

📦 **Next Steps:**
- Phase 2: Generate HRS Document (50-70 pages)
- Phase 3: Compliance validation (RoHS, CE, FCC)
- Phase 4: Netlist generation

Would you like to continue to Phase 2?
```

---

## Data Structures

### Input Data (User Requirements)

**Type:** String (Natural Language)

**Minimum Length:** 30 characters

**Example:**
```
Design a 3-phase motor controller with TMS320F28379D DSP,
10kW output power, 48V DC input, 0-400Hz output frequency,
Ethernet interface for monitoring, current sensing, and
temperature protection.
```

### Parsed Requirements (AI Output)

**Type:** JSON Object

**Schema:**
```json
{
  "system_type": "Motor_Control",
  "primary_components": {
    "processor": {
      "type": "DSP",
      "specific_part": "TMS320F28379D",
      "required_features": ["PWM", "ADC", "Ethernet", "EMIF"],
      "package": "LQFP"
    },
    "power": {
      "input_voltage": "48V",
      "output_power": "10kW",
      "rails_needed": ["3.3V", "1.8V", "5V", "15V"]
    },
    "interfaces": ["Ethernet", "CAN", "RS485"]
  },
  "specifications": {
    "frequency_range": "0-400Hz",
    "power_output": "10kW",
    "input_voltage": "48V DC"
  },
  "key_components_needed": [
    {"category": "processor", "description": "TMS320F28379D DSP", "quantity": 1},
    {"category": "gate_driver", "description": "Isolated gate driver for IGBTs", "quantity": 3},
    {"category": "current_sensor", "description": "Hall effect current sensor 50A", "quantity": 3},
    {"category": "temperature_sensor", "description": "Digital temperature sensor", "quantity": 2}
  ],
  "special_requirements": ["Isolation 2.5kV", "EMI filtering", "Overcurrent protection"],
  "certifications_needed": ["RoHS", "CE", "UL"],
  "environmental": {
    "temperature_range": "-20 to 70C",
    "protection_rating": "IP54"
  }
}
```

### Block Diagram (Generated)

**Type:** JSON Object

**Schema:**
```json
{
  "version": "1.0",
  "type": "hardware_block_diagram",
  "metadata": {
    "project": "Project_1738540800000",
    "system_type": "Motor_Control",
    "created": "2026-02-03T12:00:00.000Z"
  },
  "blocks": [
    {
      "id": "B1",
      "type": "processor",
      "label": "TMS320F28379D",
      "position": {"x": 500, "y": 300}
    },
    {
      "id": "B2",
      "type": "power_input",
      "label": "Input 48V",
      "position": {"x": 100, "y": 100}
    },
    {
      "id": "B3",
      "type": "power_regulator",
      "label": "Regulator 3.3V",
      "position": {"x": 100, "y": 200}
    }
  ],
  "connections": [
    {"from": "B2", "to": "B3", "label": "48V"},
    {"from": "B3", "to": "B1", "label": "3.3V"}
  ]
}
```

### Component Data (Scraper Output)

**Type:** JSON Array

**Schema:**
```json
[
  {
    "part_number": "TMS320F28379DZPZT",
    "manufacturer": "Texas Instruments",
    "description": "C2000 32-bit MCU 200MHz Dual-Core 1MB Flash",
    "price": "$22.50",
    "availability": "In Stock",
    "quantity_available": 5000,
    "datasheet": "https://www.ti.com/lit/ds/symlink/tms320f28379d.pdf",
    "lifecycle_status": "Active",
    "specifications": {
      "core": "C28x",
      "speed": "200MHz",
      "flash": "1MB",
      "ram": "204KB",
      "package": "LQFP-176"
    },
    "source": "DigiKey",
    "cache_hit": false,
    "scraped_at": "2026-02-03T12:05:23.000Z"
  }
]
```

### BOM (Final Output)

**Type:** JSON Object

**Schema:**
```json
{
  "project_name": "Project_1738540800000",
  "system_type": "Motor_Control",
  "created_at": "2026-02-03T12:08:45.000Z",
  "total_components": 80,
  "total_cost": 156.25,
  "currency": "USD",
  "components": [
    {
      "category": "processor",
      "part_number": "TMS320F28379DZPZT",
      "quantity": 1,
      "unit_price": 22.50,
      "total_price": 22.50
    }
  ],
  "phase_1_complete": true
}
```

---

## AI Integration

### AI Models Used

**Primary:**
- **Claude Sonnet 4.5** (Anthropic)
  - Best reasoning capability
  - Accurate component recommendations
  - Cost: $3/M input tokens, $15/M output tokens

**Alternative:**
- **GLM-4.7** (Zhipu AI)
  - Configured in workflow as fallback
  - Lower cost option
  - Base URL: `https://api.z.ai/api/paas/v4`

**Groq (Future):**
- Fast inference
- Llama 3/Mixtral models
- Cost-effective for simple tasks

### AI Tasks

1. **Requirements Parsing** (Node 5)
   - Input: Natural language requirements
   - Output: Structured JSON
   - Tokens: ~500-1000 input, ~800-1500 output

2. **Component Recommendation** (Node 15)
   - Input: List of 10-80 components
   - Output: Best component per category + rationale
   - Tokens: ~1500-3000 input, ~500-1000 output

### Token Usage Estimates

**Per Workflow Run:**
- Requirements parsing: 1,500-2,500 tokens total
- Component recommendation: 2,000-4,000 tokens total
- **Total:** ~3,500-6,500 tokens per project

**Cost Per Project:**
- Input: ~3,000 tokens × $3/M = $0.009
- Output: ~2,500 tokens × $15/M = $0.0375
- **Total:** ~$0.047 per project

**Annual (100 projects):**
- ~$4.70/year for Phase 1 only

---

## Component Scraping

### Scraper API Endpoints

**Base URL:** `http://playwright:8000`

**POST /api/scrape**
```json
{
  "search_term": "TMS320F28379D",
  "category": "processor",
  "use_cache": true
}
```

**Response:**
```json
{
  "success": true,
  "search_term": "TMS320F28379D",
  "components": [...],
  "cache_hit": false,
  "execution_time": "18.3s",
  "sources": ["DigiKey", "Mouser"]
}
```

### Caching Strategy

**Cache Duration:** 30 days

**Cache Key:** `search_term` + `category`

**Cache Hit Ratio:** Target 80%+

**Benefits:**
- Faster response (100ms vs 30s)
- Reduced load on distributor websites
- Consistent results for repeated searches

**Cache Invalidation:**
- Automatic expiry after 30 days
- Manual clear via `/api/cache/clear`
- Price staleness acceptable for design phase

---

## Error Handling

### Common Errors

**1. Requirements Too Short**
```
❌ Requirements must be at least 30 characters.

Please provide detailed hardware design requirements.

Example:
"Design a 3-phase motor controller with TMS320F28379D DSP,
10kW output power, 48V DC input, 0-400Hz output frequency,
Ethernet interface for monitoring, current sensing, and
temperature protection."
```

**2. User Rejects Diagram**
```
❌ Workflow stopped. User did not approve block diagram.

Please start over with updated requirements.
```

**3. Scraper API Timeout**
```
⚠️ Component search timed out after 60 seconds.
Retrying (attempt 2/3)...
```

**4. AI Parsing Failure**
```
⚠️ AI failed to parse requirements. Using default structure.

System Type: Digital_Controller
Processor: STM32F4 (default)
```

### Retry Logic

**Component Scraper (Node 12):**
- Max retries: 3
- Wait between: 5 seconds
- Timeout: 60 seconds

**Strategy:**
1. First attempt
2. Wait 5s → Retry
3. Wait 5s → Retry
4. Fail gracefully with partial results

### Graceful Degradation

**If scraper fails:**
- Continue with cached results only
- Use default component recommendations
- Notify user of limited data

**If AI fails:**
- Use rule-based fallback
- Default to common components (STM32, LM2596, etc.)
- Warn user to review carefully

---

## Output Artifacts

### 1. Block Diagram

**Format:** JSON + ASCII art

**Storage:** PostgreSQL `block_diagrams` table

**Schema:**
```sql
CREATE TABLE block_diagrams (
  id SERIAL PRIMARY KEY,
  project_name VARCHAR(255),
  diagram_data JSONB,
  created_at TIMESTAMP
);
```

**Future Formats:**
- PNG image (via draw.io export)
- draw.io XML (for editing)
- Mermaid diagram code

### 2. Bill of Materials (BOM)

**Format:** JSON

**Storage:** PostgreSQL `bom_items` table

**Schema:**
```sql
CREATE TABLE bom_items (
  id SERIAL PRIMARY KEY,
  project_name VARCHAR(255),
  part_number VARCHAR(100),
  quantity INTEGER,
  unit_price DECIMAL(10, 2),
  category VARCHAR(50),
  created_at TIMESTAMP
);
```

**Export Formats (Future):**
- Excel (.xlsx)
- CSV
- PDF report

### 3. Component Cache

**Format:** PostgreSQL JSONB

**Storage:** `component_cache` table

**Retention:** 30 days

---

## Usage Examples

### Example 1: RF Transceiver

**Input:**
```
Design a 2.4GHz wireless transceiver using Nordic nRF52840,
Bluetooth 5.0, antenna diversity, LiPo battery powered,
USB-C charging, temperature sensor, accelerometer.
```

**Detected Type:** `RF_Wireless`

**Components Found:**
- nRF52840 SoC
- Antenna switch
- Balun
- LiPo charger IC (MCP73831)
- USB-C connector
- BME280 sensor
- ADXL345 accelerometer

**BOM Cost:** ~$18.50

---

### Example 2: Industrial PLC

**Input:**
```
Industrial PLC with STM32F407, 8 digital inputs (24V),
4 relay outputs, Modbus RTU RS485, isolated I/O,
DIN rail mount, -40 to 85C operation.
```

**Detected Type:** `Industrial_Control`

**Components Found:**
- STM32F407 MCU
- Optocouplers (24V input)
- Relay drivers
- RS485 transceiver (isolated)
- DC-DC 24V to 5V/3.3V
- TVS diodes

**BOM Cost:** ~$32.75

---

### Example 3: Sensor Data Logger

**Input:**
```
Multi-channel data logger with 8x 16-bit ADC inputs,
SD card storage, RTC with battery backup,
LCD display, USB interface, 12V input.
```

**Detected Type:** `Sensor_System`

**Components Found:**
- ADS1115 (16-bit ADC)
- SD card interface
- DS3231 RTC
- ST7735 LCD
- FT232 USB-UART
- LM7805 regulator

**BOM Cost:** ~$24.00

---

## Recommendations for Enhancement

### Short-Term (0-3 months)

1. **Visual Block Diagram Export**
   - Integrate draw.io API
   - Export to PNG/SVG
   - Allow user editing

2. **GLB Generation (RF Systems)**
   - Detect RF frequency in requirements
   - Calculate gain/loss budget
   - Add to BOM as separate document

3. **Power Budget Calculation**
   - Sum component power consumption
   - Size power supply
   - Thermal analysis

4. **Database Persistence**
   - Save project to PostgreSQL
   - Resume interrupted workflows
   - Version control for iterations

### Medium-Term (3-6 months)

5. **Advanced Component Filtering**
   - Lifecycle status preference
   - Preferred manufacturers
   - Cost optimization mode
   - Availability threshold

6. **Multi-Approval Gates**
   - Gate 2: BOM approval before HRS
   - Edit mode: Modify components
   - Alternative selection UI

7. **Compliance Pre-Check**
   - RoHS validation
   - REACH substance check
   - ITAR flagging

### Long-Term (6-12 months)

8. **ML-Based Component Recommendation**
   - Train on historical projects
   - Learn from user preferences
   - Predict optimal choices

9. **Parametric Search Integration**
   - Direct API to Octopart
   - DigiKey/Mouser APIs
   - Real-time pricing

10. **Cost Optimization Engine**
    - Alternative component suggestions
    - Volume pricing analysis
    - Supply chain risk assessment

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-15 | Initial workflow (RF-specific) |
| 2.0 | 2026-02-03 | Universal system support, approval gate |

---

## Related Documents

- [REPOSITORY_ANALYSIS.md](./REPOSITORY_ANALYSIS.md) - Full system analysis
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Deployment instructions
- [Hardware_Pipeline_Tech_Stack.md](./Hardware_Pipeline_Tech_Stack.md) - Technology details
- [Phase1_Workflow_Usage_Guide.md](./Phase1_Workflow_Usage_Guide.md) - User guide

---

**Document Version:** 1.0
**Created:** February 3, 2026
**Author:** Hardware Pipeline Team
**Repository:** bala9066/S2S
**Branch:** claude/analyze-repo-files-TXseP
