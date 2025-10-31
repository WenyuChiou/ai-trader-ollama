#!/usr/bin/env python3
import os, sys, urllib.request

def main():
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    url = host.rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            ok = (r.status == 200)
    except Exception as e:
        print(f"[OLLAMA] not reachable at {host}: {e}")
        sys.exit(2)
    print(f"[OLLAMA] OK at {host}")
    sys.exit(0 if ok else 3)

if __name__ == "__main__":
    main()
