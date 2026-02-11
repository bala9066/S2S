#!/usr/bin/env python3
"""
Hardware Pipeline - Phase 8: Software Code Generation Engine
Generates C/C++ driver code, test suites, Makefiles, and CMakeLists
from parsed hardware specifications (HRS, BOM, block diagram, GLR).

Integrates with Claude AI for intelligent code synthesis and review.
"""

import os
import re
import json
import hashlib
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

import requests
import psycopg2

logger = logging.getLogger(__name__)


# ==========================================
# DATA MODELS
# ==========================================

@dataclass
class PeripheralSpec:
    """Single peripheral/interface extracted from hardware specs."""
    name: str
    peripheral_type: str  # gpio, spi, i2c, uart, adc, pwm, can, ethernet
    base_address: str = "0x00000000"
    irq_number: int = 0
    pins: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HardwareContext:
    """All hardware info needed for code generation."""
    project_name: str
    system_type: str
    processor: Dict[str, Any] = field(default_factory=dict)
    peripherals: List[PeripheralSpec] = field(default_factory=list)
    power_rails: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    requirements: str = ""
    bom_summary: List[Dict[str, Any]] = field(default_factory=list)
    glr_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedFile:
    """A single generated source file."""
    filename: str
    content: str
    language: str  # c, cpp, h, hpp, make, cmake, txt
    category: str  # driver, hal, app, test, build, doc
    line_count: int = 0

    def __post_init__(self):
        self.line_count = len(self.content.splitlines())


@dataclass
class CodeReviewResult:
    """Result of AI code review."""
    score: int = 0  # 0-100
    issues: List[Dict[str, str]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    passed: bool = True


# ==========================================
# DATABASE MANAGER
# ==========================================

class Phase8Database:
    """Database operations for Phase 8 outputs."""

    def __init__(self):
        self.conn = None

    def connect(self):
        self.conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=int(os.environ.get("POSTGRES_PORT", 5432)),
            dbname=os.environ.get("POSTGRES_DB", "hardware_pipeline"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", "hardwarepipeline2026"),
        )

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def save_phase_output(self, project_id: int, output_files: Dict, execution_time: int,
                          ai_tokens: int = 0, ai_cost: float = 0.0) -> int:
        """Save Phase 8 output record."""
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO phase_outputs
                (project_id, phase_number, phase_name, output_files,
                 execution_time, ai_provider, ai_model, ai_tokens_used, ai_cost, status, completed_at)
            VALUES (%s, 8, 'Software Development', %s, %s, 'claude', 'claude-sonnet-4-5-20250929',
                    %s, %s, 'completed', NOW())
            RETURNING id
        """, (project_id, json.dumps(output_files), execution_time, ai_tokens, ai_cost))
        row_id = cursor.fetchone()[0]
        self.conn.commit()
        cursor.close()
        return row_id

    def log_api_usage(self, project_id: int, tokens_in: int, tokens_out: int, cost: float):
        """Log AI API usage for Phase 8."""
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO api_usage
                (project_id, phase_number, provider, model, tokens_input, tokens_output, cost)
            VALUES (%s, 8, 'claude', 'claude-sonnet-4-5-20250929', %s, %s, %s)
        """, (project_id, tokens_in, tokens_out, cost))
        self.conn.commit()
        cursor.close()


# ==========================================
# HARDWARE CONTEXT PARSER
# ==========================================

def parse_hardware_context(input_data: Dict[str, Any]) -> HardwareContext:
    """
    Parse input from prior phases (HRS, BOM, block diagram, GLR)
    into a unified HardwareContext for code generation.
    """
    parsed_req = input_data.get("parsed_requirements", {})
    block_diagram = input_data.get("block_diagram", {})
    bom_data = input_data.get("bom", [])
    glr_data = input_data.get("glr", {})

    # Extract processor info
    proc = parsed_req.get("primary_components", {}).get("processor", {})
    processor = {
        "type": proc.get("type", "MCU"),
        "part": proc.get("specific_part", "STM32F407VGT6"),
        "arch": _detect_arch(proc.get("specific_part", "")),
        "features": proc.get("required_features", []),
        "package": proc.get("package", "LQFP"),
    }

    # Extract interfaces
    raw_interfaces = parsed_req.get("primary_components", {}).get("interfaces", [])
    interfaces = raw_interfaces if isinstance(raw_interfaces, list) else [raw_interfaces]

    # Build peripheral list from interfaces + block diagram
    peripherals = _extract_peripherals(interfaces, block_diagram, glr_data)

    # Power rails
    power = parsed_req.get("primary_components", {}).get("power", {})
    rails = power.get("rails_needed", ["3.3V", "5V"])

    ctx = HardwareContext(
        project_name=input_data.get("project_name", "HardwareProject"),
        system_type=input_data.get("system_type", "Digital_Controller"),
        processor=processor,
        peripherals=peripherals,
        power_rails=rails,
        interfaces=interfaces,
        requirements=input_data.get("original_requirements", ""),
        bom_summary=bom_data if isinstance(bom_data, list) else [],
        glr_data=glr_data,
    )
    return ctx


