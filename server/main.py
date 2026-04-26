from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import time
import datetime

from agent import generate_code
from executor import execute_code

# Load environment variables (GROQ_API_KEY)
load_dotenv()

def log_event(event_type: str, content: str):
    """Appends persistent audit logs to session.log"""
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

def code_node(state: AgentState):
    """Node that triggers the LLM to generate or fix code."""
    time.sleep(3)  # Cooldown to avoid hitting Groq's Free Tier Rate Limits (RPM)
    current_iter = state.get("iterations", 0) + 1
    print(f"\n[Agent] -> Generating code (Iteration {current_iter})...")
    
    result = generate_code(state)
    plan_text = result.get("plan", "")
    code_text = result.get("code", "")
    
    # Persistent Audit Log
    log_event("Agent Thought & Plan", plan_text)
    
    # Print the LLM's thought process/plan (omitting the raw code block for brevity)
    # We can just print the whole thought process to see what it's doing
    print(f"\n--- Agent Thinking & Planning ---\n{plan_text}\n---------------------------------")
    
    # Honesty & Safety Check
    if "I cannot do this" in plan_text or "I cannot do this" in code_text:
        print("\n[System] -> Agent correctly determined the task is impossible with current tools. Halting safely.")
        return {
            "code": code_text,
            "plan": plan_text,
            "iterations": current_iter,
            "error": "I cannot do this - task aborted by Agent."
        }
    
    return {
        "code": code_text,
        "plan": plan_text,
        "iterations": current_iter
    }

def execute_node(state: AgentState):
    """Node that runs the generated code in the local environment."""
    print("\n[Executor] -> Running code...")
    code = state.get("code", "")
    
    if state.get("error") == "I cannot do this - task aborted by Agent.":
        log_event("Executor Skipped", "Task aborted by agent logic.")
        return {"error": state.get("error")}
        
    log_event("Executor Running Code", code)
    exec_result = execute_code(code)
    
    if exec_result["success"]:
        print("[Executor] -> Execution Successful!")
        print(f"Output:\n{exec_result['output']}")
        log_event("Execution Successful", f"Output:\n{exec_result['output']}")
        return {
            "output": exec_result["output"],
            "error": None
        }
    else:
        print("[Executor] -> Execution Failed!")
        error_msg = exec_result["error"]
        print(f"Error:\n{error_msg}")
        log_event("Execution Failed", f"Error:\n{error_msg}")
        return {
            "output": exec_result["output"],
            "error": error_msg
        }

def should_continue(state: AgentState) -> str:
    """Decision node: continues loop if error exists, else end."""
    if state.get("error") == "I cannot do this - task aborted by Agent.":
        return END
    if state.get("error"):
        if state.get("iterations", 0) >= 5: # Max retries
            print("\n[System] -> Maximum iterations reached. Exiting.")
            log_event("System Warning", "Maximum iterations reached. Exiting.")
            return END
        return "code"
    return END

def build_graph():
    """Builds the ReAct langgraph workflow."""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("code", code_node)
    workflow.add_node("execute", execute_node)
    
    workflow.set_entry_point("code")
    
    workflow.add_edge("code", "execute")
    workflow.add_conditional_edges(
        "execute",
        should_continue,
        {
            "code": "code",
            END: END
        }
    )
    
    return workflow.compile()

def main():
    print("Initializing Self-Healing Specialist Coding Agent...")
    graph = build_graph()
    
    import sys
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = input("\nEnter the coding task you want me to solve: ")
        
    if not task.strip():
        print("No task provided. Exiting.")
        return
    
    initial_state = {
        "task": task,
        "code": "",
        "output": "",
        "error": None,
        "iterations": 0,
        "plan": ""
    }
    
    print(f"\nTask: {task}")
    log_event("User Task Initiated", task)
    
    final_state = graph.invoke(initial_state)
    
    if final_state.get("error"):
        print("\n[System] -> Agent failed to solve the task.")
    else:
        print("\n[System] -> Task finished successfully!")

if __name__ == "__main__":
    main()