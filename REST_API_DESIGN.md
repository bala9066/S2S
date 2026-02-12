# REST API Design - Frontend Bridge

## 🌐 API Architecture: Making Backend Frontend-Ready

This document shows how to expose the current n8n backend via REST API,
allowing any frontend (React, Vue, mobile app) to connect later.

---

## 🏗️ Current vs Proposed Architecture

### Current (n8n Only):
```
User ← n8n Chat Interface → n8n Workflow → Component API/Database
```

### Proposed (Frontend-Ready):
```
User ← React/Mobile Frontend → REST API → n8n Workflow → Component API/Database
      ↑                              ↑
      │                              └─ New FastAPI layer
      └─ Can still use n8n chat for testing
```

---

## 📡 API Endpoints Design

### Base URL: `http://localhost:8000/api/v1`

---

## 1. Projects API

### `POST /api/v1/projects`
**Create new project**

**Request:**
```json
{
  "name": "RF Transmitter System",
  "type": "RF_Wireless",
  "requirements": "Design RF system with Artix-7 FPGA, 40dBm output power, 5-18GHz frequency range, buck converters for power"
}
```

**Response:**
```json
{
  "project_id": "proj_abc123",
  "name": "RF Transmitter System",
  "type": "RF_Wireless",
  "status": "requirements_received",
  "created_at": "2026-02-11T18:30:00Z",
  "workflow_url": "http://localhost:8000/api/v1/projects/proj_abc123"
}
```

---

### `GET /api/v1/projects`
**List all projects**

**Query Parameters:**
- `limit` (int, default: 20)
- `offset` (int, default: 0)
- `status` (string, optional): filter by status
- `type` (string, optional): filter by project type

**Response:**
```json
{
  "total": 15,
  "limit": 20,
  "offset": 0,
  "projects": [
    {
      "project_id": "proj_abc123",
      "name": "RF Transmitter System",
      "type": "RF_Wireless",
      "status": "bom_generated",
      "created_at": "2026-02-11T18:30:00Z",
      "updated_at": "2026-02-11T19:15:00Z",
      "estimated_cost": 687.45
    },
    {
      "project_id": "proj_xyz789",
      "name": "Motor Controller",
      "type": "Motor_Controller",
      "status": "awaiting_approval",
      "created_at": "2026-02-10T14:20:00Z",
      "updated_at": "2026-02-10T14:45:00Z"
    }
  ]
}
```

---

### `GET /api/v1/projects/{project_id}`
**Get project details**

**Response:**
```json
{
  "project_id": "proj_abc123",
  "name": "RF Transmitter System",
  "type": "RF_Wireless",
  "status": "bom_generated",
  "created_at": "2026-02-11T18:30:00Z",
  "updated_at": "2026-02-11T19:15:00Z",
  "requirements": {
    "raw_text": "Design RF system with Artix-7 FPGA...",
    "parsed_parameters": {
      "processor": "Artix-7 FPGA",
      "power_output": "40dBm",
      "frequency_range": "5-18GHz",
      "power_management": "buck converters"
    }
  },
  "block_diagram": {
    "status": "approved",
    "total_blocks": 14,
    "diagram_url": "/api/v1/projects/proj_abc123/diagram"
  },
  "components": {
    "total": 52,
    "selected": 52,
    "estimated_cost": 687.45
  },
  "bom": {
    "status": "generated",
    "download_url": "/api/v1/projects/proj_abc123/bom/download"
  }
}
```

---

### `DELETE /api/v1/projects/{project_id}`
**Delete project**

**Response:**
```json
{
  "success": true,
  "message": "Project proj_abc123 deleted successfully"
}
```

---

## 2. Requirements API

### `POST /api/v1/projects/{project_id}/parse-requirements`
**Parse requirements using AI**

**Request:**
```json
{
  "requirements": "Design RF system with Artix-7 FPGA, 40dBm output power, 5-18GHz frequency range, buck converters for power"
}
```

**Response:**
```json
{
  "success": true,
  "parsed_data": {
    "project_type": "RF_Wireless",
    "processor": {
      "type": "FPGA",
      "family": "Artix-7",
      "suggested_part": "XC7A35T"
    },
    "rf_specs": {
      "power_output": "40dBm",
      "power_output_watts": 10,
      "frequency_range": {
        "min": 5e9,
        "max": 18e9,
        "unit": "Hz"
      }
    },
    "power_system": {
      "type": "buck_converters",
      "rails_needed": [1.0, 1.8, 3.3, 28]
    }
  },
  "confidence": 0.95,
  "ai_model": "claude-sonnet-4.5"
}
```

