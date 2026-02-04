# Hardware Pipeline - Detailed Phase-by-Phase Architecture

## Complete System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                         │
│  React Frontend / n8n Chat Interface / Streamlit Dashboard      │
└────────────┬────────────────────────────────────────────────────┘
             │
             ↓ Natural Language Requirements
┌────────────────────────────────────────────────────────────────┐
│                   n8n ORCHESTRATION LAYER                       │
│  Manages workflow state, routes between phases, error handling  │
└────────────┬───────────────────────────────────────────────────┘
             │
             ↓
┌────────────────────────────────────────────────────────────────┐
│                   8 PHASES (6 Automated, 2 Manual)              │
│  Phase 1-4 → Phase 5 (Manual) → Phase 6 → Phase 7 (Manual) → 8 │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔹 PHASE 1: Requirements Capture & Component Selection

**Duration:** ~90 seconds (automated)
**Status:** ✅ Fully Implemented

### Architecture Flow

```
User Input (Natural Language)
        ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Validate Input & Detect Type"   │
│  - JavaScript code execution                 │
│  - Regex pattern matching for system type   │
│  - Input validation (min 30 chars)          │
└──────────────┬───────────────────────────────┘
               ↓ {requirements, system_type, project_name}
┌──────────────────────────────────────────────┐
│  n8n Node: "Build AI Prompt"                 │
│  - Loads improved_ai_prompt.js template     │
│  - 3,900 token comprehensive prompt         │
│  - Instructs 12+ category extraction        │
└──────────────┬───────────────────────────────┘
               ↓ {ai_prompt, max_tokens: 4000}
┌──────────────────────────────────────────────┐
│  Claude API (Sonnet 4.5) via n8n Agent      │
│  - Processes requirements                    │
│  - Extracts 12+ component categories        │
│  - Infers missing components                │
│  - Returns structured JSON                   │
└──────────────┬───────────────────────────────┘
               ↓ JSON response (~1500 tokens)
┌──────────────────────────────────────────────┐
│  n8n Node: "Extract Parsed Data"            │
│  - Parses AI JSON response                  │
│  - Validates structure                       │
│  - Handles errors with defaults             │
└──────────────┬───────────────────────────────┘
               ↓ {parsed_requirements}
┌──────────────────────────────────────────────┐
│  n8n Node: "Generate Block Diagram"         │
│  - Loads improved_block_diagram_generator.js│
│  - Creates 20-35 blocks                     │
│  - Maps 25-45 connections                   │
│  - Generates ASCII + JSON diagram           │
└──────────────┬───────────────────────────────┘
               ↓ {block_diagram, ascii_diagram}
┌──────────────────────────────────────────────┐
│  n8n Node: "Show Diagram & Wait Approval"   │
│  - Displays diagram to user                 │
│  - Workflow PAUSES here                     │
│  - Waits for "APPROVE" or "REJECT"          │
└──────────────┬───────────────────────────────┘
               ↓ User types "APPROVE"
┌──────────────────────────────────────────────┐
│  n8n Node: "Handle Approval"                 │
│  - Validates approval action                │
│  - Passes block diagram forward             │
└──────────────┬───────────────────────────────┘
               ↓ {approved: true, block_diagram}
┌──────────────────────────────────────────────┐
│  n8n Node: "Build Component Searches"       │
│  - Extracts component categories            │
│  - Creates search queries per category      │
│  - Returns array of search tasks            │
└──────────────┬───────────────────────────────┘
               ↓ [{category, search_term}, ...]
┌──────────────────────────────────────────────┐
│  n8n Node: "Split Searches (3 per batch)"   │
│  - Batches searches for parallel execution  │
└──────────────┬───────────────────────────────┘
               ↓ Batches of 3 searches
┌──────────────────────────────────────────────┐
│  n8n Node: "Search Components (Real)"       │
│  HTTP POST: http://playwright:8000/api/scrape│
│  Body: {search_term, category, use_cache}   │
└──────────────┬───────────────────────────────┘
               ↓
    ┌──────────▼──────────────────────────────┐
    │   FastAPI REST API (scraper_api.py)     │
    │   Port 8000, Docker container           │
    │                                         │
    │   Endpoints:                            │
    │   - POST /api/scrape                    │
    │   - GET /api/health                     │
    │   - GET /api/cache/status               │
    └──────────┬──────────────────────────────┘
               ↓
    ┌──────────▼──────────────────────────────┐
    │   PostgreSQL Cache Check                │
    │   Query: SELECT FROM component_cache    │
    │   WHERE search_term = $1                │
    │   AND expires_at > NOW()                │
    └──────────┬──────────────────────────────┘
               │
         ┌─────┴─────┐
         │           │
    Cache HIT    Cache MISS
         │           │
         ↓           ↓
    Return      ┌────────────────────────────┐
    cached      │  Playwright Scraper        │
    data        │  (component_scraper.py)    │
                │  - Launches Chromium       │
                │  - Scrapes DigiKey/Mouser  │
                │  - Extracts: part number,  │
                │    description, price,     │
                │    availability, lifecycle │
                │  - 95% success rate        │
                └──────────┬─────────────────┘
                           ↓
                ┌──────────▼─────────────────┐
                │  Store in PostgreSQL       │
                │  INSERT INTO component_cache│
                │  expires_at = NOW() + 30d  │
                └──────────┬─────────────────┘
                           │
         ┌─────────────────┘
         ↓
    Return scraped data to n8n
         ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Aggregate All Components"       │
│  - Collects results from all batches       │
│  - Merges into single array                │
└──────────────┬───────────────────────────────┘
               ↓ {all_components: [...]}
┌──────────────────────────────────────────────┐
│  n8n Node: "Prepare Component Recommendations"│
│  - Builds AI prompt for selection          │
│  - Includes component details              │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  Claude API: "AI: Recommend Components"     │
│  - Analyzes options                         │
│  - Recommends best choices                  │
│  - Provides rationale                       │
└──────────────┬───────────────────────────────┘
               ↓ {recommendations: [...]}
┌──────────────────────────────────────────────┐
│  n8n Node: "Generate BOM"                   │
│  - Creates BOM summary                      │
│  - Calculates total cost                   │
│  - Formats ASCII table                      │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Show BOM & Complete"            │
│  - Displays final BOM                       │
│  - Offers to continue to Phase 2           │
└───────────────────────────────────────────────┘
```

