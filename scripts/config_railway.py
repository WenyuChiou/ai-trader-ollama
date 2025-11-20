#!/usr/bin/env python3
"""
Railway Configuration Manager
Manages Railway URL configuration for data upload
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime

# Get project root (scripts/config_railway.py -> project root)
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent
CONFIG_FILE = _project_root / "railway_config.json"

def get_railway_url() -> str:
    """Get Railway URL from config file or environment variable"""
    # First check environment variable
    url = os.environ.get("RAILWAY_URL")
    if url:
        return url
    
    # Then check config file
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("railway_url", "")
        except Exception:
            pass
    
    # Default fallback (user should configure their own URL)
    return ""

def set_railway_url(url: str) -> bool:
    """Set Railway URL in config file"""
    try:
        config = {
            "railway_url": url.strip(),
            "updated_at": datetime.now().isoformat()
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save Railway URL: {e}")
        return False

def configure_railway(url: str | None = None):
    """Interactive or programmatic configuration of Railway URL"""
    print("=" * 60)
    print("Railway Configuration")
    print("=" * 60)
    print()
    
    current_url = get_railway_url()
    print(f"Current Railway URL: {current_url}")
    print()
    
    # If URL provided as argument, use it
    if url:
        new_url = url.strip()
    else:
        # Interactive mode
        try:
            new_url = input("Enter Railway URL (press Enter to keep current): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[INFO] No input provided, keeping current URL.")
            return current_url
    
    if not new_url:
        print("Keeping current URL.")
        return current_url
    
    if not new_url.startswith("http"):
        print("[ERROR] URL must start with http:// or https://")
        return current_url
    
    if set_railway_url(new_url):
        print(f"[SUCCESS] Railway URL updated to: {new_url}")
        return new_url
    else:
        print("[ERROR] Failed to update Railway URL")
        return current_url

if __name__ == "__main__":
    import sys
    url_arg = sys.argv[1] if len(sys.argv) > 1 else None
    configure_railway(url_arg)

