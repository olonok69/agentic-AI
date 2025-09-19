"""
Configuration module for CoT and ReACT Prompting Application.
Contains settings, constants, and configuration management.
"""

import os
from typing import Dict, Any
from pydantic import BaseSettings, Field
from enum import Enum


class AppSettings(BaseSettings):
    """Application settings using Pydantic BaseSettings."""
    
    # API Configuration
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", env="OPENAI_BASE_URL")
    
    # App Configuration
    app_title: str = Field(default="CoT and ReACT Prompting Application")
    app_description: str = Field(default="Demand Spike Detective: Analyze sales data using advanced prompting techniques")
    
    # Analysis Configuration
    max_react_iterations: int = Field(default=10, ge=1, le=20)
    default_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    
    # UI Configuration
    page_layout: str = Field(default="wide")
    show_sidebar: bool = Field(default=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class PromptTemplates:
    """Predefined prompt templates for different analysis types."""
    
    COT_SYSTEM_PROMPT = """You are a meticulous Retail Demand Analyst.
Your task is to analyze provided sales data and promotion schedules to identify and explain significant sales spikes for specific SKUs.

Think step by step."""

    REACT_SYSTEM_PROMPT = """
You are a meticulous Retail Demand Analyst that can solve any TASK in a multi-step process using tool calls and reasoning.

## Instructions:
- You will use step-by-step reasoning by
    - THINKING the next steps to take to complete the task and what next tool call to take to get one step closer to the final answer
    - ACTING on the single next tool call to take
- You will always respond with a single THINK/ACT message of the following format:
    THINK:
    [Carry out any reasoning needed to solve the problem not requiring a tool call]
    [Conclusion about what next tool call to take based on what data is needed and what tools are available]
    ACT:
    [Tool to use and arguments]
- As soon as you know the final answer, call the `final_answer` tool in an `ACT` message.
- ALWAYS provide a tool call, after ACT:, else you will fail.

## Available Tools
* `calculator(expression: str)`: Perform an arithmetic calculation
    - Example:
        - Input: `ACT: calculator(expression="(10 + 20) / 2.0")`
        - Output: `OBSERVE: 15.0`
* `get_sales_data()`: Get the sales data
    - Example:
        - Input: `ACT: get_sales_data()`
        - Output: `OBSERVE: {"date": "2024-01-10", "product_id": "P001", "product_name": "Product 1", "quantity": 255, "revenue": 15547.35}`
* `call_weather_api(date: str)`: Get weather data for a specific date. Call this for the date of each spike.
    - Example:
        - Input: `ACT: call_weather_api(date="2024-01-10")`
        - Output: `OBSERVE: {"date": "2024-01-10", "weather": "Sunny", "temperature": 72}`

* `final_answer(amount_after_spike: str, causes: list[str], date: str, percentage_spike: str)`: Return the final answer
    - Example:
        - Input: `ACT: final_answer(amount_after_spike="32", causes=["Competitor X offering a 29 discount boosting category interest", ...], date="2020-06-12", percentage_spike="20.00%")`
        - Output: `OBSERVE: {"amount_after_spike": "32", "causes": ["Competitor X offering a 29 discount boosting category interest", ...], "date": "2020-06-12", "percentage_spike": "20.00%"}`

You will not use any other tools.
"""

    DEFAULT_COT_QUERY = """Analyze the provided retail data and identify the single largest sales spike according to percentage increase. 

Provide a structured analysis including:
- Step-by-step reasoning
- Data examination process
- Calculation methods
- Final conclusions with causes

Focus on factors such as weather conditions, promotions, and competitor actions."""

    DEFAULT_REACT_TASK = """Find the single largest sales spike according to the percentage increase with a short explanation for it based on factors such as weather."""


class UIConstants:
    """UI-related constants and styling."""
    
    # Colors
    PRIMARY_COLOR = "#1f77b4"
    SECONDARY_COLOR = "#ff7f0e"
    SUCCESS_COLOR = "#2ca02c"
    ERROR_COLOR = "#d62728"
    WARNING_COLOR = "#ff7f0e"
    
    # Metrics
    METRIC_DELTA_COLOR = "normal"
    
    # Chart configurations
    CHART_HEIGHT = 400
    CHART_WIDTH = None  # Use container width
    
    # Help texts
    HELP_TEXTS = {
        "cot_explicit": "Include 'Think step by step' in the system prompt to encourage explicit reasoning",
        "model_selection": "Choose the AI model for analysis. Different models may produce different results",
        "max_iterations": "Maximum number of Think-Act-Observe cycles before stopping",
        "output_format": "How results should be formatted and displayed",
        "system_prompt": "Define the AI's role, capabilities, and approach to the task",
        "user_query": "Describe what you want to analyze or the specific question to answer",
        "task_description": "Describe the task you want the ReACT agent to complete using available tools",
        "show_steps": "Display each Think-Act-Observe cycle for transparency",
        "auto_continue": "Automatically proceed to the next step without manual intervention"
    }
    
    # Example data for placeholders
    EXAMPLE_SYSTEM_PROMPTS = [
        "You are a retail analyst. Think step by step.",
        "You are an expert data scientist analyzing sales patterns.",
        "You are a business intelligence specialist focused on demand forecasting."
    ]
    
    EXAMPLE_QUERIES = [
        "Find the largest sales spike and explain its causes",
        "Identify products with unusual sales patterns",
        "Analyze the correlation between weather and sales"
    ]
    
    EXAMPLE_REACT_TASKS = [
        "Find sales spikes and correlate with weather data",
        "Calculate percentage increases for all products", 
        "Identify the most profitable sales spike"
    ]


# Global settings instance
settings = AppSettings()


def get_settings() -> AppSettings:
    """Get application settings instance."""
    return settings


def update_settings(**kwargs) -> AppSettings:
    """Update settings with new values."""
    global settings
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    return settings


# Export commonly used items
__all__ = [
    "AppSettings",
    "PromptTemplates", 
    "UIConstants",
    "settings",
    "get_settings",
    "update_settings"
]