### Data Structures

**Input:**
```json
{
  "chatInput": "Design 3-phase motor controller with TMS320F28379D DSP, 10kW..."
}
```

**Parsed Requirements (after Claude):**
```json
{
  "system_type": "Motor_Control",
  "system_overview": {
    "purpose": "3-phase motor control system",
    "key_functionality": ["PWM generation", "current sensing", "protection"]
  },
  "primary_components": {
    "processor": {
      "type": "DSP",
      "specific_part": "TMS320F28379D",
      "required_features": ["PWM", "ADC", "QEP", "CAN"]
    },
    "power_system": {
      "input_voltage": "48V",
      "rails_needed": [
        {"voltage": "5V", "current": "2A", "purpose": "gate drivers"},
        {"voltage": "3.3V", "current": "1.5A", "purpose": "DSP core"}
      ]
    },
    "power_stage": {
      "switches": {"type": "MOSFET", "quantity": 6},
      "gate_drivers": {"type": "isolated", "channels": 6}
    },
    "analog_signal_chain": {
      "adc": {"resolution": "16-bit", "channels": 8},
      "sensors": [
        {"type": "current", "interface": "analog", "method": "hall effect"}
      ]
    }
  }
}
```

**Block Diagram Output:**
```json
{
  "version": "2.0",
  "blocks": [
    {"id": "B1", "type": "processor", "label": "TMS320F28379D"},
    {"id": "B2", "type": "power_input", "label": "Input 48V"},
    {"id": "B3", "type": "power_regulator", "label": "5V @ 2A"},
    {"id": "B4", "type": "gate_driver", "label": "Gate Driver (6ch)"},
    // ... 20+ more blocks
  ],
  "connections": [
    {"from": "B2", "to": "B3", "label": "48V", "type": "power"},
    {"from": "B3", "to": "B1", "label": "5V", "type": "power"},
    // ... 30+ more connections
  ]
}
```

### Database Operations

**Tables Used:**
- `projects`: INSERT new project record
- `block_diagrams`: INSERT diagram JSON + version
- `component_cache`: SELECT for cache lookups
- `component_recommendations`: INSERT AI recommendations
- `api_usage`: INSERT Claude API usage metrics

**SQL Example:**
```sql
-- Cache lookup
SELECT * FROM component_cache
WHERE search_term = 'TMS320F28379D'
  AND category = 'processor'
  AND expires_at > NOW();

-- Insert new project
INSERT INTO projects (project_name, system_type, requirements, status, phase_completed)
VALUES ('Project_1738454400000', 'Motor_Control', '...', 'in_progress', 1);

-- Store block diagram
INSERT INTO block_diagrams (project_id, version, diagram_json, created_at)
VALUES (uuid, '2.0', '{"blocks": [...]}', NOW());
```

---

## 🔹 PHASE 2: HRS Document Generation

**Duration:** ~30 seconds (automated)
**Status:** ⚠️ Partially Implemented (template exists, full automation pending)

### Architecture Flow

