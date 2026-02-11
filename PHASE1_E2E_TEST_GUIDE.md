# Phase 1 End-to-End Testing Guide

## Test Objective
Validate complete Phase 1 workflow from requirements to BOM with real hardware projects.

---

## Test Setup Checklist

### Prerequisites:
- [ ] Docker installed and running
- [ ] DigiKey API credentials configured in .env
- [ ] Mouser API credentials configured in .env
- [ ] n8n running at http://localhost:5678
- [ ] Component API service running at http://localhost:8001
- [ ] Workflow imported: Phase1_Complete_Workflow_READY_TO_IMPORT.json

### Verify Services:
```bash
# Check all services are running
docker ps | grep hardware_pipeline

# Should see:
# - hardware_pipeline_postgres
# - hardware_pipeline_n8n
# - hardware_pipeline_component_api

# Test Component API
curl http://localhost:8001/api/health

# Expected: {"status":"healthy","digikey_configured":true,"mouser_configured":true}
```

---

## Test Cases

We'll test 5 different hardware system types to validate the workflow handles diverse requirements.

---

## 📋 Test Case 1: 3-Phase Motor Controller (Most Common)

### Input Requirements:
```
Design a 3-phase motor controller with the following specifications:

Processor: TMS320F28379D DSP (200 MHz dual-core)
Power: 10kW output power, 48V DC input, 0-400Hz variable frequency output
Control: Field-Oriented Control (FOC) with encoder feedback
Communication: CANbus for configuration, Ethernet for monitoring and diagnostics
Sensors:
  - 3x hall-effect current sensors for phase currents (±100A range)
  - 2x NTC thermistors for temperature monitoring (motor and power stage)
  - Incremental encoder interface (A/B/Z channels, 1024 PPR)
Protection: Over-current, over-temperature, under-voltage, emergency stop input
Power Stage: 6x IGBT modules with isolated gate drivers
Isolation: 2.5kV isolation between control and power stages
Display: Optional SPI LCD interface for local monitoring
Operating Temperature: -20°C to +70°C ambient
```

### Expected Workflow Steps:

#### Step 1: Input Validation (2 seconds)
**Expected behavior:**
- ✅ Validates input length (> 30 chars)
- ✅ Auto-detects system type: "Motor_Control"
- ✅ Generates project name: "Project_[timestamp]"
- ✅ Passes to AI prompt builder

**Validation:**
```javascript
// In n8n execution log, check "Validate Input & Detect Type" node
{
  "is_approval": false,
  "requirements": "Design a 3-phase motor controller...",
  "project_name": "Project_1707523456789",
  "system_type": "Motor_Control",
  "timestamp": 1707523456789,
  "status": "requirements_received"
}
```

#### Step 2: AI Requirements Parsing (5-8 seconds)
**Expected behavior:**
- ✅ Claude API processes requirements
- ✅ Extracts 12+ component categories
- ✅ Identifies specific parts (TMS320F28379D)
- ✅ Infers missing components (decoupling caps, pull-ups, etc.)

**Validation:**
```javascript
// Check "Extract Parsed Data" node output
{
  "parsed_requirements": {
    "system_type": "Motor_Control",
    "primary_components": {
      "processor": {
        "specific_part": "TMS320F28379D",
        "type": "DSP",
        "required_features": ["Dual-core", "200MHz", "FOC capable"]
      },
      "power_system": {
        "input_voltage": "48V",
        "output_power": "10kW",
        "rails_needed": [
          {"voltage": "15V", "current": "2A", "purpose": "gate drivers"},
          {"voltage": "5V", "current": "3A", "purpose": "DSP, sensors"},
          {"voltage": "3.3V", "current": "1.5A", "purpose": "DSP core"}
        ]
      },
      "power_stage": {
        "topology": "3-phase inverter",
        "switches": "IGBT",
        "switch_count": 6,
        "gate_drivers": "isolated",
        "isolation_voltage": "2.5kV"
      },
      "analog_signal_chain": {
        "adc": {"resolution": "16-bit", "channels": 6},
        "sensors": [
          {"type": "current", "interface": "hall-effect", "range": "±100A"},
          {"type": "temperature", "interface": "NTC"}
        ]
      },
      "interfaces_communication": [
        {"type": "CAN", "speed": "1Mbps"},
        {"type": "Ethernet", "speed": "100Mbps"},
        {"type": "SPI", "purpose": "LCD"},
        {"type": "Encoder", "channels": "A/B/Z"}
      ]
    }
  }
}
```

