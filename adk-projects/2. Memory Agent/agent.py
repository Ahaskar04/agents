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

new_session_id = "session_new_test_001"

new_session = session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID_STATEFUL,
     session_id=new_session_id,
)

# Verify the initial state was set correctly
retrieved_session = session_service.get_session(app_name=APP_NAME,
                                                         user_id=USER_ID_STATEFUL,
                                                         session_id = SESSION_ID_STATEFUL)

print(f"Session ID: {retrieved_session.id }")

baseAgent = Agent(
    model = MODEL_GEMINI_2_0_FLASH,
    name="base_agent",
    instruction="Always use the 'load_memory' tool to retrieve user-related information, " \
    "such as their name, location, preferences, or background.Do not answer from internal knowledge "
    "or assumptions. Rely only on 'load_memory'",
    description="This is the base agent.",
    tools=[load_memory]
)

runner = Runner(
    agent = baseAgent,
    session_service = session_service,
    memory_service = memory_service,
    app_name=APP_NAME
)

async def call_agent_async(query: str, runner, user_id, session_id):
    """Sends a query to the agent and prints the final response."""
    print(f"\n>>> User Query: {query}")
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
   await call_agent_async("My name is Ahaskar",
                           runner = runner,
                           user_id = USER_ID_STATEFUL,
                           session_id = SESSION_ID_STATEFUL
                          )
   
   await call_agent_async("I am fucking smart",
                           runner = runner,
                           user_id = USER_ID_STATEFUL,
                           session_id = SESSION_ID_STATEFUL
                          )
   
   await call_agent_async("I live in Singapore",
                           runner = runner,
                           user_id = USER_ID_STATEFUL,
                           session_id = SESSION_ID_STATEFUL
                          )
   await call_agent_async("What is my name and where do i live?",
                           runner = runner,
                           user_id = USER_ID_STATEFUL,
                           session_id = SESSION_ID_STATEFUL
                          )
   updated_session = session_service.get_session(
    app_name=APP_NAME,
    user_id=USER_ID_STATEFUL,
    session_id=SESSION_ID_STATEFUL
)
   memory_service.add_session_to_memory(updated_session)
   print("✅ Session added to memory.")

    # Now, the agent has no local session history; it must use load_memory
   await call_agent_async("What is my name and where do I live?",
                        runner = runner,
                        user_id = USER_ID_STATEFUL,
                        session_id = new_session_id)  # 👈 new session!

import asyncio
if __name__ == "__main__":
    try:
        asyncio.run(run_conversation())
    except Exception as e:
        print(f"An error occurred: {e}")