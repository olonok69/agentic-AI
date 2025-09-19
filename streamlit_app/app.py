import streamlit as st
import pandas as pd
import json
from typing import Dict, Any, List, Optional
import re
from datetime import datetime

# Import data functions
from data import (
    get_sales_data,
    get_promotions_data,
    get_weather_data,
    get_competitor_pricing_data,
    call_weather_api,
    get_email_data,
    get_customer_feedback_data,
    get_prompt_templates,
    OpenAIModels
)


def setup_page_config() -> None:
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Chain-of-Thought & ReACT Prompting Demo",
        page_icon="🧠",
        layout="wide"
    )


def display_sidebar() -> str:
    """Create sidebar with case selection."""
    st.sidebar.header("Select Case Study")
    
    cases = {
        "Demand Spike Detective (CoT)": "cot_analysis",
        "Demand Spike Detective (ReACT)": "react_analysis", 
        "Prompt Instruction Refinement": "prompt_refinement"
    }
    
    selected_case = st.sidebar.selectbox(
        "Choose a case study:",
        options=list(cases.keys())
    )
    
    return cases[selected_case]


def safe_eval(expr: str) -> float:
    """
    Safely evaluate mathematical expressions.
    
    Args:
        expr: Mathematical expression string
        
    Returns:
        Evaluated result as float
    """
    import ast
    import operator
    
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
    """
    Calculator function for ReACT agent.
    
    Args:
        expression: Mathematical expression to evaluate
        
    Returns:
        Result as float
    """
    return float(safe_eval(expression))


def get_observation_message(response: str) -> str:
    """
    Parse ReACT response and execute tool calls.
    
    Args:
        response: The THINK/ACT response from the model
        
    Returns:
        Observation message with results
    """
    from ast import literal_eval
    
    observation_message = None
    
    # Define regex patterns for tool calls
    SALES_DATA_REGEX = r"ACT:\nget_sales_data\(\)"
    WEATHER_REGEX = r"ACT:\ncall_weather_api\(date=\"(.*)\"\)"
    CALCULATOR_REGEX = r"ACT:\ncalculator\(expression=\"(.*)\"\)"
    FINAL_ANSWER_REGEX = r"ACT:\nfinal_answer\(amount_after_spike=\"(.*)\", causes=(.*), date=\"(.*)\", percentage_spike=\"(.*)\"\)"
    
    # Tool 1: get_sales_data
    if re.search(SALES_DATA_REGEX, response):
        sales_data = get_sales_data(products=["P005"])
        # Filter sales data to Product 5
        sales_data = [
            item for item in sales_data if item["product_name"] == "Product 5"
        ]
        observation_message = f"OBSERVE:\n{sales_data}"
    
    # Tool 2: call_weather_api
    elif re.search(WEATHER_REGEX, response):
        date = re.search(WEATHER_REGEX, response).groups()[0]
        weather_data = call_weather_api(date)
        observation_message = f"OBSERVE:\n{weather_data}"
    
    # Tool 3: calculator
    elif re.search(CALCULATOR_REGEX, response):
        expression = re.search(CALCULATOR_REGEX, response).groups()[0]
        observation_message = f"OBSERVE:\n{calculator(expression)}"
    
    # Tool 4: final_answer
    elif re.search(FINAL_ANSWER_REGEX, response):
        amount_after_spike, causes, date, percentage_spike = re.search(
            FINAL_ANSWER_REGEX, response
        ).groups()
        causes = literal_eval(causes)
        observation_message = f"OBSERVE:\namount_after_spike: {amount_after_spike}\ndate: {date}\npercentage_spike: {percentage_spike}\ncauses: {causes}"
    
    # Error case
    else:
        observation_message = "OBSERVE:\nInvalid tool call or tool not supported."
    
    return observation_message


