import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import threading
import os
import sys
import datetime
import webbrowser
import tkinter as tk
from tkinter import filedialog

from agent import generate_code
from executor import execute_code
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Make sure templates dir exists
os.makedirs("templates", exist_ok=True)
templates = Jinja2Templates(directory="templates")

def log_event(event_type: str, content: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"\n[{timestamp}] === {event_type} ===\n{content}\n"
    with open("session.log", "a", encoding="utf-8") as f:
        f.write(log_entry)

class AgentState(TypedDict):
    task: str
    code: str
    output: str
    error: Optional[str]
    iterations: int
    plan: str

# ReAct Logic Node Wrappers
def code_node(state: AgentState):
    current_iter = state.get("iterations", 0) + 1
    result = generate_code(state)
    plan_text = result.get("plan", "")
    code_text = result.get("code", "")
    
    log_event("Agent Thought & Plan", plan_text)
    
    if "I cannot do this" in plan_text or "I cannot do this" in code_text:
        return {"code": code_text, "plan": plan_text, "iterations": current_iter, "error": "I cannot do this - task aborted by Agent."}
    
    return {"code": code_text, "plan": plan_text, "iterations": current_iter}

def execute_node(state: AgentState):
    code = state.get("code", "")
    if state.get("error") == "I cannot do this - task aborted by Agent.":
        return {"error": state.get("error")}
        
    log_event("Executor Running Code", code)
    exec_result = execute_code(code)
    
    if exec_result["success"]:
        log_event("Execution Successful", f"Output:\n{exec_result['output']}")
        return {"output": exec_result["output"], "error": None}
    else:
        log_event("Execution Failed", f"Error:\n{exec_result['error']}")
        return {"output": exec_result["output"], "error": exec_result["error"]}

def should_continue(state: AgentState) -> str:
    if state.get("error") == "I cannot do this - task aborted by Agent.":
        return END
    if state.get("error"):
        if state.get("iterations", 0) >= 3:
            return END
        return "code"
    return END

def needs_execution(state: AgentState) -> str:
    code_text = state.get("code", "")
    if state.get("error") == "I cannot do this - task aborted by Agent.":
        return END
    
    # Dual-Mode Routing: If the agent didn't write an executable python script,
    # we assume it is just having a direct generative conversation with the user.
    if not code_text or code_text.strip() == "":
        return END
        
    return "execute"

workflow = StateGraph(AgentState)
workflow.add_node("code", code_node)
workflow.add_node("execute", execute_node)
workflow.set_entry_point("code")
# Use a conditional edge right out of the LLM node to skip execution if it's just chat
workflow.add_conditional_edges("code", needs_execution, {"execute": "execute", END: END})
workflow.add_conditional_edges("execute", should_continue, {"code": "code", END: END})
graph = workflow.compile()

class ChatRequest(BaseModel):
    prompt: str
    code: str

@app.get("/api/choose-workspace")
def choose_workspace():
    def ask():
        root = tk.Tk()
        root.withdraw()
        root.lift()
        root.attributes('-topmost', True)
        path = filedialog.askdirectory(title="Select a Workspace Folder")
        root.destroy()
        return path
        
    path = ask()
    if path and os.path.isdir(path):
        os.chdir(path)
        return {"success": True, "path": path}
    
    return {"success": False}

@app.get("/api/files")
async def list_files():
    allowed = ['.py', '.json', '.txt', '.md', '.html', '.css', '.js', '.env', '.jsx', '.ts', '.tsx', '.csv', '.yml']
    files = []
    for root, dirs, filenames in os.walk("."):
        # Ignore heavy system/dependency folders
        dirs[:] = [d for d in dirs if d not in ['.venv', 'venv', 'node_modules', '.git', '__pycache__', 'dist', 'build']]
        for f in filenames:
            if any(f.endswith(ext) for ext in allowed):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, ".")
                # Send standardized relative paths cleanly
                files.append(rel_path.replace("\\", "/"))
    return {"files": sorted(files)}

@app.get("/api/file")
async def get_file(name: str):
    if not os.path.exists(name):
        return {"content": ""}
    with open(name, "r", encoding="utf-8", errors="replace") as f:
        return {"content": f.read()}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    initial_state = {
        "task": req.prompt,
        "code": req.code,
        "output": "",
        "error": None,
        "iterations": 0,
        "plan": ""
    }
    
    log_event("User Web Prompt", req.prompt)
    final_state = graph.invoke(initial_state)
    
    return {
        "plan": final_state.get("plan"),
        "code": final_state.get("code"),
        "output": final_state.get("output"),
        "error": final_state.get("error")
    }

def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

def main():
    print("Launching Desktop IDE Window...")
    
    # Start the fastAPI backend simultaneously on a daemon thread
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()
    
    # Let server boot
    import time
    time.sleep(2)
    
    # Boot the UI wrapper
    # We no longer launch the browser for FastAPI because Vite dev server handles it.
    print("Vite handles the UI now via proxy on port 5173.")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    main()