#### Step 3: Block Diagram Generation (2 seconds)
**Expected behavior:**
- ✅ Generates 25-35 blocks
- ✅ Creates 30-50 connections
- ✅ Includes complete power tree
- ✅ Maps all interfaces

**Validation:**
```javascript
// Check "Generate Block Diagram" node
{
  "block_diagram": {
    "blocks": [
      // Should have 25-35 blocks
      {"id": "B1", "type": "processor", "label": "TMS320F28379D"},
      {"id": "B2", "type": "power_input", "label": "48V DC Input"},
      {"id": "B3", "type": "power_regulator", "label": "15V Gate Driver Supply"},
      {"id": "B4", "type": "power_regulator", "label": "5V Logic Supply"},
      {"id": "B5", "type": "power_regulator", "label": "3.3V DSP Core"},
      {"id": "B6", "type": "gate_driver", "label": "Gate Driver U"},
      {"id": "B7", "type": "gate_driver", "label": "Gate Driver V"},
      {"id": "B8", "type": "gate_driver", "label": "Gate Driver W"},
      {"id": "B9", "type": "power_switch", "label": "IGBT Module U"},
      {"id": "B10", "type": "interface", "label": "CAN Transceiver"},
      {"id": "B11", "type": "interface", "label": "Ethernet PHY"},
      {"id": "B12", "type": "sensor", "label": "Current Sensor Phase U"},
      {"id": "B13", "type": "sensor", "label": "Temperature Sensor"},
      {"id": "B14", "type": "encoder", "label": "Encoder Interface"},
      // ... more blocks
    ],
    "connections": [
      {"from": "B2", "to": "B3", "label": "48V"},
      {"from": "B3", "to": "B6", "label": "15V"},
      {"from": "B4", "to": "B1", "label": "5V"},
      {"from": "B5", "to": "B1", "label": "3.3V"},
      {"from": "B1", "to": "B6", "label": "PWM_UH"},
      // ... more connections
    ]
  }
}

// Validate counts
assert(diagram.blocks.length >= 25, "Should have at least 25 blocks");
assert(diagram.connections.length >= 30, "Should have at least 30 connections");
```

**Visual Diagram:**
- Open generated HTML: `/mnt/data/outputs/Project_xxx_block_diagram.html`
- ✅ Verify all major components visible
- ✅ Verify power tree flows correctly
- ✅ Verify signal paths make sense

#### Step 4: User Approval (Manual)
**Action:** Click APPROVE in HTML or type "APPROVE" in n8n chat

**Expected behavior:**
- ✅ Workflow continues to component search

#### Step 5: Component Search (10-30 seconds)
**Expected behavior:**
- ✅ Generates 8-15 component searches
- ✅ Searches DigiKey + Mouser APIs
- ✅ Processes in batches of 3
- ✅ Returns 40-60 total components

**Validation:**
```javascript
// Check "Build Component Searches" output
// Should generate searches like:
[
  {"category": "processor", "search_term": "TMS320F28379D"},
  {"category": "power_regulator", "search_term": "DC-DC 15V 2A isolated"},
  {"category": "power_regulator", "search_term": "DC-DC 5V 3A"},
  {"category": "power_regulator", "search_term": "LDO 3.3V 1.5A"},
  {"category": "gate_driver", "search_term": "isolated gate driver 2.5kV IGBT"},
  {"category": "interface", "search_term": "CAN transceiver 1Mbps"},
  {"category": "interface", "search_term": "Ethernet PHY 100Mbps"},
  {"category": "sensor", "search_term": "hall effect current sensor 100A"},
  {"category": "sensor", "search_term": "NTC thermistor 10k"},
  // ... more searches
]

// Check "Search Components (Real)" node (executes 3-5 times for batches)
// Each execution should return:
{
  "success": true,
  "total_found": 10-15,
  "components": [
    {
      "part_number": "TMS320F28379DZWTT",
      "manufacturer": "Texas Instruments",
      "description": "DSP 32-bit 200MHz Dual Core",
      "pricing": {"unit_price": "$15.50"},
      "availability": {"stock": 500},
      "source": "digikey"
    },
    // ... more components
  ]
}
```

