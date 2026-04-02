# Copyright (c) Meta Platforms, Inc. and affiliates.

from agent.base_agent import AgentSystem
from agent.llm_withtools import chat_with_agent

class MetaAgent(AgentSystem):
    def forward(self, repo_path, eval_path, iterations_left=None):
        """
        A meta agent that recursively self-improves.

        Args:
            repo_path (str): The path to the repository.
            eval_path (str): The path to previously generated agents and their evaluation results.
            iterations_left (int, optional): The number of remaining iterations in which the meta agent will be invoked in future. Defaults to None.
        """
        import os
        import json

        # ── Evaluation feedback ───────────────────────────────────────────────
        feedback_summary = ""
        report_data = None
        if os.path.exists(eval_path):
            reports = []
            for root, dirs, files in os.walk(eval_path):
                if "report.json" in files:
                    reports.append(os.path.join(root, "report.json"))
            if reports:
                latest_report_path = max(reports, key=os.path.getmtime)
                try:
                    with open(latest_report_path, "r") as f:
                        report_data = json.load(f)
                    score = report_data.get("overall_accuracy", "N/A")
                    feedback_summary = (
                        f"\n## Latest Evaluation Score: {score}\n"
                        f"Report details:\n```json\n{json.dumps(report_data, indent=2)[:2000]}\n```"
                    )
                except Exception as e:
                    feedback_summary = f"\n(Error reading latest report: {e})"

        # ── Patch history (what the meta agent already tried) ─────────────────
        patch_history_summary = ""
        if os.path.exists(eval_path):
            patches = []
            for root, dirs, files in os.walk(eval_path):
                if "model_patch.diff" in files:
                    patch_path = os.path.join(root, "model_patch.diff")
                    if os.path.getsize(patch_path) > 0:
                        patches.append(patch_path)
            if patches:
                patches.sort(key=os.path.getmtime)
                # Show the last 3 non-empty patches
                recent = patches[-3:]
                history_parts = []
                for p in recent:
                    try:
                        with open(p) as f:
                            diff = f.read(3000)
                        gen_label = os.path.basename(os.path.dirname(os.path.dirname(p)))
                        history_parts.append(
                            f"### Patch from {gen_label}:\n```diff\n{diff}\n```"
                        )
                    except Exception:
                        pass
                if history_parts:
                    patch_history_summary = (
                        "\n## Previous Patches (already tried — don't repeat these):\n"
                        + "\n".join(history_parts)
                    )

        # ── Domain dataset context ────────────────────────────────────────────
        domain_context = ""
        if report_data:
            domain = report_data.get("domain", "unknown")
            dataset_path = os.path.join(repo_path, "domains", domain, "dataset.py")
            if os.path.exists(dataset_path):
                try:
                    with open(dataset_path) as f:
                        domain_context = (
                            f"\n## Domain Dataset (`{domain}`):\n```python\n{f.read()[:3000]}\n```"
                        )
                except Exception:
                    pass

        # ── Current task_agent.py source ─────────────────────────────────────
        task_agent_source = ""
        task_agent_path = os.path.join(repo_path, "task_agent.py")
        if os.path.exists(task_agent_path):
            try:
                with open(task_agent_path) as f:
                    src = f.read()
                task_agent_source = (
                    f"\n## Current `task_agent.py`:\n```python\n{src}\n```"
                )
            except Exception as e:
                task_agent_source = f"\n(Error reading task_agent.py: {e})"

        # ── Instruction ───────────────────────────────────────────────────────
        iters = iterations_left if iterations_left is not None else "unknown"
        instruction = (
            f"You are a Meta-Agent responsible for self-improving the `TaskAgent`.\n"
            f"You have {iters} iteration(s) left. Maximise the evaluation score.\n"
            f"{feedback_summary}"
            f"{patch_history_summary}"
            f"{domain_context}"
            f"{task_agent_source}\n\n"
            "## Rules\n"
            f"1. ONLY modify `task_agent.py` at: `{task_agent_path}`\n"
            "2. Do NOT delete the repository or run destructive commands.\n"
            "3. Your edit MUST produce valid Python — a syntax check runs after your tool call.\n"
            "4. Do NOT repeat patches already shown above.\n\n"
            "## How to edit\n"
            "Prefer surgical `str_replace` when only a small section changes:\n"
            "<json>\n"
            "{\n"
            '  "tool_name": "editor",\n'
            '  "tool_input": {\n'
            '    "command": "str_replace",\n'
            f'    "path": "{task_agent_path}",\n'
            '    "old_str": "exact existing text (must be unique in the file)",\n'
            '    "new_str": "replacement text"\n'
            "  }\n"
            "}\n"
            "</json>\n\n"
            "Use `create` only when you want to rewrite the whole file:\n"
            "<json>\n"
            "{\n"
            '  "tool_name": "editor",\n'
            '  "tool_input": {\n'
            '    "command": "create",\n'
            f'    "path": "{task_agent_path}",\n'
            '    "file_text": "...complete new Python source as a plain string..."\n'
            "  }\n"
            "}\n"
            "</json>\n\n"
            "Study the score and failure cases, then make ONE targeted improvement."
        )

        chat_with_agent(
            instruction,
            model=self.model,
            msg_history=[],
            logging=self.log,
            tools_available='all',
        )
