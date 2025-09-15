import os

import pandas as pd
from IPython.display import Markdown, display
from lesson_2_lib import (
    # Helpers
    OpenAIModels,
    print_in_box,
    # Synthetic data
    get_competitor_pricing_data,
    get_completion,
    get_promotions_data,
    get_sales_data,
    get_weather_data,
    call_weather_api
)
import ast
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

MODEL = OpenAIModels.GPT_41_MINI

load_dotenv()

client = OpenAI()
# The first prompt in our chain
prompt_step1 = """
You are a helpful programming assistant.

I need a Python script to read a CSV file named 'input_data.csv',
calculate the average of a column named 'value', and write the
average to a new file named 'output.txt'.

Please provide a simple, step-by-step outline for this script.
"""

print("--- Calling AI for Step 1: Outline Generation ---")
outline_response = get_completion(prompt_step1, client=client, model=MODEL)

print("\n--- AI-Generated Outline ---")
print(outline_response)

input("Press Enter to continue to Step 2...")
prompt_step2 = f"""
You are a helpful programming assistant.

Based on the following outline, please write the complete Python code for the script.
Ensure you use standard libraries and include comments.

Outline:
---
{outline_response}
---
"""

print("\n--- Calling AI for Step 2: Code Generation ---")
code_response = get_completion(prompt_step2,client=client, model=MODEL)

print("\n--- AI-Generated Python Code ---")
print(code_response)
input("Press Enter to continue to Step 3...")

def check_python_syntax(code):
    """Checks for syntax errors in a string of Python code."""
    try:
        ast.parse(code.replace("```python", "").replace("```", ""))
        return True, "No syntax errors found."
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"

# Run our gate check on the generated code
is_valid, message = check_python_syntax(code_response)

print(f"\n--- Gate Check Result ---")
print(f"Code is valid: {is_valid}")
print(message)