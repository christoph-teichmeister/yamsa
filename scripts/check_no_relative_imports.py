#!/usr/bin/env python3

"""Fail when any relative imports are found in the repository."""

import argparse
import ast
from collections.abc import Iterable
from pathlib import Path

DEFAULT_EXCLUDES = {
    "node_modules",
    "static",
    "staticfiles",
    "media",
    "tmp",
    ".cache",
    ".venv",
    "venv",
    "env",
    ".git",
    "__pycache__",
    "yamsa.egg-info",
    ".local",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Disallow relative imports in Python files.")
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path(".")],
        help="Files or directories to scan (defaults to the repository root).",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Additional directories to skip when scanning.",
    )
    return parser.parse_args()


def iter_python_files(paths: Iterable[Path], *, exclude_dirs: Iterable[str]) -> Iterable[Path]:
    exclude_dirs = set(exclude_dirs)
    seen: set[Path] = set()
    for path in paths:
        if not path.exists():
            continue
        if path.is_file() and path.suffix == ".py":
            resolved = path.resolve()
            if resolved in seen or any(part in exclude_dirs for part in resolved.parts):
                continue
            seen.add(resolved)
            yield resolved
        elif path.is_dir():
            for candidate in path.rglob("*.py"):
                if any(part in exclude_dirs for part in candidate.parts):
                    continue
                resolved = candidate.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                yield resolved


def find_relative_imports(path: Path) -> list[tuple[int, str]]:
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    lines = source.splitlines()
    violations: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level > 0:
            lineno = getattr(node, "lineno", 0)
            snippet = lines[lineno - 1].strip() if 0 < lineno <= len(lines) else "<line unavailable>"
            violations.append((lineno, snippet))
    return violations


def main() -> int:
    args = parse_args()
    exclude_dirs = list(DEFAULT_EXCLUDES) + args.exclude

    violations: list[tuple[Path, int, str]] = []
    for path in iter_python_files(args.paths, exclude_dirs=exclude_dirs):
        for lineno, snippet in find_relative_imports(path):
            violations.append((path, lineno, snippet))

    if violations:
        print("Relative imports are not allowed; please replace the following:")
        for path, lineno, snippet in violations:
            print(f"{path}:{lineno}: {snippet}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
