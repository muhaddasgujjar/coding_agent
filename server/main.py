from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import time
import datetime
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from agent import generate_code
from executor import execute_code

# Load environment variables (GROQ_API_KEY)
load_dotenv()

# Initialize Rich Console natively
console = Console()

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
    # Cooldown to avoid hitting Groq's Free Tier Rate Limits (RPM)
    time.sleep(3)  
    
    current_iter = state.get("iterations", 0) + 1
    
    result = generate_code(state)
    plan_text = result.get("plan", "")
    code_text = result.get("code", "")
    
    # Persistent Audit Log
    log_event("Agent Thought & Plan", plan_text)
    
    # Render the LLM's thought process/plan beautifully using Rich Markdown Panels
    console.print(Panel(
        Markdown(plan_text), 
        title=f"[bold green]Agent Planning (Iteration {current_iter})[/bold green]", 
        border_style="green"
    ))
    
    # Honesty & Safety Check
    if "I cannot do this" in plan_text or "I cannot do this" in code_text:
        console.print("\n[bold red]System:[/bold red] Agent correctly determined the task is impossible with current tools. Halting safely.")
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
    code = state.get("code", "")
    
    if state.get("error") == "I cannot do this - task aborted by Agent.":
        log_event("Executor Skipped", "Task aborted by agent logic.")
        return {"error": state.get("error")}
        
    log_event("Executor Running Code", code)
    exec_result = execute_code(code)
    
    if exec_result["success"]:
        output_msg = exec_result['output']
        
        # Display success safely in a blue panel
        console.print(Panel(
            output_msg if output_msg.strip() else "Code executed silently successfully.", 
            title="[bold blue]Executor: Success[/bold blue]", 
            border_style="blue"
        ))
        
        log_event("Execution Successful", f"Output:\n{exec_result['output']}")
        return {
            "output": exec_result["output"],
            "error": None
        }
    else:
        error_msg = exec_result["error"]
        
        # Display errors boldly in a red panel
        console.print(Panel(
            error_msg, 
            title="[bold red]Executor: Failed[/bold red]", 
            border_style="red"
        ))
        
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
            console.print("\n[bold red]System:[/bold red] Maximum iterations reached. Exiting Loop.")
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
    workflow.add_conditional_edges("execute", should_continue, {"code": "code", END: END})
    return workflow.compile()

def main():
    graph = build_graph()
    
    # Title Display
    console.print(Panel(
        "[bold magenta]Self-Healing Specialist Coding Agent[/bold magenta]\n[dim]Interactive Mode (Type 'exit' to quit)[/dim]", 
        border_style="magenta"
    ))
    
    while True:
        try:
            # Persistent interactive cursor!
            task = console.input("\n[bold cyan]You:[/bold cyan] ")
            
            if task.lower() in ['exit', 'quit']:
                console.print("[dim]Goodbye![/dim]")
                break
                
            if not task.strip():
                continue
                
            initial_state = {
                "task": task,
                "code": "",
                "output": "",
                "error": None,
                "iterations": 0,
                "plan": ""
            }
            
            log_event("User Task Initiated", task)
            
            # The spinner runs seamlessly over the entirety of the graph invoke wrapper
            with console.status("[bold green]Agent is thinking...[/bold green]", spinner="dots"):
                final_state = graph.invoke(initial_state)
            
            if final_state.get("error"):
                console.print("\n[bold yellow]Task finished with errors or warnings.[/bold yellow]")
            else:
                console.print("\n[bold green]\u2714 Task finished successfully![/bold green]")
                
        except KeyboardInterrupt:
            console.print("\n[dim]Session interrupted. Type 'exit' to gracefully quit.[/dim]")

if __name__ == "__main__":
    main()