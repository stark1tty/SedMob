#!/usr/bin/env python3
"""
Local simulation of the Android APK startup flow.

Tests that Flask starts correctly with the same config overrides
that main.py uses on Android (explicit DB path + upload folder),
without requiring any Android-specific imports.

Usage:
    source .venv/bin/activate
    python .test/test_android_startup.py
"""
import os
import shutil
import sys
import tempfile
import threading
import time
import urllib.request

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TIMEOUT = 10  # seconds
POLL_INTERVAL = 0.3
SERVER_URL = "http://127.0.0.1:5000"


def main():
    # Create a temp directory to simulate Android's getFilesDir()
    data_dir = os.path.join(tempfile.mkdtemp(prefix="gneisswork_test_"), "gneisswork_data")
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "gneisswork.db")
    upload_dir = os.path.join(data_dir, "uploads")

    print(f"Simulated Android data dir: {data_dir}")
    print(f"Database path: {db_path}")
    print(f"Upload dir:    {upload_dir}")

    # Start Flask the same way main.py does
    flask_error = []

    def run_server():
        try:
            from sedmob.app import create_app
            app = create_app({
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
                "UPLOAD_FOLDER": upload_dir,
            })
            app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
        except Exception as e:
            flask_error.append(str(e))
            import traceback
            traceback.print_exc()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Poll for readiness (same as main.py's _check_server)
    start = time.time()
    ready = False
    while time.time() - start < TIMEOUT:
        if flask_error:
            print(f"\nFLASK CRASHED: {flask_error[0]}")
            _cleanup(data_dir)
            sys.exit(1)
        try:
            resp = urllib.request.urlopen(SERVER_URL, timeout=1)
            if resp.status == 200:
                ready = True
                break
        except Exception:
            pass
        time.sleep(POLL_INTERVAL)

    if not ready:
        print(f"\nFAILED: Server did not respond within {TIMEOUT}s")
        _cleanup(data_dir)
        sys.exit(1)

    # Verify everything was created
    checks = [
        ("Database file exists", os.path.isfile(db_path)),
        ("Upload dir exists", os.path.isdir(upload_dir)),
        ("DB file is non-empty", os.path.getsize(db_path) > 0),
    ]

    # Check a few endpoints
    for path, label in [("/", "Home page"), ("/api/profiles", "API profiles")]:
        try:
            resp = urllib.request.urlopen(SERVER_URL + path, timeout=2)
            checks.append((f"{label} ({path}) returns 200", resp.status == 200))
        except Exception as e:
            checks.append((f"{label} ({path}) returns 200", False))

    print("\n── Startup checks ──")
    all_ok = True
    for label, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {label}")
        if not passed:
            all_ok = False

    print()
    if all_ok:
        print("All checks passed — Flask starts correctly with Android-style config.")
    else:
        print("Some checks failed — review output above.")

    _cleanup(data_dir)
    sys.exit(0 if all_ok else 1)


def _cleanup(data_dir):
    parent = os.path.dirname(data_dir)
    if parent and os.path.isdir(parent) and "gneisswork_test_" in parent:
        shutil.rmtree(parent, ignore_errors=True)


if __name__ == "__main__":
    main()