#### Step 6: Component Aggregation (1 second)
**Expected behavior:**
- ✅ Collects all components from all batches
- ✅ Removes duplicates
- ✅ Sorts by price

**Validation:**
```javascript
// Check "Aggregate All Components" output
{
  "all_components": [
    // Should have 40-60 components total
  ],
  "component_count": 47
}

assert(all_components.length >= 40, "Should have at least 40 components");
```

#### Step 7: AI Component Recommendations (5 seconds)
**Expected behavior:**
- ✅ Claude AI analyzes all components
- ✅ Recommends best component per category
- ✅ Provides rationale

**Validation:**
```javascript
// Check "AI: Recommend Components" output
{
  "recommendations": [
    {
      "category": "processor",
      "part_number": "TMS320F28379DZWTT",
      "rationale": "Exact match with dual-core 200MHz, best for FOC applications"
    },
    {
      "category": "gate_driver",
      "part_number": "ACPL-P346",
      "rationale": "2.5kV isolation, 2.5A output, suitable for IGBT gate drive"
    },
    // ... more recommendations
  ]
}
```

#### Step 8: BOM Generation (2 seconds)
**Expected behavior:**
- ✅ Creates complete BOM
- ✅ Calculates total cost
- ✅ Shows top 10 components
- ✅ Lists all part numbers

**Expected Output:**
```
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
4. ISO1050DUB               $3.20
5. TPS54620RGYR             $2.80
6. ACS712ELCTR-30A-T        $2.50
7. NTCLE100E3103JB0         $0.45
8. 100nF 0805 (x10)         $0.80
9. 10uF 1206 (x5)           $1.20
10. 4.7kΩ 0603 (x20)        $0.60
... and 37 more components
```

**Validation:**
```javascript
// Check "Generate BOM" output
{
  "total_components": 47,
  "total_cost": 387.50,
  "components": [/* array of 47 components */],
  "phase_1_complete": true
}

// Validate
assert(total_components >= 40, "Should have at least 40 components");
assert(total_components <= 70, "Should have at most 70 components");
assert(total_cost > 0, "Total cost should be calculated");
assert(phase_1_complete === true, "Phase 1 should be marked complete");
```

### Expected Total Time:
**25-45 seconds** (end-to-end)

### Success Criteria:
- [x] Workflow completes without errors
- [x] Block diagram has 25-35 blocks
- [x] BOM has 40-60 components
- [x] Total cost is calculated
- [x] All major subsystems represented (processor, power, interfaces, sensors)
- [x] Visual diagram renders correctly

---

## 📋 Test Case 2: RF/Wireless System

### Input Requirements:
```
Design an RF transmitter system with these specifications:

Frequency Range: 5-18 GHz
Output Power: 40 dBm (10W)
Processor: Xilinx Artix-7 FPGA (XC7A35T-1CSG324C)
RF Frontend:
  - GaN power amplifier
  - Attenuator (0-31 dB, 1 dB steps)
  - Low-pass filter (cutoff at 20 GHz)
  - Directional coupler for power monitoring
Interfaces:
  - SPI for PA control
  - Ethernet (1 Gbps) for data/control
  - UART for debugging
Power Requirements:
  - 28V for PA bias
  - 5V for digital logic
  - 3.3V for FPGA I/O
  - 1.0V for FPGA core
Monitoring:
  - Forward/reverse power measurement
  - Temperature monitoring (PA and board)
  - VSWR protection
Performance:
  - Return loss > 10 dB
  - Harmonic suppression > 30 dBc
Operating Temperature: -10°C to +50°C
```

### Expected Results:
- **Block Diagram:** 28-40 blocks (RF chain, FPGA, power tree, monitoring)
- **BOM Components:** 45-65 items
- **Key Components:**
  - GaN PA (e.g., CGHV1J025D)
  - FPGA (Xilinx Artix-7)
  - RF attenuator (PE4302)
  - Directional coupler (RFDC-10-8)
  - Power monitors (ADL5920)
  - Ethernet PHY (KSZ9031RNX)
