"""
Environment Verification Script
Checks all prerequisites and installed components
"""
import sys
import os
import subprocess
import json
import requests
from pathlib import Path
from typing import Dict, List, Tuple

def check_python() -> Tuple[bool, str]:
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
            # Check version >= 3.10
            version_num = version.split()[1]
            major, minor = map(int, version_num.split('.')[:2])
            if major >= 3 and minor >= 10:
                return True, version
            else:
                return False, f"{version} (requires Python 3.10+)"
        else:
            return False, "Python not found"
    except Exception as e:
        return False, f"Error: {e}"

def check_ollama() -> Tuple[bool, str]:
    """Check Ollama installation"""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version
        else:
            return False, "Ollama not found in PATH"
    except FileNotFoundError:
        return False, "Ollama not installed"
    except Exception as e:
        return False, f"Error: {e}"

def check_ollama_running() -> Tuple[bool, str]:
    """Check if Ollama service is running"""
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=2)
        if response.status_code == 200:
            version_info = response.json()
            return True, f"Running (version: {version_info.get('version', 'unknown')})"
        else:
            return False, f"Service returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Service not running"
    except Exception as e:
        return False, f"Error: {e}"

def check_ollama_model() -> Tuple[bool, str]:
    """Check if deepseek-r1 model is available"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            has_model = any("deepseek-r1" in name.lower() for name in model_names)
            if has_model:
                return True, "deepseek-r1 available"
            else:
                return False, f"Model not found. Available: {', '.join(model_names[:3])}..."
        else:
            return False, f"Failed to list models: {response.status_code}"
    except Exception as e:
        return False, f"Error: {e}"

def check_virtual_env() -> Tuple[bool, str]:
    """Check virtual environment"""
    venv_path = Path(".venv")
    if venv_path.exists():
        activate_script = venv_path / "Scripts" / "activate.bat"
        if activate_script.exists():
            return True, "Virtual environment exists"
        else:
            return False, "Virtual environment incomplete"
    else:
        return False, "Virtual environment not found"

def check_python_packages() -> Tuple[bool, str]:
    """Check critical Python packages"""
    backend_dir = Path(__file__).parent.parent / "backend"
    sys.path.insert(0, str(backend_dir))
    
    critical_packages = [
        "fastapi",
        "uvicorn",
        "langchain",
        "pandas",
        "yfinance",
    ]
    
    missing = []
    for package in critical_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if not missing:
        return True, f"All critical packages installed ({len(critical_packages)} packages)"
    else:
        return False, f"Missing packages: {', '.join(missing)}"

def check_ports() -> Tuple[bool, str]:
    """Check port availability"""
    ports_to_check = [8000, 11434]
    available = []
    in_use = []
    
    for port in ports_to_check:
        try:
            response = requests.get(f"http://localhost:{port}", timeout=1)
            in_use.append(port)
        except requests.exceptions.ConnectionError:
            available.append(port)
        except:
            available.append(port)
    
    if available == ports_to_check:
        return True, f"Ports available: {', '.join(map(str, available))}"
    elif in_use:
        return True, f"Ports in use (OK if services running): {', '.join(map(str, in_use))}"
    else:
        return True, "Ports checked"

def check_directories() -> Tuple[bool, str]:
    """Check required directories"""
    required_dirs = [
        "backend/src",
        "frontend",
        "data/logs",
        "backend/config",
    ]
    
    missing = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing.append(dir_path)
    
    if not missing:
        return True, "All required directories exist"
    else:
        return False, f"Missing directories: {', '.join(missing)}"

def check_config_files() -> Tuple[bool, str]:
    """Check configuration files"""
    config_files = [
        "backend/config/config.json",
        "backend/config/agents.yaml",
    ]
    
    missing = []
    for file_path in config_files:
        if not Path(file_path).exists():
            missing.append(file_path)
    
    if not missing:
        return True, "All configuration files exist"
    else:
        return False, f"Missing files: {', '.join(missing)}"

def main():
    """Run all environment checks"""
    print("=" * 60)
    print("Environment Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Installation", check_python),
        ("Ollama Installation", check_ollama),
        ("Ollama Service", check_ollama_running),
        ("Ollama Model", check_ollama_model),
        ("Virtual Environment", check_virtual_env),
        ("Python Packages", check_python_packages),
        ("Port Availability", check_ports),
        ("Directories", check_directories),
        ("Config Files", check_config_files),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            passed, message = check_func()
            results.append({
                "name": name,
                "passed": passed,
                "message": message
            })
            
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {name}")
            print(f"        {message}")
        except Exception as e:
            results.append({
                "name": name,
                "passed": False,
                "message": f"Error: {e}"
            })
            print(f"❌ FAIL: {name}")
            print(f"        Error: {e}")
        print()
    
    # Summary
    print("=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    print()
    
    if passed == total:
        print("🎉 All checks passed! Environment is ready.")
        return 0
    else:
        print(f"⚠️  {total - passed} check(s) failed")
        print("\nPlease fix the issues above and run again.")
        print("Or run: scripts\\diagnose.bat for troubleshooting help.")
        return 1

if __name__ == "__main__":
    exit(main())

