# tests/test_prompts_debug.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml


def read_yaml(p: Path) -> Dict[str, Any]:
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def resolve_from(base_dir: Path, maybe_path: str | None) -> Path | None:
    if not maybe_path:
        return None
    p = Path(maybe_path)
    if not p.is_absolute():
        p = (base_dir / p).resolve()
    return p


def try_load_prompts_from_file(prompt_path: Path) -> Tuple[str | None, str | None, str]:
    """
    Return (system_text, user_text, mode) where mode in:
      - "yaml:system+user" (both keys present)
      - "yaml:system"      (only system key present)
      - "yaml:user"        (only user key present)
      - "text:system"      (plain text file, used as system)
    """
    mode = "text:system"
    if prompt_path.suffix.lower() in {".yml", ".yaml"}:
        try:
            data = read_yaml(prompt_path)
            sys_txt = data.get("system")
            usr_txt = data.get("user")
            if isinstance(sys_txt, str) or isinstance(usr_txt, str):
                if isinstance(sys_txt, str) and isinstance(usr_txt, str):
                    return sys_txt, usr_txt, "yaml:system+user"
                if isinstance(sys_txt, str):
                    return sys_txt, None, "yaml:system"
                if isinstance(usr_txt, str):
                    return None, usr_txt, "yaml:user"
        except Exception:
            # fall back to raw text handling below
            pass

    # Plain text or YAML parse failed → treat entire file as system prompt text
    txt = prompt_path.read_text(encoding="utf-8")
    return txt, None, mode


def main() -> None:
    ap = argparse.ArgumentParser(description="Debug prompt resolution for a single agent")
    ap.add_argument("--agent", required=True, help="Agent key in agents.yaml (e.g., market_agent)")
    ap.add_argument("--config", default="config/agents.yaml", help="Path to agents.yaml")
    args = ap.parse_args()

    config_path = Path(args.config).resolve()
    print(f"[debug] agents.yaml     : {config_path}")
    print(f"[debug] config dir      : {config_path.parent}")
    if not config_path.exists():
        print("[error] agents.yaml does not exist.")
        return

    root = read_yaml(config_path)
    agents_cfg = root.get("agents") or root
    if not isinstance(agents_cfg, dict):
        print("[error] Invalid YAML: expected mapping under 'agents' or at top-level.")
        return

    top_keys = list(agents_cfg.keys())
    print(f"[debug] available agents: {top_keys[:12]}{' ...' if len(top_keys) > 12 else ''}")

    if args.agent not in agents_cfg:
        print(f"[error] agent key '{args.agent}' not found.")
        return

    conf: Dict[str, Any] = agents_cfg[args.agent]
    print(f"[debug] agent='{args.agent}' conf keys: {sorted(conf.keys())}")

    # 1) Inspect declared sources
    prompt_file = conf.get("prompt_file")
    system_file = conf.get("system_file")
    user_file = conf.get("user_file")
    inline_system = conf.get("system")
    inline_user = conf.get("user")

    # Resolve paths relative to agents.yaml location
    prompt_file_p = resolve_from(config_path.parent, prompt_file)
    system_file_p = resolve_from(config_path.parent, system_file)
    user_file_p = resolve_from(config_path.parent, user_file)

    def show_path(label: str, p: Path | None) -> None:
        if p is None:
            print(f"[debug] {label:<12}: <none>")
        else:
            print(f"[debug] {label:<12}: {p}  (exists={p.exists()})")

    show_path("prompt_file", prompt_file_p)
    show_path("system_file", system_file_p)
    show_path("user_file", user_file_p)

    # 2) Try loading in the same precedence order our Factory uses:
    #    prompt_file → system_file/user_file (YAML-aware) → inline overrides
    sys_txt: str | None = None
    usr_txt: str | None = None

    if prompt_file_p and prompt_file_p.exists():
        s, u, mode = try_load_prompts_from_file(prompt_file_p)
        print(f"[debug] load prompt_file mode = {mode}")
        sys_txt = s or sys_txt
        usr_txt = u or usr_txt

    if system_file_p and system_file_p.exists():
        s, u, mode = try_load_prompts_from_file(system_file_p)
        print(f"[debug] load system_file  mode = {mode}")
        # system_file may also contribute a user (when YAML has both)
        sys_txt = sys_txt or s
        usr_txt = usr_txt or u

    if user_file_p and user_file_p.exists():
        s, u, mode = try_load_prompts_from_file(user_file_p)
        print(f"[debug] load user_file    mode = {mode}")
        # prefer explicit user; if YAML had only system, fall back to that text for user
        usr_txt = usr_txt or u or s

    # Inline overrides take highest precedence
    if isinstance(inline_system, str):
        sys_txt = inline_system
        print("[debug] inline system present → overrides")
    if isinstance(inline_user, str):
        usr_txt = inline_user
        print("[debug] inline user present   → overrides")

    # 3) Report lengths and first few lines
    def head(s: str | None, n: int = 400) -> str:
        if not s:
            return "<empty>"
        s = s.strip("\ufeff")  # strip possible BOM
        return s[:n] + ("..." if len(s) > n else "")

    print(f"[debug] system length  : {0 if sys_txt is None else len(sys_txt)}")
    print(f"[debug] user length    : {0 if usr_txt is None else len(usr_txt)}")
    print("======== SYSTEM (first 400 chars) ========")
    print(head(sys_txt))
    print("==========================================")
    print("========== USER (first 400 chars) =========")
    print(head(usr_txt))
    print("==========================================")

    # 4) Optional: verify what the actual Factory will produce
    try:
        from src.agents.factory import AgentFactory  # uses the project loader logic
        # llm_client can be None for this debug path
        fac = AgentFactory(config_path=str(config_path), llm_client=None)
        agent = fac.create(args.agent)
        print(f"[debug] Factory → system_len={len(agent.spec.system or '')}, user_len={len(agent.spec.user or '')}")
    except Exception as e:
        print(f"[debug] Factory check raised: {e}")


if __name__ == "__main__":
    main()
