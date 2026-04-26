import subprocess
import tempfile
import os

def list_files(directory=".") -> list:
    """Returns a list of all files in the current workspace."""
    files = []
    for f in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, f)):
            files.append(f)
    return files

def read_file(filename: str) -> str:
    """Returns the content of a specific file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return str(e)

def write_file(filename: str, content: str) -> str:
    """Creates or overwrites a file with the specified text content."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {filename}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"

def run_terminal_command(command: str) -> str:
    """Executes a terminal shell command and returns the output."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, errors='replace', timeout=30
        )
        if result.returncode == 0:
            return f"Command succeeded:\n{result.stdout}"
        else:
            return f"Command failed (Code {result.returncode}):\n{result.stderr}\n{result.stdout}"
    except Exception as e:
        return f"Command execution error: {str(e)}"

def execute_code(code: str) -> dict:
    """
    Executes the provided Python code in a temporary file.
    Captures and returns the STDOUT and STDERR.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(code)
        temp_file_path = f.name
    
    try:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        # Run the code using subprocess
        result = subprocess.run(
            ['python', temp_file_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env,
            timeout=15  # Timeout to prevent infinite loops
        )
        
        output = result.stdout
        error = result.stderr
        success = result.returncode == 0
        
        return {
            "success": success,
            "output": output,
            "error": error if error else (output if not success else None)
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "Execution timed out after 15 seconds."
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e)
        }
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
