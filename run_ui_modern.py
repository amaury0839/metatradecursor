#!/usr/bin/env python3
"""
Launch the Streamlit dashboard using the unified app entry point.
"""

import subprocess
import sys


def main() -> int:
    return subprocess.call(
        [sys.executable, "-m", "streamlit", "run", "app/main.py"],
    )


if __name__ == "__main__":
    raise SystemExit(main())
