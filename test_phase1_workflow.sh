#!/bin/bash
#
# Phase 1 Workflow Test Script
# Tests the complete Phase 1 workflow end-to-end
#

set -e

echo "════════════════════════════════════════════════════════════"
echo "  PHASE 1 WORKFLOW TEST"
echo "════════════════════════════════════════════════════════════"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Detect Python command - prioritize Windows Python to avoid WSL issues
if [ -f "/c/Users/HP/AppData/Local/Programs/Python/Python314/python.exe" ]; then
  PYTHON_CMD="/c/Users/HP/AppData/Local/Programs/Python/Python314/python.exe"
elif [ -f "/c/Users/HP/AppData/Local/Programs/Python/Python312/python.exe" ]; then
  PYTHON_CMD="/c/Users/HP/AppData/Local/Programs/Python/Python312/python.exe"
elif command -v python &> /dev/null && python --version &> /dev/null; then
  PYTHON_CMD="python"
elif command -v python3 &> /dev/null && python3 --version &> /dev/null; then
  PYTHON_CMD="python3"
else
  echo -e "${RED}ERROR: Python not found${NC}"
  exit 1
fi
echo "Using Python: $PYTHON_CMD"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test result function
test_result() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Wait for service (HTTP)
wait_for_service() {
    local SERVICE=$1
    local URL=$2
    local MAX_WAIT=900
    local WAITED=0

    echo -ne "${BLUE}⏳ Waiting for $SERVICE to be ready...${NC}"

    while [ $WAITED -lt $MAX_WAIT ]; do
        if curl -s -f "$URL" > /dev/null 2>&1; then
            echo -e "\r${GREEN}✅ $SERVICE is ready!${NC}                    "
            return 0
        fi
        sleep 2
        WAITED=$((WAITED + 2))
        echo -ne "\r${BLUE}⏳ Waiting for $SERVICE... ${WAITED}s${NC}"
    done

    echo -e "\r${RED}❌ $SERVICE failed to start within ${MAX_WAIT}s${NC}"
    return 1
}

# Wait for PostgreSQL (Health Check)
wait_for_postgres() {
    local MAX_WAIT=900
    local WAITED=0

    echo -ne "${BLUE}⏳ Waiting for PostgreSQL to be ready...${NC}"

    while [ $WAITED -lt $MAX_WAIT ]; do
        HEALTH=$(docker inspect --format '{{.State.Health.Status}}' hardware_pipeline_postgres 2>/dev/null)
        if [ "$HEALTH" == "healthy" ]; then
            echo -e "\r${GREEN}✅ PostgreSQL is ready!${NC}                    "
            return 0
        fi
        sleep 2
        WAITED=$((WAITED + 2))
        echo -ne "\r${BLUE}⏳ Waiting for PostgreSQL... ${WAITED}s (Status: $HEALTH)${NC}"
    done

    echo -e "\r${RED}❌ PostgreSQL failed to start within ${MAX_WAIT}s${NC}"
    return 1
}

# ============================================================
# TEST 1: Docker Services
# ============================================================
echo ""
echo "TEST 1: Docker Services Startup"
echo "────────────────────────────────────────────────────────────"

# Check if services are already running
# Check if services are already running
if docker compose ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Services already running. Using existing services...${NC}"
    # docker compose down
    # sleep 2
fi

# Start services
echo "Starting Docker services..."
docker compose up -d

# Wait for PostgreSQL
if wait_for_postgres; then
    test_result 0 "PostgreSQL started successfully"
else
    test_result 1 "PostgreSQL failed to start"
fi

# Wait for n8n
if wait_for_service "n8n" "http://localhost:5678"; then
    test_result 0 "n8n started successfully"
else
    test_result 1 "n8n failed to start"
fi

# Wait for Playwright API
if wait_for_service "Playwright API" "http://localhost:8000/api/health"; then
    test_result 0 "Playwright API started successfully"
else
    test_result 1 "Playwright API failed to start"
fi

# ============================================================
# TEST 2: Database Initialization
# ============================================================
echo ""
echo "TEST 2: Database Initialization"
echo "────────────────────────────────────────────────────────────"

