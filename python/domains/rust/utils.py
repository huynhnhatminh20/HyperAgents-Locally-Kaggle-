import os
from agent.llm import DEFAULT_MODEL

QUESTION_ID = "id"
GROUND_TRUTH_KEY = "label"
MODEL = os.environ.get("MODEL_NAME", DEFAULT_MODEL)

def format_input_dict(row):
    """Format a dataset row into the input dict for the task agent."""
    return {
        "domain": "rust",
        "id": row["id"],
        "code": row["code"],
        "instruction": (
            "You are a Rust compiler expert. Analyze the following Rust code snippet "
            "and classify it as exactly one of:\n"
            "  compiles    - the code is valid Rust and compiles successfully\n"
            "  borrow_error - the borrow checker rejects it (use-after-move, "
            "double-borrow, mutation while borrowed, etc.)\n"
            "  type_error  - the compiler rejects it due to a type or trait mismatch "
            "(wrong type, trait not implemented, mismatched return type, etc.)\n\n"
            "Respond with ONLY the label in lowercase: compiles, borrow_error, or type_error."
        ),
    }
