#!/usr/bin/env python3
"""
Test script for static report generation
"""
from __future__ import annotations
import sys
import os
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def test_report_generation():
    """Test report generation"""
    print("=" * 60)
    print("Testing Static Report Generation")
    print("=" * 60)
    
    # Check if script exists
    script_path = ROOT / "scripts" / "generate_static_report.py"
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False
    
    print(f"✅ Script found: {script_path}")
    
    # Check output directory
    output_dir = ROOT / "frontend"
    if not output_dir.exists():
        print(f"❌ Output directory not found: {output_dir}")
        return False
    
    print(f"✅ Output directory exists: {output_dir}")
    
    # Check if report file exists
    report_file = output_dir / "report.html"
    if report_file.exists():
        file_size = report_file.stat().st_size
        print(f"✅ Report file exists: {report_file}")
        print(f"   File size: {file_size:,} bytes")
        
        # Check file content
        with report_file.open("r", encoding="utf-8") as f:
            content = f.read()
            if "<!DOCTYPE html>" in content:
                print("✅ Valid HTML structure")
            else:
                print("❌ Invalid HTML structure")
                return False
            
            if "AI-Trader Daily Report" in content:
                print("✅ Report title found")
            else:
                print("❌ Report title not found")
                return False
            
            if "Current Value" in content:
                print("✅ Key sections found")
            else:
                print("❌ Key sections missing")
                return False
    else:
        print(f"⚠️  Report file not found: {report_file}")
        print("   Run: python scripts/generate_static_report.py")
        return False
    
    # Check data sources
    print("\n" + "=" * 60)
    print("Checking Data Sources")
    print("=" * 60)
    
    logs_dir = ROOT / "backend" / "data" / "logs"
    if logs_dir.exists():
        print(f"✅ Logs directory exists: {logs_dir}")
        
        # Check key files
        key_files = [
            "discussion_actions.jsonl",
            "equity_history.jsonl",
            "trades.jsonl",
            "filled_orders.jsonl"
        ]
        
        for key_file in key_files:
            file_path = logs_dir / key_file
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"✅ {key_file}: {size:,} bytes")
            else:
                print(f"⚠️  {key_file}: Not found (will use empty data)")
    else:
        print(f"⚠️  Logs directory not found: {logs_dir}")
    
    # Test report generation
    print("\n" + "=" * 60)
    print("Testing Report Generation")
    print("=" * 60)
    
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "--output", str(report_file)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        
        if result.returncode == 0:
            print("✅ Report generation successful")
            print("\nOutput:")
            print(result.stdout)
            
            # Check if report file was updated
            if report_file.exists():
                new_size = report_file.stat().st_size
                print(f"\n✅ Report file updated: {new_size:,} bytes")
                return True
            else:
                print("❌ Report file not created")
                return False
        else:
            print("❌ Report generation failed")
            print("\nError output:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running script: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_report_content():
    """Test report content structure"""
    print("\n" + "=" * 60)
    print("Testing Report Content")
    print("=" * 60)
    
    report_file = ROOT / "frontend" / "report.html"
    if not report_file.exists():
        print("❌ Report file not found")
        return False
    
    with report_file.open("r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for required sections
    required_sections = [
        "AI-Trader Daily Report",
        "Current Value",
        "Total Return",
        "Recent Trades",
        "Active Agents",
        "Equity History",
        "Live Dashboard"
    ]
    
    all_found = True
    for section in required_sections:
        if section in content:
            print(f"✅ Section found: {section}")
        else:
            print(f"❌ Section missing: {section}")
            all_found = False
    
    # Check for CSS styles
    if "background: linear-gradient" in content:
        print("✅ CSS styles found")
    else:
        print("⚠️  CSS styles may be missing")
    
    # Check for JavaScript (if any)
    if "<script>" in content:
        print("✅ JavaScript found")
    else:
        print("ℹ️  No JavaScript (static report)")
    
    return all_found


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("STATIC REPORT GENERATION TEST")
    print("=" * 60 + "\n")
    
    # Test 1: Report generation
    test1_passed = test_report_generation()
    
    # Test 2: Report content
    test2_passed = test_report_content()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if test1_passed and test2_passed:
        print("✅ All tests passed!")
        print("\n📊 Report is ready to view:")
        print(f"   file:///{ROOT / 'frontend' / 'report.html'}")
        print(f"\n🌐 After pushing to GitHub:")
        print(f"   https://WenyuChiou.github.io/ai-trader-ollama/report.html")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        if not test1_passed:
            print("   - Report generation test failed")
        if not test2_passed:
            print("   - Report content test failed")
        sys.exit(1)

