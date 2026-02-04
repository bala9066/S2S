# How to Apply Improved Prompts to n8n Workflow

## Quick Integration Guide

After importing `Phase1_Complete_Workflow_READY_TO_IMPORT.json` into n8n, follow these steps to apply the improved AI prompt system.

---

## Step 1: Update "Build AI Prompt" Node

1. **Open the workflow** in n8n
2. **Find and click** the node named **"Build AI Prompt"**
3. **Click "Edit Code"** (or double-click the node)
4. **Replace the entire code** with the contents of `improved_ai_prompt.js`
5. **Click "Save"**

### How to copy the code:

```bash
# From your terminal
cat /path/to/S2S/improved_ai_prompt.js

# Or via GitHub
# View: https://github.com/bala9066/S2S/blob/claude/start-implementation-Y5bqL/improved_ai_prompt.js
```

---

## Step 2: Update "Generate Block Diagram" Node

1. **Find and click** the node named **"Generate Block Diagram"**
2. **Click "Edit Code"**
3. **Replace the entire code** with the contents of `improved_block_diagram_generator.js`
4. **Click "Save"**

### How to copy the code:

```bash
# From your terminal
cat /path/to/S2S/improved_block_diagram_generator.js

# Or via GitHub
# View: https://github.com/bala9066/S2S/blob/claude/start-implementation-Y5bqL/improved_block_diagram_generator.js
```

---

## Step 3: Activate the Workflow

1. In the workflow editor, click the **"Active"** toggle in the top-right
2. It should turn **green**
3. The workflow is now listening for chat input

---

## Step 4: Test the Improved System

### Test Case 1: Motor Controller (Comprehensive)

**In n8n chat interface, enter:**

```
Design a 3-phase motor controller with TMS320F28379D DSP, 10kW output power,
48V DC input, 0-400Hz output frequency, Ethernet interface for monitoring,
current sensing with hall sensors, temperature protection with NTC thermistors,
and position feedback with incremental encoder.
```

**Expected improvements:**
- ✅ Block diagram with **24+ blocks** (was 8-12)
- ✅ **Power tree**: 48V → Protection → 5V/3.3V/1.8V/15V rails
- ✅ **Power stage**: Gate drivers + 6x MOSFETs + 3-phase inverter
- ✅ **Sensors**: Current (hall), temperature (NTC), position (encoder)
- ✅ **Signal chain**: ADC + amplifiers + filtering
- ✅ **Interfaces**: Ethernet PHY, CAN, UART

### Test Case 2: RF/Wireless System

```
Design RF system with Xilinx Artix-7 FPGA, 5-18GHz frequency range,
40dBm output power, return loss > 10dB, GaN power amplifier,
buck-boost converters for 1.0V/1.8V/3.3V/28V rails, SPI interface to PA,
temperature monitoring, and directional coupler for power measurement.
```

**Expected improvements:**
- ✅ RF component chain: FPGA → PA → Filters → Antenna
- ✅ Matching networks between stages
- ✅ Power monitoring (directional coupler)
- ✅ Multiple power rails for different sections
- ✅ Temperature sensors and protection

### Test Case 3: Digital Controller

```
Design digital controller with Zynq UltraScale+ ZU3EG MPSoC, 2GB DDR4 memory,
Gigabit Ethernet PHY, USB 3.0, PCIe Gen3 x4, SPI flash for boot, QSPI NOR flash,
operating temperature -40 to 85°C, DisplayPort output, SD card slot.
```

**Expected improvements:**
- ✅ Complete memory subsystem: DDR4 + SPI flash + QSPI flash + SD card
- ✅ All interface PHYs: Ethernet, USB, PCIe
- ✅ Display output chain
- ✅ Multiple power domains
- ✅ Clock distribution network

---

## Step 5: Compare Before vs After

### Before (Original Prompt):

```
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
```

### After (Improved Prompt):

```
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
   b. 25MHz crystal [clock]

3. ANALOG:
   a. 16-bit ADC [adc]
   b. Signal Conditioning [amplifier]

4. SENSING:
   a. Current Sensor [sensor]
   b. Temperature Sensor [sensor]
   c. Position Encoder [sensor]

5. POWER_STAGE:
   a. Gate Driver (6ch) [gate_driver]
   b. MOSFET (100V/240A) [power_switch]
   c. 3-phase inverter [output_stage]

6. COMMUNICATION:
   a. Ethernet 100Mbps [interface]
   b. Ethernet PHY [phy]
   c. Ethernet Port [connector]
   d. CAN 1Mbps [interface]
   e. CAN PHY [phy]

7. EXTERNAL:
   a. 3-Phase Motor [load]

POWER DISTRIBUTION:
  1. 5V @ 2A → gate drivers
  2. 3.3V @ 1.5A → DSP core
  3. 1.8V @ 0.8A → DSP I/O
  4. 15V @ 0.5A → analog frontend

CRITICAL SIGNAL PATHS:
  1. TMS320F28379D → [PWM Signals] → Gate Driver (6ch)
  2. Gate Driver (6ch) → [Gate Drive] → MOSFET (100V/240A)
  3. MOSFET (100V/240A) → [Switched Power] → 3-phase inverter
  4. 3-phase inverter → [Output Power] → 3-Phase Motor
  5. 3-phase inverter → [Current] → Current Sensing
  6. Current Sensing → [Feedback] → TMS320F28379D
  ... and 25 more connections
```

---

## Troubleshooting

### Issue: "Node 'Build AI Prompt' not found"

**Solution:** The node might be named differently in your workflow. Look for:
- "Build AI Prompt"
- "Prepare AI Prompt"
- Or any Code node before "AI: Parse Requirements"

### Issue: "AI response is truncated"

**Solution:** Increase max_tokens in the AI node settings:
1. Click "AI: Parse Requirements" node
2. Find "max_tokens" parameter
3. Change from `3000` to `4000`

### Issue: "Workflow execution fails at diagram generation"

**Solution:** Check the JavaScript console in n8n for errors:
1. Open browser DevTools (F12)
2. Click "Console" tab
3. Look for JavaScript errors
4. Common fix: Ensure all variables are properly defined

---

## Verification Checklist

After integration, verify:

- [ ] "Build AI Prompt" node updated with improved code
- [ ] "Generate Block Diagram" node updated with improved code
- [ ] max_tokens increased to 4000 in AI node
- [ ] Workflow activated (green toggle)
- [ ] Test with motor controller returns 20+ blocks
- [ ] Power tree shows multiple voltage rails
- [ ] Analog signal chain is included
- [ ] Power stage components are present

---

## Performance Metrics

After applying improvements, you should see:

| Metric | Target |
|--------|--------|
| Blocks per diagram | 20-35 |
| Connections per diagram | 25-45 |
| Power rails identified | 4-8 |
| Component categories | 8-12 |
| Missing critical components | <5% |
| AI response time | 5-8 seconds |

---

## Support

If you encounter issues:

1. **Check logs**: `docker compose logs -f n8n`
2. **Review guide**: Read `IMPROVED_PROMPT_GUIDE.md`
3. **Test incrementally**: Test old workflow first, then apply changes
4. **GitHub issues**: Open issue at https://github.com/bala9066/S2S/issues

---

## Quick Copy-Paste Commands

```bash
# View improved prompt
cat improved_ai_prompt.js

# View improved generator
cat improved_block_diagram_generator.js

# View full documentation
cat IMPROVED_PROMPT_GUIDE.md

# Access workflow file
ls -lh Phase1_Complete_Workflow_READY_TO_IMPORT.json
```

---

**Ready to test!** 🚀

The improved system will generate production-quality block diagrams with comprehensive component identification.