---

## 3. Block Diagram API

### `POST /api/v1/projects/{project_id}/generate-diagram`
**Generate block diagram**

**Request:** (Optional - uses parsed requirements if not provided)
```json
{
  "force_regenerate": false
}
```

**Response:**
```json
{
  "success": true,
  "diagram": {
    "blocks": [
      {
        "id": "B1",
        "type": "power_input",
        "label": "Power Input",
        "description": "12-48V DC input",
        "position": {"x": 100, "y": 50}
      },
      {
        "id": "B2",
        "type": "power_regulator",
        "label": "Buck-Boost 1.0V",
        "description": "TPS65263, 1.0V 3A for FPGA core",
        "position": {"x": 300, "y": 50}
      }
    ],
    "connections": [
      {
        "from": "B1",
        "to": "B2",
        "label": "DC power",
        "signal_type": "power"
      }
    ],
    "metadata": {
      "total_blocks": 14,
      "total_connections": 13,
      "complexity_score": 0.65
    }
  },
  "mermaid_code": "graph TD\nB1[Power Input]...",
  "html_preview_url": "/api/v1/projects/proj_abc123/diagram/preview"
}
```

---

### `GET /api/v1/projects/{project_id}/diagram`
**Get block diagram (current version)**

**Response:** Same as above

---

### `GET /api/v1/projects/{project_id}/diagram/preview`
**Get HTML preview of diagram**

**Response:** HTML page with Mermaid diagram

---

### `POST /api/v1/projects/{project_id}/diagram/approve`
**Approve block diagram**

**Request:**
```json
{
  "approved": true,
  "comments": "Looks good, proceed to component selection"
}
```

**Response:**
```json
{
  "success": true,
  "project_status": "diagram_approved",
  "next_step": "component_selection"
}
```

---

## 4. Component Search API

### `POST /api/v1/projects/{project_id}/search-components`
**Search components for blocks**

**Request:** (Automatic based on diagram)
```json
{
  "force_search": false,
  "sources": ["digikey", "mouser"],
  "limit_per_source": 5
}
```

**Response:**
```json
{
  "success": true,
  "searches_performed": 8,
  "total_components_found": 52,
  "search_time_ms": 850,
  "components_by_block": {
    "B6_FPGA": [
      {
        "part_number": "XC7A35T-1CSG324C",
        "manufacturer": "Xilinx",
        "description": "FPGA Artix-7, 324-BGA, 33,280 logic cells",
        "pricing": {
          "unit_price": "$58.50",
          "currency": "USD",
          "quantity_breaks": [
            {"qty": 1, "price": 58.50},
            {"qty": 10, "price": 52.65},
            {"qty": 100, "price": 46.80}
          ]
        },
        "availability": {
          "in_stock": true,
          "quantity": 145,
          "lead_time_days": 3
        },
        "source": "digikey",
        "datasheet_url": "https://..."
      }
    ]
  }
}
```

---

### `GET /api/v1/components/search`
**Generic component search (not tied to project)**

**Query Parameters:**
- `q` (string, required): search term
- `category` (string, optional): component category
- `sources` (array, default: ["digikey", "mouser"])
- `limit` (int, default: 10)
- `in_stock_only` (bool, default: false)

**Response:**
```json
{
  "success": true,
  "total_found": 18,
  "search_time_ms": 650,
  "components": [
    {
      "part_number": "STM32F407VGT6",
      "manufacturer": "STMicroelectronics",
      "category": "processor",
      "description": "ARM Cortex-M4 MCU, 168MHz, 1MB Flash",
      "pricing": {
        "unit_price": "$12.50",
        "currency": "USD"
      },
      "availability": {
        "in_stock": true,
        "quantity": 456
      },
      "source": "digikey"
    }
  ]
}
```

---

## 5. Component Selection API

### `POST /api/v1/projects/{project_id}/select-component`
**Select a component for a block**

**Request:**
```json
{
  "block_id": "B6",
  "part_number": "XC7A35T-1CSG324C",
  "source": "digikey",
  "reason": "Best price/performance ratio"
}
```

**Response:**
```json
{
  "success": true,
  "block_id": "B6",
  "selected_component": {
    "part_number": "XC7A35T-1CSG324C",
    "price": 58.50
  },
  "total_cost_update": 687.45
}
```

