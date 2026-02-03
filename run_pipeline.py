#!/usr/bin/env python3
"""
Hardware Pipeline - Full Automation Script
Starts the entire pipeline and imports workflows automatically
"""

import asyncio
import subprocess
import time
import sys
import os
from pathlib import Path

# Check if running in Docker or locally
IS_DOCKER = os.path.exists('/.dockerenv')

def log(message: str, emoji: str = "📌"):
    """Print formatted log message"""
    print(f"{emoji} {message}")


def run_command(cmd: list, cwd: str = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return result"""
    log(f"Running: {' '.join(cmd)}", "🔧")
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def check_docker():
    """Verify Docker is available"""
    log("Checking Docker...", "🐳")
    try:
        result = run_command(["docker", "--version"], check=False)
        if result.returncode != 0:
            log("Docker not found! Please install Docker Desktop.", "❌")
            return False
        log(f"Docker OK: {result.stdout.strip()}", "✅")
        return True
    except FileNotFoundError:
        log("Docker not found in PATH!", "❌")
        return False


def check_docker_compose():
    """Verify docker-compose is available"""
    log("Checking Docker Compose...", "🐳")
    try:
        # Try docker compose (new) first
        result = run_command(["docker", "compose", "version"], check=False)
        if result.returncode == 0:
            log(f"Docker Compose OK: {result.stdout.strip()}", "✅")
            return ["docker", "compose"]
        
        # Try docker-compose (old)
        result = run_command(["docker-compose", "--version"], check=False)
        if result.returncode == 0:
            log(f"Docker Compose OK: {result.stdout.strip()}", "✅")
            return ["docker-compose"]
        
        log("Docker Compose not found!", "❌")
        return None
    except FileNotFoundError:
        log("Docker Compose not found in PATH!", "❌")
        return None


def start_pipeline(compose_cmd: list, project_dir: str):
    """Start the Docker pipeline"""
    log("Starting Hardware Pipeline services...", "🚀")
    
    # Pull latest images
    log("Pulling Docker images...", "📥")
    run_command([*compose_cmd, "pull"], cwd=project_dir, check=False)
    
    # Start services
    log("Starting containers...", "🔄")
    result = run_command([*compose_cmd, "up", "-d"], cwd=project_dir, check=False)
    
    if result.returncode != 0:
        log(f"Failed to start services: {result.stderr}", "❌")
        return False
    
    log("Services starting...", "⏳")
    
    # Wait for services to be healthy
    max_wait = 120  # seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        # Check if playwright API is responding
        try:
            import requests
            response = requests.get("http://localhost:8000/api/health", timeout=5)
            if response.status_code == 200:
                log("Scraper API is healthy!", "✅")
                break
        except:
            pass
        
        log(f"Waiting for services... ({int(time.time() - start_time)}s)", "⏳")
        time.sleep(5)
    
    # Check n8n
    try:
        import requests
        response = requests.get("http://localhost:5678", timeout=5)
        log("n8n is accessible!", "✅")
    except:
        log("n8n may still be starting...", "⚠️")
    
    return True


async def import_workflow_via_playwright(workflow_file: str, n8n_url: str = "http://localhost:5678"):
    """Import workflow using Playwright automation"""
    log(f"Importing workflow: {workflow_file}", "📦")
    
    try:
        # Import the importer
        sys.path.insert(0, str(Path(__file__).parent))
        from n8n_workflow_import import N8nWorkflowImporter
        
        importer = N8nWorkflowImporter(n8n_url=n8n_url)
        result = await importer.import_workflow(workflow_file)
        
        if result['success']:
            log(f"Workflow imported: {result['workflow_name']}", "✅")
            return True
        else:
            log(f"Import failed: {result['message']}", "⚠️")
            return False
            
    except Exception as e:
        log(f"Workflow import error: {e}", "❌")
        return False


def status_check(compose_cmd: list, project_dir: str):
    """Show status of all services"""
    log("Service Status:", "📊")
    result = run_command([*compose_cmd, "ps"], cwd=project_dir, check=False)
    print(result.stdout)


def main():
    """Main automation entry point"""
    print("\n" + "="*60)
    print("   HARDWARE PIPELINE - AUTOMATED SETUP")
    print("="*60 + "\n")
    
    # Determine project directory
    project_dir = str(Path(__file__).parent.resolve())
    os.chdir(project_dir)
    log(f"Project directory: {project_dir}", "📁")
    
    # Check prerequisites
    if not check_docker():
        sys.exit(1)
    
    compose_cmd = check_docker_compose()
    if not compose_cmd:
        sys.exit(1)
    
    # Menu
    print("\n" + "-"*40)
    print("Options:")
    print("  1. Start Pipeline (docker-compose up)")
    print("  2. Import Workflow to n8n")
    print("  3. Start + Import (Full Setup)")
    print("  4. Check Status")
    print("  5. Stop Pipeline")
    print("  6. View Logs")
    print("-"*40)
    
    choice = input("\nSelect option (1-6): ").strip()
    
    if choice == "1":
        start_pipeline(compose_cmd, project_dir)
        print("\n✅ Pipeline started!")
        print("   n8n:          http://localhost:5678")
        print("   Scraper API:  http://localhost:8000/docs")
        print("   PgAdmin:      http://localhost:5050")
        
    elif choice == "2":
        workflow_file = Path(project_dir) / "Phase1_Complete_Workflow_READY_TO_IMPORT.json"
        if workflow_file.exists():
            asyncio.run(import_workflow_via_playwright(str(workflow_file)))
        else:
            log(f"Workflow file not found: {workflow_file}", "❌")
    
    elif choice == "3":
        # Full setup
        if start_pipeline(compose_cmd, project_dir):
            log("Waiting 30s for n8n to fully start...", "⏳")
            time.sleep(30)
            
            workflow_file = Path(project_dir) / "Phase1_Complete_Workflow_READY_TO_IMPORT.json"
            if workflow_file.exists():
                asyncio.run(import_workflow_via_playwright(str(workflow_file)))
            
            print("\n" + "="*60)
            print("   SETUP COMPLETE!")
            print("="*60)
            print("\n📍 Access Points:")
            print("   n8n Workflow:  http://localhost:5678")
            print("   Scraper API:   http://localhost:8000/docs")
            print("   PgAdmin:       http://localhost:5050")
            print("\n🧪 To test the pipeline:")
            print("   1. Open n8n at http://localhost:5678")
            print("   2. Start the workflow chat")
            print('   3. Enter: "Design a motor controller with STM32F4"')
            print("="*60 + "\n")
    
    elif choice == "4":
        status_check(compose_cmd, project_dir)
    
    elif choice == "5":
        log("Stopping pipeline...", "🛑")
        run_command([*compose_cmd, "down"], cwd=project_dir, check=False)
        log("Pipeline stopped!", "✅")
    
    elif choice == "6":
        log("Showing logs (Ctrl+C to exit)...", "📜")
        subprocess.run([*compose_cmd, "logs", "-f", "--tail=100"], cwd=project_dir)
    
    else:
        log("Invalid option!", "❌")


if __name__ == "__main__":
    main()
