"""
Interactive Setup Wizard
Guides users through initial configuration
"""
import os
import sys
import json
import secrets
from pathlib import Path
from typing import Dict, Optional

def generate_admin_secret() -> str:
    """Generate a secure random admin secret"""
    return secrets.token_urlsafe(32)

def read_env_file() -> Dict[str, str]:
    """Read existing .env file"""
    env_file = Path(".env")
    env_vars = {}
    
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars

def write_env_file(env_vars: Dict[str, str]):
    """Write .env file"""
    env_file = Path(".env")
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write("# Security Configuration\n")
        f.write(f"ADMIN_SECRET={env_vars.get('ADMIN_SECRET', '')}\n")
        f.write(f"ALLOWED_ORIGINS={env_vars.get('ALLOWED_ORIGINS', 'http://localhost:*,https://wenyuchiou.github.io')}\n")
        f.write("\n")
        f.write("# Environment\n")
        f.write(f"ENVIRONMENT={env_vars.get('ENVIRONMENT', 'development')}\n")
        f.write(f"LOG_LEVEL={env_vars.get('LOG_LEVEL', 'INFO')}\n")
        f.write("\n")
        f.write("# API Keys (Optional)\n")
        if env_vars.get('FRED_API_KEY'):
            f.write(f"FRED_API_KEY={env_vars.get('FRED_API_KEY')}\n")
        else:
            f.write("# FRED_API_KEY=your_fred_api_key_here\n")
        f.write("# Get free API key from: https://fred.stlouisfed.org/docs/api/api_key.html\n")
        f.write("\n")
        f.write("# Ollama Configuration (Optional)\n")
        if env_vars.get('OLLAMA_BASE_URL'):
            f.write(f"OLLAMA_BASE_URL={env_vars.get('OLLAMA_BASE_URL')}\n")
        else:
            f.write("# OLLAMA_BASE_URL=http://localhost:11434\n")

def validate_config_json() -> bool:
    """Validate config.json exists and is valid"""
    config_file = Path("backend/config/config.json")
    
    if not config_file.exists():
        print("  ❌ config.json not found")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            json.load(f)
        print("  ✅ config.json is valid")
        return True
    except json.JSONDecodeError as e:
        print(f"  ❌ config.json is invalid: {e}")
        return False

def validate_agents_yaml() -> bool:
    """Validate agents.yaml exists"""
    agents_file = Path("backend/config/agents.yaml")
    
    if agents_file.exists():
        print("  ✅ agents.yaml exists")
        return True
    else:
        print("  ❌ agents.yaml not found")
        return False

def create_directories():
    """Create required directories"""
    directories = [
        "data/logs",
        "data/backups",
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Created/verified: {dir_path}")

def main():
    """Run setup wizard"""
    print("=" * 60)
    print("AI Trader - Setup Wizard")
    print("=" * 60)
    print()
    print("This wizard will help you configure the system.")
    print()
    
    # Check if .env exists
    env_file = Path(".env")
    existing_env = read_env_file()
    
    if env_file.exists():
        print("⚠️  .env file already exists")
        print(f"   Current ADMIN_SECRET: {'*' * 20 if existing_env.get('ADMIN_SECRET') else 'Not set'}")
        response = input("   Do you want to update it? (y/N): ").strip().lower()
        if response != 'y':
            print("   Keeping existing .env file")
            return 0
    else:
        print("Creating new .env file...")
    
    print()
    
    # Step 1: Admin Secret
    print("[1/4] Admin Secret Configuration")
    if existing_env.get('ADMIN_SECRET'):
        response = input("   Generate new ADMIN_SECRET? (y/N): ").strip().lower()
        if response == 'y':
            admin_secret = generate_admin_secret()
            print(f"   ✅ Generated new ADMIN_SECRET: {admin_secret}")
        else:
            admin_secret = existing_env.get('ADMIN_SECRET')
            print("   ✅ Using existing ADMIN_SECRET")
    else:
        admin_secret = generate_admin_secret()
        print(f"   ✅ Generated ADMIN_SECRET: {admin_secret}")
    print()
    
    # Step 2: Allowed Origins
    print("[2/4] CORS Configuration")
    default_origins = "http://localhost:*,https://wenyuchiou.github.io"
    current_origins = existing_env.get('ALLOWED_ORIGINS', default_origins)
    print(f"   Current: {current_origins}")
    response = input(f"   Enter allowed origins (press Enter to keep current): ").strip()
    allowed_origins = response if response else current_origins
    print(f"   ✅ Set ALLOWED_ORIGINS: {allowed_origins}")
    print()
    
    # Step 3: Environment
    print("[3/4] Environment Configuration")
    current_env = existing_env.get('ENVIRONMENT', 'development')
    print(f"   Current: {current_env}")
    response = input("   Enter environment (development/production, press Enter to keep current): ").strip()
    environment = response if response else current_env
    if environment not in ['development', 'production']:
        environment = 'development'
    print(f"   ✅ Set ENVIRONMENT: {environment}")
    print()
    
    # Step 4: Optional API Keys
    print("[4/4] Optional API Keys")
    current_fred = existing_env.get('FRED_API_KEY', '')
    if current_fred:
        print(f"   Current FRED_API_KEY: {'*' * 20}")
        response = input("   Update FRED_API_KEY? (y/N): ").strip().lower()
        if response == 'y':
            fred_key = input("   Enter FRED_API_KEY (or press Enter to remove): ").strip()
        else:
            fred_key = current_fred
    else:
        fred_key = input("   Enter FRED_API_KEY (optional, press Enter to skip): ").strip()
    
    if fred_key:
        print("   ✅ FRED_API_KEY configured")
    else:
        print("   ⏭️  FRED_API_KEY skipped (optional)")
    print()
    
    # Write .env file
    env_vars = {
        'ADMIN_SECRET': admin_secret,
        'ALLOWED_ORIGINS': allowed_origins,
        'ENVIRONMENT': environment,
        'FRED_API_KEY': fred_key if fred_key else None,
    }
    
    write_env_file(env_vars)
    print("✅ .env file created/updated")
    print()
    
    # Validate configuration files
    print("Validating configuration files...")
    config_valid = validate_config_json()
    agents_valid = validate_agents_yaml()
    print()
    
    # Create directories
    print("Creating required directories...")
    create_directories()
    print()
    
    # Summary
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print("Configuration saved to .env")
    print()
    print("Next steps:")
    print("  1. Run: scripts\\verify_environment.bat")
    print("  2. Run: scripts\\test_backend.bat")
    print("  3. Run: scripts\\quick_start.bat")
    print()
    
    return 0

if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

