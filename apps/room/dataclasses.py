from dataclasses import dataclass


@dataclass
class DashboardTab:
    name: str
    get_url: str