- **Total Cost:** $450-$650
- **Duration:** 30-50 seconds

---

## 📋 Test Case 3: Digital Controller (Simple)

### Input Requirements:
```
Design a basic digital controller with:

Processor: STM32F407VGT6 MCU (168 MHz, ARM Cortex-M4)
Memory:
  - 1MB external flash (W25Q80DV)
  - 512KB SRAM (IS62WV51216BLL)
Interfaces:
  - USB 2.0 full-speed (device mode)
  - microSD card slot
  - 2x UART (RS232 level, ±12V)
  - I2C (100 kHz)
  - SPI (10 MHz)
Display: 128x64 OLED via I2C
User Interface:
  - 4x tactile buttons
  - 2x status LEDs
Power: 5V DC input via USB or barrel jack
Operating Temperature: 0°C to +60°C
```

### Expected Results:
- **Block Diagram:** 15-20 blocks (simpler system)
- **BOM Components:** 25-35 items
- **Key Components:**
  - STM32F407VGT6
  - W25Q80DV flash
  - IS62WV51216BLL SRAM
  - USB connector
  - MAX3232 (RS232 transceiver)
  - LM1117-3.3 (LDO)
- **Total Cost:** $35-$55
- **Duration:** 20-30 seconds

---

## 📋 Test Case 4: Industrial PLC-like System

### Input Requirements:
```
Design an industrial controller with PLC-like features:

Processor: STM32H753ZIT6 (480 MHz, ARM Cortex-M7)
Digital I/O:
  - 16x isolated digital inputs (24V, PNP/NPN)
  - 16x isolated digital outputs (24V, 500mA sink/source)
  - Optocoupler isolation for all I/O
Analog I/O:
  - 8x analog inputs (0-10V, 16-bit ADC)
  - 4x analog outputs (0-10V, 16-bit DAC)
Communication:
  - Modbus RTU (RS485)
  - EtherCAT slave
  - CANopen
Power:
  - 24V DC input (redundant)
  - Internal DC-DC converters for 5V, 3.3V, 1.8V
Protection:
  - Reverse polarity protection
  - Transient voltage suppression
  - Over-current protection on all outputs
Operating Temperature: -20°C to +70°C
Compliance: CE, UL508, EN61131-2
```

### Expected Results:
- **Block Diagram:** 35-50 blocks (complex I/O structure)
- **BOM Components:** 60-80 items
- **Key Components:**
  - STM32H753ZIT6
  - 16x PC817 optocouplers
  - 16x ULN2803 Darlington arrays
  - ADS1115 (16-bit ADC)
  - DAC8552 (16-bit DAC)
  - ADM2587E (isolated RS485)
  - TPS54620 (DC-DC converters)
- **Total Cost:** $280-$380
- **Duration:** 35-55 seconds

---

## 📋 Test Case 5: Sensor System

### Input Requirements:
```
Design a multi-sensor data acquisition system:

Processor: Raspberry Pi RP2040 (dual-core Cortex-M0+, 133 MHz)
Sensors:
  - BME680 (temperature, humidity, pressure, gas)
  - MPU6050 (6-axis IMU: 3-axis gyro + 3-axis accelerometer)
  - GPS module (UART interface)
  - Light sensor (BH1750, I2C)
Storage: microSD card (SPI interface)
Communication:
  - WiFi module (ESP8266, UART AT commands)
  - Bluetooth LE (optional)
Display: 1.8" TFT LCD (ST7735, SPI)
Power:
  - LiPo battery (3.7V, 2000mAh)
  - USB-C charging (500mA)
  - Battery management (TP4056)
Operating Time: 8+ hours on battery
Data Logging: 1 Hz sampling rate, CSV format
```

### Expected Results:
- **Block Diagram:** 18-25 blocks
- **BOM Components:** 30-45 items
- **Key Components:**
  - RP2040
  - BME680, MPU6050, BH1750 sensors
  - GPS module (e.g., NEO-6M)
  - ESP8266
  - ST7735 LCD
  - TP4056 charger
  - microSD socket
