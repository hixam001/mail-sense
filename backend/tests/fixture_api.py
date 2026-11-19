"""Test-only loopback server over an explicitly staged copy of trusted artifacts."""

import sys

import uvicorn

from app.main import create_app

if __name__ == "__main__":
    uvicorn.run(
        create_app(sys.argv[1]),
        host="127.0.0.1",
        port=8000,
        access_log=False,
        proxy_headers=False,
    )
