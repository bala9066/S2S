#!/usr/bin/env python3
"""
Hardware Pipeline - Phase 8: Software Generation REST API
FastAPI service that wraps phase8_codegen.py for n8n integration.
Follows the same pattern as scraper_api.py.
"""

import os
import json
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from phase8_codegen import generate_all, parse_hardware_context, ai_code_review, Phase8Database

logger = logging.getLogger(__name__)

# ==========================================
# FASTAPI APP CONFIGURATION
# ==========================================

app = FastAPI(
    title="Hardware Pipeline Phase 8 - Software Generation API",
    description="REST API for generating C/C++ driver code, tests, and build files from hardware specs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

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

class ProcessorSpec(BaseModel):
    type: str = "MCU"
    specific_part: str = "STM32F407VGT6"
    required_features: List[str] = []
    package: str = "LQFP"

class PowerSpec(BaseModel):
    input_voltage: str = "12V"
    output_power: str = "10W"
    rails_needed: List[str] = ["3.3V", "5V"]

class PrimaryComponents(BaseModel):
    processor: ProcessorSpec = ProcessorSpec()
    power: PowerSpec = PowerSpec()
    interfaces: List[str] = ["SPI", "I2C"]

class ParsedRequirements(BaseModel):
    primary_components: PrimaryComponents = PrimaryComponents()
    key_components_needed: List[Dict[str, Any]] = []
    special_requirements: List[str] = []
    certifications_needed: List[str] = []

class GenerateRequest(BaseModel):
    """Request model for /api/generate"""
    project_name: str = Field(..., min_length=1, description="Project name")
    system_type: str = Field(default="Digital_Controller", description="System type")
    original_requirements: str = Field(default="", description="Original text requirements")
    parsed_requirements: ParsedRequirements = ParsedRequirements()
    block_diagram: Dict[str, Any] = Field(default_factory=dict)
    bom: List[Dict[str, Any]] = Field(default_factory=list)
    glr: Dict[str, Any] = Field(default_factory=dict)
    project_id: Optional[int] = Field(default=None, description="DB project ID for tracking")
    run_review: bool = Field(default=False, description="Run AI code review")

class GeneratedFileResponse(BaseModel):
    filename: str
    language: str
    category: str
    line_count: int
    content: str

class CodeReviewResponse(BaseModel):
    score: int
    issues: List[Dict[str, str]]
    suggestions: List[str]
    passed: bool

class GenerateResponse(BaseModel):
    """Response model for /api/generate"""
    success: bool
    project_name: str
    system_type: str
    processor: str
    files: List[GeneratedFileResponse]
    file_count: int
    total_lines: int
    code_review: CodeReviewResponse
    generation_time_seconds: float
    timestamp: str
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database_connected: bool
    version: str

# ==========================================
# API ENDPOINTS
# ==========================================

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    db_connected = False
    try:
        db = Phase8Database()
        db.connect()
        db.disconnect()
        db_connected = True
    except Exception:
        pass

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        timestamp=datetime.now().isoformat(),
        database_connected=db_connected,
        version="1.0.0",
    )


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_code(request: GenerateRequest):
    """
    Generate all Phase 8 software artifacts from hardware specs.

    Accepts parsed requirements from prior phases and returns:
    - C driver code (HAL + device driver + main)
    - C++ driver (RAII-based)
    - Unit test suite
    - Makefile + CMakeLists.txt
    - README.md

    Example:
    ```json
    {
        "project_name": "MotorController",
        "system_type": "Motor_Control",
        "parsed_requirements": {
            "primary_components": {
                "processor": {"specific_part": "STM32F407VGT6"},
                "interfaces": ["CAN", "SPI", "PWM", "ADC"]
            }
        }
    }
    ```
    """
    try:
        input_data = {
            "project_name": request.project_name,
            "system_type": request.system_type,
            "original_requirements": request.original_requirements,
            "parsed_requirements": request.parsed_requirements.model_dump(),
            "block_diagram": request.block_diagram,
            "bom": request.bom,
            "glr": request.glr,
            "project_id": request.project_id,
        }

        result = generate_all(input_data, run_review=request.run_review)

        return GenerateResponse(
            success=result["success"],
            project_name=result["project_name"],
            system_type=result["system_type"],
            processor=result["processor"],
            files=[GeneratedFileResponse(**f) for f in result["files"]],
            file_count=result["file_count"],
            total_lines=result["total_lines"],
            code_review=CodeReviewResponse(**result["code_review"]),
            generation_time_seconds=result["generation_time_seconds"],
            timestamp=result["timestamp"],
        )

    except Exception as e:
        logger.exception("Code generation failed")
        return GenerateResponse(
            success=False,
            project_name=request.project_name,
            system_type=request.system_type,
            processor="Unknown",
            files=[],
            file_count=0,
            total_lines=0,
            code_review=CodeReviewResponse(score=0, issues=[], suggestions=[], passed=False),
            generation_time_seconds=0,
            timestamp=datetime.now().isoformat(),
            error=str(e),
        )


@app.post("/api/review")
async def review_code(request: GenerateRequest):
    """
    Generate code AND run AI code review.
    Same as /api/generate but forces run_review=True.
    """
    request.run_review = True
    return await generate_code(request)


# ==========================================
# STARTUP / SHUTDOWN
# ==========================================

@app.on_event("startup")
async def startup_event():
    print("Phase 8 Software Generation API starting...")
    print("API docs available at /docs")


@app.on_event("shutdown")
async def shutdown_event():
    print("Phase 8 API shutting down...")


# ==========================================
# MAIN ENTRY POINT
# ==========================================

if __name__ == "__main__":
    port = int(os.environ.get("PHASE8_API_PORT", 8002))
    uvicorn.run(
        "phase8_api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
    )
