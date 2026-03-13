#!/usr/bin/env python3

"""Strip ``from __future__`` imports from Python modules before committing."""

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
    parser = argparse.ArgumentParser(description="Remove `from __future__` imports from Python modules.")
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


def merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []
    merged: list[list[int]] = []
    for start, end in sorted(ranges):
        if not merged or start > merged[-1][1] + 1:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def find_future_import_ranges(source: str) -> list[tuple[int, int]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    ranges: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module != "__future__":
            continue
        start = getattr(node, "lineno", None)
        end = getattr(node, "end_lineno", start)
        if start is None:
            continue
        ranges.append((start - 1, end - 1))
    return merge_ranges(ranges)


def drop_ranges(lines: list[str], ranges: list[tuple[int, int]]) -> list[str]:
    drop = {index for start, end in ranges for index in range(start, end + 1)}
    return [line for index, line in enumerate(lines) if index not in drop]


def process_file(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")
    ranges = find_future_import_ranges(source)
    if not ranges:
        return False

    lines = source.splitlines(keepends=True)
    new_lines = drop_ranges(lines, ranges)
    path.write_text("".join(new_lines), encoding="utf-8")
    print(f"Removed __future__ import(s) from {path}")
    return True


def main() -> int:
    args = parse_args()
    exclude_dirs = list(DEFAULT_EXCLUDES) + args.exclude

    modified = False
    for path in iter_python_files(args.paths, exclude_dirs=exclude_dirs):
        if process_file(path):
            modified = True

    return 1 if modified else 0


if __name__ == "__main__":
    raise SystemExit(main())
