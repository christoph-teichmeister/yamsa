#!/usr/bin/env python3

"""Audit every Python module and flag files that declare more than one top-level class.

Intended to keep the repo aligned with the "one class per file" policy.  It walks the
tree, skips generated/static directories, and prints a summary of violations.  Use

    python scripts/check_one_class_per_file.py --fail-on-multiple

from CI or pre-commit hooks to block merges while there is any module with multiple
classes.
"""

import argparse
import ast
import json
from collections.abc import Iterator, Sequence
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


def iter_python_modules(root: Path, exclude_dirs: Sequence[str]) -> Iterator[Path]:
    exclude_dirs = set(exclude_dirs)
    for path in root.rglob("*.py"):
        if any(part in exclude_dirs for part in path.parts):
            continue
        yield path


def class_defs_from_module(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []
    return [node.name for node in tree.body if isinstance(node, ast.ClassDef)]


def collect_violations(root: Path, *, exclude_dirs: Sequence[str]) -> list[tuple[Path, list[str]]]:
    violations: list[tuple[Path, list[str]]] = []
    for module in iter_python_modules(root, exclude_dirs):
        class_names = class_defs_from_module(module)
        if len(class_names) > 1:
            violations.append((module, class_names))
    return violations


def print_report(violations: Sequence[tuple[Path, list[str]]], *, max_entries: int) -> None:
    if not violations:
        print("All scanned modules declare at most one top-level class.")
        return

    print(f"{len(violations)} modules declare multiple classes:")
    for module, class_names in sorted(violations)[:max_entries]:
        snippet = ", ".join(class_names[:5])
        suffix = "" if len(class_names) <= 5 else ", ..."
        print(f"- {module}: {len(class_names)} classes ({snippet}{suffix})")
    if len(violations) > max_entries:
        print(f"  ...and {len(violations) - max_entries} more modules not shown.")


def export_report(path: Path, violations: Sequence[tuple[Path, list[str]]]) -> None:
    payload = [{"module": str(module), "classes": class_names} for module, class_names in violations]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ensure each module declares at most one class.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Project root to scan (default: current directory).",
    )
    parser.add_argument(
        "--max-entries",
        type=int,
        default=20,
        help="How many violations to print before truncating the list.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Path to store a JSON report containing every violating module.",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Additional directories to skip when scanning.",
    )
    parser.add_argument(
        "--fail-on-multiple",
        action="store_true",
        help="Exit with code 1 if any violation is found.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    root = args.root.resolve()
    exclude_dirs = list(DEFAULT_EXCLUDES) + list(args.exclude)

    violations = collect_violations(root, exclude_dirs=exclude_dirs)
    print_report(violations, max_entries=args.max_entries)

    if args.report:
        export_report(args.report, violations)
        print(f"Report written to {args.report}")

    if args.fail_on_multiple and violations:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
