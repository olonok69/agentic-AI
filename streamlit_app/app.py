"""
CoT and ReACT Prompting Application
A Streamlit application demonstrating Chain-of-Thought and ReACT prompting techniques.
"""

import streamlit as st
import pandas as pd
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
import plotly.express as px
import plotly.graph_objects as go
from dataclasses import dataclass
import re
import ast
import operator
from enum import Enum

# Pydantic Models
class OpenAIModels(str, Enum):
    """Available OpenAI models."""
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_41_MINI = "gpt-4.1-mini"
    GPT_41_NANO = "gpt-4.1-nano"

class SalesDataPoint(BaseModel):
    """Sales data point model."""
    date: date
    product_id: str = Field(..., description="Product identifier")
    product_name: str = Field(..., description="Product name")
    quantity: int = Field(..., ge=0, description="Quantity sold")
    revenue: float = Field(..., ge=0, description="Revenue generated")

class WeatherData(BaseModel):
    """Weather data model."""
    date: str
    temperature: Dict[str, float]
    conditions: Dict[str, Any]

class PromotionData(BaseModel):
    """Promotion data model."""
    promotion_id: str
    name: str
    discount: str
    products: List[str]
    start_date: date
    end_date: date

class CompetitorPricingData(BaseModel):
    """Competitor pricing data model."""
    product: str
    date: str
    our_price: float
    competitor_sales: Dict[str, Any]
    competitor_a_price: float
    competitor_b_price: float
    competitor_c_price: float

class ChainOfThoughtRequest(BaseModel):
    """Request model for Chain of Thought analysis."""
    system_prompt: str = Field(..., description="System prompt for the AI")
    user_prompt: str = Field(..., description="User query")
    use_explicit_cot: bool = Field(True, description="Whether to use explicit CoT prompting")
    model: OpenAIModels = Field(OpenAIModels.GPT_41_NANO, description="Model to use")

class ReACTRequest(BaseModel):
    """Request model for ReACT analysis."""
    task_description: str = Field(..., description="Task to be completed")
    max_iterations: int = Field(10, ge=1, le=20, description="Maximum number of ReACT iterations")
    model: OpenAIModels = Field(OpenAIModels.GPT_41_NANO, description="Model to use")

class AnalysisResult(BaseModel):
    """Analysis result model."""
    date: str
    amount_before_increase: str
    amount_after_increase: str
    percentage_increase: str
    causes: List[str]

