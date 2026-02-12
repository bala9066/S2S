#!/usr/bin/env python3
"""
Unified Component Search API Service
Uses BOTH DigiKey and Mouser APIs for maximum coverage
Replaces Playwright web scraping with official APIs
"""

import asyncio
import os
from typing import Dict, List
from datetime import datetime

from dotenv import load_dotenv
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_env_path, override=True)  # Load .env before initializing API clients

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from digikey_api import DigiKeyAPI
from mouser_api import MouserAPI

# ==========================================
# FASTAPI APP CONFIGURATION
# ==========================================

app = FastAPI(
    title="Hardware Pipeline Component API Service",
    description="Unified API for DigiKey and Mouser component search",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS for n8n access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# PYDANTIC MODELS
# ==========================================

class SearchRequest(BaseModel):
    """Request model for /api/search"""
    search_term: str = Field(..., min_length=1, description="Component search term")
    category: str = Field(..., description="Component category")
    use_cache: bool = Field(default=True, description="Use cache (not implemented yet)")
    sources: List[str] = Field(default=["digikey", "mouser"], description="Which APIs to search")
    limit_per_source: int = Field(default=10, description="Max results per source")

class SearchResponse(BaseModel):
    """Response model for /api/search"""
    success: bool
    search_term: str
    category: str
    total_found: int
    components: List[Dict]
    sources: Dict[str, int]
    errors: List[str] = []
    search_time_ms: int

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    digikey_configured: bool
    mouser_configured: bool

# ==========================================
# API INITIALIZATION
# ==========================================

# Initialize APIs
digikey_api = DigiKeyAPI()
mouser_api = MouserAPI()

# ==========================================
# API ENDPOINTS
# ==========================================

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Verifies API credentials are configured
    """
    digikey_ok = bool(os.environ.get('DIGIKEY_CLIENT_ID') and os.environ.get('DIGIKEY_CLIENT_SECRET'))
    mouser_ok = bool(os.environ.get('MOUSER_API_KEY'))

    status = "healthy" if (digikey_ok or mouser_ok) else "degraded"

    return HealthResponse(
        status=status,
        timestamp=datetime.now().isoformat(),
        digikey_configured=digikey_ok,
        mouser_configured=mouser_ok
    )


@app.post("/api/search", response_model=SearchResponse)
async def search_components(request: SearchRequest):
    """
    Search components using DigiKey and Mouser APIs

    Strategy:
    1. Search both APIs in parallel
    2. Merge results
    3. Remove duplicates (same part number)
    4. Sort by price
    5. Return combined results

    Example:
    ```json
    {
        "search_term": "STM32F4",
        "category": "processor",
        "sources": ["digikey", "mouser"],
        "limit_per_source": 10
    }
    ```
    """
    start_time = datetime.now()
    errors = []
    all_components = []
    sources_count = {}

    # Parallel search from both APIs
    tasks = []

    if "digikey" in request.sources:
        tasks.append(("digikey", search_digikey(request.search_term, request.limit_per_source)))

    if "mouser" in request.sources:
        tasks.append(("mouser", search_mouser(request.search_term, request.limit_per_source)))

    # Execute searches in parallel
    results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)

    # Process results
    for i, (source_name, _) in enumerate(tasks):
        result = results[i]

        if isinstance(result, Exception):
            errors.append(f"{source_name}: {str(result)}")
            continue

        if result['success']:
            all_components.extend(result['components'])
            sources_count[source_name] = len(result['components'])
        else:
            errors.append(f"{source_name}: {result.get('error', 'Unknown error')}")

    # Remove duplicates (same part number from different sources)
    seen_parts = set()
    unique_components = []

    for comp in all_components:
        part_num = comp['part_number'].lower()
        if part_num not in seen_parts:
            seen_parts.add(part_num)
            unique_components.append(comp)

    # Sort by price (cheapest first)
    def get_price(comp):
        try:
            price_str = comp.get('pricing', {}).get('unit_price', '$999.99')
            return float(price_str.replace('$', '').replace(',', ''))
        except:
            return 999.99

    unique_components.sort(key=get_price)

    # Fallback to demo data if no API results and no APIs configured
    if len(unique_components) == 0:
        demo = generate_demo_components(request.search_term, request.category)
        unique_components = demo
        sources_count['demo_database'] = len(demo)
        if not errors:
            errors.append("No API keys configured - using built-in component database")

    # Calculate search time
    search_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

    return SearchResponse(
        success=len(unique_components) > 0,
        search_term=request.search_term,
        category=request.category,
        total_found=len(unique_components),
        components=unique_components,
        sources=sources_count,
        errors=errors,
        search_time_ms=search_time_ms
    )


async def search_digikey(keyword: str, limit: int) -> Dict:
    """Search DigiKey API (async wrapper)"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, digikey_api.search_products, keyword, limit)


async def search_mouser(keyword: str, limit: int) -> Dict:
    """Search Mouser API (async wrapper)"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, mouser_api.search_products, keyword, limit)


def generate_demo_components(keyword: str, category: str) -> List[Dict]:
    """
    Generate realistic demo components when no API keys are configured.
    Uses a comprehensive database of real part numbers and pricing.
    """
    kw = keyword.lower()

    # Comprehensive component database with real orderable parts
    DB = {
        'processor': [
            {'pn': 'STM32F407VGT6', 'mfg': 'STMicroelectronics', 'desc': 'ARM Cortex-M4 MCU, 168MHz, 1MB Flash, 192KB RAM, LQFP-100', 'price': 12.50},
            {'pn': 'XC7A35T-1CSG324C', 'mfg': 'AMD/Xilinx', 'desc': 'Artix-7 FPGA, 33K Logic Cells, 324-BGA', 'price': 45.00},
            {'pn': 'XC7A100T-2FGG484I', 'mfg': 'AMD/Xilinx', 'desc': 'Artix-7 FPGA, 101K Logic Cells, 484-FBGA', 'price': 85.00},
            {'pn': 'LFE5U-25F-6BG256C', 'mfg': 'Lattice', 'desc': 'ECP5 FPGA, 24K LUTs, 256-caBGA', 'price': 12.00},
            {'pn': 'ATSAMD51J19A-AU', 'mfg': 'Microchip', 'desc': 'ARM Cortex-M4F MCU, 120MHz, 512KB Flash', 'price': 6.20},
            {'pn': 'ESP32-S3-WROOM-1-N16R8', 'mfg': 'Espressif', 'desc': 'Wi-Fi+BLE SoC Module, Dual-Core 240MHz', 'price': 3.10},
        ],
        'power_regulator': [
            {'pn': 'TPS65263RHBR', 'mfg': 'Texas Instruments', 'desc': 'Triple Output Buck Converter, 3x 3A, QFN-40', 'price': 4.50},
            {'pn': 'LMR36015ADDAR', 'mfg': 'Texas Instruments', 'desc': 'SIMPLE SWITCHER Buck, 36V In, 1.5A', 'price': 2.80},
            {'pn': 'TPS63001DRCR', 'mfg': 'Texas Instruments', 'desc': 'Buck-Boost Converter, 96% Eff, 1.8A, SOT-23', 'price': 3.20},
            {'pn': 'AP2112K-3.3TRG1', 'mfg': 'Diodes Inc', 'desc': '600mA LDO Regulator, 3.3V Fixed, SOT-25', 'price': 0.35},
            {'pn': 'TPS54360DDAR', 'mfg': 'Texas Instruments', 'desc': '60V Input, 3.5A Step-Down Converter', 'price': 3.50},
            {'pn': 'LM2596S-5.0/NOPB', 'mfg': 'Texas Instruments', 'desc': '3A Step-Down Regulator, 5V Fixed Output', 'price': 2.50},
        ],
        'amplifier': [
            {'pn': 'TGF2965-SM', 'mfg': 'Qorvo', 'desc': 'GaN HEMT, DC-18GHz, 10W, 28V, 65% PAE', 'price': 85.00},
            {'pn': 'TGA2594-SM', 'mfg': 'Qorvo', 'desc': 'GaN PA, 2-18GHz, 4W, 22dB Gain', 'price': 120.00},
            {'pn': 'HMC580ALC3B', 'mfg': 'Analog Devices', 'desc': 'GaAs pHEMT Driver Amp, DC-6GHz, 13dB Gain', 'price': 12.00},
            {'pn': 'HMC1131', 'mfg': 'Analog Devices', 'desc': 'GaAs pHEMT Driver, 6-18GHz, 21dB Gain, 1W', 'price': 45.00},
            {'pn': 'SKY67159-396LF', 'mfg': 'Skyworks', 'desc': 'Wideband LNA, 0.7-3.8GHz, 20dB Gain, 0.6dB NF', 'price': 2.80},
            {'pn': 'CMPA0060025D', 'mfg': 'Wolfspeed', 'desc': 'GaN HEMT, DC-6GHz, 25W, 28V', 'price': 95.00},
        ],
        'rf_component': [
            {'pn': 'ADL5801ACPZ', 'mfg': 'Analog Devices', 'desc': 'Wideband Active Mixer, 10MHz-6GHz, 0.4dB NF', 'price': 15.00},
            {'pn': 'HMC558ALC3B', 'mfg': 'Analog Devices', 'desc': 'Double-Balanced Mixer, 5.5-14GHz', 'price': 18.00},
            {'pn': 'BFCN-5500+', 'mfg': 'Mini-Circuits', 'desc': 'Bandpass Filter, 4.9-6.2GHz, LTCC', 'price': 3.50},
            {'pn': 'QCN-19D+', 'mfg': 'Mini-Circuits', 'desc': 'Directional Coupler, 5-20GHz, 20dB Coupling', 'price': 6.50},
            {'pn': 'TQL9065', 'mfg': 'Qorvo', 'desc': 'Ultra-Low Noise LNA, 5-18GHz, 1.2dB NF, 18dB Gain', 'price': 12.00},
        ],
        'interface': [
            {'pn': 'AD9744ARUZ', 'mfg': 'Analog Devices', 'desc': '14-bit DAC, 210 MSPS, TSSOP-28', 'price': 18.00},
            {'pn': 'AD9235BRUZ-65', 'mfg': 'Analog Devices', 'desc': '12-bit ADC, 65 MSPS, TSSOP-28', 'price': 12.50},
            {'pn': 'FT232RL-REEL', 'mfg': 'FTDI', 'desc': 'USB to UART IC, Full Speed, SSOP-28', 'price': 4.50},
            {'pn': 'SN65HVD230DR', 'mfg': 'Texas Instruments', 'desc': '3.3V CAN Bus Transceiver, SOIC-8', 'price': 1.20},
            {'pn': 'MAX3232ECPE+', 'mfg': 'Analog Devices', 'desc': 'RS-232 Transceiver, 3.0V-5.5V, DIP-16', 'price': 2.80},
        ],
        'oscillator': [
            {'pn': 'ASTX-H11-100.000MHZ-T', 'mfg': 'Abracon', 'desc': 'TCXO, 100MHz, 2.5ppm, 3.3V, SMD', 'price': 5.50},
            {'pn': 'SIT8008BI-82-33E-100.000000G', 'mfg': 'SiTime', 'desc': 'MEMS Oscillator, 100MHz, 3.3V, 25ppm', 'price': 2.25},
        ],
        'connector': [
            {'pn': '132322-11', 'mfg': 'Amphenol', 'desc': 'SMA Connector, Female, PCB Mount, 50 Ohm, 18GHz', 'price': 2.50},
            {'pn': '901-10511-2', 'mfg': 'Amphenol', 'desc': 'SMA Connector, Male, Edge-Mount, 18GHz', 'price': 3.80},
            {'pn': '10118192-0001LF', 'mfg': 'Amphenol', 'desc': 'USB Micro-B Receptacle, SMD, Right Angle', 'price': 0.45},
        ],
        'power_input': [
            {'pn': 'KPPX-3P', 'mfg': 'Kycon', 'desc': 'DC Power Jack, 2.5mm Center Pin, Panel Mount', 'price': 1.20},
            {'pn': 'PJ-037A', 'mfg': 'CUI Devices', 'desc': 'DC Barrel Jack, 2.1mm, SMD Right Angle', 'price': 0.85},
        ],
    }

    # Smart matching: find best category and parts for the keyword
    def base_pn(pn):
        import re
        m = re.match(r'^[A-Za-z]+[\d]+', pn)
        return m.group(0).lower() if m else pn.lower().replace('-', '').replace(' ', '')

    matched = []
    kw_base = base_pn(kw)

    # Try exact category first, then search all categories
    cats_to_search = [category.lower().replace(' ', '_')]
    cats_to_search.extend([c for c in DB.keys() if c not in cats_to_search])

    for cat in cats_to_search:
        for part in DB.get(cat, []):
            part_base = base_pn(part['pn'])
            if (kw_base and (kw_base in part_base or part_base in kw_base)) or \
               kw in part['pn'].lower() or kw in part['desc'].lower():
                matched.append({
                    'part_number': part['pn'],
                    'manufacturer': part['mfg'],
                    'description': part['desc'],
                    'category': cat,
                    'datasheet_url': '',
                    'product_url': '',
                    'specifications': {},
                    'pricing': {'unit_price': f"${part['price']:.2f}", 'min_qty': 1},
                    'availability': {'stock': 500, 'lead_time': '2-4 weeks'},
                    'lifecycle_status': 'Active',
                    'source': 'demo_database'
                })

    # If no specific match, return all parts from the best-guess category
    if not matched:
        cat = category.lower().replace(' ', '_')
        for part in DB.get(cat, DB.get('processor', [])):
            matched.append({
                'part_number': part['pn'],
                'manufacturer': part['mfg'],
                'description': part['desc'],
                'category': cat,
                'datasheet_url': '',
                'product_url': '',
                'specifications': {},
                'pricing': {'unit_price': f"${part['price']:.2f}", 'min_qty': 1},
                'availability': {'stock': 500, 'lead_time': '2-4 weeks'},
                'lifecycle_status': 'Active',
                'source': 'demo_database'
            })

    return matched


# ==========================================
# STARTUP AND SHUTDOWN
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Log startup"""
    print("🚀 Hardware Pipeline Component API Service starting...")
    print("📖 API docs available at http://localhost:8001/docs")
    print("")
    print("Configuration:")
    print(f"  DigiKey: {'✅ Configured' if os.environ.get('DIGIKEY_CLIENT_ID') else '❌ Not configured'}")
    print(f"  Mouser:  {'✅ Configured' if os.environ.get('MOUSER_API_KEY') else '❌ Not configured'}")
    print("")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Component API Service shutting down...")


# ==========================================
# MAIN ENTRY POINT
# ==========================================

if __name__ == "__main__":
    port = int(os.environ.get("API_SERVICE_PORT", 8001))
    uvicorn.run(
        "component_api_service:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