def display_cot_analysis() -> None:
    """Display Chain-of-Thought analysis interface."""
    st.header("🔍 Demand Spike Detective - Chain of Thought Analysis")
    
    st.markdown("""
    This case demonstrates Chain-of-Thought prompting to analyze retail sales data 
    and identify the causes of demand spikes.
    """)
    
    # Load and display data
    sales_data = get_sales_data()
    promotions_data = get_promotions_data()
    weather_data = get_weather_data()
    competitor_data = get_competitor_pricing_data()
    
    # Create tabs for data visualization
    data_tab, analysis_tab = st.tabs(["📊 Data Overview", "🧠 CoT Analysis"])
    
    with data_tab:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Sales Data")
            sales_df = pd.DataFrame(sales_data)
            st.dataframe(sales_df.head(10))
            
            st.subheader("Promotions Calendar")
            promotions_df = pd.DataFrame(promotions_data)
            st.dataframe(promotions_df)
        
        with col2:
            st.subheader("Weather Data")
            weather_df = pd.DataFrame(weather_data)
            st.dataframe(weather_df)
            
            st.subheader("Competitor Pricing")
            competitor_df = pd.DataFrame(competitor_data)
            st.dataframe(competitor_df.head())
    
    with analysis_tab:
        st.subheader("Chain-of-Thought Prompt Configuration")
        
        # System prompt configuration
        system_prompt = st.text_area(
            "System Prompt:",
            value="""You are a meticulous Retail Demand Analyst.
Your task is to analyze provided sales data and promotion schedules to identify and explain significant sales spikes for specific SKUs.

Think step by step.""",
            height=100
        )
        
        # User prompt with data
        user_prompt_template = f"""
## INSTRUCTIONS:

Analyze the data provided below and hypothesize causes for any observed sales spikes.

Instructions:
* Find all sales spikes for each product
* For each product, identify the following:
    * Date of the sales spike
    * Amount of the sales spike and percentage increase
    * Possible causes of the sales spike according to the provided data
* Start with your analysis
* Conclude with the single largest spike according to the percentage increase with a short explanation for it.

## OUTPUT FORMAT:

STRUCTURED ANALYSIS:
[Structured Analysis]

LARGEST SPIKE:
```json
{{
    "date": "YYYY-MM-DD",
    "amount_before_increase": "X.XX",
    "amount_after_increase": "X.XX", 
    "percentage_increase": "X.XX%",
    "causes": [
        "Cause 1",
        "Cause 2",
        "Cause 3"
    ]
}}
```

## CONTEXT

Sales Data:
{sales_data}

Promotions Calendar:
{promotions_data}

Weather Data:
{weather_data}

Competitor Pricing Data:
{competitor_data}
"""
        
        st.text_area(
            "User Prompt (with data):",
            value=user_prompt_template,
            height=300,
            disabled=True
        )
        
        # Simulate analysis button
        if st.button("🔍 Run CoT Analysis", key="cot_analysis"):
            with st.spinner("Analyzing data with Chain-of-Thought..."):
                # Simulated response for demo
                st.success("Analysis Complete!")
                
                st.subheader("Chain-of-Thought Response:")
                sample_response = """
**STRUCTURED ANALYSIS:**

Looking at the sales data systematically:

**Product 1 Analysis:**
- Baseline quantity: ~255 units (Jan 10)
- Notable increase on Jan 12: 310 units (+21.6% increase)
- Remained elevated through Jan 15: 301 units

**Product 2 Analysis:**
- Relatively stable around 65-86 units
- No significant spikes observed

**Product 3 Analysis:**
- Baseline around 79-90 units
- Moderate increase on Jan 12: 108 units (+20% from previous day)

**Product 4 Analysis:**
- Generally stable around 130-175 units
- Some variation but no dramatic spikes

**Product 5 Analysis:**
- Baseline around 96-114 units (Jan 10-11)
- **MASSIVE SPIKE on Jan 12: 342 units** 
- This represents a 200% increase from Jan 11 (114 units)
- Returned to normal levels afterward (~100-125 units)

**Cross-referencing with external factors:**

*Weather (Jan 12):*
- Heavy rain with flood warning
- Temperature: 41.1°F (5.1°C)
- May have driven indoor shopping behavior

*Promotions:*
- Weekend Special (10% off Product 2) started Jan 12
- Could have driven general store traffic

*Competitor Activity:*
- Competitor A had a 17% discount on Product 5 on Jan 12
- May have increased category awareness/demand

**LARGEST SPIKE:**
```json
{
    "date": "2024-01-12",
    "amount_before_increase": "114",
    "amount_after_increase": "342",
    "percentage_increase": "200.00%",
    "causes": [
        "Heavy rain and flood warning drove customers to shop indoors",
        "Competitor A's 17% discount on Product 5 increased category awareness",
        "Weekend Special promotion started, driving overall store traffic"
    ]
}
```
"""
                st.markdown(sample_response)


