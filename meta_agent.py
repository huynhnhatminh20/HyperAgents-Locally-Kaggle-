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

        instruction = (
            f"You are a Meta-Agent responsible for self-improving the `TaskAgent`. "
            f"Modify the codebase at `{repo_path}` to achieve a higher evaluation score. "
            f"You have {iterations_left if iterations_left is not None else 'unknown'} iterations left."
            f"{feedback_summary}"
            f"{domain_context}"
            f"{task_agent_source}\n\n"
            "STRATEGY:\n"
            "1. Study the Domain Dataset to understand the expected labels and data format.\n"
            "2. Analyze the latest evaluation report to see exactly which examples failed.\n"
            "3. Examine the current `task_agent.py` logic and its reasoning process.\n"
            "4. Implement improvements: this could be hardcoding few-shot examples from the dataset into the prompt, "
            "adding regex rules for common failure cases, or refining the reasoning chain.\n"
            "5. Ensure your modifications are syntactically correct and maintain the required interface."
        )

        new_msg_history = chat_with_agent(instruction, model=self.model, msg_history=[], logging=self.log, tools_available='all')
