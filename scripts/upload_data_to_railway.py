#!/usr/bin/env python3
"""
Upload local data to Railway backend
Usage: python scripts/upload_data_to_railway.py
"""
import requests
import json
import sys
import os
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

# Railway backend URL
RAILWAY_URL = "https://web-production-b42d6.up.railway.app"

# Local data paths
DATA_DIRS = [
    Path("data/logs"),
    Path("backend/data/logs"),
]

def find_data_file(filename):
    """Find data file in multiple possible locations"""
    for data_dir in DATA_DIRS:
        file_path = data_dir / filename
        if file_path.exists():
            return file_path
    return None

def read_jsonl_file(file_path):
    """Read JSONL file and return list of entries"""
    if not file_path or not file_path.exists():
        return []
    
    entries = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"[WARNING] Failed to read {file_path}: {e}")
    
    return entries

def upload_conversations(conversations):
    """Upload conversations to Railway via API"""
    if not conversations:
        return False
    
    print(f"\nUploading {len(conversations)} conversations...")
    
    # Since there's no direct upload endpoint, we'll need to create one
    # For now, let's try to use a workaround or create the endpoint
    print("[INFO] Note: Railway backend needs an upload endpoint.")
    print("[INFO] This script will prepare the data for manual upload.")
    
    return True

def create_upload_endpoint_patch():
    """Create a patch file to add upload endpoint to server.py"""
    patch_code = '''
@app.post("/api/data/upload")
async def upload_data(data: dict):
    """Upload data to Railway backend"""
    try:
        import json
        from pathlib import Path
        
        logs_dir = Path("data/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Upload conversations
        if "conversations" in data:
            convo_file = logs_dir / "discussion_actions.jsonl"
            with convo_file.open("a", encoding="utf-8") as f:
                for entry in data["conversations"]:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\\n")
        
        # Upload trades
        if "trades" in data:
            trades_file = logs_dir / "trades.jsonl"
            with trades_file.open("a", encoding="utf-8") as f:
                for entry in data["trades"]:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\\n")
        
        # Upload filled orders
        if "filled_orders" in data:
            filled_file = logs_dir / "filled_orders.jsonl"
            with filled_file.open("a", encoding="utf-8") as f:
                for entry in data["filled_orders"]:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\\n")
        
        # Upload equity history
        if "equity_history" in data:
            equity_file = logs_dir / "equity_history.jsonl"
            with equity_file.open("a", encoding="utf-8") as f:
                for entry in data["equity_history"]:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\\n")
        
        return {"ok": True, "message": "Data uploaded successfully"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )
'''
    return patch_code

def upload_via_api(data_dict):
    """Try to upload data via API"""
    try:
        response = requests.post(
            f"{RAILWAY_URL}/api/data/upload",
            json=data_dict,
            timeout=60,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                return True, result.get("message", "Upload successful")
            else:
                return False, result.get("error", "Upload failed")
        elif response.status_code == 404:
            return False, "Upload endpoint not found. Need to add /api/data/upload endpoint to Railway backend."
        else:
            return False, f"API returned status {response.status_code}: {response.text}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to Railway backend"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Main function"""
    print("=" * 60)
    print("Upload Local Data to Railway")
    print("=" * 60)
    
    # Find and read data files
    print("\n[1/4] Reading local data files...")
    
    convo_file = find_data_file("discussion_actions.jsonl")
    trades_file = find_data_file("trades.jsonl")
    filled_file = find_data_file("filled_orders.jsonl")
    equity_file = find_data_file("equity_history.jsonl")
    
    conversations = read_jsonl_file(convo_file) if convo_file else []
    trades = read_jsonl_file(trades_file) if trades_file else []
    filled_orders = read_jsonl_file(filled_file) if filled_file else []
    equity_history = read_jsonl_file(equity_file) if equity_file else []
    
    print(f"   Found {len(conversations)} conversations")
    print(f"   Found {len(trades)} trades")
    print(f"   Found {len(filled_orders)} filled orders")
    print(f"   Found {len(equity_history)} equity history records")
    
    if not any([conversations, trades, filled_orders, equity_history]):
        print("\n[ERROR] No data found to upload!")
        print("   Make sure you have run a trading cycle locally first.")
        return False
    
    # Prepare data
    print("\n[2/4] Preparing data for upload...")
    data_dict = {}
    if conversations:
        data_dict["conversations"] = conversations
    if trades:
        data_dict["trades"] = trades
    if filled_orders:
        data_dict["filled_orders"] = filled_orders
    if equity_history:
        data_dict["equity_history"] = equity_history
    
    # Try to upload
    print("\n[3/4] Uploading to Railway...")
    success, message = upload_via_api(data_dict)
    
    if success:
        print(f"\n[SUCCESS] {message}")
        print("\n[4/4] Data uploaded successfully!")
        print("\nYou can now check the Railway dashboard:")
        print(f"   {RAILWAY_URL}/api/agents/conversations")
        return True
    else:
        print(f"\n[ERROR] {message}")
        print("\n[INFO] The upload endpoint doesn't exist yet.")
        print("       We need to add it to the Railway backend first.")
        print("\n[SOLUTION] Creating endpoint patch file...")
        
        # Save data to a file that can be manually uploaded
        output_file = Path("railway_data_upload.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2, ensure_ascii=False)
        
        print(f"\n[INFO] Data saved to: {output_file}")
        print("       You can manually upload this file or add the endpoint to Railway.")
        
        # Also create patch file
        patch_file = Path("railway_upload_endpoint_patch.txt")
        with open(patch_file, 'w', encoding='utf-8') as f:
            f.write(create_upload_endpoint_patch())
        
        print(f"       Endpoint code saved to: {patch_file}")
        print("\n[INFO] To add the endpoint:")
        print("       1. Add the code from patch file to backend/src/api/server.py")
        print("       2. Deploy to Railway")
        print("       3. Run this script again")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

