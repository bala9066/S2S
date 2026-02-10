#!/bin/bash

# ============================================
# COMPONENT SEARCH DIAGNOSTIC TOOL
# ============================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "════════════════════════════════════════════════════════════"
echo "  COMPONENT SEARCH DIAGNOSTIC"
echo "════════════════════════════════════════════════════════════"
echo ""

# ============================================
# TEST 1: Docker Services Status
# ============================================
echo -e "${BLUE}TEST 1: Checking Docker Services${NC}"
echo "────────────────────────────────────────────────────────────"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not installed${NC}"
    echo "   Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon not running${NC}"
    echo "   Start Docker Desktop or run: sudo systemctl start docker"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Check specific containers
echo ""
echo "Checking containers:"

POSTGRES_RUNNING=$(docker ps --filter "name=hardware_pipeline_postgres" --format "{{.Names}}" 2>/dev/null)
PLAYWRIGHT_RUNNING=$(docker ps --filter "name=hardware_pipeline_playwright" --format "{{.Names}}" 2>/dev/null)
N8N_RUNNING=$(docker ps --filter "name=hardware_pipeline_n8n" --format "{{.Names}}" 2>/dev/null)

if [ -n "$POSTGRES_RUNNING" ]; then
    echo -e "  ${GREEN}✅ PostgreSQL: Running${NC}"
else
    echo -e "  ${RED}❌ PostgreSQL: Not running${NC}"
fi

if [ -n "$PLAYWRIGHT_RUNNING" ]; then
    echo -e "  ${GREEN}✅ Playwright: Running${NC}"
else
    echo -e "  ${RED}❌ Playwright: Not running${NC}"
    echo -e "  ${YELLOW}⚠️  This is the likely cause of 0 components!${NC}"
fi

if [ -n "$N8N_RUNNING" ]; then
    echo -e "  ${GREEN}✅ n8n: Running${NC}"
else
    echo -e "  ${RED}❌ n8n: Not running${NC}"
fi

echo ""

# ============================================
# TEST 2: Playwright API Health Check
# ============================================
echo -e "${BLUE}TEST 2: Playwright API Health Check${NC}"
echo "────────────────────────────────────────────────────────────"

if [ -z "$PLAYWRIGHT_RUNNING" ]; then
    echo -e "${RED}❌ Skipped - Playwright container not running${NC}"
    echo ""
    echo -e "${YELLOW}SOLUTION: Start services with:${NC}"
    echo "  cd /home/user/S2S"
    echo "  docker compose up -d"
    echo ""
else
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/health 2>/dev/null)

    if [ -n "$HEALTH_RESPONSE" ]; then
        echo -e "${GREEN}✅ Playwright API is responding${NC}"
        echo "Response: $HEALTH_RESPONSE"

        # Parse response
        if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
            echo -e "${GREEN}✅ Status: HEALTHY${NC}"
        else
            echo -e "${YELLOW}⚠️  Status: DEGRADED${NC}"
        fi
    else
        echo -e "${RED}❌ Playwright API not responding${NC}"
        echo -e "${YELLOW}Check container logs:${NC}"
        echo "  docker logs hardware_pipeline_playwright"
    fi
fi

echo ""

# ============================================
# TEST 3: Test Component Search (Real API Call)
# ============================================
echo -e "${BLUE}TEST 3: Testing Component Search API${NC}"
echo "────────────────────────────────────────────────────────────"

if [ -z "$PLAYWRIGHT_RUNNING" ]; then
    echo -e "${RED}❌ Skipped - Playwright container not running${NC}"
