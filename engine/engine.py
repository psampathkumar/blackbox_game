#!/usr/bin/env python3
"""
Black-box engine: maps inputs -> outputs with a hidden nonlinear system.
Reads JSON from stdin, prints JSON to stdout.
Uses a file-based run counter for deterministic structure + small randomness.
"""

import json
import sys
import math
import os
import random

COUNTER_FILE = os.path.join(os.path.dirname(__file__), "run_counter.txt")

def get_run_count():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return 0
    return 0

def increment_run_count():
    count = get_run_count() + 1
    with open(COUNTER_FILE, "w") as f:
        f.write(str(count))
    return count

def compute(P, T, F, VA, VB, VC, tau, L, C, run_count):
    """
    Hidden nonlinear system.
    All inputs in [0, 1].
    Outputs: power_output, vibration, efficiency, heat_loss
    """
    # Deterministic per-run seed + small random noise (~2%)
    rng = random.Random(run_count)

    # Normalized effective inputs (some have sigmoid-like thresholds)
    def smoothstep(edge0, edge1, x):
        t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
        return t * t * (3.0 - 2.0 * t)

    # Interaction-heavy
    # Pressure and Temperature have a joint effect on base_power
    base_power = 0.3 + 0.5 * P * smoothstep(0.3, 0.7, T) + 0.2 * math.sin(2.0 * math.pi * P * T)

    # Flow modulates power non-monotonically (optimal around 0.5)
    flow_mod = 1.0 - 1.2 * abs(F - 0.5)
    flow_mod = max(0.1, flow_mod)

    # Valves A, B, C interact in a multiplicative way
    valve_term = 0.3 + 0.35 * VA + 0.35 * VB + 0.35 * VC
    valve_interaction = 1.0 + 0.3 * VA * VB - 0.2 * VB * VC + 0.1 * VA * VC
    valve_term *= valve_interaction

    # Time constant tau effect: too low or too high reduces efficiency
    tau_mod = 1.0 - 0.5 * smoothstep(0.2, 0.4, tau) - 0.3 * smoothstep(0.7, 0.9, tau)
    tau_mod = max(0.2, tau_mod)

    # Load effect on heat_loss and power
    # Threshold: L < 0.3 causes underload penalty, L > 0.8 causes overload penalty
    load_penalty = smoothstep(0.0, 0.3, 0.3 - L) + smoothstep(0.8, 1.0, L - 0.8)

    # Control signal C improves stability
    control_bonus = 0.1 * C * smoothstep(0.4, 0.7, C)

    # Core computations
    power_output = base_power * flow_mod * valve_term * tau_mod * (1.0 - 0.3 * load_penalty) + control_bonus
    # Clamp
    power_output = max(0.0, min(1.0, power_output))

    # Vibration depends on F, T, and VB
    vibration = 0.1 + 0.3 * F * T + 0.4 * VB * (1.0 - C) + 0.1 * abs(math.sin(5.0 * P))
    vibration = max(0.0, min(1.0, vibration))

    # Efficiency depends on power_output / (heat + vibration proxy)
    raw_efficiency = power_output / (0.2 + 0.8 * power_output + 0.1 * vibration + 0.15 * load_penalty)
    efficiency = max(0.0, min(1.0, raw_efficiency))

    # Heat loss depends on T, L, VA
    heat_loss = 0.15 + 0.5 * T * (1.0 - VA) + 0.2 * L + 0.1 * (1.0 - tau)
    heat_loss = max(0.0, min(1.0, heat_loss))

    # Add ~2% noise
    def add_noise(val):
        noise = rng.gauss(0, 0.015)
        return max(0.0, min(1.0, val + noise))

    return {
        "power_output": round(add_noise(power_output), 6),
        "vibration": round(add_noise(vibration), 6),
        "efficiency": round(add_noise(efficiency), 6),
        "heat_loss": round(add_noise(heat_loss), 6),
    }

def main():
    raw = sys.stdin.read()
    if not raw.strip():
        print(json.dumps({"error": "empty input"}), flush=True)
        return
    try:
        inputs = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"invalid json: {e}"}), flush=True)
        return

    required = ["P", "T", "F", "VA", "VB", "VC", "tau", "L", "C"]
    for key in required:
        if key not in inputs:
            print(json.dumps({"error": f"missing key: {key}"}), flush=True)
            return
        val = inputs[key]
        if not (isinstance(val, (int, float)) and 0.0 <= val <= 1.0):
            print(json.dumps({"error": f"key {key} must be in [0,1]"}), flush=True)
            return

    run_count = increment_run_count()
    outputs = compute(
        P=inputs["P"], T=inputs["T"], F=inputs["F"],
        VA=inputs["VA"], VB=inputs["VB"], VC=inputs["VC"],
        tau=inputs["tau"], L=inputs["L"], C=inputs["C"],
        run_count=run_count,
    )
    outputs["run_count"] = run_count
    print(json.dumps(outputs), flush=True)

if __name__ == "__main__":
    main()