```
Block Diagram + BOM from Phase 1
        ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Extract HRS Requirements"       │
│  - Reads block_diagram JSON                 │
│  - Reads parsed_requirements                │
│  - Reads BOM data                           │
│  - Prepares HRS sections                    │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Add Pin Assignments"            │
│  - Queries component datasheets             │
│  - Looks up pin numbers                     │
│  - Adds to block diagram                    │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Build HRS Sections"             │
│  - System Overview (2-3 pages)              │
│  - Block Diagram with annotations (5 pages) │
│  - Component Details (20-30 pages)          │
│  - Electrical Specs (10-15 pages)           │
│  - Power Analysis (5-10 pages)              │
│  - Interface Specs (10-15 pages)            │
│  - BOM Table (3-5 pages)                    │
│  - Test Requirements (5-10 pages)           │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  Python Script: HRS Document Generator      │
│  Library: python-docx                       │
│                                             │
│  Process:                                   │
│  1. Create Document() object                │
│  2. Add title page with metadata           │
│  3. Add table of contents                  │
│  4. For each section:                       │
│     - Add heading                           │
│     - Add paragraphs                        │
│     - Add tables (BOM, specs)               │
│     - Add images (block diagrams)           │
│  5. Apply styles and formatting            │
│  6. Generate page numbers                   │
│  7. Save as .docx file                      │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  File Storage: /outputs/                    │
│  - HRS_Project_[timestamp].docx (50-100 pages)│
│  - Block_Diagram_Detailed.drawio            │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  Database: phase_outputs table              │
│  INSERT (project_id, phase=2,               │
│          output_type='HRS',                 │
│          file_path='...docx',               │
│          page_count=70)                     │
└───────────────────────────────────────────────┘
```

### HRS Document Structure

```
Hardware Requirements Specification (HRS)
├── Cover Page (1 page)
│   └── Project name, date, version, system type
├── Table of Contents (2 pages)
├── 1. System Overview (3-5 pages)
│   ├── 1.1 Purpose and Scope
│   ├── 1.2 System Architecture
│   └── 1.3 Key Functionality
├── 2. Block Diagram (5-8 pages)
│   ├── 2.1 High-Level Architecture
│   ├── 2.2 Component Placement
│   └── 2.3 Signal Flow
├── 3. Component Details (20-30 pages)
│   ├── 3.1 Processor/FPGA Specifications
│   ├── 3.2 Power Components
│   ├── 3.3 Interface ICs
│   ├── 3.4 Analog Components
│   └── 3.5 Passives and Connectors
├── 4. Electrical Specifications (10-15 pages)
│   ├── 4.1 Power Budget Analysis
│   ├── 4.2 Voltage Rails
│   ├── 4.3 Current Requirements
│   └── 4.4 Thermal Analysis
├── 5. Interface Specifications (10-15 pages)
│   ├── 5.1 Digital Interfaces (SPI, I2C, UART)
│   ├── 5.2 High-Speed Interfaces (Ethernet, USB, PCIe)
│   ├── 5.3 Analog Interfaces
│   └── 5.4 RF Interfaces (if applicable)
├── 6. Bill of Materials (3-5 pages)
│   └── Complete BOM table with pricing
├── 7. Test Requirements (5-10 pages)
│   ├── 7.1 Functional Tests
│   ├── 7.2 Performance Tests
│   └── 7.3 Compliance Tests
└── Appendices (5-10 pages)
    ├── A. Component Datasheets References
    └── B. Calculations and Analysis
```

### Python Code Snippet

```python
from docx import Document
from docx.shared import Inches, Pt

def generate_hrs(project_data, block_diagram, bom):
    doc = Document()

    # Title page
    doc.add_heading('Hardware Requirements Specification', 0)
    doc.add_paragraph(f"Project: {project_data['project_name']}")
    doc.add_paragraph(f"System Type: {project_data['system_type']}")

    # System Overview
    doc.add_heading('1. System Overview', 1)
    doc.add_paragraph(project_data['purpose'])

    # Block Diagram
    doc.add_heading('2. Block Diagram', 1)
    # Add diagram image
    doc.add_picture('block_diagram.png', width=Inches(6))

    # Component Details
    doc.add_heading('3. Component Details', 1)
    for component in bom['components']:
        doc.add_heading(f"3.{idx} {component['part_number']}", 2)
        doc.add_paragraph(f"Description: {component['description']}")
        # ... add specs table

    # Save
    doc.save(f"HRS_{project_data['project_name']}.docx")
```

---

## 🔹 PHASE 3: Compliance Validation

**Duration:** ~15 seconds (automated)
**Status:** ⚠️ Template exists, full automation pending

### Architecture Flow

```
BOM from Phase 1
        ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Extract Compliance Requirements" │
│  - User requirements (RoHS, CE, FCC, etc.)  │
│  - Geographic markets (US, EU, China)       │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  For Each Component in BOM:                  │
│  ┌────────────────────────────────────────┐  │
│  │ Check Compliance Databases             │  │
│  │ - RoHS compliance (EU)                 │  │
│  │ - REACH substances check               │  │
│  │ - FCC certification (US RF devices)    │  │
│  │ - CE marking requirements              │  │
│  │ - Medical (IEC 60601 if applicable)    │  │
│  │ - Automotive (ISO 26262 if applicable) │  │
│  └────────────────────────────────────────┘  │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  Database Queries:                           │
│  - Query compliance_records table           │
│  - Check certification status               │
│  - Identify non-compliant parts             │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  Generate Compliance Report                  │
│  - Summary (pass/fail per standard)         │
│  - Detailed component compliance            │
│  - Non-compliant items flagged              │
│  - Recommended alternatives                 │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  Output: Compliance_Report.xlsx             │
│  Sheets:                                    │
│  1. Summary                                 │
│  2. RoHS Compliance                         │
│  3. REACH Substances                        │
│  4. FCC/CE Certifications                   │
│  5. Recommendations                         │
└───────────────────────────────────────────────┘
```