else
    echo "Searching for: STM32F4 (processor)"
    echo ""

    SEARCH_RESPONSE=$(curl -s -X POST http://localhost:8000/api/scrape \
      -H "Content-Type: application/json" \
      -d '{"search_term": "STM32F4", "category": "processor", "use_cache": true}' \
      2>/dev/null)

    if [ -n "$SEARCH_RESPONSE" ]; then
        echo "Raw Response:"
        echo "$SEARCH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SEARCH_RESPONSE"
        echo ""

        # Parse response
        SUCCESS=$(echo "$SEARCH_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)
        TOTAL=$(echo "$SEARCH_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_found', 0))" 2>/dev/null)
        CACHE_HIT=$(echo "$SEARCH_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cache_hit', False))" 2>/dev/null)

        echo "Analysis:"
        echo "  Success: $SUCCESS"
        echo "  Total Found: $TOTAL"
        echo "  Cache Hit: $CACHE_HIT"

        if [ "$TOTAL" -gt 0 ]; then
            echo -e "${GREEN}✅ API returned $TOTAL components${NC}"
        else
            echo -e "${RED}❌ API returned 0 components${NC}"
            echo -e "${YELLOW}This means the scraper is not finding components.${NC}"

            # Check for error message
            ERROR=$(echo "$SEARCH_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('error', 'None'))" 2>/dev/null)
            if [ "$ERROR" != "None" ] && [ "$ERROR" != "null" ]; then
                echo -e "${RED}Error: $ERROR${NC}"
            fi
        fi
    else
        echo -e "${RED}❌ No response from API${NC}"
    fi
fi

echo ""

# ============================================
# TEST 4: Database Connection
# ============================================
echo -e "${BLUE}TEST 4: Database Connection Test${NC}"
echo "────────────────────────────────────────────────────────────"

if [ -z "$POSTGRES_RUNNING" ]; then
    echo -e "${RED}❌ PostgreSQL not running${NC}"
else
    # Try to connect to database
    docker exec hardware_pipeline_postgres psql -U hardware_pipeline -d hardware_pipeline -c "SELECT COUNT(*) FROM component_cache;" 2>/dev/null > /tmp/db_test.txt

    if [ $? -eq 0 ]; then
        CACHE_COUNT=$(cat /tmp/db_test.txt | tail -1 | tr -d ' ')
        echo -e "${GREEN}✅ Database connected${NC}"
        echo "  Cached components: $CACHE_COUNT"
    else
        echo -e "${RED}❌ Database connection failed${NC}"
        echo -e "${YELLOW}Check if init-db.sql was run:${NC}"
        echo "  docker exec -it hardware_pipeline_postgres psql -U hardware_pipeline -d hardware_pipeline -f /docker-entrypoint-initdb.d/init-db.sql"
    fi
fi

echo ""

# ============================================
# TEST 5: Workflow JSON Analysis
# ============================================
echo -e "${BLUE}TEST 5: Workflow Configuration Check${NC}"
echo "────────────────────────────────────────────────────────────"

python3 << 'PYEOF'
import json

with open('Phase1_Complete_Workflow_READY_TO_IMPORT.json', 'r', encoding='utf-8') as f:
    workflow = json.load(f)

# Check HTTP Request node
for node in workflow['nodes']:
    if node['name'] == 'Search Components (Real)':
        params = node['parameters']
        url = params.get('url', '')

        print(f"HTTP Request Configuration:")
        print(f"  URL: {url}")
        print(f"  Method: {params.get('method')}")
        print(f"  Timeout: {params.get('options', {}).get('timeout')} ms")
        print(f"  Retry on fail: {node.get('retryOnFail')}")
        print(f"  Max tries: {node.get('maxTries')}")

        # Check if URL is correct
        if url == 'http://playwright:8000/api/scrape':
            print("  ✅ URL is correct")
        else:
            print(f"  ❌ URL should be 'http://playwright:8000/api/scrape'")

    elif node['name'] == 'Prepare Component Recommendations':
        code = node['parameters']['jsCode']

        print("\nComponent Processing Logic:")
        if 'result.json.components' in code:
            print("  ✅ Correctly accesses result.json.components")
        else:
            print("  ❌ May not be accessing components correctly")

        if '$input.all()' in code:
            print("  ✅ Uses $input.all() to get all aggregated results")
        else:
            print("  ❌ May not be collecting all results")
PYEOF

echo ""

# ============================================
# SUMMARY AND RECOMMENDATIONS
# ============================================
echo "════════════════════════════════════════════════════════════"
echo "  DIAGNOSTIC SUMMARY"
echo "════════════════════════════════════════════════════════════"
echo ""

if [ -z "$PLAYWRIGHT_RUNNING" ]; then
    echo -e "${RED}🔴 ISSUE FOUND: Playwright service not running${NC}"
    echo ""
    echo "This is why you see 0 components. The workflow cannot scrape components"
    echo "without the Playwright service running."
    echo ""
    echo -e "${YELLOW}SOLUTION:${NC}"
    echo "1. Start all services:"
    echo "   cd /home/user/S2S"
    echo "   docker compose up -d"
    echo ""
    echo "2. Wait 30 seconds for services to initialize"
    echo ""
    echo "3. Check services are running:"
    echo "   docker ps"
    echo ""
    echo "4. Test the API:"
    echo "   curl http://localhost:8000/api/health"
    echo ""
    echo "5. Re-run this diagnostic:"
    echo "   ./diagnose_component_search.sh"
    echo ""
elif [ -n "$SEARCH_RESPONSE" ] && [ "$TOTAL" -eq 0 ]; then
    echo -e "${RED}🔴 ISSUE FOUND: Playwright API returns 0 components${NC}"
    echo ""
    echo "The Playwright service is running but not returning components."
    echo ""
    echo -e "${YELLOW}POSSIBLE CAUSES:${NC}"
    echo "1. Network/firewall blocking DigiKey/Mouser access"
    echo "2. Playwright browser not installed in container"
    echo "3. Database connection issue"
    echo "4. Scraper logic bug"
    echo ""
    echo -e "${YELLOW}DEBUG STEPS:${NC}"
    echo "1. Check Playwright container logs:"
    echo "   docker logs hardware_pipeline_playwright --tail 50"
    echo ""
    echo "2. Try accessing DigiKey from container:"
    echo "   docker exec hardware_pipeline_playwright curl -I https://www.digikey.com"
    echo ""
    echo "3. Check if Playwright is installed:"
    echo "   docker exec hardware_pipeline_playwright python -c 'from playwright.sync_api import sync_playwright; print(\"OK\")'"
    echo ""
else
    echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
    echo ""
    echo "The component search system appears to be working correctly."
    echo ""
    echo "If you're still seeing 0 components in n8n workflow:"
    echo "1. Check n8n execution logs for the 'Search Components (Real)' node"
    echo "2. Verify the 'Aggregate All Components' node is collecting results"
    echo "3. Check 'Prepare Component Recommendations' node output"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
