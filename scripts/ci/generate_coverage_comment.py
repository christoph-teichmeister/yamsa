"""Build one combined Markdown coverage comment from one or more Cobertura XML reports.

Usage:
    python3 scripts/ci/generate_coverage_comment.py \
        --suite "Backend:artifacts/python-coverage.xml:85" \
        --suite "E2E:artifacts/e2e-coverage.xml:40" \
        --output code-coverage-results.md
"""

import argparse
import os
from dataclasses import dataclass
from xml.etree import ElementTree

from class_coverage import ClassCoverage


@dataclass
class Suite:
    label: str
    xml_path: str
    fail_under: float
    line_rate: float
    branch_rate: float
    classes: list[ClassCoverage]

    @property
    def passed(self) -> bool:
        return self.line_rate * 100 >= self.fail_under


def parse_suite(label: str, xml_path: str, fail_under: float) -> Suite:
    root = ElementTree.parse(xml_path).getroot()

    classes = [
        ClassCoverage(
            filename=class_element.get("filename"),
            line_rate=float(class_element.get("line-rate", 0)),
            branch_rate=float(class_element.get("branch-rate", 0)),
        )
        for class_element in root.iter("class")
    ]
    classes.sort(key=lambda entry: entry.filename)

    return Suite(
        label=label,
        xml_path=xml_path,
        fail_under=fail_under,
        line_rate=float(root.get("line-rate", 0)),
        branch_rate=float(root.get("branch-rate", 0)),
        classes=classes,
    )


def parse_suite_arg(raw: str) -> tuple[str, str, float]:
    label, xml_path, fail_under = raw.rsplit(":", 2)
    return label, xml_path, float(fail_under)


def _as_module_path(filename: str) -> str:
    return filename.removesuffix(".py").replace("/", ".")


def _breakdown_table(classes: list[ClassCoverage]) -> str:
    rows = ["| Datei | Zeilen | Branches |", "|---|---|---|"]
    for entry in classes:
        module_path = _as_module_path(entry.filename)
        rows.append(f"| {module_path} | {entry.line_rate * 100:.0f}% | {entry.branch_rate * 100:.0f}% |")

    return "\n".join(rows)


def render_suite_section(suite: Suite) -> str:
    unsatisfied = [entry for entry in suite.classes if entry.line_rate < 1.0 or entry.branch_rate < 1.0]

    lines = [f"### {suite.label} — Dateien unter 100%"]
    if unsatisfied:
        lines.append(_breakdown_table(unsatisfied))
    else:
        lines.append("Alle Dateien bei 100% ✅")

    return "\n".join(lines)


def render_suite_details(suite: Suite) -> str:
    return "\n".join(
        [
            "<details>",
            f"<summary>Vollständiger {suite.label}-Breakdown (alle Dateien)</summary>",
            "",
            _breakdown_table(suite.classes),
            "",
            "</details>",
        ]
    )


def render_comment(suites: list[Suite]) -> str:
    summary_rows = ["| Suite | Coverage | Threshold | Status |", "|---|---|---|---|"]
    for suite in suites:
        status = "✅" if suite.passed else "❌"
        summary_rows.append(f"| {suite.label} | {suite.line_rate * 100:.2f}% | {suite.fail_under:.0f}% | {status} |")

    parts = ["## Coverage Report", "\n".join(summary_rows)]
    parts.extend(render_suite_section(suite) for suite in suites)
    parts.extend(render_suite_details(suite) for suite in suites)

    return "\n\n".join(parts) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite",
        action="append",
        required=True,
        dest="suites",
        help="Format: Label:xml-path:fail-under-percent, can be passed multiple times",
    )
    parser.add_argument("--output", required=True, help="Path to write the Markdown comment to")
    args = parser.parse_args()

    suites = [parse_suite(*parse_suite_arg(raw)) for raw in args.suites]

    with open(args.output, "w") as output_file:
        output_file.write(render_comment(suites))

    passed = all(suite.passed for suite in suites)
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as handle:
            handle.write(f"passed={'true' if passed else 'false'}\n")


if __name__ == "__main__":
    main()