### Compliance Check Matrix

```
Component | RoHS | REACH | FCC | CE | Medical | Auto | Status
----------|------|-------|-----|----|---------|----- |-------
TMS320F28 | ✅   | ✅    | N/A | ✅ | ✅      | ✅   | PASS
Gate Drvr | ✅   | ✅    | N/A | ✅ | ⚠️      | ✅   | WARN
MOSFET    | ✅   | ✅    | N/A | ✅ | ✅      | ✅   | PASS
```

---

## 🔹 PHASE 4: Netlist Generation

**Duration:** ~40 seconds (automated)
**Status:** ⚠️ Logic exists, EDIF generation pending

### Architecture Flow

```
Block Diagram with Pin Assignments from Phase 2
        ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Read Block Diagram"             │
│  - Load block_diagram JSON                  │
│  - Load component pin assignments           │
│  - Load connection list                     │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Lookup Component Datasheets"    │
│  For each component:                        │
│  - Query datasheet database                 │
│  - Extract pinout information               │
│  - Map logical names to physical pins       │
│  Example:                                   │
│    TMS320F28379D Pin 23 = GPIO0             │
│    Gate Driver Pin 5 = PWM_IN1              │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Generate Net List"              │
│  Process:                                   │
│  1. Assign reference designators            │
│     (U1, U2, R1, C1, etc.)                  │
│  2. Create nets from connections            │
│     Connection: Processor → Gate Driver     │
│     Becomes: NET PWM1 U1.23 U2.5            │
│  3. Handle power nets (VCC, GND)            │
│  4. Handle differential pairs (DDR, USB)    │
│  5. Validate:                               │
│     - No floating pins                      │
│     - All power pins connected              │
│     - High-speed pairs matched              │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  Python Script: netlist_generator.py        │
│  Libraries: networkx, edifparser            │
│                                             │
│  Generate TWO formats:                      │
│                                             │
│  1. EDIF Format (.edif):                    │
│     (edif netlist_name                      │
│       (edifVersion 2 0 0)                   │
│       (edifLevel 0)                         │
│       (library library_name                 │
│         (cell component_name                │
│           (cellType GENERIC)                │
│           (view view_name                   │
│             (viewType NETLIST)              │
│             (interface                      │
│               (port pin_name ...)           │
│             (contents                       │
│               (instance inst_name ...)      │
│               (net net_name ...)            │
│     )                                       │
│                                             │
│  2. Excel Format (.xlsx):                   │
│     Sheet 1: Nets                           │
│     Sheet 2: Components                     │
│     Sheet 3: Pin Assignments                │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  Validate Netlist                           │
│  - Run DRC (Design Rule Check)              │
│  - Verify all connections                   │
│  - Check for shorts                         │
│  - Validate power distribution              │
│  - Check signal integrity rules             │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  Output Files:                              │
│  - /outputs/netlist.edif                    │
│  - /outputs/netlist.xlsx                    │
│  - /outputs/netlist_validation_report.txt   │
└───────────────────────────────────────────────┘
```

### Netlist Data Structure

**Nets (connections):**
```
NET_NAME     | NODES
-------------|------------------------
VCC_5V       | U1.1 U2.1 C1.1 C2.1
GND          | U1.2 U2.2 C1.2 C2.2
PWM1         | U1.23 U2.5
PWM2         | U1.24 U2.6
CURRENT_SENSE| U1.67 U3.3 R5.1
```

**Components (reference designators):**
```
REF_DES | PART_NUMBER   | VALUE    | PACKAGE
--------|---------------|----------|--------
U1      | TMS320F28379D | -        | LQFP176
U2      | UCC21520      | -        | SOIC8
U3      | INA240        | -        | SOT23-6
R1      | 0603          | 10k      | 0603
C1      | 0805          | 10uF     | 0805
```

**Excel Sheet 3: Pin Assignments**
```
Component | Pin# | Pin Name  | Net Name     | Connected To
----------|------|-----------|--------------|-------------
U1        | 23   | GPIO0     | PWM1         | U2 Pin 5
U1        | 24   | GPIO1     | PWM2         | U2 Pin 6
U1        | 67   | ADC_IN0   | CURRENT_SENSE| U3 Pin 3
U2        | 1    | VCC       | VCC_5V       | C1 Pin 1
U2        | 2    | GND       | GND          | C1 Pin 2
```

---

## 🔹 PHASE 5: PCB Design (Manual - User)

**Duration:** User-dependent (4-12 weeks typical)
**Status:** ✅ Defined workflow, user performs manually

### Architecture Flow

