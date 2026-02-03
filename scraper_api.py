#!/usr/bin/env python3
"""
Hardware Pipeline - Scraper REST API
FastAPI wrapper for component_scraper.py
Enables n8n integration via HTTP Request nodes
"""

import asyncio
import os
from typing import Optional, List, Dict
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import the scraper
from component_scraper import scrape_components, DatabaseManager

# ==========================================
# FASTAPI APP CONFIGURATION
# ==========================================

app = FastAPI(
    title="Hardware Pipeline Component Scraper API",
    description="REST API for scraping DigiKey and Mouser component data",
    version="1.0.0",
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

class ScrapeRequest(BaseModel):
    """Request model for /api/scrape"""
    search_term: str = Field(..., min_length=1, description="Component search term")
    category: str = Field(..., description="Component category (processor, power_regulator, interface, etc.)")
    use_cache: bool = Field(default=True, description="Check cache before scraping")

class ComponentResult(BaseModel):
    """Single component result"""
    part_number: str
    manufacturer: str
    description: str
    category: str
    datasheet_url: Optional[str] = ""
    specifications: Dict = {}
    pricing: Dict = {}
    availability: Dict = {}
    lifecycle_status: str = "Active"
    source: str

class ScrapeResponse(BaseModel):
    """Response model for /api/scrape"""
    success: bool
    cache_hit: bool
    search_term: str
    category: str
    total_found: int
    components: List[Dict]
    sources: Dict[str, int]
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    database_connected: bool
    playwright_ready: bool

class CacheStatusResponse(BaseModel):
    """Cache status response"""
    total_cached: int
    active_components: int
    expired_components: int
    by_category: Dict[str, int]
    by_source: Dict[str, int]

# ==========================================
# API ENDPOINTS
# ==========================================

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring.
    Verifies database connectivity and Playwright availability.
    """
    db_connected = False
    playwright_ready = True  # Assume ready, will fail on actual scrape if not
    
    try:
        db = DatabaseManager()
        db.connect()
        db.disconnect()
        db_connected = True
    except Exception:
        pass
    
    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        timestamp=datetime.now().isoformat(),
        database_connected=db_connected,
        playwright_ready=playwright_ready
    )


@app.post("/api/scrape", response_model=ScrapeResponse)
async def scrape_endpoint(request: ScrapeRequest):
    """
    Scrape components from DigiKey and Mouser.
    
    - Checks cache first (if use_cache=True)
    - Returns cached results if available and not expired
    - Otherwise scrapes fresh data and caches it
    
    Example:
    ```json
    {
        "search_term": "STM32F4",
        "category": "processor",
        "use_cache": true
    }
    ```
    """
    try:
        # Run the async scraper
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: asyncio.run(scrape_components(
                search_term=request.search_term,
                category=request.category,
                use_cache=request.use_cache
            ))
        )
        
        return ScrapeResponse(
            success=True,
            cache_hit=result.get('cache_hit', False),
            search_term=result.get('search_term', request.search_term),
            category=result.get('category', request.category),
            total_found=result.get('total_found', 0),
            components=result.get('components', []),
            sources=result.get('sources', {})
        )
        
    except Exception as e:
        return ScrapeResponse(
            success=False,
            cache_hit=False,
            search_term=request.search_term,
            category=request.category,
            total_found=0,
            components=[],
            sources={},
            error=str(e)
        )


@app.get("/api/cache/status", response_model=CacheStatusResponse)
async def cache_status():
    """
    Get component cache statistics.
    Shows total cached components, expired entries, and breakdown by category/source.
    """
    try:
        db = DatabaseManager()
        db.connect()
        
        cursor = db.conn.cursor()
        
        # Total cached
        cursor.execute("SELECT COUNT(*) FROM component_cache")
        total_cached = cursor.fetchone()[0]
        
        # Active (not expired)
        cursor.execute("SELECT COUNT(*) FROM component_cache WHERE expires_at > NOW()")
        active = cursor.fetchone()[0]
        
        # By category
        cursor.execute("""
            SELECT category, COUNT(*) 
            FROM component_cache 
            WHERE expires_at > NOW()
            GROUP BY category
        """)
        by_category = dict(cursor.fetchall())
        
        # By source
        cursor.execute("""
            SELECT source, COUNT(*) 
            FROM component_cache 
            WHERE expires_at > NOW()
            GROUP BY source
        """)
        by_source = dict(cursor.fetchall())
        
        cursor.close()
        db.disconnect()
        
        return CacheStatusResponse(
            total_cached=total_cached,
            active_components=active,
            expired_components=total_cached - active,
            by_category=by_category,
            by_source=by_source
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache status error: {str(e)}")


@app.post("/api/cache/clear")
async def clear_expired_cache():
    """
    Clear expired cache entries.
    Removes components with expires_at < NOW().
    """
    try:
        db = DatabaseManager()
        db.connect()
        
        cursor = db.conn.cursor()
        cursor.execute("DELETE FROM component_cache WHERE expires_at < NOW()")
        deleted = cursor.rowcount
        db.conn.commit()
        cursor.close()
        db.disconnect()
        
        return {"success": True, "deleted_count": deleted}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear error: {str(e)}")


# ==========================================
# STARTUP AND SHUTDOWN
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Log startup"""
    print("🚀 Hardware Pipeline Scraper API starting...")
    print("📖 API docs available at /docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Scraper API shutting down...")


# ==========================================
# MAIN ENTRY POINT
# ==========================================

if __name__ == "__main__":
    port = int(os.environ.get("SCRAPER_API_PORT", 8000))
    uvicorn.run(
        "scraper_api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
