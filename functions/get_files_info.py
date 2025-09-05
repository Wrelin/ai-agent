import os
from dotenv import load_dotenv
import subprocess


def get_files_info(working_directory, directory="."):
    try:
        full_path = os.path.join(working_directory, directory)
        abs_path = os.path.abspath(full_path)

        if not abs_path.startswith(os.path.abspath(working_directory)):
            return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'
        if not os.path.isdir(abs_path):
            return f'Error: "{directory}" is not a directory'

        result = ""
        for name in os.listdir(abs_path):
            name_path = os.path.join(abs_path, name)
            result += f"- {name}: file_size={os.path.getsize(name_path)} bytes, is_dir={os.path.isdir(name_path)}\n"

        return result.rstrip("\n")
    except Exception as e:
        return f"Error: {e}"


def get_file_content(working_directory, file_path):
    try:
        full_path = os.path.join(working_directory, file_path)
        abs_path = os.path.abspath(full_path)

        if not abs_path.startswith(os.path.abspath(working_directory)):
            return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'
        if not os.path.isfile(abs_path):
            return f'Error: File not found or is not a regular file: "{file_path}"'

        load_dotenv()
        character_limit = int(os.environ.get("CHARACTER_LIMIT"))
        with open(abs_path, "r") as f:
            file_content_string = f.read(character_limit)

        if len(file_content_string) >= character_limit:
            file_content_string += f'[...File "{file_path}" truncated at 10000 characters]'

        return file_content_string
    except Exception as e:
        return f"Error: {e}"


def write_file(working_directory, file_path, content):
    try:
        full_path = os.path.join(working_directory, file_path)
        abs_path = os.path.abspath(full_path)

        if not abs_path.startswith(os.path.abspath(working_directory)):
            return f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory'

        with open(abs_path, "w") as f:
            f.write(content)

        return f'Successfully wrote to "{file_path}" ({len(content)} characters written)'
    except Exception as e:
        return f"Error: {e}"


def run_python_file(working_directory, file_path, args=[]):
    try:
        full_path = os.path.join(working_directory, file_path)
        abs_path = os.path.abspath(full_path)

        if not abs_path.startswith(os.path.abspath(working_directory)):
            return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'

        if not os.path.exists(abs_path):
            return f'Error: File "{file_path}" not found.'

        if not abs_path.endswith(".py"):
            return f'Error: "{file_path}" is not a Python file.'

        try:
            output = subprocess.run(["python3", abs_path] + args, capture_output=True, text=True, timeout=30)
        except Exception as e:
            return f"Error: executing Python file: {e}"

        result = []
        if output.stdout:
            result.append(f"STDOUT: {output.stdout}")
        if output.stderr:
            result.append(f"STDERR: {output.stderr}")
        if output.returncode != 0:
            result.append(f"Process exited with code {output.returncode}")

        if not result:
            return "No output produced."

        return "\n".join(result)

    except Exception as e:
        return f"Error: {e}"

