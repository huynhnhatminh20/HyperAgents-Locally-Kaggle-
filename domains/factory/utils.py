import os
from agent.llm import DEFAULT_MODEL

QUESTION_ID = "id"
GROUND_TRUTH_KEY = "label"
MODEL = os.environ.get("MODEL_NAME", DEFAULT_MODEL)

LABELS = ["expedite", "prioritize_urgent", "rebalance", "batch_production", "optimize_throughput"]

def format_input_dict(row):
    """Format a factory scenario row into the input dict for the task agent."""
    return {
        "domain": "factory",
        "id": row["id"],
        "scenario": row["scenario"],
        "instruction": (
            "You are a factory floor controller. Analyse the production scenario and output "
            "exactly one dispatch decision from: "
            "expedite, prioritize_urgent, rebalance, batch_production, optimize_throughput.\n"
            "Decision rules (apply top-to-bottom, first match wins):\n"
            "  expedite            — any overdue jobs > 0\n"
            "  prioritize_urgent   — urgent jobs >= 3 AND overdue == 0\n"
            "  rebalance           — max_machine_load - min_machine_load > 0.55 AND urgent < 3 AND overdue == 0\n"
            "  batch_production    — largest job-type batch >= 10 AND machines balanced AND no critical pressure\n"
            "  optimize_throughput — none of the above apply\n"
            "Respond with ONLY the decision label in lowercase, nothing else."
        ),
    }
