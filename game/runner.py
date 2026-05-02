#!/usr/bin/env python3
"""
Game runner: the ONLY authority that:
- reads jobs.jsonl
- clears jobs after reading
- calls the engine via engine_wrapper
- deducts energy / updates scores
- writes results.jsonl, state.json, market files
"""

import json
import os
import time
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game.engine_wrapper import call_engine
from game.scoring import experiment_score, update_player_scores
from game.market import list_report, update_price, buy_report

SHARED_DIR = os.path.join(os.path.dirname(__file__), "..", "shared")
JOBS_PATH = os.path.join(SHARED_DIR, "jobs.jsonl")
RESULTS_PATH = os.path.join(SHARED_DIR, "results.jsonl")
STATE_PATH = os.path.join(SHARED_DIR, "state.json")
SCORE_HISTORY_PATH = os.path.join(SHARED_DIR, "score_history.jsonl")
MARKET_DIR = os.path.join(SHARED_DIR, "market")
REPORTS_DIR = os.path.join(SHARED_DIR, "reports")
OWNERSHIP_DIR = os.path.join(SHARED_DIR, "ownership")


def ensure_dirs():
    for d in [SHARED_DIR, MARKET_DIR, REPORTS_DIR, OWNERSHIP_DIR]:
        os.makedirs(d, exist_ok=True)


def load_state() -> dict:
    if not os.path.exists(STATE_PATH):
        state = {
            "tick": 0,
            "players": {},
        }
        with open(STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
        return state
    with open(STATE_PATH, "r") as f:
        return json.load(f)


def save_state(state: dict):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def ensure_player(state: dict, player: str):
    if player not in state["players"]:
        state["players"][player] = {
            "energy": 100.0,
            "experiment_score": 0.0,
            "market_profit": 0.0,
            "total_score": 0.0,
        }


def read_jobs() -> list:
    if not os.path.exists(JOBS_PATH):
        return []
    jobs = []
    with open(JOBS_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    jobs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return jobs


def clear_jobs():
    with open(JOBS_PATH, "w") as f:
        pass


def log_result(result: dict):
    with open(RESULTS_PATH, "a") as f:
        f.write(json.dumps(result) + "\n")


def log_score_history(state: dict):
    """Append a time-series snapshot of all player scores."""
    snapshot = {
        "tick": state.get("tick", 0),
        "time": time.time(),
        "players": {},
    }
    for player, data in state.get("players", {}).items():
        snapshot["players"][player] = {
            "total_score": data.get("total_score", 0.0),
            "experiment_score": data.get("experiment_score", 0.0),
            "market_profit": data.get("market_profit", 0.0),
            "energy": data.get("energy", 100.0),
        }
    with open(SCORE_HISTORY_PATH, "a") as f:
        f.write(json.dumps(snapshot) + "\n")


def process_job(state: dict, job: dict) -> dict:
    jtype = job.get("type")
    player = job.get("player", "unknown")
    ensure_player(state, player)

    if jtype == "run":
        inputs = job.get("inputs", {})
        energy = state["players"][player]["energy"]
        if energy < 1.0:
            return {
                "ok": False,
                "player": player,
                "type": "run",
                "message": "Insufficient energy for experiment.",
            }
        try:
            outputs = call_engine(inputs)
        except Exception as e:
            return {
                "ok": False,
                "player": player,
                "type": "run",
                "message": f"Engine error: {e}",
            }
        state["players"][player]["energy"] -= 1.0
        exp_score = experiment_score(outputs)
        update_player_scores(state, player, exp_score)
        result = {
            "ok": True,
            "player": player,
            "type": "run",
            "inputs": inputs,
            "outputs": outputs,
            "score": exp_score,
        }
        log_result(result)
        return result

    elif jtype == "create_report":
        report = job.get("report", {})
        report_id = report.get("id")
        if report_id is None:
            return {"ok": False, "player": player, "type": "create_report", "message": "Missing report id."}

        # Report body is markdown; store as .md
        report_path = os.path.join(REPORTS_DIR, f"report_{report_id}.md")
        body = report.get("body", "")
        if not body:
            return {"ok": False, "player": player, "type": "create_report", "message": "Report body (markdown) is empty."}
        with open(report_path, "w") as f:
            f.write(body)

        # Store metadata separately as JSON
        meta = {
            "id": report_id,
            "creator": player,
            "timestamp": report.get("timestamp", time.time()),
            "price": report.get("price", 0.0),
            "cited_reports": report.get("cited_reports", []),
        }
        meta_path = os.path.join(REPORTS_DIR, f"report_{report_id}.meta.json")
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        # Grant ownership
        own_path = os.path.join(OWNERSHIP_DIR, f"{player}.json")
        owned = []
        if os.path.exists(own_path):
            with open(own_path, "r") as f:
                owned = json.load(f)
        if report_id not in owned:
            owned.append(report_id)
        with open(own_path, "w") as f:
            json.dump(owned, f, indent=2)

        return {
            "ok": True,
            "player": player,
            "type": "create_report",
            "report_id": report_id,
        }

    elif jtype == "list_report":
        report_id = job.get("report_id")
        price = job.get("price", 0.0)
        res = list_report(player, report_id, price)
        return {
            "ok": res["ok"],
            "player": player,
            "type": "list_report",
            "message": res["message"],
        }

    elif jtype == "buy_report":
        report_id = job.get("report_id")
        res = buy_report(state, player, report_id)
        return {
            "ok": res["ok"],
            "player": player,
            "type": "buy_report",
            "message": res["message"],
        }

    elif jtype == "update_price":
        report_id = job.get("report_id")
        price = job.get("price", 0.0)
        res = update_price(player, report_id, price)
        return {
            "ok": res["ok"],
            "player": player,
            "type": "update_price",
            "message": res["message"],
        }

    return {"ok": False, "player": player, "type": jtype, "message": "Unknown job type."}


def main():
    ensure_dirs()
    print("[Runner] Started. Waiting for jobs...")
    while True:
        state = load_state()
        state["tick"] = state.get("tick", 0) + 1
        jobs = read_jobs()
        if jobs:
            clear_jobs()
            for job in jobs:
                res = process_job(state, job)
                # Optionally log non-run results to results.jsonl too for visibility
                if res.get("type") != "run":
                    log_result(res)
                print(f"[Runner] processed job: {res}")
        save_state(state)
        log_score_history(state)
        time.sleep(1.0)


if __name__ == "__main__":
    main()
