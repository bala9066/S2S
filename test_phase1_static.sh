#!/bin/bash

# ============================================
# PHASE 1 STATIC VALIDATION (No Docker Required)
# ============================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Detect Python command - prioritize Windows Python to avoid WSL issues
# Check for Windows Python installations first
if [ -f "/c/Users/HP/AppData/Local/Programs/Python/Python314/python.exe" ]; then
  PYTHON_CMD="/c/Users/HP/AppData/Local/Programs/Python/Python314/python.exe"
elif [ -f "/c/Users/HP/AppData/Local/Programs/Python/Python312/python.exe" ]; then
  PYTHON_CMD="/c/Users/HP/AppData/Local/Programs/Python/Python312/python.exe"
elif [ -f "/c/Users/HP/AppData/Local/Programs/Python/Python311/python.exe" ]; then
  PYTHON_CMD="/c/Users/HP/AppData/Local/Programs/Python/Python311/python.exe"
elif command -v python &> /dev/null && python --version &> /dev/null; then
  PYTHON_CMD="python"
elif command -v python3 &> /dev/null && python3 --version &> /dev/null; then
  PYTHON_CMD="python3"
else
  echo -e "${RED}ERROR: Python not found${NC}"
  exit 1
fi

echo "Using Python: $PYTHON_CMD"

echo "════════════════════════════════════════════════════════════"
echo "  PHASE 1 STATIC VALIDATION"
echo "════════════════════════════════════════════════════════════"
echo ""

PASS_COUNT=0
FAIL_COUNT=0

test_result() {
  if [ $1 -eq 0 ]; then
    echo -e "${GREEN}✅ PASS${NC}: $2"
    ((PASS_COUNT++))
  else
    echo -e "${RED}❌ FAIL${NC}: $2"
    ((FAIL_COUNT++))
  fi
}

# ============================================
# TEST 1: File Existence
# ============================================
echo "1. Checking Required Files..."
echo "────────────────────────────────────────────────────────────"

FILES=(
  "Phase1_Complete_Workflow_READY_TO_IMPORT.json"
  "improved_ai_prompt.js"
  "improved_block_diagram_generator.js"
  "component_scraper.py"
  "scraper_api.py"
  "docker-compose.yml"
  "init-db.sql"
  "PHASE1_TESTING_GUIDE.md"
  "INTEGRATION_INSTRUCTIONS.md"
)

for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    test_result 0 "File exists: $file"
  else
    test_result 1 "File missing: $file"
  fi
done

echo ""

# ============================================
# TEST 2: JSON Validation
# ============================================
echo "2. Validating JSON Files..."
echo "────────────────────────────────────────────────────────────"

$PYTHON_CMD -c "import json; json.load(open('Phase1_Complete_Workflow_READY_TO_IMPORT.json', encoding='utf-8'))" 2>/dev/null
test_result $? "Phase1_Complete_Workflow_READY_TO_IMPORT.json is valid JSON"

echo ""

# ============================================
# TEST 3: JavaScript Syntax
# ============================================
echo "3. Validating JavaScript Files..."
echo "────────────────────────────────────────────────────────────"

if command -v node &> /dev/null; then
  node --check improved_ai_prompt.js 2>/dev/null
  test_result $? "improved_ai_prompt.js syntax valid"

  node --check improved_block_diagram_generator.js 2>/dev/null
  test_result $? "improved_block_diagram_generator.js syntax valid"
else
  echo -e "${YELLOW}⚠️  SKIP: node not found${NC}"
fi

echo ""

# ============================================
# TEST 4: Python Syntax
# ============================================
echo "4. Validating Python Files..."
echo "────────────────────────────────────────────────────────────"

$PYTHON_CMD -m py_compile component_scraper.py 2>/dev/null
test_result $? "component_scraper.py syntax valid"

$PYTHON_CMD -m py_compile scraper_api.py 2>/dev/null
test_result $? "scraper_api.py syntax valid"

echo ""

# ============================================
# TEST 5: YAML Validation
# ============================================
echo "5. Validating YAML Files..."
echo "────────────────────────────────────────────────────────────"