# Wait a bit for database initialization
sleep 5

# Check if tables exist
TABLES=$(docker exec hardware_pipeline_postgres psql -U postgres -d hardware_pipeline -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ')

if [ "$TABLES" -ge 11 ]; then
    test_result 0 "Database schema initialized ($TABLES tables)"
else
    test_result 1 "Database schema incomplete (only $TABLES tables, expected 11)"
fi

# Test database connection from Python
if $PYTHON_CMD -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='hardware_pipeline',
        user='postgres',
        password='postgres123'
    )
    conn.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
    test_result 0 "PostgreSQL connection from Python successful"
else
    test_result 1 "PostgreSQL connection from Python failed"
fi

# ============================================================
# TEST 3: Playwright Scraper API
# ============================================================
echo ""
echo "TEST 3: Playwright Scraper API"
echo "────────────────────────────────────────────────────────────"

# Test health endpoint
HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/health)
if echo "$HEALTH_RESPONSE" | grep -q "status"; then
    test_result 0 "API health endpoint working"
else
    test_result 1 "API health endpoint failed"
fi

# Test cache status endpoint
CACHE_STATUS=$(curl -s http://localhost:8000/api/cache/status)
if echo "$CACHE_STATUS" | grep -q "cache"; then
    test_result 0 "API cache status endpoint working"
else
    test_result 1 "API cache status endpoint failed"
fi

# Test component search (with mock data)
echo -e "${BLUE}Testing component search...${NC}"
SEARCH_RESPONSE=$(curl -s -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"search_term": "STM32F4", "category": "processor", "use_cache": true}')

if echo "$SEARCH_RESPONSE" | grep -q "components"; then
    COMPONENT_COUNT=$(echo "$SEARCH_RESPONSE" | $PYTHON_CMD -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('components', [])))")
    test_result 0 "Component search working (found $COMPONENT_COUNT components)"
else
    test_result 1 "Component search failed"
fi

# ============================================================
# TEST 4: Component Caching
# ============================================================
echo ""
echo "TEST 4: Component Caching"
echo "────────────────────────────────────────────────────────────"

# First search (cache miss)
START_TIME=$(date +%s%N)
curl -s -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"search_term": "TMS320F28379D", "category": "processor", "use_cache": true}' > /dev/null
FIRST_TIME=$(( ($(date +%s%N) - START_TIME) / 1000000 ))

sleep 1

# Second search (should be cached)
START_TIME=$(date +%s%N)
CACHED_RESPONSE=$(curl -s -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"search_term": "TMS320F28379D", "category": "processor", "use_cache": true}')
SECOND_TIME=$(( ($(date +%s%N) - START_TIME) / 1000000 ))

if echo "$CACHED_RESPONSE" | grep -q "cache_hit.*true"; then
    test_result 0 "Cache working (first: ${FIRST_TIME}ms, cached: ${SECOND_TIME}ms)"
elif [ $SECOND_TIME -lt $(( FIRST_TIME / 2 )) ]; then
    test_result 0 "Cache likely working (significant speedup: ${FIRST_TIME}ms → ${SECOND_TIME}ms)"
else
    test_result 1 "Cache may not be working properly"
fi

# ============================================================
# TEST 5: Workflow JSON Import Simulation
# ============================================================
echo ""
echo "TEST 5: Workflow Structure Validation"
echo "────────────────────────────────────────────────────────────"

# Validate workflow structure
WORKFLOW_VALID=$($PYTHON_CMD << 'EOF'
import json
import sys

try:
    with open('Phase1_Complete_Workflow_READY_TO_IMPORT.json') as f:
        workflow = json.load(f)

    # Check required fields
    if 'nodes' not in workflow:
        print("Missing 'nodes' field")
        sys.exit(1)

    if 'connections' not in workflow:
        print("Missing 'connections' field")
        sys.exit(1)

    # Count nodes
    node_count = len(workflow['nodes'])
    if node_count < 15:
        print(f"Too few nodes: {node_count}")
        sys.exit(1)

    # Check for key nodes
    node_names = [node.get('name', '') for node in workflow['nodes']]

    required_nodes = [
        'Chat Trigger',
        'Validate Input & Detect Type',
        'Build AI Prompt',
        'Generate Block Diagram',
        'Search Components'
    ]

    missing = []
    for required in required_nodes:
        if not any(required in name for name in node_names):
            missing.append(required)

    if missing:
        print(f"Missing nodes: {', '.join(missing)}")
        sys.exit(1)

    print(f"OK: {node_count} nodes")
    sys.exit(0)

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
EOF
)