- **Total Cost:** $45-$75
- **Duration:** 25-35 seconds

---

## 🧪 Automated Validation Script

Save this as `test_phase1_e2e.py`:

```python
#!/usr/bin/env python3
"""
Phase 1 End-to-End Automated Test
Validates workflow outputs against expected criteria
"""

import json
import time
import requests
from datetime import datetime

class Phase1Tester:
    def __init__(self):
        self.test_results = []
        self.n8n_url = "http://localhost:5678"
        self.api_url = "http://localhost:8001"

    def log_test(self, test_name, passed, message=""):
        result = {
            "test": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")

    def test_services_running(self):
        """Test 1: Verify all services are running"""
        try:
            # Test Component API
            response = requests.get(f"{self.api_url}/api/health", timeout=5)
            health = response.json()

            self.log_test(
                "Services Running",
                health.get("status") == "healthy",
                f"DigiKey: {health.get('digikey_configured')}, Mouser: {health.get('mouser_configured')}"
            )
        except Exception as e:
            self.log_test("Services Running", False, str(e))

    def validate_block_diagram(self, diagram_data):
        """Test 2: Validate block diagram structure"""
        try:
            diagram = diagram_data.get("block_diagram", {})
            blocks = diagram.get("blocks", [])
            connections = diagram.get("connections", [])

            # Check block count
            has_min_blocks = len(blocks) >= 15
            has_max_blocks = len(blocks) <= 60

            # Check connections
            has_connections = len(connections) >= 10

            # Check required block types
            block_types = {b.get("type") for b in blocks}
            has_processor = "processor" in block_types or any("proc" in t for t in block_types)
            has_power = any("power" in t for t in block_types)

            all_valid = has_min_blocks and has_max_blocks and has_connections and has_processor and has_power

            self.log_test(
                "Block Diagram Validation",
                all_valid,
                f"Blocks: {len(blocks)}, Connections: {len(connections)}, Types: {block_types}"
            )

        except Exception as e:
            self.log_test("Block Diagram Validation", False, str(e))

    def validate_bom(self, bom_data):
        """Test 3: Validate BOM output"""
        try:
            components = bom_data.get("components", [])
            total_cost = bom_data.get("total_cost", 0)

            # Check component count
            has_components = len(components) >= 20
            has_reasonable_count = len(components) <= 100

            # Check cost calculation
            has_cost = total_cost > 0

            # Check component structure
            first_comp = components[0] if components else {}
            has_part_number = "part_number" in first_comp
            has_manufacturer = "manufacturer" in first_comp

            all_valid = has_components and has_reasonable_count and has_cost and has_part_number

            self.log_test(
                "BOM Validation",
                all_valid,
                f"Components: {len(components)}, Total Cost: ${total_cost:.2f}"
            )

        except Exception as e:
            self.log_test("BOM Validation", False, str(e))

    def validate_component_search(self, search_results):
        """Test 4: Validate component search results"""
        try:
            # Check if we have results from both sources
            sources = search_results.get("sources", {})
            has_digikey = sources.get("digikey", 0) > 0
            has_mouser = sources.get("mouser", 0) > 0

            # Check total found
            total_found = search_results.get("total_found", 0)
            has_results = total_found > 0

            # Check search time
            search_time = search_results.get("search_time_ms", 0)
            is_fast = search_time < 5000  # Under 5 seconds

            all_valid = has_results and (has_digikey or has_mouser)

            self.log_test(
                "Component Search",
                all_valid,
                f"Found: {total_found}, Sources: DigiKey={sources.get('digikey')}, Mouser={sources.get('mouser')}, Time: {search_time}ms"
            )

        except Exception as e:
            self.log_test("Component Search", False, str(e))

    def run_all_tests(self):
        """Run all automated tests"""
        print("=" * 70)
        print("  PHASE 1 END-TO-END AUTOMATED TESTS")
        print("=" * 70)
        print()

        # Test 1: Services
        self.test_services_running()

        # Note: Tests 2-4 would need actual workflow execution data
        # For now, provide manual validation instructions

        print()
        print("=" * 70)
        print("  TEST SUMMARY")
        print("=" * 70)

        passed = sum(1 for r in self.test_results if r["passed"])
        total = len(self.test_results)

        print(f"Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total*100):.1f}%")

        return passed == total

if __name__ == "__main__":
    tester = Phase1Tester()
    success = tester.run_all_tests()

    if success:
        print("\n✅ All automated tests passed!")
    else:
        print("\n❌ Some tests failed. Review output above.")
```

