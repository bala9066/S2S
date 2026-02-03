// ==========================================
// IMPROVED AI PROMPT FOR REQUIREMENTS PARSING
// Enables comprehensive block diagram generation
// ==========================================

const requirements = $json.requirements;
const systemType = $json.system_type;

const prompt = `You are an expert hardware design architect. Analyze the following hardware requirements and extract comprehensive, detailed specifications that will enable creation of a complete block diagram.

SYSTEM TYPE DETECTED: ${systemType}

USER REQUIREMENTS:
${requirements}

Your task: Extract ALL technical details and infer missing components needed for a complete, production-ready hardware design.

Return ONLY valid JSON (no markdown, no explanation):

{
  "system_type": "${systemType}",

  "system_overview": {
    "purpose": "Brief description of what this system does",
    "key_functionality": ["list main functions"],
    "design_complexity": "low/medium/high"
  },

  "primary_components": {
    "processor": {
      "type": "FPGA/MCU/DSP/CPU/MPSoC",
      "specific_part": "exact part number if mentioned, otherwise suggest appropriate",
      "required_features": ["GPIO", "ADC", "PWM", "timers", "communication interfaces", etc],
      "package": "BGA/LQFP/QFN/etc",
      "speed": "clock frequency if specified",
      "memory_internal": "flash/RAM specs if relevant"
    },

    "memory": {
      "ram_type": "DDR4/DDR3/SRAM/none",
      "ram_size": "size if specified",
      "flash_type": "SPI/QSPI/eMMC/SD",
      "flash_size": "size if specified"
    },

    "power_system": {
      "input_voltage": "main input voltage",
      "input_current": "estimated or specified",
      "output_power": "total system power",
      "rails_needed": [
        {"voltage": "5V", "current": "2A", "purpose": "peripherals"},
        {"voltage": "3.3V", "current": "1A", "purpose": "MCU core"},
        {"voltage": "1.8V", "current": "0.5A", "purpose": "I/O"}
      ],
      "protection": ["overcurrent", "overvoltage", "reverse polarity", "thermal"],
      "topology": ["buck", "boost", "LDO", "isolated"]
    },

    "interfaces_communication": [
      {"type": "Ethernet", "speed": "10/100/1000Mbps", "quantity": 1, "purpose": "monitoring"},
      {"type": "CAN", "speed": "1Mbps", "quantity": 2, "purpose": "vehicle bus"},
      {"type": "USB", "version": "2.0/3.0", "quantity": 1, "purpose": "debugging"},
      {"type": "SPI", "speed": "10MHz", "quantity": 2, "purpose": "sensor communication"},
      {"type": "I2C", "speed": "400kHz", "quantity": 1, "purpose": "EEPROM, RTC"},
      {"type": "UART", "baud": "115200", "quantity": 2, "purpose": "console, GPS"}
    ],

    "analog_signal_chain": {
      "adc": {
        "resolution": "12-bit/16-bit/24-bit",
        "channels": "number of analog inputs",
        "sample_rate": "ksps/Msps",
        "input_range": "0-5V, ±10V, etc"
      },
      "dac": {
        "resolution": "12-bit/16-bit",
        "channels": "number of analog outputs",
        "output_range": "voltage range"
      },
      "sensors": [
        {"type": "temperature", "interface": "analog/I2C", "range": "-40 to 125°C"},
        {"type": "current", "interface": "analog", "range": "0-50A", "method": "hall effect/shunt"},
        {"type": "voltage", "interface": "analog", "range": "0-48V"}
      ],
      "amplifiers": ["instrumentation amp", "op-amp stages", "differential amplifier"],
      "filtering": ["anti-aliasing filter", "noise filter", "EMI filter"]
    },

    "power_stage": {
      "relevant_for": "Motor Control, Power Electronics, RF systems",
      "type": "inverter/rectifier/amplifier/converter",
      "switches": {
        "type": "MOSFET/IGBT/GaN",
        "voltage_rating": "voltage",
        "current_rating": "current",
        "quantity": "number of switches"
      },
      "gate_drivers": {
        "type": "isolated/non-isolated",
        "channels": "number",
        "drive_current": "current capability"
      },
      "output_stage": "3-phase inverter/H-bridge/push-pull/class-D",
      "protection": ["short circuit", "over-temperature", "dead-time insertion"]
    },

    "rf_frontend": {
      "relevant_for": "RF/Wireless systems",
      "frequency_range": "5-18GHz or specific",
      "power_output": "dBm or watts",
      "components": [
        {"type": "power amplifier", "gain": "dB", "technology": "GaN/GaAs"},
        {"type": "LNA", "noise_figure": "dB"},
        {"type": "mixer", "conversion_loss": "dB"},
        {"type": "filter", "type": "bandpass/lowpass", "order": 5},
        {"type": "antenna", "type": "patch/dipole/horn", "gain": "dBi"}
      ],
      "matching_networks": ["input", "interstage", "output"],
      "shielding": "RF shielding requirements"
    },

    "clocking": {
      "primary_clock": {"frequency": "MHz", "source": "crystal/oscillator"},
      "secondary_clocks": [{"frequency": "MHz", "purpose": "specific subsystem"}],
      "rtc": "yes/no",
      "pll_requirements": "frequency synthesis needs"
    },

    "user_interface": {
      "display": {"type": "LCD/OLED/LED/none", "size": "inches", "resolution": "pixels"},
      "input": ["buttons", "touchscreen", "rotary encoder", "keypad"],
      "indicators": ["status LEDs", "7-segment display", "bargraph"]
    },

    "storage_logging": {
      "sd_card": "yes/no",
      "eeprom": {"size": "bytes/KB", "interface": "I2C/SPI"},
      "logging_requirements": "what data to log"
    },

    "mechanical_cooling": {
      "cooling": "passive heatsink/active fan/liquid/none",
      "thermal_sensors": "number and placement",
      "enclosure": "requirements for housing"
    }
  },

  "block_diagram_hints": {
    "critical_connections": [
      "describe key signal paths",
      "power distribution tree",
      "high-speed interfaces",
      "isolated sections"
    ],
    "functional_blocks": [
      "list all major functional blocks needed",
      "power supply block",
      "processing block",
      "interface blocks",
      "protection blocks"
    ],
    "signal_flow": "describe how signals flow through the system"
  },

  "electrical_specifications": {
    "voltage_levels": ["3.3V CMOS", "5V TTL", "LVDS", "differential"],
    "current_requirements": {
      "idle": "mA",
      "typical": "mA",
      "peak": "A"
    },
    "power_dissipation": "total watts",
    "frequency_ranges": {
      "digital_clocks": ["frequencies"],
      "analog_signals": ["bandwidth"],
      "switching_frequencies": ["PWM frequency"]
    }
  },

  "special_requirements": {
    "isolation": ["galvanic isolation between X and Y", "isolation voltage"],
    "emi_emc": ["shielding", "filtering", "grounding strategy"],
    "safety": ["safety standards", "protective devices", "fail-safe modes"],
    "reliability": ["redundancy", "watchdog", "fault detection"],
    "environmental": {
      "temperature_range": "operating temperature",
      "humidity": "if specified",
      "vibration": "if specified",
      "ip_rating": "ingress protection"
    }
  },

  "compliance_certifications": {
    "required": ["RoHS", "REACH", "CE", "FCC", "UL", "IEC", "ISO", "medical", "automotive"],
    "safety_standards": ["IEC 61508", "ISO 26262", "IEC 60601", etc],
    "emc_standards": ["FCC Part 15", "EN 55032", etc]
  },

  "design_constraints": {
    "size": "PCB size constraints if any",
    "cost_target": "if specified",
    "production_volume": "low/medium/high",
    "time_to_market": "if specified",
    "technology_preferences": ["specific vendors", "proven technologies"]
  },

  "derived_components_needed": [
    {
      "category": "processor/memory/power/interface/sensor/driver/protection/passive",
      "description": "specific component description",
      "quantity": 1,
      "key_specs": "important specifications",
      "rationale": "why this component is needed"
    }
  ]
}

IMPORTANT RULES:
1. Be COMPREHENSIVE - include ALL components needed for a complete design
2. INFER missing details based on system type and industry standards
3. Use SPECIFIC technical values (not "TBD" or "varies")
4. Include ALL power rails needed (core, I/O, analog, interfaces)
5. List ALL interfaces even if not explicitly mentioned but needed for the system type
6. Include protection circuitry and safety requirements
7. Consider signal integrity, EMI/EMC, thermal management
8. For Motor Control: include gate drivers, current sensing, position sensing
9. For RF/Wireless: include matching networks, filters, amplifiers
10. For Power Electronics: include PFC, rectifiers, feedback loops
11. Return ONLY the JSON object, no markdown formatting, no explanations

Extract as much detail as possible to enable generation of a production-quality block diagram.`;

return {
  json: {
    ...($json),
    ai_prompt: prompt,
    task_complexity: 'high',
    max_tokens: 4000  // Increased for comprehensive response
  }
};