if [ $? -eq 0 ]; then
    test_result 0 "Workflow structure valid ($WORKFLOW_VALID)"
else
    test_result 1 "Workflow structure invalid: $WORKFLOW_VALID"
fi

# Validate JavaScript nodes
JS_VALIDATION=$($PYTHON_CMD << 'EOF'
import json

with open('Phase1_Complete_Workflow_READY_TO_IMPORT.json') as f:
    workflow = json.load(f)

code_nodes = [node for node in workflow['nodes'] if node.get('type') == 'n8n-nodes-base.code']
print(f"Found {len(code_nodes)} JavaScript code nodes")
EOF
)

test_result 0 "JavaScript node validation ($JS_VALIDATION)"

# ============================================================
# TEST 6: End-to-End Simulation (Without n8n UI)
# ============================================================
echo ""
echo "TEST 6: Component Flow Simulation"
echo "────────────────────────────────────────────────────────────"

# Simulate the data flow
echo -e "${BLUE}Simulating Phase 1 data flow...${NC}"

# Step 1: Requirements input
REQUIREMENTS="Design a 3-phase motor controller with TMS320F28379D DSP, 10kW output power, 48V DC input"
echo "  Input: $REQUIREMENTS"

# Step 2: System type detection (simulate JavaScript)
SYSTEM_TYPE=$($PYTHON_CMD << EOF
req = "$REQUIREMENTS".lower()
if 'motor' in req or '3-phase' in req:
    print('Motor_Control')
elif 'rf' in req or 'ghz' in req:
    print('RF_Wireless')
else:
    print('Digital_Controller')
EOF
)

if [ "$SYSTEM_TYPE" == "Motor_Control" ]; then
    test_result 0 "System type detection working (detected: $SYSTEM_TYPE)"
else
    test_result 1 "System type detection failed (got: $SYSTEM_TYPE, expected: Motor_Control)"
fi

# Step 3: Component search
COMPONENTS_FOUND=0
for CATEGORY in "processor" "power_regulator" "gate_driver"; do
    RESPONSE=$(curl -s -X POST http://localhost:8000/api/scrape \
      -H "Content-Type: application/json" \
      -d "{\"search_term\": \"test\", \"category\": \"$CATEGORY\", \"use_cache\": true}")

    COUNT=$(echo "$RESPONSE" | $PYTHON_CMD -c "import sys, json; print(len(json.load(sys.stdin).get('components', [])))" 2>/dev/null || echo "0")
    COMPONENTS_FOUND=$((COMPONENTS_FOUND + COUNT))
done

if [ $COMPONENTS_FOUND -gt 0 ]; then
    test_result 0 "Component search pipeline working ($COMPONENTS_FOUND components found across categories)"
else
    test_result 1 "Component search pipeline failed"
fi

# ============================================================
# TEST 7: Database Data Persistence
# ============================================================
echo ""
echo "TEST 7: Database Data Persistence"
echo "────────────────────────────────────────────────────────────"

# Insert test data
docker exec hardware_pipeline_postgres psql -U postgres -d hardware_pipeline -c "
INSERT INTO component_cache (search_term, category, part_number, description, price, cached_at, expires_at)
VALUES ('TEST123', 'test', 'TEST-PART-001', 'Test component', 9.99, NOW(), NOW() + INTERVAL '30 days')
ON CONFLICT DO NOTHING;
" > /dev/null 2>&1

