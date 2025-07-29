import csv
import random
import os

def simulate_binary_event_market(
    market_name: str,
    steps: int,
    initial_prob: float = 0.5,
    volatility: float = 0.015,
    reveal_step: int = 600,
    resolve_step: int = 800,
    outcome: str = "random",  # "yes", "no", or "random"
    trend_strength: float = 0.01,
    seed: int = 42,
):
    assert 0 < reveal_step < resolve_step < steps, "reveal_step and resolve_step must be within range"
    assert outcome in ["yes", "no", "random"], "Invalid outcome type"

    random.seed(seed)
    probabilities = [initial_prob]

    # Determine final outcome
    if outcome == "random":
        resolved_value = random.choice([0, 1])
    elif outcome == "yes":
        resolved_value = 1
    else:
        resolved_value = 0

    for t in range(1, steps):
        prev = probabilities[-1]

        if t < reveal_step:
            change = random.gauss(0, volatility)
        elif t < resolve_step:
            time_to_resolve = max(resolve_step - t, 1)
            scaled_bias = ((1 if resolved_value == 1 else -1) * trend_strength) / time_to_resolve
            change = random.gauss(scaled_bias, volatility)

        else:
            probabilities.append(float(resolved_value))
            continue

        new_prob = max(min(prev + change, 0.99), 0.01)
        probabilities.append(new_prob)

    # Prepare file path with market name
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "sim_data")
    os.makedirs(data_dir, exist_ok=True)

    output_filename = f"{market_name}_sim.csv"
    output_path = os.path.join(data_dir, output_filename)

    # Write CSV
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["market", "timestep", "probability", "resolved_value"])
        for t, p in enumerate(probabilities):
            res = "" if t < resolve_step else resolved_value
            writer.writerow([market_name, t, round(p, 4), res])

    print(f"Sim complete for market '{market_name}'. Outcome: {'YES' if resolved_value == 1 else 'NO'}. Saved to: {output_path}")

# Example usage
if __name__ == "__main__":
    simulate_binary_event_market(
        market_name="Test_3",
        steps=10000,
        initial_prob=0.48,
        volatility=0.021,
        reveal_step=8000,
        resolve_step=9995,
        outcome="random",
        trend_strength=0.02,
        seed=123
    )