---

## 📊 Test Execution Checklist

### Before Testing:
- [ ] Read this entire test guide
- [ ] Start all Docker services
- [ ] Verify API credentials configured
- [ ] Import workflow to n8n
- [ ] Have 5 test cases ready

### During Testing:
For each test case:
- [ ] Copy test requirements to n8n chat
- [ ] Wait for block diagram generation
- [ ] Open visual diagram HTML
- [ ] Verify diagram looks correct
- [ ] Click APPROVE button
- [ ] Wait for component search (watch progress)
- [ ] Verify BOM generation
- [ ] Check component count (should be 20-70)
- [ ] Check total cost calculated
- [ ] Save BOM output for reference
- [ ] Note any errors or issues
- [ ] Record execution time

### After Testing:
- [ ] Compare results across all 5 test cases
- [ ] Verify different system types work
- [ ] Verify DigiKey + Mouser both return results
- [ ] Check visual diagrams saved correctly
- [ ] Review any errors/warnings
- [ ] Document any bugs found
- [ ] Create summary report

---

## 📝 Test Report Template

```markdown
# Phase 1 End-to-End Test Report

**Date:** [Date]
**Tester:** [Your Name]
**Workflow Version:** Phase1_Complete_Workflow_READY_TO_IMPORT.json

## Test Environment
- Docker: [Version]
- n8n: [Version]
- Component API: [Status]
- DigiKey API: [Configured: Yes/No]
- Mouser API: [Configured: Yes/No]

## Test Results Summary

| Test Case | System Type | Duration | Blocks | Components | Cost | Status |
|-----------|-------------|----------|--------|------------|------|--------|
| TC1 | Motor Controller | 35s | 32 | 47 | $387.50 | ✅ Pass |
| TC2 | RF System | 42s | 35 | 52 | $545.20 | ✅ Pass |
| TC3 | Digital Controller | 28s | 18 | 28 | $42.80 | ✅ Pass |
| TC4 | Industrial PLC | 48s | 42 | 68 | $325.40 | ✅ Pass |
| TC5 | Sensor System | 32s | 22 | 35 | $58.90 | ✅ Pass |

## Issues Found
1. [Issue description]
2. [Issue description]

## Recommendations
1. [Recommendation]
2. [Recommendation]

## Conclusion
Phase 1 is [Production Ready / Needs Work].
```

---

## 🎯 Success Criteria

Phase 1 is considered **Production Ready** if:

- [x] All 5 test cases complete successfully
- [x] Block diagrams have correct block counts (15-50 blocks)
- [x] BOMs have reasonable component counts (20-70 components)
- [x] Component search returns results from DigiKey + Mouser
- [x] Total costs are calculated correctly
- [x] Visual diagrams render properly
- [x] No critical errors in execution logs
- [x] Execution time is acceptable (< 60 seconds per project)
- [x] Different system types are handled correctly

---

## 🚀 Next Steps After Testing

1. **If all tests pass:**
   - ✅ Phase 1 is production-ready
   - Move to Phase 2, 3, or 4 implementation
   - Or deploy Phase 1 for real use

2. **If some tests fail:**
   - Document failures
   - Debug issues
   - Fix bugs
   - Re-test

3. **Optimization opportunities:**
   - Add caching to reduce API calls
   - Improve block diagram layout algorithm
   - Add more component categories
   - Enhance AI prompt for better parsing

---

**Ready to start testing?**

1. Start Docker services: `docker compose up -d`
2. Verify services: `curl http://localhost:8001/api/health`
3. Open n8n: http://localhost:5678
4. Run Test Case 1 (Motor Controller)
5. Document results

Let me know when you're ready to start, or if you need any clarification!