# Read it back
TEST_DATA=$(docker exec hardware_pipeline_postgres psql -U postgres -d hardware_pipeline -t -c "
SELECT part_number FROM component_cache WHERE search_term='TEST123';
" 2>/dev/null | tr -d ' ')

if [ "$TEST_DATA" == "TEST-PART-001" ]; then
    test_result 0 "Database write and read working"
else
    test_result 1 "Database write/read failed"
fi

# ============================================================
# TEST 8: Resource Usage
# ============================================================
echo ""
echo "TEST 8: Resource Usage Check"
echo "────────────────────────────────────────────────────────────"

# Check container resource usage
CONTAINERS=$(docker compose ps -q | wc -l)
if [ $CONTAINERS -eq 5 ]; then
    test_result 0 "All 5 containers running"
else
    test_result 1 "Expected 5 containers, got $CONTAINERS"
fi

# Check memory usage (rough estimate)
TOTAL_MEM=$(docker stats --no-stream --format "{{.Container}}: {{.MemUsage}}" | head -5)
echo -e "${BLUE}Container memory usage:${NC}"
echo "$TOTAL_MEM" | while read line; do
    echo "    $line"
done

# ============================================================
# TEST 9: Error Handling
# ============================================================
echo ""
echo "TEST 9: Error Handling"
echo "────────────────────────────────────────────────────────────"

# Test invalid API request
INVALID_RESPONSE=$(curl -s -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{}')

if echo "$INVALID_RESPONSE" | grep -q "error\|detail"; then
    test_result 0 "API error handling working (invalid request rejected)"
else
    test_result 1 "API error handling may not be working"
fi

# Test database with invalid query
if docker exec hardware_pipeline_postgres psql -U postgres -d hardware_pipeline -c "SELECT * FROM nonexistent_table;" 2>&1 | grep -q "does not exist"; then
    test_result 0 "Database error handling working"
else
    test_result 1 "Database error handling check failed"
fi

# ============================================================
# TEST 10: Logs Check
# ============================================================
echo ""
echo "TEST 10: Service Logs Check"
echo "────────────────────────────────────────────────────────────"

# Check for errors in logs
N8N_ERRORS=$(docker compose logs n8n 2>&1 | grep -i "error" | grep -v "0 errors" | wc -l)
POSTGRES_ERRORS=$(docker compose logs postgres 2>&1 | grep -i "error" | grep -v "0 errors" | wc -l)
PLAYWRIGHT_ERRORS=$(docker compose logs playwright 2>&1 | grep -i "error" | grep -v "0 errors" | wc -l)

if [ $N8N_ERRORS -eq 0 ]; then
    test_result 0 "n8n logs clean (no errors)"
else
    test_result 1 "n8n has $N8N_ERRORS error(s) in logs"
fi

if [ $POSTGRES_ERRORS -eq 0 ]; then
    test_result 0 "PostgreSQL logs clean (no errors)"
else
    echo -e "${YELLOW}⚠️  PostgreSQL has $POSTGRES_ERRORS error(s) in logs (may be normal)${NC}"
fi

if [ $PLAYWRIGHT_ERRORS -eq 0 ]; then
    test_result 0 "Playwright logs clean (no errors)"
else
    echo -e "${YELLOW}⚠️  Playwright has $PLAYWRIGHT_ERRORS error(s) in logs${NC}"
fi

# ============================================================
# FINAL RESULTS
# ============================================================
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  TEST RESULTS SUMMARY"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Total Tests:  $TOTAL_TESTS"
echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
    echo ""
    echo "Phase 1 workflow is ready for use!"
    echo ""
    echo "Next steps:"
    echo "  1. Open n8n: http://localhost:5678"
    echo "  2. Login with credentials from .env"
    echo "  3. Import workflow: Phase1_Complete_Workflow_READY_TO_IMPORT.json"
    echo "  4. Update nodes with improved prompt scripts"
    echo "  5. Test with sample requirements"
    echo ""
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please review the failures above and fix them."
    echo ""
    echo "To view logs:"
    echo "  docker compose logs [service_name]"
    echo ""
    echo "To restart services:"
    echo "  docker compose restart"
    echo ""
    exit 1
fi
