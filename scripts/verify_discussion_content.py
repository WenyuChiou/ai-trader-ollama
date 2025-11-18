"""Verify DiscussionCoordinator content completeness"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def verify_discussion_content():
    """Check if DiscussionCoordinator content in discussion_actions.jsonl is complete"""
    logs_dir = Path("data/logs")
    convo_file = logs_dir / "discussion_actions.jsonl"
    
    if not convo_file.exists():
        print("ERROR: discussion_actions.jsonl not found")
        return
    
    print("=" * 80)
    print("Checking DiscussionCoordinator Content Completeness")
    print("=" * 80)
    print()
    
    # 读取所有 DiscussionCoordinator 条目
    coordinators = []
    with convo_file.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line.strip())
                if entry.get("agent") == "DiscussionCoordinator":
                    coordinators.append(entry)
            except json.JSONDecodeError:
                continue
    
    if not coordinators:
        print("WARNING: No DiscussionCoordinator entries found")
        return
    
    print(f"Found {len(coordinators)} DiscussionCoordinator records")
    print()
    
    # Check the latest entry
    latest = coordinators[-1]
    timestamp = latest.get("timestamp", "")
    summary = latest.get("summary", "")
    content = latest.get("content", "")
    
    print(f"Latest record timestamp: {timestamp}")
    print(f"Summary length: {len(summary)} characters")
    print(f"Content length: {len(content)} characters")
    print()
    
    # Check for truncation issues
    issues = []
    
    # Check if summary ends with incomplete word
    if summary:
        # Check if ends with "|" (might be truncated)
        if summary.rstrip().endswith("|"):
            issues.append("Summary ends with '|', might be truncated")
        
        # Check if ends with incomplete word (last word < 3 chars)
        words = summary.split()
        if words and len(words[-1]) < 3:
            issues.append(f"Summary ends with incomplete word: '{words[-1]}'")
        
        # Check if contains all three analysts
        has_market = "Market Analyst" in summary or "Market" in summary
        has_technical = "Technical Analyst" in summary or "Technical" in summary
        has_fundamental = "Fundamental Analyst" in summary or "Fundamental" in summary
        
        if not (has_market and has_technical and has_fundamental):
            issues.append("Summary might be missing some analyst content")
    
    # Check if content is truncated
    if content:
        if content.rstrip().endswith("|"):
            issues.append("Content ends with '|', might be truncated")
        
        # Check Analysis part in content
        if "Analysis:" in content:
            analysis_part = content.split("Analysis:")[-1] if "Analysis:" in content else ""
            if analysis_part and len(analysis_part) < len(summary):
                issues.append("Analysis part in content is shorter than summary, might be truncated")
    
    # Show results
    if issues:
        print("ERROR: Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        print()
    else:
        print("OK: Content looks complete")
        print()
    
    # Show full content preview
    print("=" * 80)
    print("Full Summary Content:")
    print("=" * 80)
    print(summary)
    print()
    
    print("=" * 80)
    print("Full Content:")
    print("=" * 80)
    print(content)
    print()

if __name__ == "__main__":
    verify_discussion_content()

