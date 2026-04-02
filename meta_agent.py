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

        feedback_summary = ""
        # Look for the most recent report in the eval_path
        if os.path.exists(eval_path):
            reports = []
            for root, dirs, files in os.walk(eval_path):
                if "report.json" in files:
                    reports.append(os.path.join(root, "report.json"))

            if reports:
                # Sort by modification time to get the latest
                latest_report_path = max(reports, key=os.path.getmtime)
                try:
                    with open(latest_report_path, "r") as f:
                        report_data = json.load(f)
                    score = report_data.get("overall_accuracy", "N/A")
                    feedback_summary = f"\nLatest Evaluation Score: {score}\nReport details: {json.dumps(report_data, indent=2)[:2000]}"
                except Exception as e:
                    feedback_summary = f"\n(Error reading latest report: {e})"

        # Provide the current source of task_agent.py for immediate context
        task_agent_source = ""
        task_agent_path = os.path.join(repo_path, "task_agent.py")
        if os.path.exists(task_agent_path):
            try:
                with open(task_agent_path, "r") as f:
                    task_agent_source = f"\n\nCurrent `task_agent.py` source:\n```python\n{f.read()}\n```"
            except Exception as e:
                task_agent_source = f"\n(Error reading task_agent.py: {e})"

        # Identify domain and provide dataset context if possible
        domain_context = ""
        if "report_data" in locals():
            domain = report_data.get("domain", "unknown")
            dataset_path = os.path.join(repo_path, "domains", domain, "dataset.py")
            if os.path.exists(dataset_path):
                try:
                    with open(dataset_path, "r") as f:
                        domain_context = f"\n\nDomain Dataset (`{domain}`):\n```python\n{f.read()[:3000]}\n```"
                except Exception:
                    pass

        task_agent_path = os.path.join(repo_path, "task_agent.py")
        instruction = (
            f"You are a Meta-Agent responsible for self-improving the `TaskAgent`. "
            f"Rewrite `task_agent.py` to achieve a higher evaluation score. "
            f"You have {iterations_left if iterations_left is not None else 'unknown'} iterations left.\n"
            f"{feedback_summary}"
            f"{domain_context}"
            f"{task_agent_source}\n\n"
            "CRITICAL RULES:\n"
            f"1. ONLY modify `task_agent.py` at `{task_agent_path}`.\n"
            "2. NEVER delete the repository or run 'rm -rf'.\n"
            "3. Use the `bash` tool to overwrite the file with your improved version.\n\n"
            "STRATEGY:\n"
            "1. Study the current task_agent.py source and the evaluation score above.\n"
            "2. Analyze failure cases from the report.\n"
            "3. Write an improved version with a better prompt, smarter parsing, or domain-specific rules.\n\n"
            "TOOL CALL FORMAT — use bash with a heredoc to write the COMPLETE new file:\n"
            "<json>\n"
            "{\n"
            "  \"tool_name\": \"bash\",\n"
            "  \"tool_input\": {\n"
            f"    \"command\": \"cat > {task_agent_path} << 'PYEOF'\\n<COMPLETE NEW task_agent.py CONTENT>\\nPYEOF\"\n"
            "  }\n"
            "}\n"
            "</json>\n\n"
            "Replace <COMPLETE NEW task_agent.py CONTENT> with the full improved Python source. "
            "Write the COMPLETE file in ONE bash call. Do NOT use str_replace."
        )

        new_msg_history = chat_with_agent(instruction, model=self.model, msg_history=[], logging=self.log, tools_available='all')
