#!/usr/bin/env python3
"""
Check Conversation Status and Trading Cycle
检查对话记录状态和交易周期
"""

import json
import os
from pathlib import Path
from datetime import datetime
import requests
from typing import Optional, Dict, Any

def check_api_status() -> bool:
    """Check if API is running"""
    try:
        response = requests.get("http://localhost:8000/api/market/status", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_market_status() -> Optional[Dict[str, Any]]:
    """Get market status from API"""
    try:
        response = requests.get("http://localhost:8000/api/market/status", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"ERROR: Cannot get market status: {e}")
    return None

def check_conversation_log() -> Optional[Path]:
    """Find conversation log file"""
    possible_paths = [
        Path("data/logs/discussion_actions.jsonl"),
        Path("backend/data/logs/discussion_actions.jsonl"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    return None

def analyze_conversation_log(file_path: Path):
    """Analyze conversation log file"""
    print(f"Found file: {file_path}")
    
    lines = file_path.read_text(encoding="utf-8").strip().split("\n")
    if not lines or not lines[0]:
        print("File is empty")
        return
    
    print(f"Total records: {len(lines)}")
    print()
    
    # Get last 3 records
    print("Last 3 conversation records:")
    last3 = lines[-3:] if len(lines) >= 3 else lines
    
    for line in last3:
        try:
            data = json.loads(line)
            timestamp = data.get("timestamp", "N/A")
            agent = data.get("agent", "N/A")
            content = data.get("content", "N/A")
            if len(content) > 100:
                content = content[:100] + "..."
            
            print(f"  [{timestamp}] {agent}")
            print(f"    {content}")
            print()
        except Exception as e:
            print(f"  ERROR: Cannot parse line: {e}")
    
    # Check time difference
    try:
        last_line = lines[-1]
        last_data = json.loads(last_line)
        last_timestamp = last_data.get("timestamp")
        
        if last_timestamp:
            # Parse UTC timestamp
            last_time = datetime.fromisoformat(last_timestamp.replace("Z", "+00:00"))
            now = datetime.now(last_time.tzinfo)
            diff = now - last_time
            
            print("=== Time Analysis ===")
            print(f"Last record time: {last_timestamp} (UTC)")
            print(f"Current time: {now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}Z (UTC)")
            print(f"Time difference: {diff.total_seconds() / 3600:.2f} hours")
            print()
            
            if diff.total_seconds() / 3600 > 2:
                print("WARNING: No new conversation records for more than 2 hours!")
                print()
                print("Possible reasons:")
                print("  1. Market is closed (auto-trade stops when market closes)")
                print("  2. Frontend page is not open (auto-trade requires frontend)")
                print("  3. Auto-trade timer stopped")
                print("  4. API error preventing trade cycle execution")
                print()
                print("Solutions:")
                print("  1. Open frontend page: frontend\\monitor.html")
                print("  2. Manually trigger trade cycle from frontend")
                print("  3. Check if market is open (auto-trade only runs during trading hours)")
                print("  4. Check error logs: backend\\logs\\error_log.jsonl")
    except Exception as e:
        print(f"Cannot analyze time difference: {e}")

def check_error_logs():
    """Check error logs"""
    possible_paths = [
        Path("backend/logs/error_log.jsonl"),
        Path("backend/data/logs/error_log.jsonl"),
    ]
    
    error_file = None
    for path in possible_paths:
        if path.exists():
            error_file = path
            break
    
    if error_file:
        lines = error_file.read_text(encoding="utf-8").strip().split("\n")
        if lines and lines[0]:
            print(f"Found error log: {error_file}")
            print(f"Total error records: {len(lines)}")
            print()
            
            print("Last 3 error records:")
            last3 = lines[-3:] if len(lines) >= 3 else lines
            
            for line in last3:
                try:
                    data = json.loads(line)
                    timestamp = data.get("timestamp") or data.get("time", "N/A")
                    level = data.get("level", "N/A")
                    message = data.get("message", "N/A")
                    if len(message) > 150:
                        message = message[:150] + "..."
                    
                    color_code = "\033[91m" if level in ["ERROR", "CRITICAL"] else "\033[93m"
                    reset_code = "\033[0m"
                    print(f"  {color_code}[{level}]{reset_code} {timestamp}")
                    print(f"    {message}")
                    print()
                except:
                    pass
        else:
            print("Error log is empty")
    else:
        print("No error log file found")

def main():
    import sys
    import io
    # Fix encoding for Windows console
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 40)
    print("Conversation Status Check")
    print("对话记录状态检查")
    print("=" * 40)
    print()
    
    # Check API status
    print("=== API Status ===")
    if check_api_status():
        print("OK: API is running (port 8000)")
    else:
        print("ERROR: API is not running (port 8000 not accessible)")
        print()
        print("Solution: Start the API first")
        return
    print()
    
    # Check market status
    print("=== Market Status ===")
    market_status = get_market_status()
    if market_status:
        is_open = market_status.get("is_open", False)
        if is_open:
            print("Market Status: OPEN")
        else:
            print("Market Status: CLOSED")
        print(f"Current Time: {market_status.get('current_time', 'N/A')}")
        print(f"Market Time: {market_status.get('market_time', 'N/A')}")
    print()
    
    # Check conversation log
    print("=== Conversation Log ===")
    convo_file = check_conversation_log()
    if convo_file:
        analyze_conversation_log(convo_file)
    else:
        print("ERROR: Conversation log file not found")
        print("Searched locations:")
        print("  - data\\logs\\discussion_actions.jsonl")
        print("  - backend\\data\\logs\\discussion_actions.jsonl")
    print()
    
    # Check error logs
    print("=== Error Logs ===")
    check_error_logs()
    print()
    
    print("=" * 40)
    print("Check Complete")
    print("检查完成")
    print("=" * 40)

if __name__ == "__main__":
    main()

