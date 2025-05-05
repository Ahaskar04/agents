# ADK Function Tools Guide

## Overview

The Agent Development Kit (ADK) provides powerful tools for creating custom functionality in your agents. This guide focuses on two primary tool types: `FunctionTool` and `LongRunningFunctionTool`, explaining their differences, use cases, and implementation patterns.

## Table of Contents

- [Getting Started](#getting-started)
- [FunctionTool](#functiontool)
  - [Core Concepts](#core-concepts)
  - [Implementation](#implementation)
  - [Best Practices](#best-practices)
  - [Example](#functiontool-example)
- [LongRunningFunctionTool](#longrunningfunctiontool)
  - [Core Concepts](#longrunningfunctiontool-core-concepts)
  - [Implementation](#longrunningfunctiontool-implementation)
  - [Intermediate Updates](#intermediate-updates)
  - [Example](#longrunningfunctiontool-example)
- [Choosing Between Tools](#choosing-between-tools)
- [Advanced Topics](#advanced-topics)

## Getting Started

Install the ADK package:

```bash
pip install google-adk
```

Import the required tools:

```python
from google.adk.tools import FunctionTool, LongRunningFunctionTool
```

## FunctionTool

### Core Concepts

`FunctionTool` transforms a standard Python function into a tool that your agent can utilize. It's designed for operations that complete relatively quickly and return a single result.

### Implementation

1. Define your function with clear parameters and return types:

```python
def my_function(param1: str, param2: int) -> dict:
    """
    Well-documented docstring explaining the function's purpose.

    Args:
        param1 (str): Description of first parameter
        param2 (int): Description of second parameter

    Returns:
        dict: Dictionary with results

    Raises:
        ValueError: When invalid inputs are provided
    """
    # Function logic here
    return {
        "status": "success",
        "result": some_result
    }
```

2. Create the tool:

```python
my_tool = FunctionTool(func=my_function)
```

### Best Practices

- Use descriptive function and parameter names
- Write comprehensive docstrings (they're used by the LLM to understand the tool)
- Return dictionaries with a "status" key and meaningful structured data
- Keep parameters simple and use primitive data types when possible
- Handle errors gracefully and return informative error messages

### FunctionTool Example

```python
from google.adk.tools import FunctionTool

def convert_temperature(value: float, from_unit: str, to_unit: str) -> dict:
    """
    Convert temperature from one unit to another.

    Args:
        value (float): The temperature value to convert
        from_unit (str): Original temperature unit (Celsius, Fahrenheit, Kelvin)
        to_unit (str): Target temperature unit (Celsius, Fahrenheit, Kelvin)

    Returns:
        dict: Conversion result with original and converted values

    Raises:
        ValueError: If unsupported units are provided
    """
    units = ["Celsius", "Fahrenheit", "Kelvin"]
    if from_unit not in units or to_unit not in units:
        return {
            "status": "error",
            "message": f"Unsupported unit. Use one of: {', '.join(units)}"
        }

    # Conversion logic
    if from_unit == "Celsius":
        if to_unit == "Fahrenheit":
            result = (value * 9/5) + 32
        elif to_unit == "Kelvin":
            result = value + 273.15
        else:
            result = value
    elif from_unit == "Fahrenheit":
        if to_unit == "Celsius":
            result = (value - 32) * 5/9
        elif to_unit == "Kelvin":
            result = (value - 32) * 5/9 + 273.15
        else:
            result = value
    elif from_unit == "Kelvin":
        if to_unit == "Celsius":
            result = value - 273.15
        elif to_unit == "Fahrenheit":
            result = (value - 273.15) * 9/5 + 32
        else:
            result = value

    return {
        "status": "success",
        "original_value": value,
        "original_unit": from_unit,
        "converted_value": round(result, 2),
        "converted_unit": to_unit,
        "message": f"{value} {from_unit} is {result:.2f} {to_unit}."
    }

# Create the tool
temperature_converter = FunctionTool(func=convert_temperature)
```

## LongRunningFunctionTool

### LongRunningFunctionTool Core Concepts

`LongRunningFunctionTool` is designed for time-consuming operations where providing progress updates enhances the user experience. It uses Python generator functions to yield intermediate updates while processing.

### LongRunningFunctionTool Implementation

1. Define a generator function that yields updates and returns a final result:

```python
def my_long_running_generator(param1: str, param2: int):
    """
    Well-documented docstring explaining the function's purpose.

    Args:
        param1 (str): Description of first parameter
        param2 (int): Description of second parameter

    Yields:
        dict: Progress updates during execution

    Returns:
        dict: Final result upon completion
    """
    # Initial setup
    yield {"status": "pending", "message": "Starting operation..."}

    # Process in stages, yielding updates
    # ...processing logic...
    yield {"status": "pending", "progress": 50, "message": "Halfway done"}

    # Final processing
    # ...more logic...

    # Return final result
    return {"status": "completed", "result": final_result}
```

2. Create the tool:

```python
my_long_tool = LongRunningFunctionTool(func=my_long_running_generator)
```

### Intermediate Updates

When designing your generator function, consider including these keys in your yielded dictionaries:

- `status`: String indicating current state ("pending", "running", "waiting_for_input")
- `progress`: Numeric value (percentage or steps completed)
- `message`: Descriptive text explaining current status
- `estimated_completion_time`: If calculable, when the operation might finish

### LongRunningFunctionTool Example

```python
from google.adk.tools import LongRunningFunctionTool
import time

def process_large_file(file_size: int, processing_type: str):
    """
    Simulate processing a large file with progress updates.

    Args:
        file_size (int): Size of file in MB to simulate
        processing_type (str): Type of processing to simulate

    Yields:
        dict: Progress updates during processing

    Returns:
        dict: Final processing results
    """
    # Initial setup
    yield {
        "status": "pending",
        "progress": 0,
        "message": f"Starting {processing_type} processing on {file_size}MB file..."
    }

    # Simulate processing in chunks
    chunk_size = 10  # MB per chunk
    total_chunks = file_size // chunk_size

    for chunk in range(1, total_chunks + 1):
        # Simulate work
        time.sleep(1)  # Simulate 1 second of processing per chunk

        progress = int((chunk / total_chunks) * 100)
        yield {
            "status": "running",
            "progress": progress,
            "message": f"Processed {chunk * chunk_size}MB of {file_size}MB ({progress}%)",
            "estimated_completion_time": f"Approximately {total_chunks - chunk} seconds remaining"
        }

    # Final processing
    time.sleep(0.5)  # Final processing step

    # Return completed result
    return {
        "status": "completed",
        "file_size": file_size,
        "processing_type": processing_type,
        "total_time": total_chunks + 0.5,
        "message": f"Successfully completed {processing_type} processing on {file_size}MB file."
    }

# Create the tool
file_processor = LongRunningFunctionTool(func=process_large_file)
```

## Choosing Between Tools

| Use FunctionTool when:                        | Use LongRunningFunctionTool when:           |
| --------------------------------------------- | ------------------------------------------- |
| Operation completes quickly (seconds)         | Operation takes significant time (minutes+) |
| No need for progress updates                  | Users benefit from progress updates         |
| Simple, atomic operations                     | Complex, multi-stage processes              |
| No human intervention needed during execution | Might require human approval during process |
| Result is immediately available               | Result takes time to generate               |

## Advanced Topics

### Error Handling

Both tool types should handle errors gracefully:

```python
# For FunctionTool
def my_function(param):
    try:
        # Logic that might fail
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# For LongRunningFunctionTool
def my_generator(param):
    try:
        yield {"status": "pending"}
        # Logic that might fail
        if error_condition:
            return {"status": "error", "message": "Something went wrong"}
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

### Using with Agents

Register your tools with your agent:

```python
from google.adk import Agent

my_agent = Agent(
    # Other agent configuration...
    tools=[my_tool, my_long_tool]
)
```

---

## Additional Resources

- [ADK Documentation](https://adk.docs.example.com)
- [Function Tools API Reference](https://adk.docs.example.com/api/tools)
- [Example Projects](https://github.com/example/adk-examples)

---

This README provides an overview of the Agent Development Kit's function tools. For more detailed information, refer to the official documentation.
