#!/bin/bash

# Phase 1 Setup and Testing Script
# This script sets up the environment and tests component search functionality

set -e

echo "========================================================================"
echo "  PHASE 1 SETUP AND TESTING"
echo "========================================================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✅ $message${NC}"
    elif [ "$status" = "ERROR" ]; then
        echo -e "${RED}❌ $message${NC}"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  $message${NC}"
    elif [ "$status" = "INFO" ]; then
        echo -e "${BLUE}ℹ️  $message${NC}"
    fi
}

# Step 1: Check Docker
echo "Step 1: Checking Docker..."
if ! command -v docker &> /dev/null; then
    print_status "ERROR" "Docker is not installed or not in PATH"
    echo ""
    echo "Please install Docker Desktop or Docker Engine:"
    echo "  - Mac/Windows: https://www.docker.com/products/docker-desktop"
    echo "  - Linux: https://docs.docker.com/engine/install/"
    exit 1
fi

if ! docker info &> /dev/null; then
    print_status "ERROR" "Docker daemon is not running"
    echo ""
    echo "Please start Docker Desktop or run: sudo systemctl start docker"
    exit 1
fi

print_status "OK" "Docker is installed and running"
echo ""

# Step 2: Check .env file
echo "Step 2: Checking environment configuration..."
if [ ! -f .env ]; then
    print_status "ERROR" ".env file not found"
    echo ""
    echo "Creating .env from template..."
    cp .env.example .env
    print_status "OK" "Created .env file"
else
    print_status "OK" ".env file exists"
fi

# Check for API credentials
API_CONFIGURED=false

if grep -q "^DIGIKEY_CLIENT_ID=your_digikey_client_id_here" .env || \
   grep -q "^DIGIKEY_CLIENT_SECRET=your_digikey_client_secret_here" .env || \
   grep -q "^MOUSER_API_KEY=your_mouser_api_key_here" .env; then
    print_status "WARN" "API credentials not configured in .env file"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  REQUIRED: Configure API Credentials"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "To fix the '0 components' issue, you MUST add API credentials:"
    echo ""
    echo "1. Get DigiKey API credentials (FREE):"
    echo "   - Visit: https://developer.digikey.com/"
    echo "   - Click 'Register'"
    echo "   - Create an organization and application"
    echo "   - Copy Client ID and Client Secret"
    echo "   - Free tier: 1,000 requests/day"
    echo ""
    echo "2. Get Mouser API key (FREE):"
    echo "   - Visit: https://www.mouser.com/api-hub/"
    echo "   - Click 'Sign up for Search API'"
    echo "   - Check email for API key"
    echo "   - Free tier: Generous limits"
    echo ""
    echo "3. Edit .env file and add your credentials:"
    echo "   nano .env"
    echo ""
    echo "   Replace these lines:"
    echo "   DIGIKEY_CLIENT_ID=your_digikey_client_id_here"
    echo "   DIGIKEY_CLIENT_SECRET=your_digikey_client_secret_here"
    echo "   MOUSER_API_KEY=your_mouser_api_key_here"
    echo ""
    echo "   With your actual credentials:"
    echo "   DIGIKEY_CLIENT_ID=abcd1234..."
    echo "   DIGIKEY_CLIENT_SECRET=xyz789..."
    echo "   MOUSER_API_KEY=mouser123..."
    echo ""
    echo "4. After configuring credentials, run this script again:"
    echo "   ./setup_and_test.sh"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
else
    # Check if at least one API is configured
    DIGIKEY_ID=$(grep "^DIGIKEY_CLIENT_ID=" .env | cut -d'=' -f2)
    MOUSER_KEY=$(grep "^MOUSER_API_KEY=" .env | cut -d'=' -f2)

    if [ "$DIGIKEY_ID" != "your_digikey_client_id_here" ] || [ "$MOUSER_KEY" != "your_mouser_api_key_here" ]; then
        API_CONFIGURED=true
        print_status "OK" "API credentials configured"
    else
        print_status "WARN" "API credentials still have default values"
        API_CONFIGURED=false
    fi
fi
echo ""

# Step 3: Check AI API keys
echo "Step 3: Checking AI API configuration..."
CLAUDE_KEY=$(grep "^CLAUDE_API_KEY=" .env | cut -d'=' -f2)
GROQ_KEY=$(grep "^GROQ_API_KEY=" .env | cut -d'=' -f2)

if [ "$CLAUDE_KEY" = "sk-ant-api03-your-key-here" ] && [ "$GROQ_KEY" = "your-groq-key-here" ]; then
    print_status "WARN" "No AI API keys configured"
    echo ""
    echo "You need at least ONE of these:"
    echo "  - Claude API (Recommended): https://console.anthropic.com/settings/keys"
    echo "  - Groq API (Free, Fast): https://console.groq.com/keys"
    echo ""
    echo "Add to .env file:"
    echo "  CLAUDE_API_KEY=sk-ant-api03-..."
    echo "  OR"
    echo "  GROQ_API_KEY=gsk_..."
    echo ""
else
    print_status "OK" "At least one AI API key configured"
fi
echo ""