```
┌──────────────────────────────────────────────┐
│  USER RECEIVES:                              │
│  - netlist.edif                             │
│  - Block diagram                            │
│  - HRS document                             │
│  - BOM                                      │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  USER STEP 1: Import to EDA Tool            │
│  ┌────────────────────────────────────────┐  │
│  │ Altium Designer:                       │  │
│  │  File → Import → EDIF netlist          │  │
│  │ Xpedition:                             │  │
│  │  File → Import → Netlist → EDIF        │  │
│  │ KiCad:                                 │  │
│  │  Tools → Update PCB from Schematic     │  │
│  └────────────────────────────────────────┘  │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  EDA Tool Auto-Generates Schematic           │
│  - Places components                        │
│  - Draws connections from netlist           │
│  - User reviews and adjusts                 │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  USER STEP 2: Design PCB Layout             │
│  - Select board stackup (2-8 layers)       │
│  - Place components                         │
│  - Route traces                             │
│  - Add copper pours (GND/power planes)      │
│  - Run DRC (Design Rule Check)              │
│  - Generate Gerber files                    │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  OUTPUT:                                     │
│  - Schematic.pdf                            │
│  - PCB Layout files                         │
│  - Gerber files (for fabrication)           │
│  - BOM (updated from layout)                │
└───────────────────────────────────────────────┘
```

**Note:** Phase 5 automation (AI-powered PCB layout) is FUTURE SCOPE (Phase 2 of project).

---

## 🔹 PHASE 6: GLR (Glue Logic Requirements) Generation

**Duration:** ~40 seconds (automated)
**Status:** ⚠️ Logic defined, full automation pending

### Architecture Flow

```
Block Diagram + Netlist from Phase 4
        ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Identify FPGA I/O Requirements"  │
│  - Extract FPGA/processor from block diagram│
│  - Identify all interface connections       │
│  - Determine I/O types needed               │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Build GLR Table"                 │
│  For each interface:                        │
│  ┌────────────────────────────────────────┐  │
│  │ Signal Name                            │  │
│  │ Pin Number                             │  │
│  │ Direction (input/output/bidir)         │  │
│  │ Voltage Level (3.3V, 1.8V, LVDS)       │  │
│  │ Drive Strength (2mA, 4mA, 8mA)         │  │
│  │ Pull-up/down requirement               │  │
│  │ Timing constraints                     │  │
│  │ Special requirements (differential)    │  │
│  └────────────────────────────────────────┘  │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  Claude API: "Generate I/O Specs"            │
│  - Analyze interface types                  │
│  - Determine electrical requirements        │
│  - Generate timing diagrams (if needed)     │
│  - Add notes and recommendations            │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  Python Script: GLR Generator                │
│  Library: openpyxl                          │
│                                             │
│  Generate GLR.xlsx with sheets:             │
│  1. Summary (overview of all I/O)          │
│  2. Digital I/O (GPIO, SPI, I2C, UART)      │
│  3. High-Speed I/O (DDR, Ethernet, PCIe)    │
│  4. Analog I/O (ADC, DAC)                   │
│  5. Power and Ground pins                   │
│  6. Programming/Debug pins (JTAG)           │
│  7. Timing Diagrams                         │
│  8. Register Map (placeholder for Phase 7)  │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  Output: GLR_Project_[timestamp].xlsx       │
│  This becomes THE specification for         │
│  FPGA/MCU implementation in Phase 7         │
└───────────────────────────────────────────────┘
```

### GLR Excel Structure

**Sheet 1: Digital I/O**
```
Signal   | Pin# | Dir | Voltage | Drive | Pull | Speed  | Notes
---------|------|-----|---------|-------|------|--------|-------
SPI_CLK  | A5   | OUT | 3.3V    | 8mA   | None | 10MHz  | To flash
SPI_MISO | A6   | IN  | 3.3V    | -     | None | 10MHz  | From flash
SPI_MOSI | A7   | OUT | 3.3V    | 4mA   | None | 10MHz  | To flash
SPI_CS   | A8   | OUT | 3.3V    | 4mA   | Up   | -      | Active low
```

**Sheet 2: High-Speed I/O**
```
Signal    | Pin# | Type        | Voltage | Impedance | Termination
----------|------|-------------|---------|-----------|------------
DDR_DQ0   | B12  | Bidirectional| 1.5V   | 50Ω      | On-die
DDR_DQ1   | B13  | Bidirectional| 1.5V   | 50Ω      | On-die
DDR_CK_P  | C1   | Differential| 1.5V   | 100Ω     | External
DDR_CK_N  | C2   | Differential| 1.5V   | 100Ω     | External
```

---

## 🔹 PHASE 7: FPGA/MCU HDL Implementation (Manual - User)

**Duration:** User-dependent (4-12 weeks for FPGA)
**Status:** ✅ Defined workflow, user performs manually

### Architecture Flow

