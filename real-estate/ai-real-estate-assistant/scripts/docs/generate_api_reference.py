from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[2]
    api_root = project_root / "apps" / "api"
    # Add api_root to path for imports to work (code uses "from api.xxx")
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from api.openapi_markdown import export_api_reference_markdown

    # Default paths are relative to project root, not current working directory
    default_schema = project_root / "docs" / "api" / "openapi.json"
    default_output = project_root / "docs" / "api" / "API_REFERENCE.generated.md"

    parser = argparse.ArgumentParser(
        description="Generate a Markdown API reference from the committed OpenAPI schema snapshot."
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=default_schema,
        help=f"Input OpenAPI JSON schema path (default: {default_schema}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help=f"Output Markdown file path (default: {default_output}).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if output differs from the committed generated Markdown.",
    )
    args = parser.parse_args()

    export_api_reference_markdown(
        schema_path=args.schema, output_path=args.output, check=args.check
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
