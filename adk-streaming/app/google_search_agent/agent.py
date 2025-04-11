from google.adk.agents import Agent
from google.adk.tools import google_search  # Import the tool

root_agent = Agent(
   # A unique name for the agent.
   name="basic_search_agent",
   # The Large Language Model (LLM) that agent will use.
   model="gemini-2.0-flash-exp",
   # A short description of the agent's purpose.
   description="Agent to answer questions about our platform Vani.",
   # Instructions to set the agent's behavior.
   instruction="You talk in mathili(local language of Bihar, India). You are customer servce for Vani, a platform that's known for integrative voive to voice conversations to websites and platforms. You are to answer questions about Vani and its features. If you don't know the answer, say coming soon.",
   # Add google_search tool to perform grounding with Google search.
   tools=[google_search]
)