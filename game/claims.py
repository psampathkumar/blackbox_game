"""
Ground truth relations of the engine and claim evaluation.
"""

# Ground truth of the engine's behavior.
# This hardcoded knowledge is used by the runner to evaluate claims.
TRUE_RELATIONS = {
    "interaction": [
        ("P", "T", "positive"),   # Base power depends on P and T jointly
        ("P", "T", "sinusoidal"), # sin(2*pi*P*T) term
        ("VA", "VB", "positive"), # valve_interaction has +0.3*VA*VB
        ("VB", "VC", "negative"), # valve_interaction has -0.2*VB*VC
        ("VA", "VC", "positive"), # valve_interaction has +0.1*VA*VC
        ("F", "T", "positive"),   # vibration has F*T term
        ("VB", "C", "negative"),  # vibration has VB*(1-C) => VB and C negative interaction
    ],
    "monotonic": [
        ("P", "power_output", "positive"),
        ("VA", "valve_term", "positive"),
        ("VB", "valve_term", "positive"),
        ("VC", "valve_term", "positive"),
        ("T", "heat_loss", "positive"),
        ("L", "heat_loss", "positive"),
        ("C", "vibration", "negative"),
    ],
    "threshold": [
        ("T", "power_output", 0.3, 0.7),   # smoothstep threshold on T for base_power
        ("tau", "power_output", 0.2, 0.4), # tau too low reduces efficiency
        ("tau", "power_output", 0.7, 0.9), # tau too high reduces efficiency
        ("L", "power_output", 0.0, 0.3),   # L < 0.3 underload penalty
        ("L", "power_output", 0.8, 1.0),   # L > 0.8 overload penalty
        ("C", "power_output", 0.4, 0.7),   # control_bonus smoothstep
    ],
    "independence": [
        ("P", "heat_loss"),   # P does not directly appear in heat_loss
        ("F", "heat_loss"),   # F does not directly appear in heat_loss
        ("C", "heat_loss"),   # C does not directly appear in heat_loss
    ],
}


def evaluate_claim(claim: dict) -> bool:
    """
    Evaluate a single claim against TRUE_RELATIONS.
    Returns True if the claim matches the ground truth.
    """
    ctype = claim.get("type")
    if ctype == "interaction":
        var1 = claim.get("var1")
        var2 = claim.get("var2")
        direction = claim.get("direction")
        for v1, v2, d in TRUE_RELATIONS.get("interaction", []):
            if {v1, v2} == {var1, var2} and d == direction:
                return True
        return False

    elif ctype == "monotonic":
        var = claim.get("var")
        target = claim.get("target")
        direction = claim.get("direction")
        for v, t, d in TRUE_RELATIONS.get("monotonic", []):
            if v == var and t == target and d == direction:
                return True
        return False

    elif ctype == "threshold":
        var = claim.get("var")
        target = claim.get("target")
        low = claim.get("low")
        high = claim.get("high")
        for v, t, l, h in TRUE_RELATIONS.get("threshold", []):
            if v == var and t == target and l == low and h == high:
                return True
        return False

    elif ctype == "independence":
        var = claim.get("var")
        # independence only has one tuple element in our storage above: (var, target)
        # But our TRUE_RELATIONS stores (var, target) pairs.
        # We check if the claimed var is independent of any target by looking for exact match.
        target = claim.get("target")
        for v, t in TRUE_RELATIONS.get("independence", []):
            if v == var and t == target:
                return True
        return False

    return False
