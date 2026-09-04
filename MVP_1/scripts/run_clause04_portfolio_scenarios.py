"""Run all persistent Clause 04 portfolio scenarios."""

from pathlib import Path

from agentic_assessment.portfolio_scenarios import PortfolioScenarioRunner


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = PROJECT_ROOT / "scenarios" / "clause04"
OUTPUT_ROOT = PROJECT_ROOT / "reports" / "portfolio" / "clause04"


def main() -> None:
    results = PortfolioScenarioRunner(output_root=OUTPUT_ROOT).run_directory(
        SCENARIO_ROOT
    )
    print("Clause 04 portfolio scenarios completed:")
    for result in results:
        print(
            f"  {result.scenario_id}: {result.workflow_state} / "
            f"{result.report_status} -> {result.output_dir}"
        )


if __name__ == "__main__":
    main()
