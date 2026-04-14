import os
from agent.llm import DEFAULT_MODEL

QUESTION_ID = "id"
GROUND_TRUTH_KEY = "label"
MODEL = os.environ.get("MODEL_NAME", DEFAULT_MODEL)

def format_input_dict(row):
    return {
        "domain": "emotion",
        "text": row["text"],
        "id": row["id"],
        "instruction": (
            "Detect the primary emotion expressed in the following text. "
            "Choose exactly one of: joy, anger, sadness, fear, surprise. "
            "Respond with ONLY the emotion label in lowercase."
        ),
    }
