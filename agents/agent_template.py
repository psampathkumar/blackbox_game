#!/usr/bin/env python3
"""
Agent template showing how to interact with the file-based API.
Agents ONLY read shared files and write jobs.jsonl.
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
RESULTS_PATH = os.path.join(SHARED_DIR, "results.jsonl")
MARKET_DIR = os.path.join(SHARED_DIR, "market")
LISTINGS_PATH = os.path.join(MARKET_DIR, "listings.jsonl")
OWNERSHIP_DIR = os.path.join(SHARED_DIR, "ownership")

PLAYER_NAME = "template_agent"


def read_state():
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH, "r") as f:
        return json.load(f)


def read_results_tail(n=5):
    if not os.path.exists(RESULTS_PATH):
        return []
    lines = []
    with open(RESULTS_PATH, "r") as f:
        for line in f:
            lines.append(json.loads(line))
    return lines[-n:]


def read_listings():
    if not os.path.exists(LISTINGS_PATH):
        return []
    items = []
    with open(LISTINGS_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def read_owned_reports():
    own_path = os.path.join(OWNERSHIP_DIR, f"{PLAYER_NAME}.json")
    if not os.path.exists(own_path):
        return []
    with open(own_path, "r") as f:
        return json.load(f)


def submit_job(job: dict):
    with open(JOBS_PATH, "a") as f:
        f.write(json.dumps(job) + "\n")


def run_experiment(inputs: dict):
    job = {
        "type": "run",
        "player": PLAYER_NAME,
        "inputs": inputs,
    }
    submit_job(job)


def create_report(report_id: int, summary: str, claims: list, evidence: list, confidence: float):
    job = {
        "type": "create_report",
        "player": PLAYER_NAME,
        "report": {
            "id": report_id,
            "creator": PLAYER_NAME,
            "timestamp": time.time(),
            "summary": summary,
            "claims": claims,
            "evidence": evidence,
            "confidence": confidence,
        },
    }
    submit_job(job)


def list_report(report_id: int, price: float):
    job = {
        "type": "list_report",
        "player": PLAYER_NAME,
        "report_id": report_id,
        "price": price,
    }
    submit_job(job)


def buy_report(report_id: int):
    job = {
        "type": "buy_report",
        "player": PLAYER_NAME,
        "report_id": report_id,
    }
    submit_job(job)


def update_price(report_id: int, price: float):
    job = {
        "type": "update_price",
        "player": PLAYER_NAME,
        "report_id": report_id,
        "price": price,
    }
    submit_job(job)


def decide_action(state):
    """
    Override this with your agent strategy.
    This template does nothing by default.
    """
    pass


def main():
    print(f"[{PLAYER_NAME}] Agent started.")
    while True:
        state = read_state()
        listings = read_listings()
        owned = read_owned_reports()
        results = read_results_tail()

        # Minimal example: if energy > 10, run an experiment
        my_state = state.get("players", {}).get(PLAYER_NAME, {})
        energy = my_state.get("energy", 100.0)
        if energy > 10:
            inputs = {
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
            run_experiment(inputs)
            print(f"[{PLAYER_NAME}] Submitted run experiment.")

        time.sleep(3.0)


if __name__ == "__main__":
    main()
