import os
import asyncio
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

# No API key needed for local models!

helloWorldAgent = Agent(
    name="Hello_World_Agent",
    model=LiteLlm(model="ollama_chat/qwen3:4b"),  # <-- Local model
    description="Provides basic information about google adk and its capabilities.",
    instruction="You are a helpful service agent. "
                "You should respond in a friendly and helpful manner.",
    # tools=[google_search]  # Note: google_search still needs API key
)

session_service = InMemorySessionService()

APP_NAME = "Hello_World_Agent"
USER_ID = "user1"
SESSION_ID = "session1"

async def call_agent_async(query: str, runner, user_id, session_id):
    print(f"User: {query}")
    content = types.Content(role='user', parts=[types.Part(text=query)])
    final_response_text = "Agent response not available."
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response():
            final_response_text = event.content.parts[0].text
            break
    print(f"Agent: {final_response_text}")

async def run_conversation():
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    
    runner = Runner(
        agent=helloWorldAgent,
        app_name=APP_NAME,
        session_service=session_service
    )
    
    await call_agent_async("Hi, my name is Ahaskar. What do you do?", runner, USER_ID, SESSION_ID)
    await call_agent_async("What is my name?", runner, USER_ID, SESSION_ID)

if __name__ == "__main__":
    try:
        asyncio.run(run_conversation())
    except Exception as e:
        print(f"An error occurred: {e}")