```
┌──────────────────────────────────────────────┐
│  USER RECEIVES:                              │
│  - GLR.xlsx (complete I/O specifications)   │
│  - Block diagram                            │
│  - HRS document                             │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  USER STEP 1: Create FPGA/MCU Project       │
│  FPGA (Xilinx Vivado / Intel Quartus):     │
│    - Create new project                     │
│    - Select device from BOM                 │
│    - Import pin constraints from GLR        │
│  MCU (Code Composer / STM32Cube):           │
│    - Create new project                     │
│    - Configure peripherals from GLR         │
│    - Generate initialization code           │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  USER STEP 2: Write HDL Code (FPGA)         │
│  or Firmware (MCU)                          │
│                                             │
│  For FPGA (Verilog/VHDL):                   │
│  - Write top-level module                  │
│  - Implement interfaces (SPI, I2C, etc.)    │
│  - Write control logic                      │
│  - Add state machines                       │
│  - Create register map                      │
│                                             │
│  For MCU (C/C++):                           │
│  - Configure clock tree                     │
│  - Initialize peripherals                   │
│  - Write interrupt handlers                 │
│  - Implement protocol stacks                │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  USER STEP 3: Synthesis & Testing           │
│  FPGA:                                      │
│    - Run synthesis                          │
│    - Place and route                        │
│    - Generate bitstream                     │
│    - Timing analysis                        │
│  MCU:                                       │
│    - Compile firmware                       │
│    - Link libraries                         │
│    - Generate binary/hex file               │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  USER STEP 4: Create Register Map           │
│  Document all registers:                    │
│  - Address                                  │
│  - Bit fields                               │
│  - Access type (R/W/RO)                     │
│  - Reset value                              │
│  - Description                              │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  OUTPUT:                                     │
│  - HDL source files (.v, .vhd) or firmware  │
│  - Bitstream (.bit) or binary (.bin)        │
│  - Register map (for Phase 8)               │
└───────────────────────────────────────────────┘
```

**Note:** Phase 7 automation (AI-generated HDL/firmware) is FUTURE SCOPE (Phase 2 of project).

---

## 🔹 PHASE 8: Software Generation & Code Review

**Duration:** ~60 seconds (automated)
**Status:** ✅ Fully Implemented

### Architecture Flow

```
Register Map + GLR from Phase 7
        ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Extract Register Map"           │
│  - Parse register addresses                 │
│  - Extract bit fields                       │
│  - Identify access types (R/W/RO)           │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Build Driver Generation Prompt" │
│  - Include register map                     │
│  - Include interface specifications         │
│  - Specify language (C/C++)                 │
│  - Request error handling                   │
│  - Request test generation                  │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  Claude API: "Generate Drivers"              │
│  Generates:                                 │
│  - Hardware abstraction layer (HAL)         │
│  - Register access functions                │
│  - Error handling                           │
│  - Bounds checking                          │
│  - Logging/debug functions                  │
│  - Example usage code                       │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "AI Code Review"                 │
│  Tools chained:                             │
│  ┌────────────────────────────────────────┐  │
│  │ 1. SonarQube Analysis                  │  │
│  │    - Code complexity                   │  │
│  │    - Code smells                       │  │
│  │    - Maintainability index             │  │
│  │    Output: quality_score (0-10)        │  │
│  ├────────────────────────────────────────┤  │
│  │ 2. Semgrep Security Scan               │  │
│  │    - Buffer overflows                  │  │
│  │    - SQL injection                     │  │
│  │    - XSS vulnerabilities               │  │
│  │    Output: vulnerability_list          │  │
│  ├────────────────────────────────────────┤  │
│  │ 3. MISRA-C Compliance Check            │  │
│  │    - Checks embedded C standards       │  │
│  │    - Safety-critical rules             │  │
│  │    Output: compliance_percentage       │  │
│  ├────────────────────────────────────────┤  │
│  │ 4. Clang-Tidy Static Analysis          │  │
│  │    - Memory leaks                      │  │
│  │    - Null pointer dereferences         │  │
│  │    - Use-after-free                    │  │
│  │    Output: defect_list                 │  │
│  └────────────────────────────────────────┘  │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Fix Issues if Found"            │
│  If quality_score < 8.0:                    │
│    - Claude API: "Fix code issues"          │
│    - Re-run code review                     │
│    - Iterate until passing                  │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Generate Qt GUI"                 │
│  Claude API generates:                      │
│  - Main window UI (.ui file)                │
│  - Control widgets (buttons, sliders)       │
│  - Status displays                          │
│  - Signal/slot connections                  │
│  - Integration with HAL drivers             │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Generate Tests"                  │
│  Claude API generates:                      │
│  - Unit tests (pytest/gtest)                │
│  - Integration tests                        │
│  - Mock hardware drivers                    │
│  - Test fixtures                            │
│  - Coverage targets                         │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  n8n Node: "Git Integration"                 │
│  Process:                                   │
│  1. Initialize Git repo (if new)            │
│  2. Create feature branch                   │
│  3. Stage all generated files               │
│  4. Generate meaningful commit message:     │
│     "feat: add hardware drivers for [device]"│
│     "- Add register access functions"       │
│     "- Implement error handling"            │
│     "- Generate unit tests"                 │
│     "- Quality score: 8.5/10"               │
│     "- MISRA-C compliance: 98%"             │
│  5. Commit with metadata                    │
│  6. Push to remote (if configured)          │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│  Output Files:                               │
│  /outputs/software/                         │
│  ├── src/                                   │
│  │   ├── hal_driver.c                      │
│  │   ├── hal_driver.h                      │
│  │   └── device_control.c                  │
│  ├── gui/                                   │
│  │   ├── main_window.ui                    │
│  │   └── main_window.cpp                   │
│  ├── tests/                                 │
│  │   ├── test_hal.cpp                      │
│  │   └── mock_hardware.cpp                 │
│  ├── docs/                                  │
│  │   ├── API_Documentation.md              │
│  │   └── User_Guide.md                     │
│  ├── code_review_report.txt                │
│  └── .git/ (Git repository)                │
└───────────────────────────────────────────────┘
```

