import os
import asyncio
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types # For creating message Content/Parts
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools import LongRunningFunctionTool
from google.adk.memory import InMemoryMemoryService

from google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset import OpenAPIToolset


os.environ["GOOGLE_API_KEY"] = "AIzaSyBs5PMuwcBY5-M8dk7L5mR_GRicZEVWX0k"

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

# Import necessary session components
from google.adk.sessions import InMemorySessionService

# Create a NEW session service instance for this state demonstration
session_service_stateful = InMemorySessionService()
print("✅ New InMemorySessionService created for state demonstration.")
memory_service = InMemoryMemoryService()

# Define a NEW session ID for this part of the tutorials
SESSION_ID_STATEFUL = "session_state_demo_001"
USER_ID_STATEFUL = "user_state_demo"
APP_NAME = "weather_tutorial_app"

# Create the session, providing the initial state
session_stateful = session_service_stateful.create_session(
    app_name=APP_NAME, # Use the consistent app name
    user_id=USER_ID_STATEFUL,
    session_id=SESSION_ID_STATEFUL
)
print(f"✅ Session '{SESSION_ID_STATEFUL}' created for user '{USER_ID_STATEFUL}'.")

# @title Define the temperature conversion tool
from google.adk.tools import FunctionTool

# --- Sample OpenAPI Specification (JSON String) ---
# A basic Pet Store API example using httpbin.org as a mock server
openapi_spec_string = '''
{
  "openapi": "3.0.0",
  "info": {
    "title": "Spoonacular Recipe API",
    "version": "1.0.0",
    "description": "Endpoints to fetch and analyze recipe data."
  },
  "components": {
    "securitySchemes": {
      "apiKey": {
        "type": "apiKey",
        "in": "query",
        "name": "apiKey"
      }
    }
  },
  "servers": [{
    "url": "https://api.spoonacular.com",
    "description": "Production server"
  }],
  "paths": {
    "/recipes/complexSearch": {
      "get": {
        "operationId": "searchRecipes",
        "parameters": [
          {
            "name": "query",
            "in": "query",
            "required": true,
            "schema": {"type": "string"}
          }
        ],
        "responses": {
          "200": {
            "description": "Search results",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "results": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "id": {"type": "integer"},
                          "title": {"type": "string"}
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
'''
from google.oauth2.credentials import Credentials
import json

# --- Create OpenAPIToolset ---
generated_tools_list = []
try:
    # Instantiate the toolset with the spec string
    recipe_toolset = OpenAPIToolset(
        spec_str=openapi_spec_string,
        spec_str_type="json"
        # No authentication needed for httpbin.org
    )
    # Get all tools generated from the spec
    generated_tools_list = recipe_toolset.get_tools()
    print(f"Generated {len(generated_tools_list)} tools from OpenAPI spec:")
    for tool in generated_tools_list:
        # Tool names are snake_case versions of operationId
        print(f"- Tool Name: '{tool.name}', Description: {tool.description[:60]}...")

except ValueError as ve:
    print(f"Validation Error creating OpenAPIToolset: {ve}")
    # Handle error appropriately, maybe exit or skip agent creation
except Exception as e:
    print(f"Unexpected Error creating OpenAPIToolset: {e}")
    # Handle error appropriately

AGENT_MODEL = MODEL_GEMINI_2_0_FLASH

recipe_agent = Agent(
    model = AGENT_MODEL,
    name = "Recipe_Bot",
    tools=generated_tools_list,
    instruction = f"""
You are a helpful recipe assistant that suggests detailed recipes based on dish names provided by the user.
Use the available tools to retrieve and analyze recipe data from Spoonacular.
Available tools: {', '.join([t.name for t in generated_tools_list])}.

When fetching a recipe:
- First, use the appropriate tool to get the recipe ID from the dish name.
- Then, use the ID to fetch full recipe details and instructions.
- Confirm the dish name and summarize key details like ingredients, cook time, and number of steps.
- Highlight any unusual steps or ingredients.
Always store the retrieved recipes in memory so they can be referenced later in the session.
""",
    description = "You are a recipe assistant. You take a dish name and suggests recipes."
)

# Find the tool for search_recipes
search_tool = next(t for t in generated_tools_list if t.name == "search_recipes")

# Function to call the tool with the API key
async def wrapped_search_recipes(tool_context: ToolContext, query: str):
    # Inject API key
    api_key = "c3176bf0d356401092406ab4fa31d8e4"
    if "apiKey=" not in query:
        query += f"&apiKey={api_key}"
    
    # Call the original tool function
    response = await search_tool.execute(tool_context, query)
    return response

# Use this wrapped function in your runner
search_tool.execute = wrapped_search_recipes

# Rest of your code continues...


runner = Runner(
    agent = recipe_agent,
    app_name= APP_NAME,
    session_service = session_service_stateful,
    memory_service=memory_service
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
   await call_agent_async("Can you suggest a recipe for spaghetti carbonara?",
                           runner = runner,
                           user_id = USER_ID_STATEFUL,
                           session_id = SESSION_ID_STATEFUL
                          )

import asyncio
if __name__ == "__main__":
    try:
        asyncio.run(run_conversation())
    except Exception as e:
        print(f"An error occurred: {e}")