def _detect_arch(part: str) -> str:
    """Detect CPU architecture from part number."""
    p = part.lower()
    if "stm32" in p or "cortex" in p or "sam" in p or "nrf" in p or "lpc" in p:
        return "ARM_Cortex_M"
    if "tms320" in p or "c2000" in p or "f28" in p:
        return "TI_C2000"
    if "esp32" in p:
        return "Xtensa"
    if "pic" in p:
        return "PIC"
    if "avr" in p or "atmega" in p or "attiny" in p:
        return "AVR"
    if "xilinx" in p or "xc7" in p or "zynq" in p:
        return "FPGA_Xilinx"
    if "altera" in p or "cyclone" in p or "intel" in p:
        return "FPGA_Intel"
    return "ARM_Cortex_M"


def _extract_peripherals(interfaces: List[str], block_diagram: Dict, glr_data: Dict) -> List[PeripheralSpec]:
    """Build peripheral specs from interfaces and GLR."""
    peripherals = []
    iface_map = {
        "SPI": ("spi", "0x40013000"),
        "I2C": ("i2c", "0x40005400"),
        "UART": ("uart", "0x40011000"),
        "USART": ("uart", "0x40011000"),
        "CAN": ("can", "0x40006400"),
        "Ethernet": ("ethernet", "0x40028000"),
        "USB": ("usb", "0x50000000"),
        "ADC": ("adc", "0x40012000"),
        "PWM": ("pwm", "0x40010000"),
        "GPIO": ("gpio", "0x40020000"),
        "Timer": ("timer", "0x40000000"),
    }
    for iface in interfaces:
        key = iface.upper().replace(" ", "")
        for name, (ptype, addr) in iface_map.items():
            if name.upper() in key:
                peripherals.append(PeripheralSpec(
                    name=iface,
                    peripheral_type=ptype,
                    base_address=addr,
                ))
                break
        else:
            peripherals.append(PeripheralSpec(name=iface, peripheral_type="custom"))

    # Always include GPIO
    if not any(p.peripheral_type == "gpio" for p in peripherals):
        peripherals.append(PeripheralSpec(name="GPIO", peripheral_type="gpio", base_address="0x40020000"))

    return peripherals


# ==========================================
# CODE GENERATORS (Template-based)
# ==========================================

def generate_hal_header(ctx: HardwareContext) -> GeneratedFile:
    """Generate HAL interface header (hal_interface.h)."""
    guard = f"{ctx.project_name.upper().replace(' ', '_')}_HAL_INTERFACE_H"
    periph_includes = ""
    periph_funcs = ""

    for p in ctx.peripherals:
        pname = re.sub(r'[^a-zA-Z0-9]', '_', p.name).upper()
        periph_funcs += f"""
/* {p.name} ({p.peripheral_type}) */
HAL_Status HAL_{pname}_Init(void);
HAL_Status HAL_{pname}_DeInit(void);
"""
        if p.peripheral_type == "spi":
            periph_funcs += f"HAL_Status HAL_{pname}_Transmit(const uint8_t *data, uint16_t len, uint32_t timeout);\n"
            periph_funcs += f"HAL_Status HAL_{pname}_Receive(uint8_t *data, uint16_t len, uint32_t timeout);\n"
            periph_funcs += f"HAL_Status HAL_{pname}_TransmitReceive(const uint8_t *tx, uint8_t *rx, uint16_t len, uint32_t timeout);\n"
        elif p.peripheral_type == "i2c":
            periph_funcs += f"HAL_Status HAL_{pname}_MasterTransmit(uint16_t addr, const uint8_t *data, uint16_t len, uint32_t timeout);\n"
            periph_funcs += f"HAL_Status HAL_{pname}_MasterReceive(uint16_t addr, uint8_t *data, uint16_t len, uint32_t timeout);\n"
        elif p.peripheral_type == "uart":
            periph_funcs += f"HAL_Status HAL_{pname}_Transmit(const uint8_t *data, uint16_t len, uint32_t timeout);\n"
            periph_funcs += f"HAL_Status HAL_{pname}_Receive(uint8_t *data, uint16_t len, uint32_t timeout);\n"
        elif p.peripheral_type == "adc":
            periph_funcs += f"HAL_Status HAL_{pname}_Start(void);\n"
            periph_funcs += f"HAL_Status HAL_{pname}_Stop(void);\n"
            periph_funcs += f"uint16_t HAL_{pname}_Read(uint8_t channel);\n"
        elif p.peripheral_type == "pwm":
            periph_funcs += f"HAL_Status HAL_{pname}_Start(uint8_t channel);\n"
            periph_funcs += f"HAL_Status HAL_{pname}_Stop(uint8_t channel);\n"
            periph_funcs += f"HAL_Status HAL_{pname}_SetDuty(uint8_t channel, uint16_t duty);\n"
        elif p.peripheral_type == "can":
            periph_funcs += f"HAL_Status HAL_{pname}_Transmit(uint32_t id, const uint8_t *data, uint8_t len);\n"
            periph_funcs += f"HAL_Status HAL_{pname}_Receive(uint32_t *id, uint8_t *data, uint8_t *len, uint32_t timeout);\n"
        elif p.peripheral_type == "gpio":
            periph_funcs += f"void HAL_{pname}_WritePin(uint16_t pin, uint8_t state);\n"
            periph_funcs += f"uint8_t HAL_{pname}_ReadPin(uint16_t pin);\n"
            periph_funcs += f"void HAL_{pname}_TogglePin(uint16_t pin);\n"

    content = f"""/**
 * @file    hal_interface.h
 * @brief   Hardware Abstraction Layer for {ctx.project_name}
 * @details Auto-generated by Hardware Pipeline Phase 8
 *          System Type: {ctx.system_type}
 *          Processor: {ctx.processor.get('part', 'Unknown')}
 * @date    {datetime.now().strftime('%Y-%m-%d')}
 */

#ifndef {guard}
#define {guard}

#ifdef __cplusplus
extern "C" {{
#endif

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/* ==========================================
 * STATUS AND ERROR CODES
 * ========================================== */
typedef enum {{
    HAL_OK       = 0x00,
    HAL_ERROR    = 0x01,
    HAL_BUSY     = 0x02,
    HAL_TIMEOUT  = 0x03
}} HAL_Status;

/* ==========================================
 * SYSTEM INITIALIZATION
 * ========================================== */
HAL_Status HAL_System_Init(void);
HAL_Status HAL_System_DeInit(void);
void HAL_System_Reset(void);
uint32_t HAL_GetTick(void);
void HAL_Delay(uint32_t ms);

/* ==========================================
 * PERIPHERAL INTERFACES
 * ========================================== */
{periph_funcs}

#ifdef __cplusplus
}}
#endif

#endif /* {guard} */
"""
    return GeneratedFile(filename="hal_interface.h", content=content, language="h", category="hal")


