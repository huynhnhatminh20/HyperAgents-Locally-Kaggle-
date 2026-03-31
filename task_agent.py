from agent.base_agent import AgentSystem
from agent.llm_withtools import chat_with_agent
from utils.common import extract_jsons

class ThoughtLog:
    """A log to store the agent's internal reasoning process."""
    def __init__(self):
        self.thoughts = []

    def log(self, thought: str):
        self.thoughts.append(thought)

    def get_full_log(self) -> str:
        return "\n".join([f"- {t}" for t in self.thoughts])

class TaskAgent(AgentSystem):
    def forward(self, inputs):
        """
        An agent that solves a given task with internal reasoning.

        Args:
            inputs (dict): A dictionary with input data for the task.

        Returns:
            tuple:
                - prediction (str): The prediction made by the agent.
                - new_msg_history (list): A list of messages representing the message history.
        """
        thought_log = ThoughtLog()
        domain = inputs.get('domain', 'unknown')

        # Initial reasoning step
        thought_log.log(f"Received task for domain: {domain}")
        thought_log.log(f"Input data keys: {list(inputs.keys())}")

        instruction = f"""You are a reasoning agent.
First, analyze the task and plan your response.
Then, provide your final answer in the required JSON format.

Task input:
```
{inputs}
```

Respond in JSON format:
<json>
{{
    "reasoning": "your step-by-step thought process",
    "response": "your final prediction"
}}
</json>"""

        new_msg_history = chat_with_agent(instruction, model=self.model, msg_history=[], logging=self.log)

        # Extract the response and reasoning
        prediction = "None"
        try:
            last_msg = new_msg_history[-1]['text']
            extracted_jsons = extract_jsons(last_msg)
            if extracted_jsons:
                data = extracted_jsons[-1]
                prediction = data.get('response', 'None')
                reasoning = data.get('reasoning', 'No reasoning provided')
                thought_log.log(f"LLM Reasoning: {reasoning}")
        except Exception as e:
            self.log(f"Error extracting prediction: {e}")
            prediction = "None"

        # The thought_log can be inspected by the MetaAgent in future iterations
        return prediction, new_msg_history
