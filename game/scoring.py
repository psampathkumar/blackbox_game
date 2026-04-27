"""
Scoring logic for experiments and knowledge claims.
"""

from .claims import evaluate_claim


def experiment_score(outputs: dict) -> float:
    """
    Per-run score based on engine outputs.
    Score = power_output - 0.2 * heat_loss - 0.1 * vibration
    """
    power = outputs.get("power_output", 0.0)
    heat = outputs.get("heat_loss", 0.0)
    vib = outputs.get("vibration", 0.0)
    return power - 0.2 * heat - 0.1 * vib


def knowledge_score(report: dict) -> float:
    """
    Score based on report claims precision.
    precision = correct_claims / total_claims
    score = precision * confidence
    """
    claims = report.get("claims", [])
    if not claims:
        return 0.0
    correct = sum(1 for c in claims if evaluate_claim(c))
    precision = correct / len(claims)
    confidence = report.get("confidence", 0.5)
    return precision * confidence


def update_player_scores(state: dict, player: str, exp_score: float, know_score: float = 0.0):
    """
    Update cumulative scores in state for a player.
    """
    if player not in state["players"]:
        state["players"][player] = {
            "energy": 100.0,
            "experiment_score": 0.0,
            "knowledge_score": 0.0,
            "market_profit": 0.0,
            "total_score": 0.0,
        }
    p = state["players"][player]
    p["experiment_score"] += exp_score
    p["knowledge_score"] += know_score
    p["total_score"] = p["experiment_score"] + p["market_profit"] + p["knowledge_score"]