### Code Review Output Example

```
╔══════════════════════════════════════════════╗
║         AUTOMATED CODE REVIEW REPORT         ║
╠══════════════════════════════════════════════╣
║  Project: Motor_Controller_Drivers           ║
║  Date: 2026-02-04                           ║
║  Files Analyzed: 12                          ║
╚══════════════════════════════════════════════╝

QUALITY METRICS:
┌────────────────────────────┬─────────┬────────┐
│ Metric                     │ Score   │ Status │
├────────────────────────────┼─────────┼────────┤
│ Code Complexity            │ 8.2/10  │ ✅ PASS│
│ Maintainability Index      │ 85/100  │ ✅ PASS│
│ Test Coverage              │ 92%     │ ✅ PASS│
│ Documentation Coverage     │ 88%     │ ✅ PASS│
│ MISRA-C Compliance         │ 98%     │ ✅ PASS│
└────────────────────────────┴─────────┴────────┘

SECURITY SCAN (Semgrep):
✅ No critical vulnerabilities found
✅ No high-risk issues found
⚠️  1 medium-risk issue found:
   - File: hal_driver.c:145
   - Issue: Potential integer overflow
   - Recommendation: Add bounds checking

STATIC ANALYSIS (Clang-Tidy):
✅ No memory leaks detected
✅ No null pointer dereferences
✅ No use-after-free issues

OVERALL QUALITY SCORE: 8.5/10 ✅ APPROVED

RECOMMENDATIONS:
1. Add input validation to register_write() function
2. Increase test coverage for error paths
3. Add Doxygen comments to public API functions
```

---

## Database Schema Summary

### Tables Used Across All Phases

```sql
-- Master project tracking
projects (
  id UUID PRIMARY KEY,
  project_name VARCHAR,
  system_type VARCHAR,
  requirements TEXT,
  status VARCHAR,
  phase_completed INT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- Outputs from each phase
phase_outputs (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  phase INT,
  output_type VARCHAR,  -- 'HRS', 'BOM', 'Netlist', 'GLR', 'Software'
  file_path VARCHAR,
  created_at TIMESTAMP
)

-- Component caching (Phase 1)
component_cache (
  id UUID PRIMARY KEY,
  search_term VARCHAR,
  category VARCHAR,
  part_number VARCHAR,
  manufacturer VARCHAR,
  description TEXT,
  price DECIMAL,
  availability VARCHAR,
  lifecycle_status VARCHAR,
  datasheet_url VARCHAR,
  cached_at TIMESTAMP,
  expires_at TIMESTAMP
)

-- Block diagrams (Phase 1)
block_diagrams (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  version VARCHAR,
  diagram_json JSONB,
  ascii_representation TEXT,
  created_at TIMESTAMP
)

-- BOM items (Phase 1)
bom_items (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  reference_designator VARCHAR,
  part_number VARCHAR,
  description TEXT,
  quantity INT,
  unit_price DECIMAL,
  total_price DECIMAL
)

-- Compliance tracking (Phase 3)
compliance_records (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  component_id UUID,
  standard_name VARCHAR,  -- 'RoHS', 'CE', 'FCC'
  compliant BOOLEAN,
  certification_number VARCHAR,
  checked_at TIMESTAMP
)

-- AI API usage tracking
api_usage (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  phase INT,
  provider VARCHAR,  -- 'Claude', 'GPT-4'
  model VARCHAR,
  tokens_used INT,
  cost DECIMAL,
  called_at TIMESTAMP
)

-- Component recommendations (Phase 1)
component_recommendations (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  category VARCHAR,
  recommended_part VARCHAR,
  rationale TEXT,
  alternatives JSONB,  -- Array of alternative parts
  created_at TIMESTAMP
)

-- Scraping queue for background processing
scraping_queue (
  id UUID PRIMARY KEY,
  search_term VARCHAR,
  category VARCHAR,
  priority INT,
  status VARCHAR,  -- 'pending', 'processing', 'completed', 'failed'
  attempts INT,
  created_at TIMESTAMP,
  processed_at TIMESTAMP
)

-- System logs
system_logs (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  phase INT,
  log_level VARCHAR,  -- 'INFO', 'WARNING', 'ERROR'
  message TEXT,
  metadata JSONB,
  logged_at TIMESTAMP
)
```

---

## Service Communication Architecture

