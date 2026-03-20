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

    from api.main import app as fastapi_app
    from api.openapi_export import export_openapi_schema

    # Default path is relative to project root, not current working directory
    default_output = project_root / "docs" / "api" / "openapi.json"

    parser = argparse.ArgumentParser(
        description="Export FastAPI OpenAPI schema to JSON."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help=f"Output JSON file path (default: {default_output}).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if output differs from the committed schema.",
    )
    args = parser.parse_args()

    export_openapi_schema(app=fastapi_app, output_path=args.output, check=args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