---

### `GET /api/v1/projects/{project_id}/components`
**Get all selected components**

**Response:**
```json
{
  "total_selected": 14,
  "total_cost": 687.45,
  "components": [
    {
      "block_id": "B6",
      "part_number": "XC7A35T-1CSG324C",
      "quantity": 1,
      "unit_price": 58.50,
      "total_price": 58.50
    }
  ]
}
```

---

## 6. BOM API

### `POST /api/v1/projects/{project_id}/generate-bom`
**Generate Bill of Materials**

**Request:**
```json
{
  "include_alternates": true,
  "currency": "USD"
}
```

**Response:**
```json
{
  "success": true,
  "bom": {
    "project_id": "proj_abc123",
    "project_name": "RF Transmitter System",
    "generated_at": "2026-02-11T19:15:00Z",
    "total_components": 52,
    "total_cost": 687.45,
    "currency": "USD",
    "categories": [
      {
        "category": "RF",
        "count": 8,
        "total_cost": 220.18,
        "percentage": 32
      },
      {
        "category": "Power",
        "count": 12,
        "total_cost": 165.00,
        "percentage": 24
      }
    ],
    "items": [
      {
        "reference": "U1",
        "quantity": 1,
        "part_number": "XC7A35T-1CSG324C",
        "manufacturer": "Xilinx",
        "description": "FPGA Artix-7",
        "category": "processor",
        "unit_price": 58.50,
        "total_price": 58.50,
        "source": "digikey",
        "lead_time_days": 3
      }
    ]
  }
}
```

---

### `GET /api/v1/projects/{project_id}/bom`
**Get generated BOM**

**Response:** Same as above

---

### `GET /api/v1/projects/{project_id}/bom/download`
**Download BOM in various formats**

**Query Parameters:**
- `format` (string): csv, excel, pdf, json

**Response:** File download

---

## 7. Real-Time Updates (WebSocket)

### `WS /api/v1/ws/{project_id}`
**WebSocket connection for real-time updates**

**Messages from server:**

**1. Progress Update:**
```json
{
  "type": "progress",
  "step": "parsing_requirements",
  "progress": 0.25,
  "message": "AI is analyzing requirements..."
}
```

**2. Diagram Generated:**
```json
{
  "type": "diagram_ready",
  "diagram_url": "/api/v1/projects/proj_abc123/diagram",
  "blocks_count": 14
}
```

**3. Component Search Complete:**
```json
{
  "type": "components_found",
  "total_found": 52,
  "estimated_cost": 687.45
}
```

**4. Error:**
```json
{
  "type": "error",
  "error_code": "API_RATE_LIMIT",
  "message": "DigiKey API rate limit exceeded. Retry in 60 seconds.",
  "retry_after": 60
}
```

---

## 8. Authentication (Future)

### `POST /api/v1/auth/register`
**Register new user**

### `POST /api/v1/auth/login`
**Login**

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### `POST /api/v1/auth/refresh`
**Refresh access token**

---

## 9. Health & Status API

### `GET /api/v1/health`
**Check API health**

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "n8n": "healthy",
    "component_api": "healthy",
    "claude_api": "healthy",
    "digikey_api": "configured",
    "mouser_api": "configured"
  },
  "uptime_seconds": 3600
}
```

---

### `GET /api/v1/stats`
**Get system statistics**

**Response:**
```json
{
  "total_projects": 15,
  "total_boms_generated": 12,
  "total_components_searched": 1450,
  "average_project_cost": 450.75,
  "api_usage": {
    "digikey_requests_today": 145,
    "mouser_requests_today": 132
  }
}
```

---

## 🏗️ Implementation Plan

### Phase 1: Core API (1 week)

**Days 1-2: Setup FastAPI**
```bash
# Create new FastAPI application
mkdir backend_api
cd backend_api
pip install fastapi uvicorn sqlalchemy pydantic