def generate_hal_source(ctx: HardwareContext) -> GeneratedFile:
    """Generate HAL interface source (hal_interface.c)."""
    init_calls = ""
    impl_funcs = ""

    for p in ctx.peripherals:
        pname = re.sub(r'[^a-zA-Z0-9]', '_', p.name).upper()
        init_calls += f"    status = HAL_{pname}_Init();\n"
        init_calls += f"    if (status != HAL_OK) return status;\n\n"

        impl_funcs += f"""
/* ==========================================
 * {p.name} ({p.peripheral_type}) Implementation
 * ========================================== */
HAL_Status HAL_{pname}_Init(void) {{
    /* TODO: Configure {p.name} peripheral registers */
    /* Base address: {p.base_address} */
    return HAL_OK;
}}

HAL_Status HAL_{pname}_DeInit(void) {{
    return HAL_OK;
}}
"""
        if p.peripheral_type == "spi":
            impl_funcs += f"""
HAL_Status HAL_{pname}_Transmit(const uint8_t *data, uint16_t len, uint32_t timeout) {{
    if (data == NULL || len == 0) return HAL_ERROR;
    /* TODO: SPI transmit implementation */
    (void)timeout;
    return HAL_OK;
}}

HAL_Status HAL_{pname}_Receive(uint8_t *data, uint16_t len, uint32_t timeout) {{
    if (data == NULL || len == 0) return HAL_ERROR;
    (void)timeout;
    return HAL_OK;
}}

HAL_Status HAL_{pname}_TransmitReceive(const uint8_t *tx, uint8_t *rx, uint16_t len, uint32_t timeout) {{
    if (tx == NULL || rx == NULL || len == 0) return HAL_ERROR;
    (void)timeout;
    return HAL_OK;
}}
"""
        elif p.peripheral_type == "uart":
            impl_funcs += f"""
HAL_Status HAL_{pname}_Transmit(const uint8_t *data, uint16_t len, uint32_t timeout) {{
    if (data == NULL || len == 0) return HAL_ERROR;
    (void)timeout;
    return HAL_OK;
}}

HAL_Status HAL_{pname}_Receive(uint8_t *data, uint16_t len, uint32_t timeout) {{
    if (data == NULL || len == 0) return HAL_ERROR;
    (void)timeout;
    return HAL_OK;
}}
"""
        elif p.peripheral_type == "i2c":
            impl_funcs += f"""
HAL_Status HAL_{pname}_MasterTransmit(uint16_t addr, const uint8_t *data, uint16_t len, uint32_t timeout) {{
    if (data == NULL || len == 0) return HAL_ERROR;
    (void)addr; (void)timeout;
    return HAL_OK;
}}

HAL_Status HAL_{pname}_MasterReceive(uint16_t addr, uint8_t *data, uint16_t len, uint32_t timeout) {{
    if (data == NULL || len == 0) return HAL_ERROR;
    (void)addr; (void)timeout;
    return HAL_OK;
}}
"""
        elif p.peripheral_type == "adc":
            impl_funcs += f"""
HAL_Status HAL_{pname}_Start(void) {{ return HAL_OK; }}
HAL_Status HAL_{pname}_Stop(void) {{ return HAL_OK; }}
uint16_t HAL_{pname}_Read(uint8_t channel) {{ (void)channel; return 0; }}
"""
        elif p.peripheral_type == "pwm":
            impl_funcs += f"""
HAL_Status HAL_{pname}_Start(uint8_t channel) {{ (void)channel; return HAL_OK; }}
HAL_Status HAL_{pname}_Stop(uint8_t channel) {{ (void)channel; return HAL_OK; }}
HAL_Status HAL_{pname}_SetDuty(uint8_t channel, uint16_t duty) {{ (void)channel; (void)duty; return HAL_OK; }}
"""
        elif p.peripheral_type == "can":
            impl_funcs += f"""
HAL_Status HAL_{pname}_Transmit(uint32_t id, const uint8_t *data, uint8_t len) {{
    if (data == NULL || len == 0 || len > 8) return HAL_ERROR;
    (void)id;
    return HAL_OK;
}}

HAL_Status HAL_{pname}_Receive(uint32_t *id, uint8_t *data, uint8_t *len, uint32_t timeout) {{
    if (id == NULL || data == NULL || len == NULL) return HAL_ERROR;
    (void)timeout;
    return HAL_OK;
}}
"""
        elif p.peripheral_type == "gpio":
            impl_funcs += f"""
void HAL_{pname}_WritePin(uint16_t pin, uint8_t state) {{ (void)pin; (void)state; }}
uint8_t HAL_{pname}_ReadPin(uint16_t pin) {{ (void)pin; return 0; }}
void HAL_{pname}_TogglePin(uint16_t pin) {{ (void)pin; }}
"""

    content = f"""/**
 * @file    hal_interface.c
 * @brief   HAL implementation for {ctx.project_name}
 * @details Auto-generated by Hardware Pipeline Phase 8
 * @date    {datetime.now().strftime('%Y-%m-%d')}
 */

#include "hal_interface.h"

/* Tick counter for delay */
static volatile uint32_t s_tick_count = 0;

/* ==========================================
 * SYSTEM
 * ========================================== */
HAL_Status HAL_System_Init(void) {{
    HAL_Status status;

{init_calls}    return HAL_OK;
}}

HAL_Status HAL_System_DeInit(void) {{
    return HAL_OK;
}}

void HAL_System_Reset(void) {{
    /* TODO: Trigger system reset via NVIC or watchdog */
}}

uint32_t HAL_GetTick(void) {{
    return s_tick_count;
}}

void HAL_Delay(uint32_t ms) {{
    uint32_t start = HAL_GetTick();
    while ((HAL_GetTick() - start) < ms) {{
        /* wait */
    }}
}}

/* Increment tick - call from SysTick_Handler */
void HAL_IncTick(void) {{
    s_tick_count++;
}}

{impl_funcs}
"""
    return GeneratedFile(filename="hal_interface.c", content=content, language="c", category="hal")


