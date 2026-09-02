from dataclasses import dataclass


@dataclass
class ClassCoverage:
    filename: str
    line_rate: float
    branch_rate: float