# Project structure:
backend_api/
├── main.py              # FastAPI app
├── routers/
│   ├── projects.py      # Projects endpoints
│   ├── diagrams.py      # Diagram endpoints
│   ├── components.py    # Component endpoints
│   └── bom.py           # BOM endpoints
├── models/              # Database models
├── schemas/             # Pydantic schemas
├── services/
│   └── n8n_client.py    # n8n API client
└── database.py          # Database connection
```

**Days 3-4: Projects + Requirements API**
- POST /projects
- GET /projects
- GET /projects/{id}
- POST /projects/{id}/parse-requirements

**Days 5-7: Diagram + Components + BOM API**
- POST /projects/{id}/generate-diagram
- POST /projects/{id}/search-components
- POST /projects/{id}/generate-bom

---

### Phase 2: WebSocket + Real-time (2-3 days)

- WebSocket endpoint for real-time updates
- Progress tracking
- Error handling

---

### Phase 3: Authentication (2-3 days)

- JWT authentication
- User registration/login
- Protected endpoints

---

### Phase 4: Documentation (1 day)

- OpenAPI/Swagger auto-generated
- API documentation site
- Example requests/responses

---

## 💻 Example FastAPI Code

### `backend_api/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import projects, diagrams, components, bom

app = FastAPI(
    title="Hardware Pipeline API",
    version="1.0.0",
    description="REST API for Hardware Design Automation"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(diagrams.router, prefix="/api/v1", tags=["diagrams"])
app.include_router(components.router, prefix="/api/v1", tags=["components"])
app.include_router(bom.router, prefix="/api/v1", tags=["bom"])

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

### `backend_api/routers/projects.py`

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    type: str
    requirements: str

class Project(BaseModel):
    project_id: str
    name: str
    type: str
    status: str
    created_at: datetime
    updated_at: datetime

@router.post("/", response_model=Project)
async def create_project(project: ProjectCreate):
    """Create a new hardware project"""

    # Generate unique ID
    project_id = f"proj_{uuid.uuid4().hex[:10]}"

    # Call n8n workflow via HTTP
    # (This triggers the existing Phase 1 workflow)
    n8n_result = await trigger_n8n_workflow(
        project_name=project.name,
        project_type=project.type,
        requirements=project.requirements
    )

    # Save to database
    db_project = await save_project_to_db(
        project_id=project_id,
        name=project.name,
        type=project.type,
        status="requirements_received"
    )

    return db_project

@router.get("/", response_model=List[Project])
async def list_projects(limit: int = 20, offset: int = 0):
    """List all projects"""
    projects = await get_projects_from_db(limit=limit, offset=offset)
    return projects

@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get project details"""
    project = await get_project_from_db(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
```

---

## 🚀 How Frontend Connects

### React Example:

```typescript
// frontend/src/api/projects.ts
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

export const createProject = async (data: {
  name: string;
  type: string;
  requirements: string;
}) => {
  const response = await axios.post(`${API_BASE}/projects`, data);
  return response.data;
};

export const getProject = async (projectId: string) => {
  const response = await axios.get(`${API_BASE}/projects/${projectId}`);
  return response.data;
};

export const generateDiagram = async (projectId: string) => {
  const response = await axios.post(
    `${API_BASE}/projects/${projectId}/generate-diagram`
  );
  return response.data;
};

// React component
const CreateProject = () => {
  const [requirements, setRequirements] = useState('');

  const handleSubmit = async () => {
    const project = await createProject({
      name: 'RF Transmitter',
      type: 'RF_Wireless',
      requirements: requirements
    });

    // Navigate to project page
    navigate(`/projects/${project.project_id}`);
  };

  return (
    <div>
      <textarea value={requirements} onChange={e => setRequirements(e.target.value)} />
      <button onClick={handleSubmit}>Create Project</button>
    </div>
  );
};
```

---

## 📊 Summary

### What This Achieves:

✅ **Decouples frontend from backend**
- Any frontend can connect (React, Vue, Mobile)
- Backend can evolve independently

✅ **Keeps existing n8n workflows**
- No need to rewrite backend logic
- API wraps n8n calls

✅ **Professional API design**
- RESTful patterns
- OpenAPI documentation
- Versioned endpoints

✅ **Frontend-ready**
- Build UI whenever ready
- Can test API with Postman/Insomnia first
- WebSocket for real-time UX

✅ **Future-proof**
- Authentication ready
- Multi-user ready
- Mobile app ready

---

## 🎯 Recommendation

1. **This week:** Fix "0 components" issue, test backend with n8n
2. **Next week:** Build REST API layer (5-7 days)
3. **Week 3-4:** Build React frontend (if desired)

**Benefits:**
- Can use n8n chat while building API
- Can test API with Postman before frontend
- Frontend becomes simple consumer of API
- Mobile app becomes possible later

---

**Want me to implement this REST API layer, or focus on backend testing first?**
