# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
"""Run the full DevTeam Crisis simulation suite and produce reports."""

from __future__ import annotations

from pathlib import Path

from dogfood.dev_team_crisis.runner import Scenario, render_report, write_json_report

REPORT_DIR = Path(__file__).resolve().parent / "reports"


def main() -> int:
    """Execute D1, D2, D3 and write Markdown/JSON reports."""
    # Import lazily so a phase can be imported even if another is broken.
    from dogfood.dev_team_crisis.phase_d1 import run_all as run_d1
    from dogfood.dev_team_crisis.phase_d2 import run_all as run_d2
    from dogfood.dev_team_crisis.phase_d3 import run_all as run_d3

    all_scenarios: list[Scenario] = []

    print("=== D1: Emergency internal plugin delivery ===")
    all_scenarios.extend(run_d1())

    print("=== D2: Pre-launch repo rescue ===")
    all_scenarios.extend(run_d2())

    print("=== D3: Multi-developer policy conflict ===")
    all_scenarios.extend(run_d3())

    report = render_report("DevTeam Crisis Simulation Report", all_scenarios)
    md_path = REPORT_DIR / "dev_team_crisis_report.md"
    json_path = REPORT_DIR / "dev_team_crisis_report.json"
    write_json_report("DevTeam Crisis Simulation Report", all_scenarios, json_path)
    md_path.write_text(report, encoding="utf-8")

    print(report)
    return 0 if all(s.passed for s in all_scenarios) else 1


if __name__ == "__main__":
    raise SystemExit(main())