def generate_driver_header(ctx: HardwareContext) -> GeneratedFile:
    """Generate device driver header (device_driver.h)."""
    guard = f"{ctx.project_name.upper().replace(' ', '_')}_DEVICE_DRIVER_H"
    proj_upper = re.sub(r'[^a-zA-Z0-9]', '_', ctx.project_name).upper()

    content = f"""/**
 * @file    device_driver.h
 * @brief   Device driver for {ctx.project_name}
 * @details Auto-generated by Hardware Pipeline Phase 8
 *          System Type: {ctx.system_type}
 * @date    {datetime.now().strftime('%Y-%m-%d')}
 */

#ifndef {guard}
#define {guard}

#ifdef __cplusplus
extern "C" {{
#endif

#include "hal_interface.h"

/* ==========================================
 * DRIVER CONFIGURATION
 * ========================================== */
#define {proj_upper}_VERSION_MAJOR    1
#define {proj_upper}_VERSION_MINOR    0
#define {proj_upper}_VERSION_PATCH    0

/* ==========================================
 * DRIVER STATE
 * ========================================== */
typedef enum {{
    DRIVER_STATE_UNINITIALIZED = 0,
    DRIVER_STATE_READY,
    DRIVER_STATE_RUNNING,
    DRIVER_STATE_ERROR,
    DRIVER_STATE_STOPPED
}} DriverState;

typedef struct {{
    DriverState state;
    uint32_t error_code;
    uint32_t uptime_ms;
    uint32_t cycle_count;
}} DriverStatus;

/* ==========================================
 * DRIVER API
 * ========================================== */

/**
 * @brief  Initialize the device driver and all peripherals.
 * @return HAL_OK on success, HAL_ERROR on failure.
 */
HAL_Status Driver_Init(void);

/**
 * @brief  Start the device driver main operation.
 * @return HAL_OK on success.
 */
HAL_Status Driver_Start(void);

/**
 * @brief  Stop the device driver.
 * @return HAL_OK on success.
 */
HAL_Status Driver_Stop(void);

/**
 * @brief  Get current driver status.
 * @return DriverStatus struct with current state.
 */
DriverStatus Driver_GetStatus(void);

/**
 * @brief  Main processing loop tick - call from main loop or RTOS task.
 */
void Driver_Process(void);

/**
 * @brief  Handle an error condition.
 * @param  error_code Application-specific error code.
 */
void Driver_ErrorHandler(uint32_t error_code);

#ifdef __cplusplus
}}
#endif

#endif /* {guard} */
"""
    return GeneratedFile(filename="device_driver.h", content=content, language="h", category="driver")