def display_react_analysis() -> None:
    """Display ReACT analysis interface."""
    st.header("🔄 Demand Spike Detective - ReACT Agent")
    
    st.markdown("""
    This case demonstrates ReACT (Reason + Act) prompting with tool usage.
    The agent can Think, Act (use tools), and Observe results iteratively.
    """)
    
    # Tool definitions
    st.subheader("🛠️ Available Tools")
    
    tools_info = {
        "calculator(expression)": "Perform arithmetic calculations",
        "get_sales_data()": "Retrieve sales data for analysis",
        "call_weather_api(date)": "Get weather data for specific date",
        "final_answer(...)": "Return structured final analysis"
    }
    
    for tool, description in tools_info.items():
        st.code(f"{tool}: {description}")
    
    # ReACT System Prompt
    st.subheader("🤖 ReACT System Prompt")
    
    react_system_prompt = """
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
* `get_sales_data()`: Get the sales data  
* `call_weather_api(date: str)`: Get weather data for a specific date
* `final_answer(amount_after_spike: str, causes: list[str], date: str, percentage_spike: str)`: Return the final answer
"""
    
    st.code(react_system_prompt, language="text")
    
    # Interactive ReACT Demo
    st.subheader("🎯 Interactive ReACT Demo")
    
    if st.button("🚀 Start ReACT Analysis", key="react_start"):
        st.markdown("### ReACT Execution Steps")
        
        # Step 1
        with st.expander("Step 1: Initial Thinking & Action", expanded=True):
            st.markdown("**Agent Response:**")
            step1_response = """
THINK:
* I need to find the largest sales spike according to percentage increase.
* First, I should get the sales data to analyze all products and their quantities over time.
* Once I have the sales data, I can identify spikes and calculate percentage increases.
* Tool call needed: Get the sales data first.

ACT:
get_sales_data()
"""
            st.code(step1_response)
            
            # Simulated observation
            st.markdown("**Observation:**")
            observation1 = get_observation_message(step1_response)
            st.code(observation1)
        
        # Step 2  
        with st.expander("Step 2: Calculate Percentage Increases", expanded=False):
            st.markdown("**Agent Response:**")
            step2_response = """
THINK:
* Looking at the sales data, I can see Product 5 had quantities: 114 on Jan 11, then 342 on Jan 12.
* This appears to be the largest jump. Let me calculate the percentage increase.
* Percentage increase = ((342 - 114) / 114) * 100
* I need to use the calculator to compute this precisely.

ACT:
calculator(expression="((342 - 114) / 114) * 100")
"""
            st.code(step2_response)
            
            observation2 = get_observation_message(step2_response)
            st.code(f"**Observation:**\n{observation2}")
        
        # Step 3
        with st.expander("Step 3: Investigate Weather Conditions", expanded=False):
            st.markdown("**Agent Response:**") 
            step3_response = """
THINK:
* The spike occurred on 2024-01-12 with a 200% increase - this is significant!
* I should investigate what external factors might have caused this spike.
* Weather conditions could be a contributing factor. Let me check the weather for Jan 12.

ACT:
call_weather_api(date="2024-01-12")
"""
            st.code(step3_response)
            
            observation3 = get_observation_message(step3_response)
            st.code(f"**Observation:**\n{observation3}")
        
        # Step 4 - Final Answer
        with st.expander("Step 4: Final Analysis", expanded=False):
            st.markdown("**Agent Response:**")
            step4_response = """
THINK:
* I've identified the largest spike: Product 5 on 2024-01-12 with 200% increase (114 → 342 units)
* Weather data shows heavy rain and flood warning on that date
* This likely drove customers indoors and increased demand for Product 5
* I have enough information to provide the final answer.

ACT:
final_answer(amount_after_spike="342", causes=["Heavy rain and flood warning drove customers to shop indoors", "Weather conditions created increased demand for indoor products", "Extreme weather event concentrated shopping activity"], date="2024-01-12", percentage_spike="200.00%")
"""
            st.code(step4_response)
            
            observation4 = get_observation_message(step4_response)
            st.success("**Final Result:**")
            st.code(observation4)