$PYTHON_CMD -c "import yaml; yaml.safe_load(open('docker-compose.yml', encoding='utf-8'))" 2>/dev/null
test_result $? "docker-compose.yml is valid YAML"

echo ""

# ============================================
# TEST 6: Workflow Node Count
# ============================================
echo "6. Analyzing Workflow Structure..."
echo "────────────────────────────────────────────────────────────"

NODE_COUNT=$($PYTHON_CMD -c "import json; data=json.load(open('Phase1_Complete_Workflow_READY_TO_IMPORT.json', encoding='utf-8')); print(len(data.get('nodes', [])))" 2>/dev/null)

if [ "$NODE_COUNT" -ge 15 ]; then
  test_result 0 "Workflow has $NODE_COUNT nodes (expected 15+)"
else
  test_result 1 "Workflow has $NODE_COUNT nodes (expected 15+)"
fi

CONN_COUNT=$($PYTHON_CMD -c "import json; data=json.load(open('Phase1_Complete_Workflow_READY_TO_IMPORT.json', encoding='utf-8')); conns=data.get('connections', {}); print(sum(len(v) for v in conns.values()) if isinstance(conns, dict) else len(conns))" 2>/dev/null)

if [ "$CONN_COUNT" -ge 10 ]; then
  test_result 0 "Workflow has $CONN_COUNT connections (expected 10+)"
else
  test_result 1 "Workflow has $CONN_COUNT connections (expected 10+)"
fi

echo ""

# ============================================
# TEST 7: JavaScript Logic Tests
# ============================================
echo "7. Testing JavaScript Logic..."
echo "────────────────────────────────────────────────────────────"

if command -v node &> /dev/null; then
  # Test improved_ai_prompt.js logic - mock the $json variable that n8n provides
  cat > /tmp/test_ai_prompt.js << 'EOF'
// Mock the n8n $json context
const $json = {
  requirements: 'Test motor controller with TMS320F28379D, 10kW power',
  system_type: 'Motor_Control'
};

// Load the improved prompt logic
const fs = require('fs');
const code = fs.readFileSync('improved_ai_prompt.js', 'utf8');

// Execute in a function context
const result = eval('(function() { ' + code + ' })()');

// Extract the prompt from the returned result
const prompt = result && result.json && result.json.ai_prompt ? result.json.ai_prompt : '';

// Check if prompt includes all required sections
const expectedSections = [
  'power_system',
  'analog_signal_chain',
  'power_stage',
  'interfaces_communication'
];

let allPresent = true;
for (const section of expectedSections) {
  if (!prompt.includes(section)) {
    console.error('Missing section:', section);
    allPresent = false;
  }
}

if (allPresent && prompt.length > 2000) {
  console.log('SUCCESS');
  process.exit(0);
} else {
  console.error('Prompt length:', prompt.length);
  process.exit(1);
}
EOF

  node /tmp/test_ai_prompt.js 2>/dev/null
  test_result $? "AI prompt includes all required sections"

  # Test block diagram generator logic - mock the $json variable that n8n provides
  cat > /tmp/test_diagram.js << 'EOF'
// Mock the n8n $json context
const $json = {
  parsed_requirements: {
    primary_components: {
      processor: { specific_part: 'TMS320F28379D', type: 'DSP' },
      power_system: {
        input_voltage: '48V',
        rails_needed: [
          { voltage: '5V', current: '2A', purpose: 'gate drivers' },
          { voltage: '3.3V', current: '1.5A', purpose: 'DSP core' }
        ]
      },
      analog_signal_chain: {
        adc: { resolution: '16-bit', channels: 8 },
        sensors: [
          { type: 'current', interface: 'analog' }
        ]
      }
    }
  },
  project_name: 'Test_Project',
  system_type: 'Motor_Control'
};

// Load diagram generator code
const fs = require('fs');
const code = fs.readFileSync('improved_block_diagram_generator.js', 'utf8');