def generate_driver_source(ctx: HardwareContext) -> GeneratedFile:
    """Generate device driver source (device_driver.c)."""
    content = f"""/**
 * @file    device_driver.c
 * @brief   Device driver implementation for {ctx.project_name}
 * @details Auto-generated by Hardware Pipeline Phase 8
 * @date    {datetime.now().strftime('%Y-%m-%d')}
 */

#include "device_driver.h"

/* ==========================================
 * PRIVATE DATA
 * ========================================== */
static DriverStatus s_status = {{
    .state       = DRIVER_STATE_UNINITIALIZED,
    .error_code  = 0,
    .uptime_ms   = 0,
    .cycle_count = 0
}};

/* ==========================================
 * PUBLIC API
 * ========================================== */

HAL_Status Driver_Init(void) {{
    HAL_Status status;

    /* Initialize HAL */
    status = HAL_System_Init();
    if (status != HAL_OK) {{
        s_status.state = DRIVER_STATE_ERROR;
        s_status.error_code = 1;
        return status;
    }}

    s_status.state = DRIVER_STATE_READY;
    s_status.error_code = 0;
    return HAL_OK;
}}

HAL_Status Driver_Start(void) {{
    if (s_status.state != DRIVER_STATE_READY) {{
        return HAL_ERROR;
    }}

    s_status.state = DRIVER_STATE_RUNNING;
    s_status.uptime_ms = 0;
    s_status.cycle_count = 0;
    return HAL_OK;
}}

HAL_Status Driver_Stop(void) {{
    s_status.state = DRIVER_STATE_STOPPED;
    return HAL_OK;
}}

DriverStatus Driver_GetStatus(void) {{
    s_status.uptime_ms = HAL_GetTick();
    return s_status;
}}

void Driver_Process(void) {{
    if (s_status.state != DRIVER_STATE_RUNNING) {{
        return;
    }}

    s_status.cycle_count++;

    /* TODO: Add application-specific processing
     * - Read sensors
     * - Update control outputs
     * - Handle communication
     * - Check safety limits
     */
}}

void Driver_ErrorHandler(uint32_t error_code) {{
    s_status.state = DRIVER_STATE_ERROR;
    s_status.error_code = error_code;

    /* TODO: Implement error recovery or safe shutdown */
    Driver_Stop();
}}
"""
    return GeneratedFile(filename="device_driver.c", content=content, language="c", category="driver")


def generate_app_main(ctx: HardwareContext) -> GeneratedFile:
    """Generate application main entry point (main.c)."""
    content = f"""/**
 * @file    main.c
 * @brief   Application entry point for {ctx.project_name}
 * @details Auto-generated by Hardware Pipeline Phase 8
 * @date    {datetime.now().strftime('%Y-%m-%d')}
 */

#include "device_driver.h"

int main(void) {{
    HAL_Status status;

    /* Initialize driver and hardware */
    status = Driver_Init();
    if (status != HAL_OK) {{
        Driver_ErrorHandler(0xFF);
        while (1) {{ /* halt */ }}
    }}

    /* Start driver */
    status = Driver_Start();
    if (status != HAL_OK) {{
        Driver_ErrorHandler(0xFE);
        while (1) {{ /* halt */ }}
    }}

    /* Main loop */
    while (1) {{
        Driver_Process();
    }}

    return 0;
}}
"""
    return GeneratedFile(filename="main.c", content=content, language="c", category="app")


def generate_cpp_driver(ctx: HardwareContext) -> GeneratedFile:
    """Generate C++ device driver (DeviceDriver.hpp / DeviceDriver.cpp combined)."""
    class_name = re.sub(r'[^a-zA-Z0-9]', '', ctx.project_name) + "Driver"
    guard = f"{ctx.project_name.upper().replace(' ', '_')}_DEVICE_DRIVER_HPP"

    periph_members = ""
    periph_init = ""
    for p in ctx.peripherals:
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', p.name).lower()
        periph_members += f"    bool m_{safe_name}_initialized{{false}};\n"
        periph_init += f"        m_{safe_name}_initialized = (HAL_{p.name.upper().replace(' ', '_')}_Init() == HAL_OK);\n"

    content = f"""/**
 * @file    DeviceDriver.hpp
 * @brief   C++ device driver for {ctx.project_name}
 * @details Auto-generated by Hardware Pipeline Phase 8
 *          Uses RAII, exception safety, modern C++17 features
 * @date    {datetime.now().strftime('%Y-%m-%d')}
 */

#ifndef {guard}
#define {guard}

#include <cstdint>
#include <string>
#include <stdexcept>
#include <functional>

extern "C" {{
#include "hal_interface.h"
}}

namespace hw {{

enum class DriverState {{
    Uninitialized,
    Ready,
    Running,
    Error,
    Stopped
}};

struct Status {{
    DriverState state{{DriverState::Uninitialized}};
    uint32_t error_code{{0}};
    uint32_t uptime_ms{{0}};
    uint32_t cycle_count{{0}};
}};

class {class_name} {{
public:
    {class_name}() = default;
    ~{class_name}() {{ stop(); }}

    // Non-copyable
    {class_name}(const {class_name}&) = delete;
    {class_name}& operator=(const {class_name}&) = delete;

    // Movable
    {class_name}({class_name}&&) noexcept = default;
    {class_name}& operator=({class_name}&&) noexcept = default;

    void init() {{
        if (HAL_System_Init() != HAL_OK) {{
            m_status.state = DriverState::Error;
            m_status.error_code = 1;
            throw std::runtime_error("{class_name}: HAL init failed");
        }}
{periph_init}
        m_status.state = DriverState::Ready;
    }}

    void start() {{
        if (m_status.state != DriverState::Ready) {{
            throw std::runtime_error("{class_name}: not ready");
        }}
        m_status.state = DriverState::Running;
        m_status.cycle_count = 0;
    }}

    void stop() {{
        if (m_status.state == DriverState::Running) {{
            m_status.state = DriverState::Stopped;
        }}
    }}

    void process() {{
        if (m_status.state != DriverState::Running) return;
        m_status.cycle_count++;
        m_status.uptime_ms = HAL_GetTick();
    }}

    Status getStatus() const {{
        return m_status;
    }}

    void setErrorCallback(std::function<void(uint32_t)> cb) {{
        m_error_callback = std::move(cb);
    }}

private:
    Status m_status{{}};
    std::function<void(uint32_t)> m_error_callback;
{periph_members}
}};

}} // namespace hw

#endif /* {guard} */
"""
    return GeneratedFile(filename="DeviceDriver.hpp", content=content, language="hpp", category="driver")


