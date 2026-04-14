# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
from agent.llm import DEFAULT_MODEL

QUESTION_ID = "id"
GROUND_TRUTH_KEY = "label"
MODEL = os.environ.get("MODEL_NAME", DEFAULT_MODEL)

def format_input_dict(row):
    """Format a dataset row into the input dict for the task agent."""
    return {
        "domain": "text_classify",
        "text": row["text"],
        "id": row["id"],
        "instruction": (
            "Classify the sentiment of the following text as exactly one of: "
            "positive, negative, or neutral. "
            "Respond with ONLY the label in lowercase."
        ),
    }
