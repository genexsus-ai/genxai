"""Export a Studio workflow into runnable code artifacts.

Usage:
  python scripts/export_studio_workflow.py --workflow-id wf_xxx --output-dir studio/exports
"""

from __future__ import annotations

import argparse
from pathlib import Path

from studio.backend.services.export_service import export_workflow_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export Studio workflow to code")
    parser.add_argument("--workflow-id", required=True, help="Studio workflow id")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output directory (default: studio/exports/<workflow_id>)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir) if args.output_dir else None
    result = export_workflow_code(args.workflow_id, output_dir=output_dir)
    print(f"Exported workflow '{result.workflow_id}' to {result.export_path}")


if __name__ == "__main__":
    main()