# Data Generation Functions (Based on the notebook library)
@st.cache_data
def get_sales_data(products: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Generate sample sales data."""
    from datetime import date
    
    data = [
        {"date": date(2024, 1, 10), "product_id": "P001", "product_name": "Product 1", "quantity": 255, "revenue": 15547.35},
        {"date": date(2024, 1, 10), "product_id": "P002", "product_name": "Product 2", "quantity": 65, "revenue": 2297.1},
        {"date": date(2024, 1, 10), "product_id": "P003", "product_name": "Product 3", "quantity": 90, "revenue": 7301.7},
        {"date": date(2024, 1, 10), "product_id": "P004", "product_name": "Product 4", "quantity": 171, "revenue": 8296.92},
        {"date": date(2024, 1, 10), "product_id": "P005", "product_name": "Product 5", "quantity": 96, "revenue": 2587.2},
        {"date": date(2024, 1, 11), "product_id": "P001", "product_name": "Product 1", "quantity": 235, "revenue": 14327.95},
        {"date": date(2024, 1, 11), "product_id": "P002", "product_name": "Product 2", "quantity": 86, "revenue": 3039.24},
        {"date": date(2024, 1, 11), "product_id": "P003", "product_name": "Product 3", "quantity": 79, "revenue": 6409.27},
        {"date": date(2024, 1, 11), "product_id": "P004", "product_name": "Product 4", "quantity": 145, "revenue": 7035.4},
        {"date": date(2024, 1, 11), "product_id": "P005", "product_name": "Product 5", "quantity": 114, "revenue": 3072.3},
        {"date": date(2024, 1, 12), "product_id": "P001", "product_name": "Product 1", "quantity": 310, "revenue": 18900.7},
        {"date": date(2024, 1, 12), "product_id": "P002", "product_name": "Product 2", "quantity": 80, "revenue": 2827.2},
        {"date": date(2024, 1, 12), "product_id": "P003", "product_name": "Product 3", "quantity": 108, "revenue": 8762.04},
        {"date": date(2024, 1, 12), "product_id": "P004", "product_name": "Product 4", "quantity": 143, "revenue": 6938.36},
        {"date": date(2024, 1, 12), "product_id": "P005", "product_name": "Product 5", "quantity": 342, "revenue": 9216.9},
        {"date": date(2024, 1, 13), "product_id": "P001", "product_name": "Product 1", "quantity": 302, "revenue": 18412.94},
        {"date": date(2024, 1, 13), "product_id": "P002", "product_name": "Product 2", "quantity": 68, "revenue": 2403.12},
        {"date": date(2024, 1, 13), "product_id": "P003", "product_name": "Product 3", "quantity": 96, "revenue": 7788.48},
        {"date": date(2024, 1, 13), "product_id": "P004", "product_name": "Product 4", "quantity": 130, "revenue": 6307.6},
        {"date": date(2024, 1, 13), "product_id": "P005", "product_name": "Product 5", "quantity": 103, "revenue": 2775.85},
        {"date": date(2024, 1, 14), "product_id": "P001", "product_name": "Product 1", "quantity": 305, "revenue": 18595.85},
        {"date": date(2024, 1, 14), "product_id": "P002", "product_name": "Product 2", "quantity": 84, "revenue": 2968.56},
        {"date": date(2024, 1, 14), "product_id": "P003", "product_name": "Product 3", "quantity": 99, "revenue": 8031.87},
        {"date": date(2024, 1, 14), "product_id": "P004", "product_name": "Product 4", "quantity": 167, "revenue": 8102.84},
        {"date": date(2024, 1, 14), "product_id": "P005", "product_name": "Product 5", "quantity": 104, "revenue": 2802.8},
        {"date": date(2024, 1, 15), "product_id": "P001", "product_name": "Product 1", "quantity": 301, "revenue": 18351.97},
        {"date": date(2024, 1, 15), "product_id": "P002", "product_name": "Product 2", "quantity": 73, "revenue": 2579.82},
        {"date": date(2024, 1, 15), "product_id": "P003", "product_name": "Product 3", "quantity": 89, "revenue": 7220.57},
        {"date": date(2024, 1, 15), "product_id": "P004", "product_name": "Product 4", "quantity": 126, "revenue": 6113.52},
        {"date": date(2024, 1, 15), "product_id": "P005", "product_name": "Product 5", "quantity": 100, "revenue": 2695.0},
        {"date": date(2024, 1, 16), "product_id": "P001", "product_name": "Product 1", "quantity": 226, "revenue": 13779.22},
        {"date": date(2024, 1, 16), "product_id": "P002", "product_name": "Product 2", "quantity": 80, "revenue": 2827.2},
        {"date": date(2024, 1, 16), "product_id": "P003", "product_name": "Product 3", "quantity": 83, "revenue": 6733.79},
        {"date": date(2024, 1, 16), "product_id": "P004", "product_name": "Product 4", "quantity": 175, "revenue": 8491.0},
        {"date": date(2024, 1, 16), "product_id": "P005", "product_name": "Product 5", "quantity": 125, "revenue": 3368.75},
    ]
    
    if products:
        return [item for item in data if item["product_id"] in products]
    return data

@st.cache_data
def get_promotions_data() -> List[Dict[str, Any]]:
    """Generate sample promotions data."""
    return [
        {
            "promotion_id": "PROMO001",
            "name": "Weekend Special",
            "discount": "10% off",
            "products": ["P002"],
            "start_date": date(2024, 1, 12),
            "end_date": date(2024, 1, 14),
        },
        {
            "promotion_id": "PROMO002",
            "name": "Flash Sale",
            "discount": "15% off",
            "products": ["P001", "P003", "P005"],
            "start_date": date(2024, 1, 15),
            "end_date": date(2024, 1, 16),
        },
    ]

@st.cache_data
def get_weather_data() -> List[Dict[str, Any]]:
    """Generate sample weather data."""
    return [
        {"date": "2024-01-10", "temperature": {"fahrenheit": 23.4, "celsius": -4.8}, "conditions": {"main": "Clear", "precipitation": "None", "precipitation_amount": 0, "special_event": None}},
        {"date": "2024-01-11", "temperature": {"fahrenheit": 39.3, "celsius": 4.1}, "conditions": {"main": "Clear", "precipitation": "None", "precipitation_amount": 0, "special_event": None}},
        {"date": "2024-01-12", "temperature": {"fahrenheit": 41.1, "celsius": 5.1}, "conditions": {"main": "Heavy Rain", "precipitation": "Heavy Rain", "precipitation_amount": 2.7, "special_event": "Flood Warning"}},
        {"date": "2024-01-13", "temperature": {"fahrenheit": 27.2, "celsius": -2.6}, "conditions": {"main": "Clear", "precipitation": "None", "precipitation_amount": 0, "special_event": None}},
        {"date": "2024-01-14", "temperature": {"fahrenheit": 22.9, "celsius": -5.1}, "conditions": {"main": "Clear", "precipitation": "None", "precipitation_amount": 0, "special_event": None}},
        {"date": "2024-01-15", "temperature": {"fahrenheit": 33.2, "celsius": 0.7}, "conditions": {"main": "Clear", "precipitation": "None", "precipitation_amount": 0, "special_event": "High Winds"}},
        {"date": "2024-01-16", "temperature": {"fahrenheit": 23.3, "celsius": -4.8}, "conditions": {"main": "Clear", "precipitation": "None", "precipitation_amount": 0, "special_event": None}},
    ]

# Utility Functions
def safe_eval(expr: str) -> Union[int, float]:
    """Safely evaluate mathematical expressions."""
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.USub: operator.neg,
    }
    
    def eval_node(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](eval_node(node.left), eval_node(node.right))
        elif isinstance(node, ast.UnaryOp):
            return operators[type(node.op)](eval_node(node.operand))
        elif isinstance(node, ast.Expr):
            return eval_node(node.value)
        else:
            raise TypeError(f"Unsupported type: {type(node)}")
    
    result = eval_node(ast.parse(expr, mode="eval").body)
    
    if isinstance(result, float):
        return round(result, 2)
    elif isinstance(result, int):
        return result
    else:
        raise RuntimeError(f"Unsupported result type: {type(result)}")

def calculator(expression: str) -> float:
    """Calculate mathematical expressions safely."""
    return float(safe_eval(expression))

# Simulation Functions (Mock implementations)
def simulate_cot_analysis(request: ChainOfThoughtRequest) -> str:
    """Simulate Chain of Thought analysis."""
    # This would normally call an actual LLM API
    base_analysis = """
STRUCTURED ANALYSIS:

Step 1: Data Overview
I need to examine the sales data for any significant spikes across products P001-P005 from January 10-16, 2024.

Step 2: Identify Sales Spikes
Looking at the quantity data for each product:
- Product 1: Relatively stable (255→235→310→302→305→301→226)
- Product 2: Stable with minor variations (65→86→80→68→84→73→80)
- Product 3: Stable (90→79→108→96→99→89→83)
- Product 4: Stable (171→145→143→130→167→126→175)
- Product 5: MAJOR SPIKE on Jan 12 (96→114→342→103→104→100→125)

Step 3: Calculate Percentage Increases
Product 5 shows the largest spike:
- Before spike (Jan 11): 114 units
- During spike (Jan 12): 342 units
- Percentage increase: ((342-114)/114) × 100 = 200%

Step 4: Analyze Contributing Factors
Checking data for Jan 12, 2024:
- Weather: Heavy rain with flood warning
- Promotions: Weekend Special promotion started (though for Product 2)
- This suggests Product 5 may be weather-related (umbrellas, rain gear, etc.)

LARGEST SPIKE:
```json
{
    "date": "2024-01-12",
    "amount_before_increase": "114",
    "amount_after_increase": "342",
    "percentage_increase": "200.00%",
    "causes": [
        "Heavy rain and flood warning created immediate demand",
        "Product 5 likely weather-dependent (rain gear, umbrellas)",
        "Weekend promotion may have increased overall store traffic"
    ]
}
```
    """
    
    return base_analysis

def simulate_react_step(step: int, context: str) -> Dict[str, str]:
    """Simulate a single ReACT step."""
    if step == 1:
        return {
            "think": "I need to get the sales data first to identify any sales spikes.",
            "act": "get_sales_data()",
            "observe": str(get_sales_data(products=["P005"]))
        }
    elif step == 2:
        return {
            "think": "I can see Product 5 has a major spike on 2024-01-12. Let me check the weather for that date.",
            "act": "call_weather_api(date=\"2024-01-12\")",
            "observe": str(get_weather_data()[2])  # Jan 12 weather data
        }
    elif step == 3:
        return {
            "think": "The weather shows heavy rain and flood warning. Let me calculate the percentage increase.",
            "act": "calculator(expression=\"((342-114)/114)*100\")",
            "observe": "200.0"
        }
    else:
        return {
            "think": "I have all the information needed for the final answer.",
            "act": "final_answer(amount_after_spike=\"342\", causes=[\"Heavy rain created demand for weather-related products\", \"Flood warning increased urgency\"], date=\"2024-01-12\", percentage_spike=\"200.00%\")",
            "observe": "Analysis complete: 200% spike on 2024-01-12 due to severe weather conditions"
        }

# Streamlit App
def main():
    st.set_page_config(
        page_title="CoT and ReACT Prompting",
        page_icon="🧠",
        layout="wide"
    )
    
    st.title("Chain-of-Thought and ReACT Prompting Application")
    st.markdown("**Demand Spike Detective**: Analyze sales data using advanced prompting techniques")
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose Analysis Type",
        ["Overview", "Chain-of-Thought Analysis", "ReACT Analysis", "Data Explorer"]
    )
    
    if page == "Overview":
        show_overview()
    elif page == "Chain-of-Thought Analysis":
        show_cot_analysis()
    elif page == "ReACT Analysis":
        show_react_analysis()
    elif page == "Data Explorer":
        show_data_explorer()

def show_overview():
    """Show application overview."""
    st.header("Application Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Chain-of-Thought (CoT) Prompting")
        st.write("""
        Chain-of-Thought prompting guides AI models through step-by-step reasoning:
        
        **Key Features:**
        - Explicit reasoning steps
        - Structured analysis format
        - Clear problem decomposition
        - Improved accuracy for complex tasks
        
        **Use Cases:**
        - Complex analytical tasks
        - Mathematical reasoning
        - Multi-step problem solving
        """)
        
        with st.expander("CoT Example"):
            st.code("""
System Prompt: "You are a retail analyst. Think step by step."

User: "Find sales spikes in the data"

AI Response:
Step 1: Examine the data...
Step 2: Calculate differences...
Step 3: Identify patterns...
Conclusion: Product 5 shows 200% spike on Jan 12
            """, language="text")
    
    with col2:
        st.subheader("ReACT (Reasoning + Acting)")
        st.write("""
        ReACT combines reasoning with tool usage in an iterative loop:
        
        **Key Features:**
        - Think → Act → Observe pattern
        - Tool integration
        - Dynamic decision making
        - Interactive problem solving
        
        **Use Cases:**
        - Multi-step analysis requiring tools
        - Dynamic data retrieval
        - Complex decision trees
        """)
        
        with st.expander("ReACT Example"):
            st.code("""
THINK: I need sales data to find spikes
ACT: get_sales_data()
OBSERVE: [sales data returned]

THINK: I see a spike on Jan 12, need weather data
ACT: call_weather_api(date="2024-01-12")
OBSERVE: Heavy rain, flood warning

THINK: Now I can calculate the increase
ACT: calculator(expression="((342-114)/114)*100")
OBSERVE: 200.0
            """, language="text")

def show_cot_analysis():
    """Show Chain-of-Thought analysis interface."""
    st.header("Chain-of-Thought Analysis")
    
    with st.expander("What is Chain-of-Thought Prompting?"):
        st.write("""
        Chain-of-Thought (CoT) prompting is a technique that encourages AI models to break down 
        complex problems into step-by-step reasoning. This approach improves accuracy and 
        provides transparency in the decision-making process.
        
        **Benefits:**
        - More accurate results for complex tasks
        - Transparent reasoning process  
        - Better handling of multi-step problems
        - Easier to debug and validate responses
        """)
    
    # Configuration
    st.subheader("Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        use_explicit_cot = st.checkbox(
            "Use Explicit CoT", 
            value=True, 
            help="Include 'Think step by step' in the system prompt"
        )
        
        model = st.selectbox(
            "Model Selection",
            options=[model.value for model in OpenAIModels],
            help="Choose the AI model for analysis"
        )
    
    with col2:
        output_format = st.selectbox(
            "Output Format",
            ["Structured Analysis", "Free Form", "JSON Only"],
            help="How results should be formatted"
        )
    
    # System Prompt Configuration
    st.subheader("System Prompt")
    
    default_system_prompt = """You are a meticulous Retail Demand Analyst.
Your task is to analyze provided sales data and promotion schedules to identify and explain significant sales spikes for specific SKUs.

Think step by step."""
    
    system_prompt = st.text_area(
        "System Prompt",
        value=default_system_prompt,
        height=150,
        help="Define the AI's role and approach"
    )
    
    # User Query
    st.subheader("Analysis Query")
    
    default_query = """Analyze the provided retail data and identify the single largest sales spike according to percentage increase. 

Provide a structured analysis including:
- Step-by-step reasoning
- Data examination process
- Calculation methods
- Final conclusions with causes

Focus on factors such as weather conditions, promotions, and competitor actions."""
    
    user_query = st.text_area(
        "Your Query",
        value=default_query,
        height=150,
        help="Describe what you want to analyze"
    )
    
    # Analysis Button
    if st.button("Run CoT Analysis", type="primary"):
        with st.spinner("Analyzing data using Chain-of-Thought reasoning..."):
            try:
                # Create request
                request = ChainOfThoughtRequest(
                    system_prompt=system_prompt,
                    user_prompt=user_query,
                    use_explicit_cot=use_explicit_cot,
                    model=OpenAIModels(model)
                )
                
                # Run analysis (simulated)
                result = simulate_cot_analysis(request)
                
                # Display results
                st.subheader("Analysis Results")
                
                # Split analysis and JSON
                if "```json" in result:
                    analysis_part = result.split("```json")[0].strip()
                    json_part = result.split("```json")[1].split("```")[0].strip()
                    
                    st.markdown("**Reasoning Process:**")
                    st.markdown(analysis_part)
                    
                    st.markdown("**Key Findings:**")
                    try:
                        findings = json.loads(json_part)
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Date of Spike", findings["date"])
                            st.metric("Percentage Increase", findings["percentage_increase"])
                        
                        with col2:
                            st.metric("Before Spike", findings["amount_before_increase"])
                            st.metric("After Spike", findings["amount_after_increase"])
                        
                        st.markdown("**Identified Causes:**")
                        for i, cause in enumerate(findings["causes"], 1):
                            st.write(f"{i}. {cause}")
                        
                        # Show raw JSON
                        with st.expander("Raw JSON Response"):
                            st.json(findings)
                            
                    except json.JSONDecodeError:
                        st.error("Could not parse JSON results")
                        st.code(json_part)
                else:
                    st.markdown(result)
                
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")

def show_react_analysis():
    """Show ReACT analysis interface."""
    st.header("ReACT (Reasoning + Acting) Analysis")
    
    with st.expander("What is ReACT Prompting?"):
        st.write("""
        ReACT (Reasoning + Acting) is an advanced prompting technique that combines reasoning 
        with the ability to use tools and take actions. It follows a Think → Act → Observe pattern.
        
        **How it works:**
        1. **Think**: The AI reasons about what needs to be done next
        2. **Act**: The AI calls a tool or takes an action  
        3. **Observe**: The AI processes the results and decides next steps
        4. **Repeat**: Until the task is complete
        
        **Available Tools:**
        - `get_sales_data()`: Retrieve sales information
        - `call_weather_api(date)`: Get weather data for specific dates
        - `calculator(expression)`: Perform mathematical calculations
        - `final_answer(...)`: Provide the final analysis result
        """)
    
    # Configuration
    st.subheader("Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_iterations = st.slider(
            "Max Iterations", 
            min_value=1, 
            max_value=20, 
            value=10,
            help="Maximum number of Think-Act-Observe cycles"
        )
        
        model = st.selectbox(
            "Model Selection",
            options=[model.value for model in OpenAIModels],
            index=0,
            help="Choose the AI model for analysis"
        )
    
    with col2:
        show_intermediate_steps = st.checkbox(
            "Show Intermediate Steps", 
            value=True,
            help="Display each Think-Act-Observe cycle"
        )
        
        auto_continue = st.checkbox(
            "Auto Continue",
            value=True,
            help="Automatically continue to next step"
        )
    
    # Task Description
    st.subheader("Task Description")
    
    default_task = """Find the single largest sales spike according to the percentage increase with a short explanation for it based on factors such as weather."""
    
    task_description = st.text_area(
        "Task for ReACT Agent",
        value=default_task,
        height=100,
        help="Describe the task you want the ReACT agent to complete"
    )
    
    # Available Tools Display
    with st.expander("Available Tools Reference"):
        st.code("""
Available Tools:

1. get_sales_data()
   - Returns: Sales data for all products
   - Example: ACT: get_sales_data()

2. call_weather_api(date: str)  
   - Returns: Weather data for specified date
   - Example: ACT: call_weather_api(date="2024-01-12")

3. calculator(expression: str)
   - Returns: Result of mathematical calculation
   - Example: ACT: calculator(expression="(342-114)/114*100")

4. final_answer(amount_after_spike: str, causes: list[str], date: str, percentage_spike: str)
   - Returns: Final analysis result
   - Example: ACT: final_answer(amount_after_spike="342", causes=["Weather"], date="2024-01-12", percentage_spike="200%")
        """, language="text")
    
    # Analysis Controls
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Start ReACT Analysis", type="primary"):
            st.session_state.react_running = True
            st.session_state.react_step = 0
            st.session_state.react_context = ""
            st.session_state.react_complete = False
    
    with col2:
        if st.button("Reset Analysis"):
            for key in ['react_running', 'react_step', 'react_context', 'react_complete']:
                if key in st.session_state:
                    del st.session_state[key]
    
    # ReACT Execution
    if st.session_state.get('react_running', False):
        st.subheader("ReACT Execution")
        
        # Initialize if needed
        if 'react_step' not in st.session_state:
            st.session_state.react_step = 0
        
        if not st.session_state.get('react_complete', False):
            current_step = st.session_state.react_step + 1
            
            with st.spinner(f"Executing ReACT Step {current_step}..."):
                # Simulate ReACT step
                step_result = simulate_react_step(current_step, st.session_state.get('react_context', ''))
                
                # Display step
                st.markdown(f"### Step {current_step}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**THINK:**")
                    st.info(step_result['think'])
                
                with col2:
                    st.markdown("**ACT:**")  
                    st.code(step_result['act'])
                
                with col3:
                    st.markdown("**OBSERVE:**")
                    st.success(step_result['observe'])
                
                # Update context
                st.session_state.react_context += f"Step {current_step}: {step_result}\n"
                st.session_state.react_step += 1
                
                # Check if complete
                if "final_answer" in step_result['act']:
                    st.session_state.react_complete = True
                    st.success("ReACT Analysis Complete!")
                    
                    # Show final summary
                    st.subheader("Final Results")
                    st.json({
                        "conclusion": "Product 5 experienced a 200% sales spike on 2024-01-12",
                        "primary_cause": "Heavy rain and flood warning",
                        "supporting_factors": ["Weather-dependent product demand", "Emergency purchasing behavior"],
                        "quantitative_result": "342 units (up from 114 units)"
                    })
                    
                elif st.session_state.react_step >= max_iterations:
                    st.error("Maximum iterations reached without completion")
                    st.session_state.react_complete = True
                
                # Auto-continue or manual control
                if auto_continue and not st.session_state.react_complete:
                    st.rerun()
                elif not auto_continue and not st.session_state.react_complete:
                    if st.button(f"Continue to Step {current_step + 1}"):
                        st.rerun()

def show_data_explorer():
    """Show data exploration interface."""
    st.header("Data Explorer")
    
    st.write("Explore the sample data used in the analysis examples.")
    
    # Data type selector
    data_type = st.selectbox(
        "Select Data Type",
        ["Sales Data", "Promotions Data", "Weather Data"]
    )
    
    if data_type == "Sales Data":
        st.subheader("Sales Data")
        sales_data = get_sales_data()
        df = pd.DataFrame(sales_data)
        
        st.dataframe(df, use_container_width=True)
        
        # Visualization
        st.subheader("Sales Visualization")
        
        # Line chart
        fig = px.line(
            df, 
            x='date', 
            y='quantity', 
            color='product_name',
            title='Sales Quantity Over Time'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Highlight the spike
        product_5_data = df[df['product_id'] == 'P005'].copy()
        
        fig2 = px.bar(
            product_5_data,
            x='date',
            y='quantity', 
            title='Product 5 Sales Spike Analysis',
            color='quantity',
            color_continuous_scale='Reds'
        )
        fig2.add_annotation(
            x='2024-01-12',
            y=342,
            text="200% Spike!",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="red"
        )
        st.plotly_chart(fig2, use_container_width=True)
        
    elif data_type == "Promotions Data":
        st.subheader("Promotions Data")
        promotions_data = get_promotions_data()
        df = pd.DataFrame(promotions_data)
        st.dataframe(df, use_container_width=True)
        
        # Timeline visualization
        st.subheader("Promotion Timeline")
        
        fig = px.timeline(
            df,
            x_start='start_date',
            x_end='end_date', 
            y='name',
            color='discount',
            title='Promotion Schedule'
        )
        st.plotly_chart(fig, use_container_width=True)
        
    elif data_type == "Weather Data":
        st.subheader("Weather Data") 
        weather_data = get_weather_data()
        
        # Process weather data for display
        weather_display = []
        for item in weather_data:
            weather_display.append({
                'date': item['date'],
                'temperature_c': item['temperature']['celsius'],
                'temperature_f': item['temperature']['fahrenheit'], 
                'conditions': item['conditions']['main'],
                'precipitation': item['conditions']['precipitation'],
                'special_event': item['conditions'].get('special_event', 'None')
            })
        
        df = pd.DataFrame(weather_display)
        st.dataframe(df, use_container_width=True)
        
        # Weather visualization
        st.subheader("Weather Visualization")
        
        fig = px.line(
            df,
            x='date', 
            y='temperature_c',
            title='Temperature Over Time',
            markers=True
        )
        
        # Add annotations for special weather events
        for idx, row in df.iterrows():
            if row['special_event'] != 'None':
                fig.add_annotation(
                    x=row['date'],
                    y=row['temperature_c'],
                    text=row['special_event'],
                    showarrow=True,
                    arrowhead=2
                )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Data Statistics
    st.subheader("Data Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Sales Records", len(get_sales_data()))
    
    with col2:
        st.metric("Promotions", len(get_promotions_data()))
    
    with col3: 
        st.metric("Weather Records", len(get_weather_data()))

if __name__ == "__main__":
    main()