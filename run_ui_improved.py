#!/usr/bin/env python3
"""Run the improved Streamlit UI with modern design and crypto support"""

import subprocess
import sys

if __name__ == "__main__":
    # Run the improved UI
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "app/ui_improved.py"],
        check=False
    )
