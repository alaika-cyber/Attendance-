#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
REQUIREMENTS_FILE = BACKEND_DIR / "requirements.txt"


def run_command(command: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=str(cwd) if cwd else None, env=env, check=True)


def main() -> None:
    if not REQUIREMENTS_FILE.exists():
        raise FileNotFoundError(f"Could not find requirements file: {REQUIREMENTS_FILE}")

    print("Installing backend packages...")
    run_command([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])

    print("Starting backend server on http://0.0.0.0:8000 ...")
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    run_command(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--reload",
        ],
        cwd=BACKEND_DIR,
        env=env,
    )


if __name__ == "__main__":
    main()