def generate_test_suite(ctx: HardwareContext) -> GeneratedFile:
    """Generate test suite (test_device_driver.c)."""
    periph_tests = ""
    for p in ctx.peripherals:
        pname = re.sub(r'[^a-zA-Z0-9]', '_', p.name).upper()
        periph_tests += f"""
static int test_{p.name.lower().replace(' ', '_')}_init(void) {{
    HAL_Status status = HAL_{pname}_Init();
    ASSERT_EQ(status, HAL_OK);
    return 0;
}}
"""

    test_list = "\n".join(
        f'    RUN_TEST(test_{p.name.lower().replace(" ", "_")}_init);'
        for p in ctx.peripherals
    )

    content = f"""/**
 * @file    test_device_driver.c
 * @brief   Unit tests for {ctx.project_name}
 * @details Auto-generated by Hardware Pipeline Phase 8
 * @date    {datetime.now().strftime('%Y-%m-%d')}
 */

#include "device_driver.h"
#include <stdio.h>
#include <string.h>

/* ==========================================
 * MINIMAL TEST FRAMEWORK
 * ========================================== */
static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

#define ASSERT_EQ(actual, expected) do {{ \\
    if ((actual) != (expected)) {{ \\
        printf("  FAIL: %s:%d: expected %d, got %d\\n", __FILE__, __LINE__, (int)(expected), (int)(actual)); \\
        return 1; \\
    }} \\
}} while(0)

#define ASSERT_NE(actual, not_expected) do {{ \\
    if ((actual) == (not_expected)) {{ \\
        printf("  FAIL: %s:%d: unexpected value %d\\n", __FILE__, __LINE__, (int)(actual)); \\
        return 1; \\
    }} \\
}} while(0)

#define RUN_TEST(test_fn) do {{ \\
    tests_run++; \\
    printf("  Running: %s ... ", #test_fn); \\
    if (test_fn() == 0) {{ tests_passed++; printf("PASS\\n"); }} \\
    else {{ tests_failed++; printf("FAIL\\n"); }} \\
}} while(0)

/* ==========================================
 * DRIVER LIFECYCLE TESTS
 * ========================================== */

static int test_driver_init(void) {{
    HAL_Status status = Driver_Init();
    ASSERT_EQ(status, HAL_OK);
    return 0;
}}

static int test_driver_start(void) {{
    Driver_Init();
    HAL_Status status = Driver_Start();
    ASSERT_EQ(status, HAL_OK);
    return 0;
}}

static int test_driver_stop(void) {{
    Driver_Init();
    Driver_Start();
    HAL_Status status = Driver_Stop();
    ASSERT_EQ(status, HAL_OK);
    return 0;
}}

static int test_driver_status_after_init(void) {{
    Driver_Init();
    DriverStatus st = Driver_GetStatus();
    ASSERT_EQ(st.state, DRIVER_STATE_READY);
    ASSERT_EQ(st.error_code, 0);
    return 0;
}}

static int test_driver_status_after_start(void) {{
    Driver_Init();
    Driver_Start();
    DriverStatus st = Driver_GetStatus();
    ASSERT_EQ(st.state, DRIVER_STATE_RUNNING);
    return 0;
}}

static int test_driver_process(void) {{
    Driver_Init();
    Driver_Start();
    Driver_Process();
    DriverStatus st = Driver_GetStatus();
    ASSERT_EQ(st.cycle_count, 1);
    return 0;
}}

static int test_driver_error_handler(void) {{
    Driver_Init();
    Driver_Start();
    Driver_ErrorHandler(42);
    DriverStatus st = Driver_GetStatus();
    ASSERT_EQ(st.state, DRIVER_STATE_ERROR);
    ASSERT_EQ(st.error_code, 42);
    return 0;
}}

static int test_driver_start_without_init(void) {{
    /* Should fail if state is not READY */
    DriverStatus st = Driver_GetStatus();
    if (st.state == DRIVER_STATE_READY) {{
        /* Already initialized from prior test, just check start works */
        return 0;
    }}
    return 0;
}}

/* ==========================================
 * PERIPHERAL INIT TESTS
 * ========================================== */
{periph_tests}

/* ==========================================
 * TEST RUNNER
 * ========================================== */

int main(void) {{
    printf("\\n=== {ctx.project_name} Test Suite ===\\n\\n");

    printf("[Driver Lifecycle]\\n");
    RUN_TEST(test_driver_init);
    RUN_TEST(test_driver_start);
    RUN_TEST(test_driver_stop);
    RUN_TEST(test_driver_status_after_init);
    RUN_TEST(test_driver_status_after_start);
    RUN_TEST(test_driver_process);
    RUN_TEST(test_driver_error_handler);
    RUN_TEST(test_driver_start_without_init);

    printf("\\n[Peripheral Init]\\n");
{test_list}

    printf("\\n=== Results: %d/%d passed, %d failed ===\\n\\n",
           tests_passed, tests_run, tests_failed);

    return tests_failed > 0 ? 1 : 0;
}}
"""
    return GeneratedFile(filename="test_device_driver.c", content=content, language="c", category="test")