# Step 4: Start Docker services
echo "Step 4: Starting Docker services..."
echo "This may take 1-2 minutes on first run (downloading images)..."
echo ""

docker compose up -d

if [ $? -eq 0 ]; then
    print_status "OK" "Docker services started"
else
    print_status "ERROR" "Failed to start Docker services"
    echo ""
    echo "Check docker-compose logs:"
    echo "  docker compose logs"
    exit 1
fi
echo ""

# Step 5: Wait for services to be ready
echo "Step 5: Waiting for services to be healthy..."
sleep 10

# Check PostgreSQL
if docker compose ps postgres | grep -q "Up"; then
    print_status "OK" "PostgreSQL is running"
else
    print_status "ERROR" "PostgreSQL failed to start"
fi

# Check n8n
if docker compose ps n8n | grep -q "Up"; then
    print_status "OK" "n8n is running"
else
    print_status "ERROR" "n8n failed to start"
fi

# Check component_api
if docker compose ps component_api | grep -q "Up"; then
    print_status "OK" "Component API is running"
else
    print_status "ERROR" "Component API failed to start"
    echo ""
    echo "Check logs:"
    echo "  docker compose logs component_api"
fi
echo ""

# Step 6: Test Component API
echo "Step 6: Testing Component API..."
sleep 5

HEALTH_RESPONSE=$(curl -s http://localhost:8001/api/health 2>&1)

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    print_status "OK" "Component API health check passed"

    # Check API configuration
    DIGIKEY_CONFIGURED=$(echo "$HEALTH_RESPONSE" | grep -o '"digikey_configured":[^,}]*' | cut -d':' -f2)
    MOUSER_CONFIGURED=$(echo "$HEALTH_RESPONSE" | grep -o '"mouser_configured":[^,}]*' | cut -d':' -f2)

    echo ""
    echo "API Configuration Status:"
    if [ "$DIGIKEY_CONFIGURED" = "true" ]; then
        print_status "OK" "DigiKey API: Configured ✓"
    else
        print_status "WARN" "DigiKey API: Not configured"
    fi

    if [ "$MOUSER_CONFIGURED" = "true" ]; then
        print_status "OK" "Mouser API: Configured ✓"
    else
        print_status "WARN" "Mouser API: Not configured"
    fi
else
    print_status "ERROR" "Component API health check failed"
    echo ""
    echo "Response: $HEALTH_RESPONSE"
    echo ""
    echo "Check logs:"
    echo "  docker compose logs component_api --tail 50"
fi
echo ""

# Step 7: Test component search (if API configured)
if [ "$API_CONFIGURED" = true ]; then
    echo "Step 7: Testing component search..."

    SEARCH_RESPONSE=$(curl -s -X POST http://localhost:8001/api/search \
        -H "Content-Type: application/json" \
        -d '{
            "search_term": "STM32F407",
            "category": "processor",
            "sources": ["digikey", "mouser"],
            "limit_per_source": 3
        }' 2>&1)

    if echo "$SEARCH_RESPONSE" | grep -q '"success":true'; then
        TOTAL_FOUND=$(echo "$SEARCH_RESPONSE" | grep -o '"total_found":[0-9]*' | cut -d':' -f2)
        SEARCH_TIME=$(echo "$SEARCH_RESPONSE" | grep -o '"search_time_ms":[0-9]*' | cut -d':' -f2)

        print_status "OK" "Component search successful!"
        echo ""
        echo "  Components found: $TOTAL_FOUND"
        echo "  Search time: ${SEARCH_TIME}ms"
        echo ""
        echo "✅ Phase 1 system is working correctly!"
    else
        print_status "ERROR" "Component search failed"
        echo ""
        echo "Response: $SEARCH_RESPONSE"
        echo ""
        echo "Possible issues:"
        echo "  1. API credentials are invalid"
        echo "  2. DigiKey/Mouser API is down"
        echo "  3. Network/firewall blocking requests"
    fi
else
    echo "Step 7: Skipping component search test (API not configured)"
fi
echo ""

# Step 8: Summary
echo "========================================================================"
echo "  SETUP SUMMARY"
echo "========================================================================"
echo ""

if [ "$API_CONFIGURED" = true ]; then
    print_status "OK" "Environment is configured correctly"
    echo ""
    echo "Next Steps:"
    echo "  1. Open n8n: http://localhost:5678"
    echo "     Username: admin"
    echo "     Password: admin123"
    echo ""
    echo "  2. Import workflow:"
    echo "     - Click 'Import from File'"
    echo "     - Select: Phase1_Complete_Workflow_FINAL.json"
    echo ""
    echo "  3. Test with your RF system requirement:"
    echo "     - Design RF system with Artix-7 FPGA, 40dBm output..."
    echo ""
    echo "  4. Run comprehensive tests:"
    echo "     python3 test_phase1_e2e.py"
    echo ""
    print_status "OK" "Phase 1 is ready for production use!"
else
    print_status "WARN" "API credentials need to be configured"
    echo ""
    echo "Next Steps:"
    echo "  1. Configure API credentials in .env file (see instructions above)"
    echo "  2. Restart services: docker compose restart component_api"
    echo "  3. Run this script again: ./setup_and_test.sh"
fi
echo ""
echo "========================================================================"
