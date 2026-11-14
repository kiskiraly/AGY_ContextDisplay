#!/usr/bin/env python3
"""
Cross-platform installer for AGY_ContextDisplay (`agy-context-hook`).

Works natively on Windows, macOS, and Linux using only the Python 3 standard
library. Installs the hook script into `~/.gemini/hooks/agy-context-hook.py`,
installs the `/context` skill, and merges the `context-status-hook` entry into
`~/.gemini/config/hooks.json` using the exact active Python interpreter and
resolved absolute paths (avoiding `~` and `python3` shell mismatches on Windows).
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

HOOK_KEY = "context-status-hook"
REPO_DIR = Path(__file__).resolve().parent
SOURCE_HOOK = REPO_DIR / "agy-context-hook"
SOURCE_SKILL = REPO_DIR / "skills" / "context" / "SKILL.md"


def configure_stdio() -> None:
    """Ensure UTF-8 stdio on Windows consoles and pipes."""
    for stream_name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def build_hook_command(python_exe: str, script_path: Path) -> str:
    """Build a shell-safe `PreInvocation` command for the current OS."""
    if os.name == "nt":
        cmd = subprocess.list2cmdline([python_exe, str(script_path), "pre"])
    else:
        cmd = f"{shlex.quote(python_exe)} {shlex.quote(str(script_path))} pre"
    return f"{cmd} || echo {{}}"


def load_hooks_json(hooks_path: Path) -> Dict[str, Any]:
    """Load existing hooks.json or return an empty dict if missing/blank."""
    if not hooks_path.exists():
        return {}
    raw = hooks_path.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Existing hooks file {hooks_path} contains invalid JSON ({exc}). "
            "Please fix it before running the installer."
        ) from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"Existing hooks file {hooks_path} must be a JSON object.")
    return data


def install(
    gemini_dir: Optional[Path] = None,
    bin_dir: Optional[Path] = None,
    python_exe: Optional[str] = None,
    dry_run: bool = False,
) -> int:
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required.", file=sys.stderr)
        return 1

    if not SOURCE_HOOK.is_file():
        print(f"Error: Hook script not found at {SOURCE_HOOK}", file=sys.stderr)
        return 1
    if not SOURCE_SKILL.is_file():
        print(f"Error: Skill file not found at {SOURCE_SKILL}", file=sys.stderr)
        return 1

    default_gemini = Path.home() / ".gemini"
    target_gemini = (gemini_dir or default_gemini).expanduser().resolve()
    py_exe = python_exe or os.path.abspath(sys.executable)

    hooks_dir = target_gemini / "hooks"
    hook_dest = hooks_dir / "agy-context-hook.py"
    cmd_shim = hooks_dir / "agy-context-hook.cmd"
    skill_dest = target_gemini / "config" / "skills" / "context" / "SKILL.md"
    hooks_json_path = target_gemini / "config" / "hooks.json"

    # Also install POSIX CLI entrypoint in ~/.local/bin when using default ~/.gemini.
    posix_bin_dest: Optional[Path] = None
    if os.name != "nt":
        if bin_dir is not None:
            posix_bin_dest = bin_dir.expanduser().resolve() / "agy-context-hook"
        elif gemini_dir is None:
            posix_bin_dest = Path.home() / ".local" / "bin" / "agy-context-hook"

    try:
        hooks_data = load_hooks_json(hooks_json_path)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    hook_command = build_hook_command(py_exe, hook_dest)
    hooks_data[HOOK_KEY] = {
        "PreInvocation": [
            {
                "type": "command",
                "command": hook_command,
                "timeout": 4,
            }
        ]
    }

    action_prefix = "[dry-run] " if dry_run else ""
    print(f"{action_prefix}Installing agy-context-hook for platform: {sys.platform}")
    print(f"{action_prefix}  Hook script : {hook_dest}")
    if os.name == "nt":
        print(f"{action_prefix}  CMD wrapper : {cmd_shim}")
    if posix_bin_dest is not None:
        print(f"{action_prefix}  CLI binary  : {posix_bin_dest}")
    print(f"{action_prefix}  Skill file  : {skill_dest}")
    print(f"{action_prefix}  Hooks config: {hooks_json_path}")
    print(f"{action_prefix}  Hook command: {hook_command}")

    if not dry_run:
        hooks_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE_HOOK, hook_dest)
        if os.name != "nt":
            hook_dest.chmod(hook_dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        else:
            cmd_shim.write_text(
                f'@echo off\r\n"{py_exe}" "%~dp0agy-context-hook.py" %*\r\n',
                encoding="utf-8",
            )

        if posix_bin_dest is not None:
            posix_bin_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SOURCE_HOOK, posix_bin_dest)
            posix_bin_dest.chmod(
                posix_bin_dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            )

        skill_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE_SKILL, skill_dest)

        hooks_json_path.parent.mkdir(parents=True, exist_ok=True)
        hooks_json_path.write_text(
            json.dumps(hooks_data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print("\nInstallation complete. Test the terminal panel with:")
    print(f"  {subprocess.list2cmdline([py_exe, str(hook_dest), '--panel']) if os.name == 'nt' else f'{shlex.quote(py_exe)} {shlex.quote(str(hook_dest))} --panel'}")
    return 0


def uninstall(
    gemini_dir: Optional[Path] = None,
    bin_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> int:
    default_gemini = Path.home() / ".gemini"
    target_gemini = (gemini_dir or default_gemini).expanduser().resolve()

    hooks_dir = target_gemini / "hooks"
    hook_dest = hooks_dir / "agy-context-hook.py"
    cmd_shim = hooks_dir / "agy-context-hook.cmd"
    skill_dest = target_gemini / "config" / "skills" / "context" / "SKILL.md"
    hooks_json_path = target_gemini / "config" / "hooks.json"

    posix_bin_dest: Optional[Path] = None
    if os.name != "nt":
        if bin_dir is not None:
            posix_bin_dest = bin_dir.expanduser().resolve() / "agy-context-hook"
        elif gemini_dir is None:
            posix_bin_dest = Path.home() / ".local" / "bin" / "agy-context-hook"

    action_prefix = "[dry-run] " if dry_run else ""

    for target in (hook_dest, cmd_shim, posix_bin_dest, skill_dest):
        if target is not None and target.exists():
            print(f"{action_prefix}Removing {target}")
            if not dry_run:
                target.unlink()

    if hooks_json_path.exists():
        try:
            hooks_data = load_hooks_json(hooks_json_path)
        except RuntimeError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if HOOK_KEY in hooks_data:
            print(f"{action_prefix}Removing '{HOOK_KEY}' from {hooks_json_path}")
            if not dry_run:
                hooks_data.pop(HOOK_KEY, None)
                hooks_json_path.write_text(
                    json.dumps(hooks_data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )

    print("Uninstall complete.")
    return 0


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(
        description="Cross-platform installer for AGY_ContextDisplay (Windows, macOS, Linux)."
    )
    parser.add_argument(
        "--gemini-dir",
        type=Path,
        default=None,
        help="Override target ~/.gemini directory (defaults to ~/.gemini).",
    )
    parser.add_argument(
        "--bin-dir",
        type=Path,
        default=None,
        help="Override POSIX CLI bin directory (defaults to ~/.local/bin on macOS/Linux).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying any files.",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove installed hook files, skill, and hooks.json entry.",
    )
    args = parser.parse_args()

    if args.uninstall:
        return uninstall(gemini_dir=args.gemini_dir, bin_dir=args.bin_dir, dry_run=args.dry_run)
    return install(gemini_dir=args.gemini_dir, bin_dir=args.bin_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