try {
  // Execute in a function context
  const result = eval('(function() { ' + code + ' })()');
  
  // Verify it returns valid output
  if (result && result.json) {
    console.log('SUCCESS: Diagram generator executes without errors');
    process.exit(0);
  } else {
    console.error('No valid result returned');
    process.exit(1);
  }
} catch (e) {
  console.error('Error:', e.message);
  process.exit(1);
}
EOF

  node /tmp/test_diagram.js 2>/dev/null
  test_result $? "Block diagram generator logic valid"
fi

echo ""

# ============================================
# TEST 8: Database Schema
# ============================================
echo "8. Analyzing Database Schema..."
echo "────────────────────────────────────────────────────────────"

EXPECTED_TABLES=(
  "component_cache"
  "projects"
  "phase_outputs"
  "block_diagrams"
  "bom_items"
)

for table in "${EXPECTED_TABLES[@]}"; do
  if grep -q "CREATE TABLE.*$table" init-db.sql; then
    test_result 0 "Schema includes table: $table"
  else
    test_result 1 "Schema missing table: $table"
  fi
done

echo ""

# ============================================
# TEST 9: Documentation Completeness
# ============================================
echo "9. Checking Documentation..."
echo "────────────────────────────────────────────────────────────"

# Check PHASE1_TESTING_GUIDE.md
if grep -q "Test Case 1: Motor Controller" PHASE1_TESTING_GUIDE.md; then
  test_result 0 "Testing guide includes test cases"
else
  test_result 1 "Testing guide missing test cases"
fi

if grep -q "Prerequisites" PHASE1_TESTING_GUIDE.md; then
  test_result 0 "Testing guide includes prerequisites"
else
  test_result 1 "Testing guide missing prerequisites"
fi

# Check INTEGRATION_INSTRUCTIONS.md
if grep -q "Step 1: Update" INTEGRATION_INSTRUCTIONS.md; then
  test_result 0 "Integration guide includes steps"
else
  test_result 1 "Integration guide missing steps"
fi

echo ""

# ============================================
# TEST 10: Code Quality Checks
# ============================================
echo "10. Code Quality Checks..."
echo "────────────────────────────────────────────────────────────"

# Check for TODO/FIXME in critical files
if ! grep -q "TODO\|FIXME" improved_ai_prompt.js improved_block_diagram_generator.js; then
  test_result 0 "No TODO/FIXME in production code"
else
  test_result 1 "Found TODO/FIXME in production code"
fi

# Check file sizes are reasonable
AI_PROMPT_SIZE=$(wc -c < improved_ai_prompt.js)
if [ "$AI_PROMPT_SIZE" -gt 2000 ] && [ "$AI_PROMPT_SIZE" -lt 10000 ]; then
  test_result 0 "AI prompt size reasonable ($AI_PROMPT_SIZE bytes)"
else
  test_result 1 "AI prompt size unusual ($AI_PROMPT_SIZE bytes)"
fi

DIAGRAM_SIZE=$(wc -c < improved_block_diagram_generator.js)
if [ "$DIAGRAM_SIZE" -gt 4000 ] && [ "$DIAGRAM_SIZE" -lt 20000 ]; then
  test_result 0 "Diagram generator size reasonable ($DIAGRAM_SIZE bytes)"
else
  test_result 1 "Diagram generator size unusual ($DIAGRAM_SIZE bytes)"
fi

echo ""

# ============================================
# FINAL REPORT
# ============================================
echo "════════════════════════════════════════════════════════════"
echo "  STATIC VALIDATION SUMMARY"
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "Total Tests: $((PASS_COUNT + FAIL_COUNT))"
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "${RED}Failed: $FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
  echo -e "${GREEN}✅ ALL STATIC VALIDATIONS PASSED${NC}"
  echo ""
  echo "Phase 1 files are structurally valid and ready for runtime testing."
  echo "Next step: Run Docker-based tests with './test_phase1_workflow.sh'"
  exit 0
else
  echo -e "${RED}❌ SOME VALIDATIONS FAILED${NC}"
  echo ""
  echo "Please review the failures above before proceeding."
  exit 1
fi
