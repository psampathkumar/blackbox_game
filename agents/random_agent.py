#!/usr/bin/env python3
"""
Random agent: submits random experiments and occasionally creates reports.
"""

import json
import os
import time
import random

# Allow an agent workspace anywhere on disk by pointing to the tournament shared folder.
SHARED_DIR = os.environ.get("BLACKBOX_SHARED_DIR")
if not SHARED_DIR:
    SHARED_DIR = os.path.join(os.path.dirname(__file__), "..", "shared")

JOBS_PATH = os.path.join(SHARED_DIR, "jobs.jsonl")
STATE_PATH = os.path.join(SHARED_DIR, "state.json")
OWNERSHIP_DIR = os.path.join(SHARED_DIR, "ownership")

PLAYER_NAME = "random_agent"


def read_state():
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH, "r") as f:
        return json.load(f)


def submit_job(job: dict):
    with open(JOBS_PATH, "a") as f:
        f.write(json.dumps(job) + "\n")


def random_inputs():
    return {
        "P": round(random.random(), 2),
        "T": round(random.random(), 2),
        "F": round(random.random(), 2),
        "VA": round(random.random(), 2),
        "VB": round(random.random(), 2),
        "VC": round(random.random(), 2),
        "tau": round(random.random(), 2),
        "L": round(random.random(), 2),
        "C": round(random.random(), 2),
    }


def run_experiment(inputs: dict):
    submit_job({
        "type": "run",
        "player": PLAYER_NAME,
        "inputs": inputs,
    })


def create_simple_report(report_id: int):
    submit_job({
        "type": "create_report",
        "player": PLAYER_NAME,
        "report": {
            "id": report_id,
            "creator": PLAYER_NAME,
            "timestamp": time.time(),
            "summary": "Random exploratory report.",
            "claims": [
                {"type": "monotonic", "var": "P", "target": "power_output", "direction": "positive"},
            ],
            "evidence": [
                {"inputs": random_inputs(), "outputs": {}}
            ],
            "confidence": 0.5,
        },
    })


def main():
    print(f"[{PLAYER_NAME}] Agent started.")
    tick = 0
    while True:
        state = read_state()
        my_state = state.get("players", {}).get(PLAYER_NAME, {})
        energy = my_state.get("energy", 100.0)

        if energy >= 1.0:
            run_experiment(random_inputs())
            print(f"[{PLAYER_NAME}] Submitted random experiment.")

        if tick % 10 == 0 and energy >= 5.0:
            # Occasionally try to create a report
            report_id = random.randint(1000, 9999)
            create_simple_report(report_id)
            print(f"[{PLAYER_NAME}] Submitted report creation.")

        tick += 1
        time.sleep(2.0)


if __name__ == "__main__":
    main()
