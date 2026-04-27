import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import re

# We read the model name from env or default to llama-3.3-70b-versatile
MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

SYSTEM_PROMPT = """You are a Hybrid IDE Coding Assistant.
You possess a dual-mode engine: Conversational and Agentic.

### MODE 1: CONVERSATIONAL (Generative)
- If the user greets you, asks a general question, or wants a conceptual explanation, respond directly and naturally like ChatGPT using pure Markdown.
- CRITICAL: YOU MUST ENTIRELY OMIT ANY ```python CODE BLOCKS in this mode! Do NOT write python scripts to `print()` your answers. The UI relies on you NOT sending code blocks so it can render text natively!
- DO NOT output internal 'thoughts', 'Plans', or 'Step 1/2/3' logic structures. Just talk directly to the user.

### MODE 2: AGENTIC (Execution)
- If the user asks you to interact with their system, files, or execute logic (e.g., "create a file", "read the directory", "run this command"), you must enter your ReAct loop: Plan -> Code -> Execute -> Debug.
- In this mode ONLY, write a short plan, then output exactly ONE runnable Python script enclosed in ```python and ``` blocks.
- The system will automatically execute your generated script locally in a sandbox.
- If there's an error, you will Debug it and provide updated code.

When you write python code (MODE 2):
- Ensure it is complete and runnable.
- It must print its results to standard output so the executor can capture it.
- Provide ONLY ONE python code block in your response.

Windows Compatibility Rules:
- RULE: Never use literal non-ASCII characters (like ° or emojis) in strings. 
- RULE: Always use Unicode escape sequences for special characters (e.g., use '\\u00b0' for the degree symbol).
- RULE: If a SyntaxError: (unicode error) occurs, do not attempt to encode/decode the string; instead, remove the special character or replace it with an escape sequence.

Robustness & Error Handling Rules:
- RULE: If an external request (e.g. API call) or logical operation fails (like a non-200 status code), you MUST `raise Exception` with a descriptive message. 
- RULE: DO NOT gracefully print a failure message and exit with 0. The system relies on exceptions to trigger the self-healing loop.
- RULE: Validate all intermediate data (e.g., check status codes, verify keys exist in JSON, verify it saved successfully). If validation fails, immediately raise an exception.

Token-Saver Rules:
- RULE: Never re-write the entire file if only one function needs a fix. Use a 'search-and-replace' format or comment blocks to indicate unchanged code.
- RULE: Before writing new code, always call `list_files()` to see what is already there. You can import Tools via `from executor import list_files, read_file, write_file, run_terminal_command`.
- RULE: Be extremely concise. Do not explain the code unless specifically asked.

Auto-Dependency Management Rule:
- RULE: If your code fails with a `ModuleNotFoundError`, it means a package is missing. In your very next attempt, use `run_terminal_command("pip install <package>")` to install it, then you may execute your main logic.

Honesty & Safety Rule:
- RULE: If the task is impossible with the current tools, you MUST explicitly say "I cannot do this" in your plan or code response. Do not hallucinate or guess.
"""

def get_llm():
    # Requires GROQ_API_KEY environment variable to be set
    return ChatGroq(model=MODEL_NAME, temperature=0.1)

def extract_code(content: str) -> str:
    """Extracts python code from markdown code blocks."""
    # Find all python blocks (either python or python3)
    match = re.search(r"```python\s*(.*?)```", content, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Fallback to any code block
    match = re.search(r"```\s*(.*?)```", content, re.DOTALL)
    if match:
        return match.group(1).strip()
        
    # If no code block is found, return empty indicating it was conversational output
    return ""

def generate_code(state: dict) -> dict:
    """
    LLM generation node. Generates or attempts to fix code based on the current state.
    """
    llm = get_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    
    task = state.get("task")
    previous_code = state.get("code")
    error = state.get("error")
    
    if error:
        prompt = (
            f"Original Task: {task}\n\n"
            f"Your previous code:\n```python\n{previous_code}\n```\n\n"
            f"Execution failed with the following error/output:\n{error}\n\n"
            "Please analyze the error (Debug), explain what went wrong (Plan), and provide the fixed code (Code)."
        )
        messages.append(HumanMessage(content=prompt))
    else:
        prompt = f"Task: {task}\n\nPlease Plan your approach, then Code it."
        messages.append(HumanMessage(content=prompt))
    
    response = llm.invoke(messages)
    content = response.content
    
    # Extract the code from the response
    code = extract_code(content)
    
    return {
        "code": code,
        "plan": content # Store the entire response for logging/debugging
    }
