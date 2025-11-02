# scripts/check_ollama.py
from __future__ import annotations
import os, sys, requests

HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

def main() -> int:
    try:
        r = requests.get(f"{HOST.rstrip('/')}/api/version", timeout=3)
        if r.ok:
            print(r.json())
            return 0
        print(r.text)
        return 1
    except Exception as e:
        print(e)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
