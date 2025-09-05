import os
from dotenv import load_dotenv
from openai import OpenAI
import sys
import functions.get_files_info as functions
import json

TOOL_MAPPING = {
    "get_files_info": functions.get_files_info,
    "get_file_content": functions.get_file_content,
    "run_python_file": functions.run_python_file,
    "write_file": functions.write_file,
}


def call_function(tool_call, verbose=False):
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments)

    if verbose:
        print(f"Calling function: {function_name}({function_args})")
    else:
        print(f" - Calling function: {function_name}")

    function_args["working_directory"] = "./calculator"

    if function_name not in TOOL_MAPPING:
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps({"error": f"Unknown function: {function_name}"}),
        }

    tool_response = TOOL_MAPPING[function_name](**function_args)

    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps({"result": tool_response}),
    }


if len(sys.argv) < 2:
    exit(1)

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENAI_API_KEY"),
)

system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories
- Read file contents
- Execute Python files with optional arguments
- Write or overwrite files

For this you could only use tools 'get_files_info', 'get_file_content', 'run_python_file', and 'write_file'. You should never try to use other tools.

All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
You can consider directory "calculator" as working directory.
You should always start with list files and directories.
You should always read file content even if you know it from previous requests, it could change.
Never run files before reading their contents.

Don't ask to provide you more info, get it yourself using provided tools.
"""

data = {
    "model": os.environ.get("MODEL"),
    "messages": [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": sys.argv[1],
        }
    ],
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_files_info",
            "description": "Lists files in the specified directory along with their sizes, constrained to the working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself."
                    }
                },
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_content",
            "description": "Get content of specified file, constrained to the working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to file, relative to the working directory."
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_python_file",
            "description": "Exec specified python file, constrained to the working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to file, relative to the working directory."
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of optional arguments to exec file."
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Overwrite specified file with content, constrained to the working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to file, relative to the working directory."
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write in file."
                    }
                },
                "required": ["file_path", "content"]
            }
        }
    },
]

data["tools"] = tools

verbose = len(sys.argv) >= 3 and sys.argv[2] == "--verbose"

try:
    for i in range(0, 20):
        completion = client.chat.completions.create(**data)
        tool_calls = completion.choices[0].message.tool_calls
        if not tool_calls:
            break

        tool_call = tool_calls[0]

        data["messages"].append(tool_call)

        new_message = call_function(tool_call, verbose)
        data["messages"].append(new_message)
        if verbose:
            print(f"-> {new_message['content']}")

    text = completion.choices[0].message.content
    prompt_tokens = completion.usage.prompt_tokens
    candidates_token = completion.usage.completion_tokens
except Exception as e:
    text = e.__str__()
    prompt_tokens = 19
    candidates_token = len(text.split())

print(text)
if verbose:
    print(f"User prompt: {sys.argv[1]}")
    print(f"Prompt tokens: {prompt_tokens}")
    print(f"Response tokens: {candidates_token}")
