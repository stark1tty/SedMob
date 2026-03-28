#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

def ensure_dependencies():
    """Install missing packages from requirements.txt before starting."""
    requirements = Path(__file__).parent / "sedmob" / "requirements.txt"
    if not requirements.exists():
        return
    cmd = [sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements)]
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        # Retry with --user if permission denied (e.g. system Python)
        try:
            subprocess.check_call(cmd[:5] + ["--user"] + cmd[5:])
        except subprocess.CalledProcessError:
            print("Warning: could not install dependencies from requirements.txt")

if __name__ == "__main__":
    ensure_dependencies()
    from sedmob.app import create_app
    app = create_app()
    app.run(debug=True, port=5000)
