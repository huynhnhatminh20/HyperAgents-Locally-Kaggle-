import re
import json

from agent.llm import get_response_from_llm
from agent.tools import load_tools

def get_tooluse_prompt(tool_infos=[]):
    """
    Get the prompt for using the available tools.
    """
    # If no tools are available, return an empty string
    if not tool_infos or len(tool_infos) == 0:
        return ""
    # Create the prompt
    tools_available = [str(tool_info) for tool_info in tool_infos]
    tools_available = '\n\n'.join(tools_available) if tools_available else 'None'
    tooluse_prompt = """Here are the available tools:
```
{tools_available}
```

Use only one tool (if needed) in this format:
<json>
{{
    "tool_name": ...,
    "tool_input": ...
}}
</json>

ONLY USE ONE TOOL PER RESPONSE, AND STRICTLY FOLLOW THE FORMAT OF TOOL_NAME AND TOOL_INPUT ABOVE.
DO NOT HALLUCINATE OR MAKE UP ANYTHING.
""".format(tools_available=tools_available)
    return tooluse_prompt.strip()

def should_retry_tool_use(response, tool_uses=None):
    """
    Check if the response attempts to use a tool,
    but ran out of output context.
    """
    # If there are tool uses, we don't need to check for retry
    if tool_uses is not None and len(tool_uses) > 0:
        return False

    # Find positions of the markers
    json_pos = response.find("<json>")
    tool_name_pos = response.find("tool_name")
    tool_input_pos = response.find("tool_input")

    # Check ordering and length condition
    if (
        json_pos != -1
        and tool_name_pos != -1
        and tool_input_pos != -1
        and json_pos < tool_name_pos < tool_input_pos
        and len(response) >= 2000
    ):
        return True

    # No retry
    return False

def check_for_tool_uses(response):
    """
    Checks if the response contains one or more tool calls in json code blocks.
    Returns a list of tool use dictionaries.
    Handles common local model formatting errors.
    """
    def _collect_backtick_matches(text):
        """Extract JSON objects from ```json...``` blocks using a brace-depth walker.

        A simple lazy regex fails when the heredoc command string inside the JSON
        contains triple-backtick fences (e.g. Python f-strings with inline code).
        """
        found = []
        start = text.find('```json')
        while start != -1:
            brace_start = text.find('{', start)
            if brace_start == -1:
                break
            depth, in_string, escape_next, pos = 0, False, False, brace_start
            while pos < len(text):
                ch = text[pos]
                if escape_next:
                    escape_next = False
                elif ch == '\\' and in_string:
                    escape_next = True
                elif ch == '"' and not escape_next:
                    in_string = not in_string
                elif not in_string:
                    if ch == '{':
                        depth += 1
                    elif ch == '}':
                        depth -= 1
                        if depth == 0:
                            found.append(text[brace_start:pos + 1])
                            break
                pos += 1
            start = text.find('```json', start + 1)
        return found

    def _parse_matches(matches):
        tool_uses = []
        for match in matches:
            # Strip any accidental markdown fencing inside the captured block
            match = re.sub(r'^```(json)?', '', match, flags=re.MULTILINE)
            match = re.sub(r'```$', '', match, flags=re.MULTILINE).strip()
            try:
                tool_use = json.loads(match)
            except json.JSONDecodeError:
                # Fuzzy parse: trailing commas, unquoted keys
                try:
                    fixed = re.sub(r',\s*([}\]])', r'\1', match)
                    fixed = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', fixed)
                    tool_use = json.loads(fixed)
                except Exception:
                    continue
            if 'tool_name' not in tool_use or 'tool_input' not in tool_use:
                continue
            tool_uses.append(tool_use)
        return tool_uses

    # Primary: <json>...</json> tags
    pattern = r'<json>\s*(.*?)\s*</json>'
    json_tag_matches = re.findall(pattern, response, re.DOTALL)
    tool_uses = _parse_matches(json_tag_matches)

    # Fallback: ```json blocks — many local models use this format.
    # Also used when the primary pattern matched only example/template <json>
    # blocks (e.g. from the tooluse prompt itself) that fail to parse as valid
    # tool calls, leaving tool_uses empty despite non-empty json_tag_matches.
    if not tool_uses:
        backtick_matches = _collect_backtick_matches(response)
        tool_uses = _parse_matches(backtick_matches)

    return tool_uses if tool_uses else None

def process_tool_call(tools_dict, tool_name, tool_input):
    try:
        if tool_name in tools_dict:
            return tools_dict[tool_name]['function'](**tool_input)
        else:
            return f"Error: Tool '{tool_name}' not found"
    except Exception as e:
        return f"Error executing tool '{tool_name}': {str(e)}"

def chat_with_agent(
    msg,
    model="claude-4-sonnet-genai",
    msg_history=None,
    logging=print,
    tools_available=[],  # Empty list means no tools, 'all' means all tools
    multiple_tool_calls=False,  # Whether to allow multiple tool calls in a single response
    max_tool_calls=40,  # Maximum number of tool calls allowed in a single response, -1 for unlimited
):
    get_response_fn = get_response_from_llm
    # Construct message
    if msg_history is None:
        msg_history = []
    new_msg_history = msg_history

    try:
        # Load all tools
        all_tools = load_tools(logging=logging, names=tools_available)
        tools_dict = {tool['info']['name']: tool for tool in all_tools}
        system_msg = f"{get_tooluse_prompt([tool['info'] for tool in all_tools])}\n\n"
        num_tool_calls = 0

        # Call API
        logging(f"Input: {repr(msg)}")
        response, new_msg_history, info = get_response_fn(
            msg=system_msg + msg,
            model=model,
            msg_history=new_msg_history,
        )
        logging(f"Output: {repr(response)}")
        # logging(f"Info: {repr(info)}")

        # Tool use
        tool_uses = check_for_tool_uses(response)
        retry_tool_use = should_retry_tool_use(response, tool_uses)
        while tool_uses or retry_tool_use:
            # Check for max tool calls
            if max_tool_calls > 0 and num_tool_calls >= max_tool_calls:
                logging("Error: Maximum number of tool calls reached.")
                break

            tool_msgs = []

            # Process tool uses
            if tool_uses:
                tool_uses = tool_uses if multiple_tool_calls else tool_uses[:1]
                for tool_use in tool_uses:
                    tool_name = tool_use['tool_name']
                    tool_input = tool_use['tool_input']
                    tool_output = process_tool_call(tools_dict, tool_name, tool_input)
                    num_tool_calls += 1
                    tool_msg = f'''<json>
    {{
        "tool_name": "{tool_name}",
        "tool_input": {tool_input},
        "tool_output": "{tool_output}"
    }}
    </json>'''.strip()
                    logging(f"Tool output: {repr(tool_msg)}")
                    tool_msgs.append(tool_msg)

            # Check for retry
            if retry_tool_use:
                logging("Error: Output context exceeded. Please try again.")
                tool_msgs.append("Error: Output context exceeded. Please try again.")

            # Get tool response
            response, new_msg_history, info = get_response_fn(
                msg=system_msg + '\n\n'.join(tool_msgs),
                model=model,
                msg_history=new_msg_history,
            )
            logging(f"Output: {repr(response)}")
            # logging(f"Info: {repr(info)}")

            # Check for next tool use
            tool_uses = check_for_tool_uses(response)
            retry_tool_use = should_retry_tool_use(response, tool_uses)

    except Exception as e:
        logging(f"Error: {str(e)}")
        raise e

    return new_msg_history

if __name__ == "__main__":
    msg = """hello"""
    new_msg_history = chat_with_agent(msg)
