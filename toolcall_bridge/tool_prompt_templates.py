import json
from typing import Union


def format_system_and_tools(system_prompt: Union[str, None], tools=None):
    result = system_prompt or ""
    if tools:
        tools_json = "\n".join(json.dumps(tool, ensure_ascii=False) for tool in tools)

        tool_template = """
# Tools

You may call one or more functions to assist with the user query.
<tools>
{tools_json}
</tools>

For function call returns, you should first print <｜tool▁calls▁begin｜>
For each function call, you should return object like:
<｜tool▁call▁begin｜>function<｜tool▁sep｜><function_name>
```json
<function_arguments_in_json_format>
```<｜tool▁call▁end｜>
Just follow the ouput format to use tools when needed."""

        result += tool_template.format(tools_json=tools_json)

    return result
