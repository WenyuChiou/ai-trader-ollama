#!/usr/bin/env python3
"""验证 discussion_actions.jsonl 文件格式"""
import json
import sys
from pathlib import Path

def validate_discussion_actions(file_path):
    """验证 discussion_actions.jsonl 格式"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path}")
        return False
    
    print(f"[CHECK] File: {file_path}")
    print("=" * 80)
    
    valid_count = 0
    invalid_count = 0
    issues = []
    
    # 必需的字段（根据类型不同）
    required_fields_by_type = {
        "discussion": ["timestamp", "date", "agent", "type", "content"],
        "tool": ["timestamp", "date", "agent", "type", "tool_name", "tool_category", "tool_result"],
    }
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"[INFO] Total lines: {len(lines)}")
    print()
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        
        try:
            data = json.loads(line)
            valid_count += 1
            
            # 检查必需字段
            entry_type = data.get("type", "unknown")
            required_fields = required_fields_by_type.get(entry_type, ["timestamp", "date", "agent", "type"])
            
            missing_fields = []
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                issues.append(f"Line {i}: 缺少字段 {missing_fields} (type={entry_type})")
            
            # 显示前5行的详细信息
            if i <= 5:
                print(f"[OK] Line {i}:")
                print(f"   Type: {entry_type}")
                print(f"   Agent: {data.get('agent', 'N/A')}")
                print(f"   Timestamp: {data.get('timestamp', 'N/A')[:20]}...")
                print(f"   Date: {data.get('date', 'N/A')}")
                if entry_type == "tool":
                    print(f"   Tool: {data.get('tool_name', 'N/A')}")
                    print(f"   Category: {data.get('tool_category', 'N/A')}")
                elif entry_type == "discussion":
                    print(f"   Stance: {data.get('stance', 'N/A')}")
                    print(f"   Round: {data.get('round', 'N/A')}")
                    print(f"   Summary: {data.get('summary', 'N/A')[:50]}...")
                print()
                
        except json.JSONDecodeError as e:
            invalid_count += 1
            issues.append(f"Line {i}: JSON parse error - {str(e)[:100]}")
        except Exception as e:
            invalid_count += 1
            issues.append(f"Line {i}: Error - {str(e)[:100]}")
    
    print("=" * 80)
    print(f"[OK] Valid records: {valid_count}")
    print(f"[ERROR] Invalid records: {invalid_count}")
    
    if issues:
        print(f"\n[WARN] Found {len(issues)} issues:")
        for issue in issues[:10]:
            print(f"   {issue}")
        if len(issues) > 10:
            print(f"   ... and {len(issues) - 10} more issues")
    
    # 检查格式是否符合前端要求
    print("\n" + "=" * 80)
    print("[CHECK] Frontend compatibility:")
    print("=" * 80)
    
    # 检查是否有 discussion 和 tool 类型
    discussion_count = 0
    tool_count = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("type") == "discussion":
                    discussion_count += 1
                elif data.get("type") == "tool":
                    tool_count += 1
            except:
                pass
    
    print(f"[OK] Discussion records: {discussion_count}")
    print(f"[OK] Tool records: {tool_count}")
    
    # 检查字段完整性
    print("\n[CHECK] Field completeness:")
    sample_discussion = None
    sample_tool = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("type") == "discussion" and not sample_discussion:
                    sample_discussion = data
                elif data.get("type") == "tool" and not sample_tool:
                    sample_tool = data
                if sample_discussion and sample_tool:
                    break
            except:
                pass
    
    if sample_discussion:
        print("\n[INFO] Discussion sample fields:")
        for key in ["timestamp", "date", "agent", "round", "type", "content", "summary", "stance", "tools_used"]:
            has_field = key in sample_discussion
            value_preview = str(sample_discussion.get(key, ""))[:50] if has_field else "N/A"
            print(f"   {'[OK]' if has_field else '[MISS]'} {key}: {value_preview}...")
    
    if sample_tool:
        print("\n[INFO] Tool sample fields:")
        for key in ["timestamp", "date", "agent", "type", "tool_name", "tool_category", "tool_result", "content"]:
            has_field = key in sample_tool
            value_preview = str(sample_tool.get(key, ""))[:50] if has_field else "N/A"
            print(f"   {'[OK]' if has_field else '[MISS]'} {key}: {value_preview}...")
    
    print("\n" + "=" * 80)
    if invalid_count == 0 and len(issues) == 0:
        print("[SUCCESS] Format validation passed! File can be displayed in frontend.")
        return True
    else:
        print("[WARN] Found some issues, but most records are correctly formatted.")
        return False

if __name__ == "__main__":
    # 默认路径
    default_path = Path(__file__).parent.parent / "data" / "logs" / "discussion_actions.jsonl"
    
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        file_path = default_path
    
    success = validate_discussion_actions(file_path)
    sys.exit(0 if success else 1)