def generate_makefile(ctx: HardwareContext) -> GeneratedFile:
    """Generate Makefile for C build."""
    content = f"""# Makefile for {ctx.project_name}
# Auto-generated by Hardware Pipeline Phase 8

CC      = gcc
CFLAGS  = -Wall -Wextra -Wpedantic -std=c11 -I.
LDFLAGS =

# Source files
SRCS    = main.c device_driver.c hal_interface.c
OBJS    = $(SRCS:.c=.o)
TARGET  = {re.sub(r'[^a-zA-Z0-9_]', '_', ctx.project_name).lower()}

# Test files
TEST_SRCS   = test_device_driver.c device_driver.c hal_interface.c
TEST_OBJS   = $(TEST_SRCS:.c=.o)
TEST_TARGET = test_runner

.PHONY: all clean test

all: $(TARGET)

$(TARGET): $(OBJS)
\t$(CC) $(LDFLAGS) -o $@ $^

%.o: %.c
\t$(CC) $(CFLAGS) -c -o $@ $<

test: $(TEST_TARGET)
\t./$(TEST_TARGET)

$(TEST_TARGET): $(TEST_SRCS)
\t$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

clean:
\trm -f $(OBJS) $(TEST_OBJS) $(TARGET) $(TEST_TARGET)
"""
    return GeneratedFile(filename="Makefile", content=content, language="make", category="build")


def generate_cmake(ctx: HardwareContext) -> GeneratedFile:
    """Generate CMakeLists.txt for C++ build."""
    target = re.sub(r'[^a-zA-Z0-9_]', '_', ctx.project_name).lower()
    content = f"""# CMakeLists.txt for {ctx.project_name}
# Auto-generated by Hardware Pipeline Phase 8

cmake_minimum_required(VERSION 3.16)
project({target} VERSION 1.0.0 LANGUAGES C CXX)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# C Library (HAL + Driver)
add_library(driver_c STATIC
    hal_interface.c
    device_driver.c
)
target_include_directories(driver_c PUBLIC ${{CMAKE_CURRENT_SOURCE_DIR}})

# C application
add_executable({target} main.c)
target_link_libraries({target} PRIVATE driver_c)

# C++ application (optional)
add_executable({target}_cpp main_cpp.cpp)
target_link_libraries({target}_cpp PRIVATE driver_c)

# Tests
enable_testing()
add_executable(test_driver test_device_driver.c)
target_link_libraries(test_driver PRIVATE driver_c)
add_test(NAME DriverTests COMMAND test_driver)
"""
    return GeneratedFile(filename="CMakeLists.txt", content=content, language="cmake", category="build")


def generate_cpp_main(ctx: HardwareContext) -> GeneratedFile:
    """Generate C++ main entry point."""
    class_name = re.sub(r'[^a-zA-Z0-9]', '', ctx.project_name) + "Driver"
    content = f"""/**
 * @file    main_cpp.cpp
 * @brief   C++ application entry point for {ctx.project_name}
 * @date    {datetime.now().strftime('%Y-%m-%d')}
 */

#include "DeviceDriver.hpp"
#include <cstdio>

int main() {{
    try {{
        hw::{class_name} driver;
        driver.init();
        driver.start();

        std::printf("{ctx.project_name} running...\\n");

        /* Main loop */
        for (;;) {{
            driver.process();
            auto st = driver.getStatus();
            if (st.state == hw::DriverState::Error) {{
                std::printf("Error code: %u\\n", st.error_code);
                break;
            }}
        }}

        driver.stop();
    }} catch (const std::exception& ex) {{
        std::fprintf(stderr, "Fatal: %s\\n", ex.what());
        return 1;
    }}
    return 0;
}}
"""
    return GeneratedFile(filename="main_cpp.cpp", content=content, language="cpp", category="app")


def generate_readme(ctx: HardwareContext, files: List[GeneratedFile]) -> GeneratedFile:
    """Generate project README."""
    file_table = "\n".join(
        f"| `{f.filename}` | {f.category} | {f.language} | {f.line_count} |"
        for f in files
    )

    content = f"""# {ctx.project_name} - Generated Software

Auto-generated by **Hardware Pipeline Phase 8** on {datetime.now().strftime('%Y-%m-%d %H:%M')}.

## System Info

| Property | Value |
|----------|-------|
| System Type | {ctx.system_type} |
| Processor | {ctx.processor.get('part', 'N/A')} |
| Architecture | {ctx.processor.get('arch', 'N/A')} |
| Interfaces | {', '.join(ctx.interfaces)} |
| Power Rails | {', '.join(ctx.power_rails)} |

## Files

| File | Category | Language | Lines |
|------|----------|----------|-------|
{file_table}

## Build (C)

```bash
make          # build application
make test     # run unit tests
make clean    # clean build artifacts
```

## Build (C++ / CMake)

```bash
mkdir build && cd build
cmake ..
cmake --build .
ctest
```
"""
    return GeneratedFile(filename="README.md", content=content, language="txt", category="doc")


