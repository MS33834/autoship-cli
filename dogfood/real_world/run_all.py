"""Run the full A→B→C real-world validation suite and produce reports."""

from __future__ import annotations

from pathlib import Path

from dogfood.real_world.phase_a import run_all as run_phase_a
from dogfood.real_world.phase_b import run_all as run_phase_b
from dogfood.real_world.phase_c import run_all as run_phase_c
from dogfood.real_world.runner import Scenario, render_report, write_json_report

REPORT_DIR = Path(__file__).resolve().parent / "reports"


def main() -> int:
    """Execute all phases and write Markdown/JSON reports."""
    all_scenarios: list[Scenario] = []

    print("=== Phase A: end-to-end scenario tests ===")
    phase_a = run_phase_a()
    all_scenarios.extend(phase_a)

    print("=== Phase B: plugin ecosystem stress tests ===")
    phase_b = run_phase_b()
    all_scenarios.extend(phase_b)

    print("=== Phase C: fault-injection drills ===")
    phase_c = run_phase_c()
    all_scenarios.extend(phase_c)

    report = render_report("AutoShip-CLI Real-World Validation Report", all_scenarios)
    md_path = REPORT_DIR / "real_world_report.md"
    json_path = REPORT_DIR / "real_world_report.json"
    write_json_report("AutoShip-CLI Real-World Validation Report", all_scenarios, json_path)
    md_path.write_text(report, encoding="utf-8")

    print(report)
    return 0 if all(s.passed for s in all_scenarios) else 1


if __name__ == "__main__":
    raise SystemExit(main())
