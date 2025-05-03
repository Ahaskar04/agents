import os
import asyncio
from google.adk.agents import Agent
# from google.adk.models.lite_llm import LiteLlm # For multi-model support
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.genai import types # For creating message Content/Parts

os.environ["GOOGLE_API_KEY"] = "AIzaSyBs5PMuwcBY5-M8dk7L5mR_GRicZEVWX0k"

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

AGENT_MODEL = MODEL_GEMINI_2_0_FLASH

helloWorldAgent = Agent(
    name = "Hello_World_Agent",
    model = AGENT_MODEL,
    description="Provides basic information about google adk(agent developmenet kit) and its capabilities.",
    instruction="You are a helpful service agent. "
                "You will be asked to provide information about yourself and your capabilities. "
                "You can answer questions about the google adk and its features. "
                "You can also provide information about the google adk agent development kit. "
                "You can search the internet for information about the google adk and its features. "
                "You should think step-by-step before answering. Explain your reasoning as a thought before giving the final answer."
                "You should respond in a friendly and helpful manner.",
     tools=[google_search]
)

session_service = InMemorySessionService()

APP_NAME = "Hello_World_Agent"
USER_ID = "user1"
SESSION_ID = "session1"

session = session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID
)

runner = Runner(
    agent=helloWorldAgent,
    app_name=APP_NAME,
    session_service=session_service
)

async def call_agent_async(query: str, runner, user_id, session_id):
    """Sends the query to the agent and returns the response."""
    print(f"User: {query}")
    content = types.Content(role = 'user', parts = [types.Part(text = query)])
    final_response_text = "Agent response not available."
    async for event in runner.run_async(user_id = user_id, session_id = session_id, new_message = content):
        # print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")
        if event.is_final_response():
            final_response_text = event.content.parts[0].text
            break
    print(f"Agent: {final_response_text}")

async def run_conversation():
    """Runs the conversation with the agent."""
    await call_agent_async("Hi, my name is Ahaskar. What do you do", runner, USER_ID, SESSION_ID)
    await call_agent_async("What is my name?", runner, USER_ID, SESSION_ID)

import asyncio
if __name__ == "__main__":
    try:
        asyncio.run(run_conversation())
    except Exception as e:
        print(f"An error occurred: {e}")