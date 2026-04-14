"""
Agent classes for the agent-to-agent communication loop.
"""
from __future__ import annotations

import sys
import os

_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from agent.llm import get_response_from_llm


# ── helpers ──────────────────────────────────────────────────────────────────

def _word_count(text: str) -> int:
    return len(text.split())


def _make_history(system_prompt: str) -> list:
    """Start a fresh conversation history with a system message."""
    return [{"role": "system", "content": system_prompt}]


# ── CommunicatingAgent ────────────────────────────────────────────────────────

class CommunicatingAgent:
    """
    One side of the two-agent communication pair.

    Each round the agent is given a fresh history seeded with its system prompt
    (which includes the task context and accumulated overseer tips).
    """

    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model
        self.history: list = []
        self.tips: list[str] = []          # tips from overseer across rounds
        self.word_counts: list[int] = []   # words per message this round

    # ── round lifecycle ───────────────────────────────────────────────────────

    def start_round(self, system_prompt: str) -> None:
        """Reset conversation history for a new round."""
        full_prompt = system_prompt
        if self.tips:
            tips_block = "\n".join(f"  • {t}" for t in self.tips)
            full_prompt += (
                f"\n\nOVERSEER TIPS FROM PREVIOUS ROUNDS (apply these now):\n{tips_block}"
            )
        self.history = _make_history(full_prompt)
        self.word_counts = []

    def receive(self, message: str) -> str:
        """
        Receive a message from the other agent and generate a reply.
        Returns the reply text.
        """
        reply, self.history, _ = get_response_from_llm(
            msg=message,
            model=self.model,
            msg_history=self.history,
        )
        self.word_counts.append(_word_count(reply))
        return reply

    def add_tip(self, tip: str) -> None:
        """Accumulate overseer tip for future rounds."""
        self.tips.append(tip)

    @property
    def avg_words(self) -> float:
        if not self.word_counts:
            return 0.0
        return sum(self.word_counts) / len(self.word_counts)


# ── OverseerAgent ─────────────────────────────────────────────────────────────

OVERSEER_SYSTEM = """\
You are the Overseer of a two-agent communication experiment.
Your job after each round:

1. READ the full exchange between Agent A and Agent B.
2. SCORE the round's communication efficiency on a scale 1–10 where:
   • 1 = extremely verbose, full of filler, redundancy, hedging
   • 5 = adequate but room to improve
   • 10 = perfectly compressed, every word carries signal, zero waste
3. Give SPECIFIC TIPS to each agent (2–3 bullet points each):
   • Point to exact phrases that were wasteful or unclear
   • Suggest concrete alternatives or structural improvements
   • Encourage developing shorthand, abbreviations, or schemas if appropriate
4. If the task has a verification question, VERIFY whether the information
   was transmitted correctly and completely.

Respond in this exact format:
SCORE: <1–10>
VERDICT: <one sentence on whether information was transmitted correctly>
TIPS FOR AGENT A:
• <tip 1>
• <tip 2>
• <tip 3 if needed>
TIPS FOR AGENT B:
• <tip 1>
• <tip 2>
• <tip 3 if needed>
"""


class OverseerAgent:
    """
    Third-party agent that watches the A↔B exchange and coaches both sides.
    """

    def __init__(self, model: str):
        self.model = model
        self.scores: list[int] = []
        self.history: list = []

    def evaluate(
        self,
        exchange_log: list[dict],  # [{"agent": "A"|"B", "text": "..."}]
        task_context: str = "",
        verification_questions: list[str] | None = None,
        agent_b_last_reply: str = "",
    ) -> dict:
        """
        Evaluate one round of exchange and return parsed feedback.

        Returns:
            {
                "score": int,
                "verdict": str,
                "tips_a": list[str],
                "tips_b": list[str],
                "raw": str,
            }
        """
        # Build prompt
        exchange_text = "\n\n".join(
            f"[Agent {e['agent']}]: {e['text']}" for e in exchange_log
        )
        prompt_parts = []
        if task_context:
            prompt_parts.append(f"TASK CONTEXT:\n{task_context}")
        prompt_parts.append(f"EXCHANGE:\n{exchange_text}")
        if verification_questions:
            qs = "\n".join(f"  {i+1}. {q}" for i, q in enumerate(verification_questions))
            prompt_parts.append(
                f"VERIFICATION — check Agent B's replies against these questions:\n{qs}\n"
                f"Agent B's last reply: {agent_b_last_reply}"
            )
        prompt = "\n\n".join(prompt_parts)

        raw, self.history, _ = get_response_from_llm(
            msg=prompt,
            model=self.model,
            msg_history=_make_history(OVERSEER_SYSTEM),
        )
        return self._parse(raw)

    def _parse(self, raw: str) -> dict:
        result = {"score": 5, "verdict": "", "tips_a": [], "tips_b": [], "raw": raw}
        section = None
        for line in raw.splitlines():
            stripped = line.strip()
            if stripped.startswith("SCORE:"):
                try:
                    result["score"] = int("".join(c for c in stripped.split(":", 1)[1] if c.isdigit() or c == ".").split(".")[0])
                except (ValueError, IndexError):
                    pass
                self.scores.append(result["score"])
            elif stripped.startswith("VERDICT:"):
                result["verdict"] = stripped.split(":", 1)[1].strip()
            elif "TIPS FOR AGENT A" in stripped.upper():
                section = "a"
            elif "TIPS FOR AGENT B" in stripped.upper():
                section = "b"
            elif stripped.startswith("•") or stripped.startswith("-"):
                tip = stripped.lstrip("•- ").strip()
                if tip:
                    if section == "a":
                        result["tips_a"].append(tip)
                    elif section == "b":
                        result["tips_b"].append(tip)
        return result
