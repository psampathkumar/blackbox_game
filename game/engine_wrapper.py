"""
Wrapper to invoke the engine binary.
The runner is the ONLY authority allowed to call the engine.
"""

import json
import subprocess
import os

ENGINE_PATH = os.path.join(os.path.dirname(__file__), "..", "engine", "engine.bin")

def call_engine(inputs: dict) -> dict:
    """
    Call the engine binary with JSON inputs via stdin.
    Returns parsed JSON output.
    Falls back to calling engine.py directly if .bin is missing.
    """
    if os.path.exists(ENGINE_PATH):
        cmd = [ENGINE_PATH]
    else:
        # Fallback for local development without pyinstaller
        py_path = os.path.join(os.path.dirname(__file__), "..", "engine", "engine.py")
        cmd = ["python", py_path]

    proc = subprocess.run(
        cmd,
        input=json.dumps(inputs),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Engine error: {proc.stderr}")
    return json.loads(proc.stdout)