def display_prompt_refinement() -> None:
    """Display Prompt Instruction Refinement interface."""
    st.header("✨ Prompt Instruction Refinement")
    
    st.markdown("""
    This case demonstrates how to systematically improve prompts through iterative refinement.
    We'll explore different approaches to email analysis and sentiment analysis tasks.
    """)
    
    # Case selection
    refinement_case = st.selectbox(
        "Select refinement scenario:",
        ["Email Analysis", "Customer Sentiment Analysis", "Professional Email Composition"]
    )
    
    if refinement_case == "Email Analysis":
        display_email_analysis_refinement()
    elif refinement_case == "Customer Sentiment Analysis":
        display_sentiment_analysis_refinement()
    else:
        display_email_composition_refinement()


def display_email_analysis_refinement() -> None:
    """Display email analysis prompt refinement."""
    st.subheader("📧 Email Analysis Prompt Refinement")
    
    # Get sample email data
    emails = get_email_data()
    templates = get_prompt_templates()
    
    # Email selection
    selected_email_id = st.selectbox(
        "Select email to analyze:",
        options=[email["id"] for email in emails],
        format_func=lambda x: f"Email {x}: {[e for e in emails if e['id']==x][0]['subject'][:50]}..."
    )
    
    selected_email = [email for email in emails if email["id"] == selected_email_id][0]
    
    # Display selected email
    with st.expander("📧 Selected Email Content", expanded=True):
        st.markdown(f"**Subject:** {selected_email['subject']}")
        st.markdown(f"**From:** {selected_email['from']}")
        st.markdown(f"**To:** {selected_email['to']}")
        st.markdown(f"**Date:** {selected_email['date']}")
        st.markdown(f"**Priority:** {selected_email['priority']}")
        st.markdown(f"**Content:**")
        st.text(selected_email['content'])
    
    # Prompt refinement comparison
    st.subheader("🔄 Prompt Refinement Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 Basic Prompt")
        basic_prompt = templates["basic_email_summary"]
        st.code(basic_prompt)
        
        st.markdown("**Simulated Response:**")
        basic_response = f"This email is about {selected_email['subject'].lower()}. It was sent by {selected_email['from']} regarding the mentioned topic."
        st.info(basic_response)
        
        st.markdown("**Issues with Basic Prompt:**")
        st.markdown("""
        - Too generic and vague
        - Doesn't extract key information
        - No structured output
        - Misses actionable insights
        """)
    
    with col2:
        st.markdown("### ⚡ Refined Prompt")
        refined_prompt = templates["detailed_email_analysis"]
        st.code(refined_prompt)
        
        st.markdown("**Simulated Response:**")
        
        # Generate contextual response based on email content
        if selected_email['priority'] == 'critical':
            refined_response = f"""
**1. Summary:** Security alert requiring immediate password reset due to suspicious login activity.

**2. Priority Level:** CRITICAL - Requires immediate action within 1 hour.

**3. Key Action Items:**
- Reset password immediately using provided link
- Contact IT security if unauthorized access suspected
- Review recent account activity

**4. Recommended Next Steps:**
- Execute password reset now
- Enable 2FA if not already active
- Monitor account for further suspicious activity
- Update password manager with new credentials
"""
        elif selected_email['priority'] == 'high':
            refined_response = f"""
**1. Summary:** {selected_email['subject']} requires preparation and attendance for tomorrow's meeting.

**2. Priority Level:** HIGH - Time-sensitive with tomorrow deadline.

**3. Key Action Items:**
- Review attached budget spreadsheet before 2 PM meeting
- Prepare input on marketing overage discussion
- Consider proposals for training budget reallocation

**4. Recommended Next Steps:**
- Block calendar time today for document review
- Prepare questions and suggestions for meeting
- Gather supporting data for budget discussions
"""
        else:
            refined_response = f"""
**1. Summary:** {selected_email['subject']} - informal/informational communication.

**2. Priority Level:** LOW - No urgent action required.

**3. Key Action Items:**
- Respond if RSVP requested
- Note event details if relevant

**4. Recommended Next Steps:**
- Add to calendar if attending
- Respond by specified deadline if applicable
"""
        
        st.success(refined_response)
        
        st.markdown("**Improvements in Refined Prompt:**")
        st.markdown("""
        - Structured analysis format
        - Clear priority assessment
        - Actionable item extraction
        - Specific next steps
        - Contextual understanding
        """)