```
┌─────────────────────────────────────────────────────┐
│                    DOCKER NETWORK                    │
│                  bridge: hardware_pipeline           │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────┐     │
│  │  n8n                                       │     │
│  │  Port: 5678 (external), 5678 (internal)   │     │
│  │  Hostname: n8n                             │     │
│  │  Environment:                              │     │
│  │    - DB_TYPE=postgresqldb                  │     │
│  │    - DB_POSTGRESDB_HOST=postgres           │     │
│  │    - CLAUDE_API_KEY=[from .env]            │     │
│  └──────┬─────────────────────────────────────┘     │
│         │ HTTP                                      │
│         ↓                                           │
│  ┌────────────────────────────────────────────┐     │
│  │  Playwright Service                        │     │
│  │  Port: 8000 (internal)                     │     │
│  │  Hostname: playwright                      │     │
│  │  Runs: FastAPI (scraper_api.py)            │     │
│  │  Chromium headless browser                 │     │
│  └──────┬─────────────────────────────────────┘     │
│         │ SQL                                       │
│         ↓                                           │
│  ┌────────────────────────────────────────────┐     │
│  │  PostgreSQL                                │     │
│  │  Port: 5432 (external), 5432 (internal)   │     │
│  │  Hostname: postgres                        │     │
│  │  Database: hardware_pipeline               │     │
│  │  User: postgres                            │     │
│  │  Volume: postgres_data                     │     │
│  └────────────────────────────────────────────┘     │
│                                                      │
│  ┌────────────────────────────────────────────┐     │
│  │  Redis                                     │     │
│  │  Port: 6379 (internal)                     │     │
│  │  Hostname: redis                           │     │
│  │  Used for: Session management, caching     │     │
│  └────────────────────────────────────────────┘     │
│                                                      │
│  ┌────────────────────────────────────────────┐     │
│  │  pgAdmin                                   │     │
│  │  Port: 5050 (external), 80 (internal)     │     │
│  │  Hostname: pgadmin                         │     │
│  │  For: Database administration GUI          │     │
│  └────────────────────────────────────────────┘     │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Performance Metrics per Phase

| Phase | Duration | AI API Calls | DB Queries | Network I/O | CPU Usage |
|-------|----------|--------------|------------|-------------|-----------|
| **Phase 1** | ~90s | 2-3 | 50-100 | High (scraping) | Medium |
| **Phase 2** | ~30s | 0-1 | 10-20 | Low | Low |
| **Phase 3** | ~15s | 0 | 20-30 | Medium | Low |
| **Phase 4** | ~40s | 0 | 30-50 | Low | Medium |
| **Phase 5** | User | 0 | 0 | 0 | 0 |
| **Phase 6** | ~40s | 1-2 | 20-30 | Low | Low |
| **Phase 7** | User | 0 | 0 | 0 | 0 |
| **Phase 8** | ~60s | 2-3 | 10-20 | Low | Medium |
| **TOTAL** | ~6 min | 5-9 | 140-250 | High | Medium |

---

## Error Handling Architecture

```
┌─────────────────────────────────────────────┐
│  Every n8n Node Has Error Handler          │
├─────────────────────────────────────────────┤
│                                             │
│  Try/Catch Blocks:                          │
│  - Catch JavaScript errors                  │
│  - Catch API timeout errors                 │
│  - Catch database errors                    │
│                                             │
│  Retry Logic:                               │
│  - API calls: 3 retries with exponential   │
│    backoff (2s, 4s, 8s)                     │
│  - Scraping: 2 retries per component        │
│  - Database: 2 retries with 1s delay        │
│                                             │
│  Fallback Mechanisms:                       │
│  - If Claude API fails → try GLM-4          │
│  - If scraping fails → use cached data      │
│  - If no cached data → use mock data        │
│                                             │
│  Logging:                                   │
│  - All errors logged to system_logs table   │
│  - Critical errors trigger user notification│
│  - Stack traces saved for debugging         │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Summary Table

| Phase | What Happens | Technologies Used | Input | Output | Status |
|-------|-------------|-------------------|-------|--------|--------|
| **1** | Requirements → Block Diagram → BOM | n8n, Claude API, Playwright, PostgreSQL | Natural language | Block diagram, BOM, components | ✅ Implemented |
| **2** | HRS Document Generation | python-docx, n8n | Block diagram, BOM | HRS.docx (50-100 pages) | ⚠️ Partial |
| **3** | Compliance Validation | Database queries, APIs | BOM | Compliance report | ⚠️ Partial |
| **4** | Netlist Generation | networkx, edifparser | Block diagram + pins | netlist.edif, netlist.xlsx | ⚠️ Logic ready |
| **5** | PCB Design (Manual) | User's EDA tool | Netlist | PCB Gerbers | ✅ Defined |
| **6** | GLR Generation | openpyxl, Claude API | Netlist | GLR.xlsx | ⚠️ Logic ready |
| **7** | FPGA/MCU (Manual) | User's tools | GLR | HDL/firmware + register map | ✅ Defined |
| **8** | Software + Code Review | Claude API, SonarQube, Git | Register map | Drivers, GUI, tests | ✅ Implemented |

---

**Document Version:** 1.0
**Date:** February 4, 2026
**Repository:** github.com/bala9066/S2S
**Branch:** claude/start-implementation-Y5bqL
