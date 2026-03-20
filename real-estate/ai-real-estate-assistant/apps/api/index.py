"""
Vercel Serverless Entry Point for FastAPI Backend

This file serves as the entry point for Vercel's Python serverless functions.
It imports and exposes the FastAPI application for serverless deployment.
"""

# pylint: disable=wrong-import-position
import sys
from pathlib import Path

# Add apps/api to Python path for imports
api_dir = Path(__file__).parent
sys.path.insert(0, str(api_dir))

# Import the FastAPI application
from api.main import app  # noqa: E402

# Vercel serverless handler - this is what Vercel will call
handler = app

# For local testing with uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
