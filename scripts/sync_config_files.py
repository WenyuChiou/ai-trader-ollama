#!/usr/bin/env python3
"""
Sync configuration files between backend/config and config directories
This ensures both locations have the same configuration
"""
from __future__ import annotations
import sys
import os
from pathlib import Path
import shutil

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]

def sync_config_files():
    """Sync config files from backend/config to config/"""
    print("=" * 60)
    print("Syncing Configuration Files")
    print("=" * 60)
    
    backend_config_dir = ROOT / "backend" / "config"
    root_config_dir = ROOT / "config"
    
    # Ensure root config directory exists
    root_config_dir.mkdir(parents=True, exist_ok=True)
    
    files_to_sync = [
        ("config.json", "Trading configuration"),
        ("agents.yaml", "Agent configuration"),
    ]
    
    synced_count = 0
    for filename, description in files_to_sync:
        backend_file = backend_config_dir / filename
        root_file = root_config_dir / filename
        
        if not backend_file.exists():
            print(f"⚠️  {description} not found: {backend_file}")
            continue
        
        try:
            # Copy from backend/config to config/
            shutil.copy2(backend_file, root_file)
            print(f"✅ Synced {description}")
            print(f"   {backend_file} → {root_file}")
            synced_count += 1
        except Exception as e:
            print(f"❌ Failed to sync {filename}: {e}")
    
    print("\n" + "=" * 60)
    if synced_count == len(files_to_sync):
        print(f"✅ Successfully synced {synced_count} configuration file(s)")
    else:
        print(f"⚠️  Synced {synced_count}/{len(files_to_sync)} file(s)")
    print("=" * 60)
    
    return synced_count == len(files_to_sync)

if __name__ == "__main__":
    try:
        success = sync_config_files()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

