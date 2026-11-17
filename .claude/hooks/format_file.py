#!/usr/bin/env python3
"""PostToolUse hook: format and lint the file Claude Code just wrote or edited.

- Python files: ``ruff format`` then ``ruff check --fix``.
- Frontend files (.ts/.vue/.js/.css/.json): ``prettier --write`` and, for code, ``eslint --fix``.

If problems remain after auto-fixing, they are written to stderr and the hook exits with
code 2, which Claude Code feeds back to Claude so it can fix them right away.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PRETTIER_SUFFIXES = {".ts", ".vue", ".js", ".mjs", ".css", ".json"}
ESLINT_SUFFIXES = {".ts", ".vue", ".js", ".mjs"}


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None  # tool not installed yet (e.g. before `make setup`)


def report(tool: str, path: Path, result: subprocess.CompletedProcess[str]) -> int:
    sys.stderr.write(f"{tool} found problems in {path}:\n{result.stdout}{result.stderr}\n")
    return 2


def handle_python(path: Path, root: Path) -> int:
    run(["uv", "run", "--quiet", "ruff", "format", str(path)], root)
    result = run(["uv", "run", "--quiet", "ruff", "check", "--fix", str(path)], root)
    if result is not None and result.returncode != 0:
        return report("ruff", path, result)
    return 0


def handle_frontend(path: Path, frontend: Path) -> int:
    if not (frontend / "node_modules").exists():
        return 0
    run(["npx", "--no-install", "prettier", "--write", str(path)], frontend)
    if path.suffix in ESLINT_SUFFIXES:
        result = run(["npx", "--no-install", "eslint", "--fix", str(path)], frontend)
        if result is not None and result.returncode != 0:
            return report("eslint", path, result)
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    file_path = payload.get("tool_input", {}).get("file_path")
    if not file_path:
        return 0

    root = Path(os.environ.get("CLAUDE_PROJECT_DIR", payload.get("cwd", "."))).resolve()
    path = Path(file_path).resolve()
    if not path.is_file() or root not in path.parents:
        return 0

    frontend = root / "frontend"
    if path.suffix == ".py":
        return handle_python(path, root)
    if path.suffix in PRETTIER_SUFFIXES and frontend in path.parents:
        return handle_frontend(path, frontend)
    return 0


if __name__ == "__main__":
    sys.exit(main())