def display_sentiment_analysis_refinement() -> None:
    """Display sentiment analysis prompt refinement."""
    st.subheader("💭 Customer Sentiment Analysis Refinement")
    
    # Get customer feedback data
    feedback_data = get_customer_feedback_data()
    templates = get_prompt_templates()
    
    # Feedback selection
    selected_feedback_id = st.selectbox(
        "Select customer feedback:",
        options=[f["id"] for f in feedback_data],
        format_func=lambda x: f"Feedback {x} - {[f for f in feedback_data if f['id']==x][0]['customer_name']} ({[f for f in feedback_data if f['id']==x][0]['rating']}/5 stars)"
    )
    
    selected_feedback = [f for f in feedback_data if f["id"] == selected_feedback_id][0]
    
    # Display selected feedback
    with st.expander("💬 Selected Customer Feedback", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rating", f"{selected_feedback['rating']}/5")
        with col2:
            st.metric("Product", selected_feedback['product'])
        with col3:
            st.metric("Channel", selected_feedback['channel'])
        
        st.markdown(f"**Customer:** {selected_feedback['customer_name']}")
        st.markdown(f"**Date:** {selected_feedback['date']}")
        st.markdown(f"**Feedback:**")
        st.text(selected_feedback['feedback'])
    
    # Refinement comparison
    st.subheader("🔄 Sentiment Analysis Refinement")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 Basic Sentiment Prompt")
        st.code(templates["sentiment_analysis_basic"])
        
        # Simple sentiment based on rating
        if selected_feedback['rating'] >= 4:
            basic_sentiment = "Positive"
        elif selected_feedback['rating'] <= 2:
            basic_sentiment = "Negative"
        else:
            basic_sentiment = "Neutral"
        
        st.info(f"**Response:** {basic_sentiment}")
        
        st.markdown("**Limitations:**")
        st.markdown("""
        - One-word response
        - No nuance or details
        - Misses business insights
        - No actionable recommendations
        """)
    
    with col2:
        st.markdown("### ⚡ Detailed Sentiment Analysis")
        st.code(templates["sentiment_analysis_detailed"])
        
        # Generate detailed analysis based on feedback
        rating = selected_feedback['rating']
        feedback_text = selected_feedback['feedback'].lower()
        
        if rating >= 4:
            sentiment = "Positive"
            score = rating * 2
            if "outstanding" in feedback_text or "fantastic" in feedback_text:
                themes = ["Product Quality", "Customer Service", "User Experience"]
                issues_praise = ["Exceeded expectations", "Outstanding service", "High recommendation likelihood"]
                actions = ["Leverage positive feedback for marketing", "Identify success factors to replicate", "Follow up for testimonials"]
            else:
                themes = ["Product Satisfaction", "Overall Experience"]
                issues_praise = ["Product works as expected", "Satisfied with purchase"]
                actions = ["Monitor for continued satisfaction", "Encourage reviews"]
        elif rating <= 2:
            sentiment = "Negative"
            score = rating * 2
            if "terrible" in feedback_text or "disappointed" in feedback_text:
                themes = ["Product Quality Issues", "Customer Service Problems", "Return Process"]
                issues_praise = ["Product failure", "Poor customer service", "Complicated return process"]
                actions = ["Immediate customer service follow-up", "Product quality review", "Return process improvement"]
            else:
                themes = ["Product Issues", "Service Concerns"]
                issues_praise = ["Product problems", "Service dissatisfaction"]
                actions = ["Customer retention outreach", "Issue resolution priority"]
        else:
            sentiment = "Neutral"
            score = rating * 2
            themes = ["Average Experience", "Mixed Feedback"]
            issues_praise = ["Meets basic expectations", "Room for improvement"]
            actions = ["Identify improvement opportunities", "Gather more detailed feedback"]
        
        detailed_response = f"""
**1. Overall Sentiment:** {sentiment}
**2. Sentiment Score:** {score}/10
**3. Key Themes:** {', '.join(themes)}
**4. Specific Points:** {', '.join(issues_praise)}
**5. Business Actions:**
{chr(10).join([f'   • {action}' for action in actions])}
"""
        
        st.success(detailed_response)
        
        st.markdown("**Improvements:**")
        st.markdown("""
        - Quantified sentiment scoring
        - Thematic analysis
        - Specific issue identification  
        - Actionable business recommendations
        - Structured, comprehensive output
        """)


def display_email_composition_refinement() -> None:
    """Display email composition prompt refinement."""
    st.subheader("✉️ Professional Email Composition")
    
    st.markdown("This scenario demonstrates refining prompts for email composition tasks.")
    
    # Context input
    email_context = st.text_area(
        "Email Context:",
        value="A client is asking about the status of their project deliverables. The project is running 2 days behind schedule due to unexpected technical challenges. We need to inform them professionally while maintaining confidence.",
        height=100
    )
    
    templates = get_prompt_templates()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 Basic Composition Prompt")
        basic_prompt = "Write a professional email response."
        st.code(basic_prompt)
        
        st.markdown("**Simulated Response:**")
        basic_email = """
Dear Client,

Thank you for your email. I wanted to update you on your project status.

Best regards,
Team
"""
        st.text(basic_email)
        
        st.markdown("**Issues:**")
        st.markdown("""
        - Too generic
        - Lacks specific details
        - No clear structure
        - Misses key context
        - Unprofessional brevity
        """)
    
    with col2:
        st.markdown("### ⚡ Refined Composition Prompt")
        st.code(templates["professional_email_composer"])
        
        st.markdown("**Simulated Response:**")
        refined_email = """
Subject: Project Update - Revised Timeline

Dear [Client Name],

I hope this email finds you well. I'm writing to provide you with an important update regarding your project deliverables.

We've encountered some unexpected technical challenges that require additional development time to ensure the highest quality output. While this means we're running approximately 2 days behind our original timeline, I want to assure you that our team is working diligently to minimize any further delays.

Here's what we're doing to address this:
• Our senior developers are prioritizing your project
• We've implemented additional quality checks
• We're maintaining daily progress reviews

The revised delivery date is now [specific date], and I'm confident we can meet this updated timeline while delivering the exceptional results you expect.

I apologize for any inconvenience this may cause and appreciate your understanding. Please feel free to reach out with any questions or concerns.

Best regards,
[Your Name]
Project Manager
"""
        st.text(refined_email)
        
        st.markdown("**Improvements:**")
        st.markdown("""
        - Professional structure and tone
        - Addresses specific situation
        - Provides clear explanations
        - Includes action items
        - Maintains client confidence
        - Appropriate length and detail
        """)
    
    # Interactive refinement exercise
    st.subheader("🎯 Try Your Own Refinement")
    
    user_context = st.text_area(
        "Enter your email scenario:",
        placeholder="Describe the situation that requires an email response..."
    )
    
    user_prompt = st.text_area(
        "Write your refined prompt:",
        placeholder="Create a detailed prompt that would generate a high-quality email response..."
    )
    
    if st.button("💡 Analyze Your Prompt") and user_prompt and user_context:
        st.markdown("### Prompt Analysis")
        
        # Simple analysis of user's prompt
        prompt_lower = user_prompt.lower()
        analysis_points = []
        
        if "tone" in prompt_lower:
            analysis_points.append("✅ Specifies tone requirements")
        else:
            analysis_points.append("⚠️ Consider specifying tone (professional, friendly, etc.)")
        
        if "structure" in prompt_lower or "format" in prompt_lower:
            analysis_points.append("✅ Addresses structure/format")
        else:
            analysis_points.append("⚠️ Consider specifying email structure")
        
        if "word" in prompt_lower or "length" in prompt_lower:
            analysis_points.append("✅ Includes length constraints")
        else:
            analysis_points.append("⚠️ Consider adding length guidelines")
        
        if "action" in prompt_lower or "call" in prompt_lower:
            analysis_points.append("✅ Mentions call-to-action")
        else:
            analysis_points.append("⚠️ Consider including call-to-action requirements")
        
        for point in analysis_points:
            if "✅" in point:
                st.success(point)
            else:
                st.warning(point)


def main() -> None:
    """Main application function."""
    setup_page_config()
    
    st.title("🧠 Chain-of-Thought & ReACT Prompting Demo")
    st.markdown("Interactive demonstrations of advanced prompting techniques")
    
    # Get selected case from sidebar
    selected_case = display_sidebar()
    
    # Display appropriate case
    if selected_case == "cot_analysis":
        display_cot_analysis()
    elif selected_case == "react_analysis":
        display_react_analysis()
    elif selected_case == "prompt_refinement":
        display_prompt_refinement()
    
    # Footer
    st.markdown("---")
    st.markdown("💡 **Tip:** Try different prompts and see how the structure affects the output quality!")


if __name__ == "__main__":
    main()