"""
CLI to run eval scenarios and print a summary report.
"""
from __future__ import annotations

import json
from backend.evals.runner import run_all


def main() -> None:
    report = run_all()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
