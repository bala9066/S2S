#!/usr/bin/env python3
"""
Phase 1 End-to-End Automated Test
Validates workflow outputs and system health
"""

import json
import time
import requests
from datetime import datetime

GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

class Phase1E2ETester:
    def __init__(self):
        self.test_results = []
        self.n8n_url = "http://localhost:5678"
        self.api_url = "http://localhost:8001"

    def print_header(self, title):
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)

    def log_test(self, test_name, passed, message="", details=""):
        result = {
            "test": test_name,
            "passed": passed,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)

        status = f"{GREEN}✅ PASS{NC}" if passed else f"{RED}❌ FAIL{NC}"
        print(f"\n{status}: {test_name}")
        if message:
            print(f"   {message}")
        if details and not passed:
            print(f"   {YELLOW}Details: {details}{NC}")

    def test_docker_services(self):
        """Test 1: Check Docker services are running"""
        import subprocess

        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )

            containers = result.stdout.strip().split('\n')

            required = [
                "hardware_pipeline_postgres",
                "hardware_pipeline_n8n",
                "hardware_pipeline_component_api"
            ]

            running = [c for c in required if c in containers]

            self.log_test(
                "Docker Services",
                len(running) == len(required),
                f"Running: {len(running)}/{len(required)} - {', '.join(running)}",
                f"Missing: {set(required) - set(running)}" if len(running) < len(required) else ""
            )

        except Exception as e:
            self.log_test("Docker Services", False, str(e))

    def test_component_api_health(self):
        """Test 2: Component API health check"""
        try:
            response = requests.get(f"{self.api_url}/api/health", timeout=5)
            health = response.json()

            is_healthy = health.get("status") == "healthy"
            digikey = health.get("digikey_configured", False)
            mouser = health.get("mouser_configured", False)

            self.log_test(
                "Component API Health",
                is_healthy and (digikey or mouser),
                f"Status: {health.get('status')}, DigiKey: {digikey}, Mouser: {mouser}",
                "Configure API keys in .env file" if not (digikey or mouser) else ""
            )

        except requests.exceptions.ConnectionError:
            self.log_test(
                "Component API Health",
                False,
                "Cannot connect to API",
                "Start services: docker compose up -d"
            )
        except Exception as e:
            self.log_test("Component API Health", False, str(e))

    def test_component_search(self):
        """Test 3: Component search functionality"""
        try:
            test_payload = {
                "search_term": "STM32F4",
                "category": "processor",
                "sources": ["digikey", "mouser"],
                "limit_per_source": 5
            }

            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/api/search",
                json=test_payload,
                timeout=15
            )
            search_time = (time.time() - start_time) * 1000

            result = response.json()

            success = result.get("success", False)
            total_found = result.get("total_found", 0)
            sources = result.get("sources", {})

            self.log_test(
                "Component Search",
                success and total_found > 0,
                f"Found: {total_found} components, Time: {search_time:.0f}ms, Sources: {sources}",
                result.get("errors", []) if not success else ""
            )

        except Exception as e:
            self.log_test("Component Search", False, str(e))

    def test_n8n_connectivity(self):
        """Test 4: n8n connectivity"""
        try:
            response = requests.get(self.n8n_url, timeout=5, allow_redirects=False)

            is_accessible = response.status_code in [200, 302]

            self.log_test(
                "n8n Connectivity",
                is_accessible,
                f"n8n accessible at {self.n8n_url}",
                f"Status code: {response.status_code}" if not is_accessible else ""
            )

        except requests.exceptions.ConnectionError:
            self.log_test(
                "n8n Connectivity",
                False,
                "Cannot connect to n8n",
                "Check if n8n is running: docker ps | grep n8n"
            )
        except Exception as e:
            self.log_test("n8n Connectivity", False, str(e))

    def test_workflow_file(self):
        """Test 5: Workflow file validation"""
        try:
            with open('Phase1_Complete_Workflow_READY_TO_IMPORT.json', 'r') as f:
                workflow = json.load(f)

            nodes = workflow.get('nodes', [])
            connections = workflow.get('connections', {})

            # Check for key nodes
            node_names = [n.get('name', '') for n in nodes]
            required_nodes = [
                'Chat Trigger',
                'Validate Input & Detect Type',
                'Build AI Prompt',
                'Generate Block Diagram',
                'Search Components (Real)',
                'Generate BOM'
            ]

            missing_nodes = [n for n in required_nodes if n not in node_names]

            self.log_test(
                "Workflow File Validation",
                len(missing_nodes) == 0,
                f"Nodes: {len(nodes)}, Connections: {len(connections)}",
                f"Missing nodes: {missing_nodes}" if missing_nodes else ""
            )

        except FileNotFoundError:
            self.log_test(
                "Workflow File Validation",
                False,
                "Workflow file not found",
                "Expected: Phase1_Complete_Workflow_READY_TO_IMPORT.json"
            )
        except Exception as e:
            self.log_test("Workflow File Validation", False, str(e))

    def test_mermaid_generator(self):
        """Test 6: Mermaid diagram generator"""
        try:
            # Test that the mermaid generator script exists and can be imported
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "mermaid_diagram_generator",
                "mermaid_diagram_generator.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Test the converter function
            test_diagram = {
                "blocks": [
                    {"id": "B1", "type": "processor", "label": "Test MCU"},
                    {"id": "B2", "type": "power_input", "label": "5V Input"}
                ],
                "connections": [
                    {"from": "B2", "to": "B1", "label": "5V"}
                ]
            }

            mermaid_code = module.block_diagram_to_mermaid(test_diagram)

            has_blocks = "Test MCU" in mermaid_code
            has_connections = "-->" in mermaid_code

            self.log_test(
                "Mermaid Diagram Generator",
                has_blocks and has_connections,
                "Mermaid converter working correctly"
            )

        except Exception as e:
            self.log_test("Mermaid Diagram Generator", False, str(e))

    def test_api_modules(self):
        """Test 7: DigiKey and Mouser API modules"""
        try:
            import importlib.util

            modules_ok = True
            messages = []

            # Test DigiKey API
            try:
                spec = importlib.util.spec_from_file_location("digikey_api", "digikey_api.py")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                messages.append("DigiKey module: OK")
            except Exception as e:
                modules_ok = False
                messages.append(f"DigiKey module: FAIL - {str(e)}")

            # Test Mouser API
            try:
                spec = importlib.util.spec_from_file_location("mouser_api", "mouser_api.py")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                messages.append("Mouser module: OK")
            except Exception as e:
                modules_ok = False
                messages.append(f"Mouser module: FAIL - {str(e)}")

            self.log_test(
                "API Modules",
                modules_ok,
                ", ".join(messages)
            )

        except Exception as e:
            self.log_test("API Modules", False, str(e))

    def run_all_tests(self):
        """Run all automated tests"""
        self.print_header("PHASE 1 END-TO-END AUTOMATED TESTS")
        print(f"\n{BLUE}Starting automated tests...{NC}")

        # Run all tests
        self.test_docker_services()
        self.test_component_api_health()
        self.test_component_search()
        self.test_n8n_connectivity()
        self.test_workflow_file()
        self.test_mermaid_generator()
        self.test_api_modules()

        # Print summary
        self.print_header("TEST SUMMARY")

        passed = sum(1 for r in self.test_results if r["passed"])
        total = len(self.test_results)
        success_rate = (passed/total*100) if total > 0 else 0

        print(f"\nTotal Tests: {total}")
        print(f"{GREEN}Passed: {passed}{NC}")
        print(f"{RED}Failed: {total - passed}{NC}")
        print(f"Success Rate: {success_rate:.1f}%")

        # Show failed tests
        failed_tests = [r for r in self.test_results if not r["passed"]]
        if failed_tests:
            print(f"\n{RED}Failed Tests:{NC}")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['message']}")
                if test.get('details'):
                    print(f"    → {test['details']}")

        print("\n" + "=" * 70)

        if passed == total:
            print(f"\n{GREEN}✅ All tests passed! Phase 1 is ready for end-to-end testing.{NC}\n")
            print(f"Next step: Open n8n at {self.n8n_url} and run test cases.\n")
            print("See PHASE1_E2E_TEST_GUIDE.md for test cases.")
        else:
            print(f"\n{YELLOW}⚠️  Some tests failed. Fix issues before proceeding.{NC}\n")
            print("Review the failed tests above and address each issue.")

        return passed == total


def main():
    tester = Phase1E2ETester()
    success = tester.run_all_tests()

    exit(0 if success else 1)


if __name__ == "__main__":
    main()