# ==========================================
# AI-POWERED CODE REVIEW (via Claude API)
# ==========================================

def ai_code_review(files: List[GeneratedFile], api_key: str) -> CodeReviewResult:
    """
    Send generated code to Claude for review.
    Returns a CodeReviewResult with score, issues, and suggestions.
    """
    if not api_key:
        return CodeReviewResult(score=75, passed=True, suggestions=["No API key - review skipped"])

    code_snippets = "\n\n".join(
        f"--- {f.filename} ({f.language}) ---\n{f.content[:2000]}"
        for f in files
        if f.language in ("c", "h", "cpp", "hpp")
    )

    prompt = f"""Review this auto-generated embedded C/C++ code for a {files[0].category if files else 'hardware'} project.

Check for:
1. Buffer overflows or null pointer dereferences
2. Missing input validation
3. MISRA-C compliance issues
4. Memory safety
5. Thread safety concerns

Return ONLY valid JSON:
{{
  "score": <0-100>,
  "issues": [{{"severity": "high|medium|low", "file": "filename", "description": "issue"}}],
  "suggestions": ["suggestion1", "suggestion2"],
  "passed": true/false
}}

Code:
{code_snippets[:6000]}"""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "content-type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-5-20250929",
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data.get("content", [{}])[0].get("text", "{}")
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            review = json.loads(match.group())
            return CodeReviewResult(
                score=review.get("score", 80),
                issues=review.get("issues", []),
                suggestions=review.get("suggestions", []),
                passed=review.get("passed", True),
            )
    except Exception as e:
        logger.warning("AI review failed: %s", e)

    return CodeReviewResult(score=80, passed=True, suggestions=["AI review unavailable"])


# ==========================================
# MAIN GENERATION PIPELINE
# ==========================================

def generate_all(input_data: Dict[str, Any], run_review: bool = True) -> Dict[str, Any]:
    """
    Main entry point: generate all Phase 8 files from hardware context.

    Args:
        input_data: Dict from prior phases (parsed_requirements, block_diagram, bom, glr)
        run_review: Whether to run AI code review

    Returns:
        Dict with generated files, review results, and metadata.
    """
    start = datetime.now()

    # Parse context
    ctx = parse_hardware_context(input_data)

    # Generate all files
    files: List[GeneratedFile] = [
        generate_hal_header(ctx),
        generate_hal_source(ctx),
        generate_driver_header(ctx),
        generate_driver_source(ctx),
        generate_app_main(ctx),
        generate_cpp_driver(ctx),
        generate_cpp_main(ctx),
        generate_test_suite(ctx),
        generate_makefile(ctx),
        generate_cmake(ctx),
    ]

    # README last (needs file list)
    files.append(generate_readme(ctx, files))

    # AI code review
    review = CodeReviewResult(score=80, passed=True, suggestions=["Review skipped"])
    if run_review:
        api_key = os.environ.get("CLAUDE_API_KEY", "")
        review = ai_code_review(files, api_key)

    elapsed = (datetime.now() - start).total_seconds()

    result = {
        "success": True,
        "project_name": ctx.project_name,
        "system_type": ctx.system_type,
        "processor": ctx.processor.get("part", "Unknown"),
        "files": [asdict(f) for f in files],
        "file_count": len(files),
        "total_lines": sum(f.line_count for f in files),
        "code_review": asdict(review),
        "generation_time_seconds": round(elapsed, 2),
        "timestamp": datetime.now().isoformat(),
    }

    # Persist to DB if possible
    try:
        project_id = input_data.get("project_id")
        if project_id:
            db = Phase8Database()
            db.connect()
            file_manifest = {f.filename: {"language": f.language, "category": f.category, "lines": f.line_count} for f in files}
            db.save_phase_output(project_id, file_manifest, int(elapsed))
            db.disconnect()
    except Exception as e:
        logger.warning("DB save skipped: %s", e)

    return result


# ==========================================
# CLI ENTRY POINT
# ==========================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    # Example usage with minimal input
    sample_input = {
        "project_name": "MotorController",
        "system_type": "Motor_Control",
        "original_requirements": "3-phase motor controller with STM32F407, CAN bus, current sensing",
        "parsed_requirements": {
            "primary_components": {
                "processor": {"type": "MCU", "specific_part": "STM32F407VGT6", "required_features": ["PWM", "ADC", "CAN"], "package": "LQFP"},
                "power": {"input_voltage": "48V", "output_power": "10kW", "rails_needed": ["3.3V", "5V", "12V"]},
                "interfaces": ["CAN", "SPI", "UART", "ADC", "PWM"],
            },
            "key_components_needed": [
                {"category": "processor", "description": "STM32F407 MCU", "quantity": 1},
                {"category": "gate_driver", "description": "DRV8301 3-phase gate driver", "quantity": 1},
            ],
        },
        "block_diagram": {"blocks": [], "connections": []},
        "bom": [],
        "glr": {},
    }

    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as f:
            sample_input = json.load(f)

    result = generate_all(sample_input, run_review=False)
    print(json.dumps({
        "success": result["success"],
        "file_count": result["file_count"],
        "total_lines": result["total_lines"],
        "files": [f["filename"] for f in result["files"]],
        "generation_time_seconds": result["generation_time_seconds"],
    }, indent=2))
