# Formwerk domain scoring for HyperAgents
#
# Scores task agent predictions by comparing parameter suggestions
# against known-good solutions OR running the actual evaluator.

import json

def score_prediction(prediction: str, label: str, scenario: dict) -> dict:
    """Score a parameter prediction against the expected label.

    Returns dict with:
      correct: bool
      score: float (0-1, partial credit)
      reason: str
    """
    try:
        pred_params = json.loads(prediction)
    except json.JSONDecodeError:
        return {"correct": False, "score": 0.0,
                "reason": f"Could not parse prediction as JSON: {prediction[:100]}"}

    try:
        expected = json.loads(label)
    except json.JSONDecodeError:
        return {"correct": False, "score": 0.0, "reason": "Bad label"}

    if not isinstance(pred_params, dict):
        return {"correct": False, "score": 0.0,
                "reason": "Prediction must be a JSON object"}

    # Score: count how many expected params are within 20% of target
    total_keys = len(expected)
    if total_keys == 0:
        return {"correct": True, "score": 1.0, "reason": "No params to check"}

    matches = 0
    reasons = []
    for key, target_val in expected.items():
        if key not in pred_params:
            reasons.append(f"missing {key}")
            continue

        pred_val = pred_params[key]
        if isinstance(target_val, (int, float)) and isinstance(pred_val, (int, float)):
            target = float(target_val)
            pred = float(pred_val)
            if target == 0:
                if abs(pred) < 0.01:
                    matches += 1
                else:
                    reasons.append(f"{key}: {pred} (expected ~0)")
            else:
                ratio = abs(pred - target) / abs(target)
                if ratio <= 0.25:  # within 25% of target
                    matches += 1
                else:
                    reasons.append(f"{key}: {pred} (expected ~{target}, off by {ratio*100:.0f}%)")
        else:
            if pred_val == target_val:
                matches += 1
            else:
                reasons.append(f"{key}: {pred_val} != {target_val}")

    score = matches / total_keys
    correct = score >= 0.8  # 80% of params must be close

    return {
        "correct": correct,
        "score": score,
        "reason": "; ".join(reasons) if reasons else "all params match"
    }
