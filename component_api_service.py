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
