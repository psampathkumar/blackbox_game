"""
Scoring logic for experiments.
"""


def experiment_score(outputs: dict) -> float:
    """
    Per-run score based on engine outputs.
    Score = power_output - 0.2 * heat_loss - 0.1 * vibration
    """
    power = outputs.get("power_output", 0.0)
    heat = outputs.get("heat_loss", 0.0)
    vib = outputs.get("vibration", 0.0)
    return power - 0.2 * heat - 0.1 * vib


def update_player_scores(state: dict, player: str, exp_score: float):
    """
    Update cumulative scores in state for a player.
    Total = experiment_score + market_profit
    """
    if player not in state["players"]:
        state["players"][player] = {
            "energy": 100.0,
            "experiment_score": 0.0,
            "market_profit": 0.0,
            "total_score": 0.0,
        }
    p = state["players"][player]
    p["experiment_score"] += exp_score
    p["total_score"] = p["experiment_score"] + p["market_profit"]
