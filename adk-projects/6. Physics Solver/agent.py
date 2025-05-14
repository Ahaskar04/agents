# from __future__ import annotations

import os
import asyncio
from google.adk.agents import LlmAgent
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService, Session
from google.adk.memory import InMemoryMemoryService # Import MemoryService
from google.adk.runners import Runner
from google.adk.tools import load_memory # Tool to query memory
from google.genai.types import Content, Part
from google.adk.memory import BaseMemoryService
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types 

from math import sin, cos, tan, radians, log, exp, sqrt 
from typing import Any, Dict, List, Optional, Tuple
try:
    import sympy as sp
except ImportError:  
    sp = None  
try:
    import pint 
except ImportError:  
    pint = None  

os.environ["GOOGLE_API_KEY"] = "AIzaSyBs5PMuwcBY5-M8dk7L5mR_GRicZEVWX0k"
MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"


session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

# Define a NEW session ID 
SESSION_ID_STATEFUL = "session_state_demo_001"
USER_ID_STATEFUL = "user_state_demo"
APP_NAME = "weather_tutorial_app"

session_stateful = session_service.create_session(
    app_name=APP_NAME, # Use the consistent app name
    user_id=USER_ID_STATEFUL,
    session_id=SESSION_ID_STATEFUL,
)
print(f"✅ Session '{SESSION_ID_STATEFUL}' created for user '{USER_ID_STATEFUL}'.")


def numeric_solver(
    expression: str,
    precision: int = 3
) -> dict:
    """
    Evaluate a simple math expression numerically.

    Parameters
    ----------
    expression : str
        A valid Python expression (e.g., "sin(30)", "5**2 + 7").
    precision : int
        Decimal places to round the result.

    Returns
    -------
    dict with keys: result, latex, steps
    """
    # Safe context for math functions (angles in degrees)
    safe_locals = {
        "sin": lambda x: sin(radians(x)),
        "cos": lambda x: cos(radians(x)),
        "tan": lambda x: tan(radians(x)),
        "log": log,
        "exp": exp,
        "sqrt": sqrt,
    }

    steps = []

    # Step 1: Evaluate
    try:
        value = float(eval(expression, {"__builtins__": {}}, safe_locals))
    except Exception as e:
        return {"error": f"Failed to evaluate: {e}"}

    steps.append(f"Evaluated: {expression} → {value}")

    # Step 2: Round
    rounded_val = round(value, precision)
    steps.append(f"Rounded to {precision} dp → {rounded_val}")

    # Step 3: Generate LaTeX (optional)
    if sp:
        try:
            latex_expr = sp.latex(sp.sympify(expression))
            latex_result = rf"{latex_expr} = {rounded_val}"
        except Exception:
            latex_result = rf"{rounded_val}"
    else:
        latex_result = rf"{rounded_val}"

    return {
        "result": rounded_val,
        "latex": latex_result,
        "steps": steps
    }



numeric_solver_tool = FunctionTool(func = numeric_solver)

AGENT_MODEL = MODEL_GEMINI_2_0_FLASH

todo_agent = Agent(
    model=AGENT_MODEL,
    name = "Numeric_Solver_Assistant",
    instruction="You're a numeric assistant. Given a math or physics question, try to convert it into a valid expression and call the numeric_solver_tool. You MUST call the tool whenever an expression is evaluable.",
    description="A numeric solver agent that can solve physics problems.",
    tools=[numeric_solver_tool]
)

runner = Runner(
    agent = todo_agent,
    app_name= APP_NAME,
    session_service = session_service,
)

async def call_agent_async(query: str, runner, user_id, session_id):
    """Sends a query to the agent and prints the final response."""
    print(f"\n>>> User   Query: {query}")
      # Prepare the user's message in ADK format
    content = types.Content(role='user', parts=[types.Part(text=query)])

    final_response_text = "Agent did not produce a final response." # Default

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response():
          if event.content and event.content.parts:
             # Assuming text response in the first part
             final_response_text = event.content.parts[0].text
          elif event.actions and event.actions.escalate: # Handle potential errors/escalations
             final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
          # Add more checks here if needed (e.g., specific error codes)
          break 
    print(f"<<< Agent Response: {final_response_text}")

async def run_conversation():
   await call_agent_async("What is sin(30)?",
                           runner = runner,
                           user_id = USER_ID_STATEFUL,
                           session_id = SESSION_ID_STATEFUL,
                          )
   
   
if __name__ == "__main__":
    try:
        asyncio.run(run_conversation())
    except Exception as e:
        print(f"An error occurred: {e}")