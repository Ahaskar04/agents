# To-Do List Assistant
# Add, list, delete tasks using state.
# Use artifacts to save and retrieve to-do lists (e.g., as text files).
# ARtifacts are immutable, so we need to save a new version of the artifact each time we modify it.

import os
import asyncio
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
import google.genai.types as types # For creating message Content/Parts
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools import LongRunningFunctionTool
from google.adk.artifacts import InMemoryArtifactService
import google.genai.types as types
from google.adk.tools.tool_context import ToolContext


os.environ["GOOGLE_API_KEY"] = "AIzaSyBs5PMuwcBY5-M8dk7L5mR_GRicZEVWX0k"

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

# Import necessary session components
from google.adk.sessions import InMemorySessionService

# Create a NEW session service instance for this state demonstration
session_service_stateful = InMemorySessionService()
artifact_service_stateful = InMemoryArtifactService()
print("✅ New InMemorySessionService created for state demonstration.")

# Define a NEW session ID for this part of the tutorial
SESSION_ID_STATEFUL = "session_state_demo_001"
USER_ID_STATEFUL = "user_state_demo"
APP_NAME = "weather_tutorial_app"

# Create the session, providing the initial state
session_stateful = session_service_stateful.create_session(
    app_name=APP_NAME, # Use the consistent app name
    user_id=USER_ID_STATEFUL,
    session_id=SESSION_ID_STATEFUL,
)
print(f"✅ Session '{SESSION_ID_STATEFUL}' created for user '{USER_ID_STATEFUL}'.")

def add_task(tool_context: ToolContext, task: str) -> None:
    """
    Add a task to the to-do list.
    Args:
        task (str): The task to add.
    Returns:
        int: The version of the artifact.
    """
    filename = "to-do.txt"
    old_tasks = ""

    # Try loading existing artifact
    try:
        artifact = tool_context.load_artifact(filename)
        if artifact and artifact.inline_data:
            old_tasks = artifact.inline_data.data.decode("utf-8")
    except Exception:
        # If no artifact yet, start fresh
        pass

    # Append new task with newline
    updated_tasks = old_tasks + task + "\n"

    # Save updated list
    text_artifact = types.Part(
        inline_data=types.Blob(data=updated_tasks.encode("utf-8"),
        mime_type="text/plain")
    )

    tool_context.save_artifact(filename=filename, artifact=text_artifact)

add_task_tool = FunctionTool(func = add_task)

def list_tasks(tool_context: ToolContext):
    """
    List all the tasks in the to-do list.
    """
    filename = "to-do.txt"
    text_artifact = tool_context.load_artifact(filename)
    text_bytes = text_artifact.inline_data.data
    text = text_bytes.decode("utf-8")
    return text

list_tasks_tool = FunctionTool(func = list_tasks)

AGENT_MODEL = MODEL_GEMINI_2_0_FLASH

todo_agent = Agent(
    model=AGENT_MODEL,
    name = "ToDo_List_Assistant",
    instruction="You are a helpful assistant that helps the user manage their to-do list.",
    description="Add, list, delete tasks using state.",
    tools=[add_task_tool, list_tasks_tool],
)

runner = Runner(
    agent = todo_agent,
    app_name= APP_NAME,
    session_service = session_service_stateful,
    artifact_service = artifact_service_stateful
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
   await call_agent_async("add task: Buy groceries",
                           runner = runner,
                           user_id = USER_ID_STATEFUL,
                           session_id = SESSION_ID_STATEFUL,
                          )
   await call_agent_async("add task: Finish homework",
                           runner = runner,
                           user_id = USER_ID_STATEFUL,
                           session_id = SESSION_ID_STATEFUL,
                          )
   await call_agent_async("show all tasks",
                           runner = runner,
                           user_id = USER_ID_STATEFUL,
                           session_id = SESSION_ID_STATEFUL,
                          )
   
   
if __name__ == "__main__":
    try:
        asyncio.run(run_conversation())
    except Exception as e:
        print(f"An error occurred: {e}")