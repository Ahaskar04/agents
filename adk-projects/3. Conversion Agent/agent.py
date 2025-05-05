# Unit Converter Bot
# Tools: One tool for each type (e.g., temperature, distance, mass).
# Use ToolContext and state management to remember conversion history.

import os
import asyncio
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types # For creating message Content/Parts
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools import LongRunningFunctionTool

os.environ["GOOGLE_API_KEY"] = "AIzaSyBs5PMuwcBY5-M8dk7L5mR_GRicZEVWX0k"

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

# Import necessary session components
from google.adk.sessions import InMemorySessionService

# Create a NEW session service instance for this state demonstration
session_service_stateful = InMemorySessionService()
print("✅ New InMemorySessionService created for state demonstration.")

# Define a NEW session ID for this part of the tutorial
SESSION_ID_STATEFUL = "session_state_demo_001"
USER_ID_STATEFUL = "user_state_demo"
APP_NAME = "weather_tutorial_app"

# Define initial state data - user prefers Celsius initially
initial_state = {
    "user_preference_temperature_unit": "Celsius"
}

# Create the session, providing the initial state
session_stateful = session_service_stateful.create_session(
    app_name=APP_NAME, # Use the consistent app name
    user_id=USER_ID_STATEFUL,
    session_id=SESSION_ID_STATEFUL,
    state=initial_state # <<< Initialize state during creation
)
print(f"✅ Session '{SESSION_ID_STATEFUL}' created for user '{USER_ID_STATEFUL}'.")

# @title Define the temperature conversion tool
from google.adk.tools import FunctionTool

def convert_temperature(value: int, from_unit: str, to_unit: str) -> dict:
    """
    Convert temperature from one unit to another.
    Supported units: Celsius, Fahrenheit, Kelvin

    Args: 
        value(int): The temperature value to convert.
        from_unit(str): The unit of the input temperature value.
        to_unit(str): The unit to convert the temperature value to.

    Returns:
        dict: A dictionary containing the converted temperature value, original value, 
              and units for conversion.

    Raises:
        ValueError: If the input unit is not supported.
    """
    if from_unit == "Celsius":
        if to_unit == "Fahrenheit":
            result = (value * 9/5) + 32
        elif to_unit == "Kelvin":
            result = value + 273.15
        else:
            raise ValueError(f"Unsupported conversion to {to_unit}")
    elif from_unit == "Fahrenheit":
        if to_unit == "Celsius":
            result = (value - 32) * 5/9
        elif to_unit == "Kelvin":
            result = (value - 32) * 5/9 + 273.15
        else:
            raise ValueError(f"Unsupported conversion to {to_unit}")
    elif from_unit == "Kelvin":
        if to_unit == "Celsius":
            result = value - 273.15
        elif to_unit == "Fahrenheit":
            result = (value - 273.15) * 9/5 + 32
        else:
            raise ValueError(f"Unsupported conversion to {to_unit}")
    else:
        raise ValueError(f"Unsupported temperature unit: {from_unit}")
    
    # Instead of using ToolContext/ToolResponse, return a dictionary
    return {
        "status": "success",
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": round(result, 2),
        "converted_unit": to_unit,
        "message": f"{value} {from_unit} is {result:.2f} {to_unit}."
    }

# Create the function tool using the ADK's FunctionTool class
convert_temperature_tool = FunctionTool(func=convert_temperature)

# Alternative way to create the tool
# convert_temperature_tool = FunctionTool.from_function(
#     func=convert_temperature
# )
    


# @title Define the distance conversion tool
def convert_distance(value: int, from_unit: str, to_unit: str) -> int:
    """
    Convert distance from one unit to another.
    Supported units: meters, kilometers, miles

    Args: 
        value(int): The distance value to convert.
        from_unit(str): The unit of the input distance value.
        to_unit(str): The unit to convert the distance value to.

    Returns:
        int: The converted distance value.

    Raises:
        ValueError: If the input unit is not supported.
    """
    if from_unit == "meters":
        if to_unit == "kilometers":
            result = value / 1000
        elif to_unit == "miles":
            result = value / 1609.34
    elif from_unit == "kilometers":
        if to_unit == "meters":
            result = value * 1000
        elif to_unit == "miles":
            result = value / 1.60934
    elif from_unit == "miles":
        if to_unit == "meters":
            result = value * 1609.34
        elif to_unit == "kilometers":
            result = value * 1.60934
    else:
        raise ValueError("Unsupported distance unit")
    
    return {
        "status": "success",
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": round(result, 2),
        "converted_unit": to_unit,
        "message": f"{value} {from_unit} is {result:.2f} {to_unit}."
    }
    
convert_distance_tool = FunctionTool(func=convert_distance)

# @title Define the mass conversion tool
def convert_mass(value: int, from_unit: str, to_unit: str) -> int:
    """
    Convert mass from one unit to another.
    Supported units: grams, kilograms, pounds

    Args: 
        value(int): The mass value to convert.
        from_unit(str): The unit of the input mass value.
        to_unit(str): The unit to convert the mass value to.

    Returns:
        int: The converted mass value.

    Raises:
        ValueError: If the input unit is not supported.
    """
    if from_unit == "grams":
        if to_unit == "kilograms":
            result = value / 1000
        elif to_unit == "pounds":
            result = value / 453.592
    elif from_unit == "kilograms":
        if to_unit == "grams":
            result = value * 1000
        elif to_unit == "pounds":
            result = value * 2.20462
    elif from_unit == "pounds":
        if to_unit == "grams":
            result = value * 453.592
        elif to_unit == "kilograms":
            result = value / 2.20462
    else:
        raise ValueError("Unsupported mass unit")
        return {
        "status": "success",
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": round(result, 2),
        "converted_unit": to_unit,
        "message": f"{value} {from_unit} is {result:.2f} {to_unit}."
    }
    
convert_mass_tool = FunctionTool(func=convert_mass)

AGENT_MODEL = MODEL_GEMINI_2_0_FLASH

# @title Define the agent
conversion_agent = Agent(
    model = AGENT_MODEL,
    name = "Converter_Bot",
    instruction= "You are a unit conversion bot. Convert the given value from one unit to another.",
    description = "A bot that converts units of measurement.",
    tools = [convert_temperature_tool, convert_distance_tool, convert_mass_tool]
)

runner = Runner(
    agent = conversion_agent,
    app_name= APP_NAME,
    session_service = session_service_stateful
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
   await call_agent_async("What is 100 Celsius in Fahrenheit?",
                           runner = runner,
                           user_id = USER_ID_STATEFUL,
                           session_id = SESSION_ID_STATEFUL
                          )
   
   await call_agent_async("What is 100 kilograms in pounds?",
                           runner = runner,
                           user_id = USER_ID_STATEFUL,
                           session_id = SESSION_ID_STATEFUL
                          )
   
   await call_agent_async("What is 1000 meters in kilometers?",
                           runner = runner,
                           user_id = USER_ID_STATEFUL,
                           session_id = SESSION_ID_STATEFUL
                          )
   
if __name__ == "__main__":
    try:
        asyncio.run(run_conversation())
    except Exception as e:
        print(f"An error occurred: {e}")