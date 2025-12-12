"""
System Diagnosis Tool
Automatically detects common issues and provides fixes
"""
import sys
import os
import subprocess
import requests
import json
from pathlib import Path
from typing import List, Dict, Tuple

def check_python() -> Tuple[bool, str, str]:
    """Check Python installation"""
    try:
        result = subprocess.run(
            ["python", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            major, minor = map(int, version.split()[1].split('.')[:2])
            if major >= 3 and minor >= 10:
                return True, "OK", version
            else:
                return False, "Version too old", f"{version} (requires Python 3.10+)"
        else:
            return False, "Not found", "Python not in PATH"
    except Exception as e:
        return False, "Error", str(e)

def check_ollama() -> Tuple[bool, str, str]:
    """Check Ollama installation and service"""
    try:
        # Check installation
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return False, "Not installed", "Install from https://ollama.ai/"
        
        # Check service
        try:
            response = requests.get("http://localhost:11434/api/version", timeout=2)
            if response.status_code == 200:
                return True, "OK", "Service running"
            else:
                return False, "Service error", f"Status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Service not running", "Run: ollama serve"
    except FileNotFoundError:
        return False, "Not installed", "Install from https://ollama.ai/"
    except Exception as e:
        return False, "Error", str(e)

def check_virtual_env() -> Tuple[bool, str, str]:
    """Check virtual environment"""
    venv_path = Path(".venv")
    if not venv_path.exists():
        return False, "Not found", "Run: scripts\\install.bat"
    
    activate_script = venv_path / "Scripts" / "activate.bat"
    if not activate_script.exists():
        return False, "Incomplete", "Recreate: python -m venv .venv"
    
    return True, "OK", "Virtual environment exists"

def check_dependencies() -> Tuple[bool, str, str]:
    """Check Python dependencies"""
    backend_dir = Path(__file__).parent.parent / "backend"
    sys.path.insert(0, str(backend_dir))
    
    critical_packages = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "langchain": "langchain",
        "pandas": "pandas",
        "yfinance": "yfinance",
    }
    
    missing = []
    for import_name, package_name in critical_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        return False, "Missing packages", f"Install: pip install {' '.join(missing)}"
    else:
        return True, "OK", f"All {len(critical_packages)} packages installed"

def check_port(port: int) -> Tuple[bool, str, str]:
    """Check if port is available or in use"""
    try:
        response = requests.get(f"http://localhost:{port}", timeout=1)
        return False, "In use", f"Port {port} is already in use"
    except requests.exceptions.ConnectionError:
        return True, "Available", f"Port {port} is available"
    except:
        return True, "Available", f"Port {port} appears available"

def check_config_files() -> Tuple[bool, str, str]:
    """Check configuration files"""
    config_file = Path("backend/config/config.json")
    agents_file = Path("backend/config/agents.yaml")
    
    issues = []
    if not config_file.exists():
        issues.append("config.json missing")
    else:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            issues.append(f"config.json invalid: {e}")
    
    if not agents_file.exists():
        issues.append("agents.yaml missing")
    
    if issues:
        return False, "Issues found", "; ".join(issues)
    else:
        return True, "OK", "All config files valid"

def check_env_file() -> Tuple[bool, str, str]:
    """Check .env file"""
    env_file = Path(".env")
    if not env_file.exists():
        return False, "Not found", "Run: scripts\\setup_wizard.bat"
    
    # Check for ADMIN_SECRET
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'ADMIN_SECRET' not in content or 'ADMIN_SECRET=' not in content:
            return False, "Incomplete", "ADMIN_SECRET not configured"
    
    return True, "OK", ".env file exists"

def check_directories() -> Tuple[bool, str, str]:
    """Check required directories"""
    required_dirs = [
        "data/logs",
        "backend/src",
        "frontend",
    ]
    
    missing = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing.append(dir_path)
    
    if missing:
        return False, "Missing directories", "; ".join(missing)
    else:
        return True, "OK", "All directories exist"

def main():
    """Run diagnosis"""
    print("=" * 60)
    print("System Diagnosis Tool")
    print("=" * 60)
    print()
    print("Checking system components...")
    print()
    
    checks = [
        ("Python Installation", check_python),
        ("Ollama Installation", check_ollama),
        ("Virtual Environment", check_virtual_env),
        ("Python Dependencies", check_dependencies),
        ("Port 8000", lambda: check_port(8000)),
        ("Port 11434", lambda: check_port(11434)),
        ("Configuration Files", check_config_files),
        ("Environment File", check_env_file),
        ("Directories", check_directories),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            passed, status, message = check_func()
            results.append({
                "name": name,
                "passed": passed,
                "status": status,
                "message": message
            })
            
            if passed:
                print(f"✅ {name}: {status} - {message}")
            else:
                print(f"❌ {name}: {status} - {message}")
        except Exception as e:
            results.append({
                "name": name,
                "passed": False,
                "status": "Error",
                "message": str(e)
            })
            print(f"❌ {name}: Error - {e}")
    
    print()
    print("=" * 60)
    print("Diagnosis Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    failed = [r for r in results if not r["passed"]]
    
    print(f"Passed: {passed}/{total}")
    print()
    
    if failed:
        print("Issues Found:")
        print()
        for issue in failed:
            print(f"❌ {issue['name']}")
            print(f"   Status: {issue['status']}")
            print(f"   Issue: {issue['message']}")
            print()
        
        print("Recommended Fixes:")
        print()
        
        # Provide specific fixes
        fixes = []
        for issue in failed:
            if "Python" in issue['name'] and "too old" in issue['message']:
                fixes.append("  - Install Python 3.10+ from https://www.python.org/downloads/")
            elif "Ollama" in issue['name'] and "Not installed" in issue['status']:
                fixes.append("  - Install Ollama from https://ollama.ai/")
            elif "Ollama" in issue['name'] and "not running" in issue['message']:
                fixes.append("  - Start Ollama: ollama serve")
            elif "Virtual Environment" in issue['name']:
                fixes.append("  - Run: scripts\\install.bat")
            elif "Dependencies" in issue['name']:
                fixes.append("  - Run: scripts\\install.bat (installs dependencies)")
            elif "Port" in issue['name'] and "in use" in issue['message']:
                port = "8000" if "8000" in issue['name'] else "11434"
                fixes.append(f"  - Stop process on port {port} or use different port")
            elif "Configuration" in issue['name']:
                fixes.append("  - Check backend\\config\\config.json and agents.yaml")
            elif "Environment File" in issue['name']:
                fixes.append("  - Run: scripts\\setup_wizard.bat")
            elif "Directories" in issue['name']:
                fixes.append("  - Run: scripts\\install.bat (creates directories)")
        
        for fix in set(fixes):  # Remove duplicates
            print(fix)
        print()
        print("For detailed setup, see: docs\\INSTALLATION.md")
        return 1
    else:
        print("🎉 All checks passed! System is ready.")
        print()
        print("Next steps:")
        print("  1. Run: scripts\\test_backend.bat")
        print("  2. Run: scripts\\quick_start.bat")
        return 0

if __name__ == "__main__":
    exit(main())

