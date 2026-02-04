#!/bin/bash
#
# Phase 1 Pre-Flight Check Script
# Validates environment before testing Phase 1 workflow
#

set -e

echo "════════════════════════════════════════════════════════════"
echo "  PHASE 1 PRE-FLIGHT CHECK"
echo "════════════════════════════════════════════════════════════"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

# Function to check command
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✅ $1 found${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 NOT found${NC}"
        FAILURES=$((FAILURES + 1))
        return 1
    fi
}

# Function to check file
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅ $1 exists${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 MISSING${NC}"
        FAILURES=$((FAILURES + 1))
        return 1
    fi
}

echo "1. Checking Required Commands..."
echo "────────────────────────────────────────────────────────────"
check_command docker
check_command python3
check_command node
check_command git
echo ""

echo "2. Checking Docker..."
echo "────────────────────────────────────────────────────────────"
if docker info &> /dev/null; then
    echo -e "${GREEN}✅ Docker daemon is running${NC}"
    echo "   Docker version: $(docker --version)"
else
    echo -e "${RED}❌ Docker daemon is NOT running${NC}"
    FAILURES=$((FAILURES + 1))
fi
echo ""

echo "3. Checking Docker Compose..."
echo "────────────────────────────────────────────────────────────"
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
    echo -e "${GREEN}✅ Docker Compose (plugin) found${NC}"
    echo "   Version: $(docker compose version)"
elif docker-compose --version &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    echo -e "${GREEN}✅ Docker Compose (standalone) found${NC}"
    echo "   Version: $(docker-compose --version)"
else
    echo -e "${RED}❌ Docker Compose NOT found${NC}"
    FAILURES=$((FAILURES + 1))
fi
echo ""

echo "4. Checking Required Files..."
echo "────────────────────────────────────────────────────────────"
check_file "docker-compose.yml"
check_file ".env.example"
check_file "Phase1_Complete_Workflow_READY_TO_IMPORT.json"
check_file "component_scraper.py"
check_file "scraper_api.py"
check_file "init-db.sql"
check_file "improved_ai_prompt.js"
check_file "improved_block_diagram_generator.js"
echo ""

echo "5. Checking .env File..."
echo "────────────────────────────────────────────────────────────"
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"

    # Check for Claude API key
    if grep -q "CLAUDE_API_KEY=sk-ant" .env 2>/dev/null; then
        echo -e "${GREEN}✅ CLAUDE_API_KEY is set${NC}"
    else
        echo -e "${YELLOW}⚠️  CLAUDE_API_KEY not set or invalid${NC}"
        echo "   Please add your Claude API key to .env file"
        FAILURES=$((FAILURES + 1))
    fi

    # Check for PostgreSQL password
    if grep -q "POSTGRES_PASSWORD=" .env 2>/dev/null; then
        echo -e "${GREEN}✅ POSTGRES_PASSWORD is set${NC}"
    else
        echo -e "${YELLOW}⚠️  POSTGRES_PASSWORD not set${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  .env file NOT found${NC}"
    echo "   Creating from .env.example..."
    if cp .env.example .env; then
        echo -e "${GREEN}✅ Created .env from template${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env and add your CLAUDE_API_KEY${NC}"
        FAILURES=$((FAILURES + 1))
    else
        echo -e "${RED}❌ Failed to create .env${NC}"
        FAILURES=$((FAILURES + 1))
    fi
fi
echo ""

echo "6. Validating File Syntax..."
echo "────────────────────────────────────────────────────────────"

# Validate JSON
if python3 -c "import json; json.load(open('Phase1_Complete_Workflow_READY_TO_IMPORT.json'))" 2>/dev/null; then
    echo -e "${GREEN}✅ Workflow JSON is valid${NC}"
else
    echo -e "${RED}❌ Workflow JSON is INVALID${NC}"
    FAILURES=$((FAILURES + 1))
fi

# Validate YAML
if python3 -c "import yaml; yaml.safe_load(open('docker-compose.yml'))" 2>/dev/null; then
    echo -e "${GREEN}✅ docker-compose.yml is valid${NC}"
else
    echo -e "${RED}❌ docker-compose.yml is INVALID${NC}"
    FAILURES=$((FAILURES + 1))
fi

# Validate JavaScript
if node --check improved_ai_prompt.js 2>/dev/null; then
    echo -e "${GREEN}✅ improved_ai_prompt.js syntax valid${NC}"
else
    echo -e "${RED}❌ improved_ai_prompt.js has syntax errors${NC}"
    FAILURES=$((FAILURES + 1))
fi

if node --check improved_block_diagram_generator.js 2>/dev/null; then
    echo -e "${GREEN}✅ improved_block_diagram_generator.js syntax valid${NC}"
else
    echo -e "${RED}❌ improved_block_diagram_generator.js has syntax errors${NC}"
    FAILURES=$((FAILURES + 1))
fi

# Validate Python
if python3 -m py_compile component_scraper.py 2>/dev/null; then
    echo -e "${GREEN}✅ component_scraper.py syntax valid${NC}"
else
    echo -e "${RED}❌ component_scraper.py has syntax errors${NC}"
    FAILURES=$((FAILURES + 1))
fi

if python3 -m py_compile scraper_api.py 2>/dev/null; then
    echo -e "${GREEN}✅ scraper_api.py syntax valid${NC}"
else
    echo -e "${RED}❌ scraper_api.py has syntax errors${NC}"
    FAILURES=$((FAILURES + 1))
fi
echo ""

echo "7. Checking Port Availability..."
echo "────────────────────────────────────────────────────────────"
PORTS=(5432 5678 8000 6379 5050)
PORT_NAMES=("PostgreSQL" "n8n" "Playwright API" "Redis" "pgAdmin")

for i in "${!PORTS[@]}"; do
    PORT=${PORTS[$i]}
    NAME=${PORT_NAMES[$i]}

    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -ln 2>/dev/null | grep -q ":$PORT "; then
        echo -e "${YELLOW}⚠️  Port $PORT ($NAME) is already in use${NC}"
        echo "   You may need to stop existing services or change ports"
    else
        echo -e "${GREEN}✅ Port $PORT ($NAME) is available${NC}"
    fi
done
echo ""

echo "8. Checking Disk Space..."
echo "────────────────────────────────────────────────────────────"
AVAILABLE_GB=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$AVAILABLE_GB" -gt 5 ]; then
    echo -e "${GREEN}✅ Sufficient disk space: ${AVAILABLE_GB}GB available${NC}"
else
    echo -e "${YELLOW}⚠️  Low disk space: only ${AVAILABLE_GB}GB available${NC}"
    echo "   Recommended: at least 10GB free"
fi
echo ""

echo "════════════════════════════════════════════════════════════"
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ PRE-FLIGHT CHECK PASSED${NC}"
    echo ""
    echo "You are ready to start Phase 1 testing!"
    echo ""
    echo "Next steps:"
    echo "  1. Make sure CLAUDE_API_KEY is set in .env"
    echo "  2. Run: docker compose up -d"
    echo "  3. Run: ./test_phase1_workflow.sh"
    exit 0
else
    echo -e "${RED}❌ PRE-FLIGHT CHECK FAILED${NC}"
    echo ""
    echo "Found $FAILURES issue(s). Please fix them before proceeding."
    exit 1
fi
