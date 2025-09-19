# CoT and ReACT Prompting Application - Implementation Guide

## Overview

This application demonstrates Chain-of-Thought (CoT) and ReACT (Reasoning + Acting) prompting techniques using Python, Pydantic for data validation, and Streamlit for the user interface. The application focuses on analyzing retail sales data to identify and explain demand spikes.

## Features

### 🧠 Chain-of-Thought Analysis
- Step-by-step reasoning for complex analysis
- Configurable prompting strategies
- Structured output formatting
- Interactive prompt engineering

### 🔄 ReACT Analysis  
- Think-Act-Observe reasoning pattern
- Tool integration and usage
- Dynamic decision making
- Real-time execution tracking

### 📊 Data Explorer
- Interactive data visualization
- Sales trend analysis
- Weather correlation insights
- Promotion timeline tracking

### 🛠️ Built with Best Practices
- Pydantic models for data validation
- Type hints throughout
- Clean separation of concerns
- Comprehensive error handling

## Installation & Setup

### 1. Prerequisites
- Python 3.8 or higher
- pip package manager
- Git (optional)

### 2. Clone or Download
```bash
# Option 1: Clone repository (if using git)
git clone <your-repo-url>
cd cot-react-prompting-app

# Option 2: Create new directory and copy files
mkdir cot-react-prompting-app
cd cot-react-prompting-app
```

### 3. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Environment Configuration
Create a `.env` file in the project root:

```env
# OpenAI API Configuration (if using real API)
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# Alternative endpoints (uncomment if needed)
# OPENAI_BASE_URL=https://openai.vocareum.com/v1

# App Configuration
APP_TITLE=CoT and ReACT Prompting Application
MAX_REACT_ITERATIONS=10
DEFAULT_TEMPERATURE=0.7
```

### 6. Project Structure
```
cot-react-prompting-app/
├── app.py                 # Main Streamlit application
├── config.py              # Configuration and settings
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
├── README.md             # Project documentation
└── data/                 # Sample data directory (optional)
    ├── sales_data.json
    ├── weather_data.json
    └── promotions_data.json
```

## Running the Application

### 1. Start the Streamlit App
```bash
streamlit run app.py
```

### 2. Access the Application
- Open your web browser
- Navigate to `http://localhost:8501`
- The application should load automatically

### 3. Navigate the Interface
- **Overview**: Introduction to CoT and ReACT techniques
- **Chain-of-Thought Analysis**: Interactive CoT prompting
- **ReACT Analysis**: Tool-based reasoning simulation
- **Data Explorer**: Examine and visualize sample data

## Usage Instructions

### Chain-of-Thought Analysis

1. **Configure Analysis Settings**
   - Toggle "Use Explicit CoT" to include/exclude step-by-step prompting
   - Select the AI model (simulated in this demo)
   - Choose output format preference

2. **Customize System Prompt**
   - Define the AI's role and capabilities
   - Include specific instructions or constraints
   - Add domain expertise context

3. **Enter Analysis Query**
   - Describe the analysis task clearly
   - Specify desired output format
   - Include any specific requirements

4. **Run Analysis**
   - Click "Run CoT Analysis"
   - View step-by-step reasoning process
   - Examine final results and JSON output

### ReACT Analysis

1. **Configure ReACT Settings**
   - Set maximum iterations (1-20)
   - Choose model for analysis
   - Toggle intermediate step display
   - Enable/disable auto-continuation

2. **Define Task**
   - Describe the task for the ReACT agent
   - Ensure task can be completed with available tools
   - Be specific about desired outcomes

3. **Execute ReACT Loop**
   - Click "Start ReACT Analysis"
   - Observe Think-Act-Observe cycles
   - Monitor progress and tool usage
   - Review final results

### Data Explorer

1. **Select Data Type**
   - Choose from Sales, Promotions, or Weather data
   - View raw data tables
   - Examine data structure and patterns

2. **Analyze Visualizations**
   - Interactive charts and graphs
   - Trend analysis and spike identification
   - Correlation insights

3. **Export Insights**
   - Use findings to inform prompt engineering
   - Identify patterns for analysis focus

## Customization Options

### 1. Extending Data Sources
```python
# Add new data sources in app.py
@st.cache_data
def get_custom_data() -> List[Dict[str, Any]]:
    """Add your custom data source here."""
    return your_data

# Update data explorer to include new sources
def show_data_explorer():
    data_type = st.selectbox(
        "Select Data Type",
        ["Sales Data", "Promotions Data", "Weather Data", "Custom Data"]
    )
```

### 2. Adding New Tools for ReACT
```python
# Extend the simulation function
def simulate_react_step(step: int, context: str) -> Dict[str, str]:
    # Add new tool logic
    if "new_tool_call" in context:
        return {
            "think": "I need to use the new tool...",
            "act": "new_tool(parameters)",
            "observe": "Tool result here"
        }
```

### 3. Custom Prompt Templates
```python
# In config.py - PromptTemplates class
CUSTOM_SYSTEM_PROMPT = """Your custom system prompt here..."""

CUSTOM_USER_QUERY = """Your custom analysis query..."""
```

### 4. UI Customization
```python
# Modify Streamlit configuration
st.set_page_config(
    page_title="Your Custom Title",
    page_icon="🔍",  # Your preferred icon
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-header {
        color: #1f77b4;
        font-size: 2.5rem;
    }
</style>
""", unsafe_allow_html=True)
```

## API Integration (Optional)

To integrate with actual OpenAI API:

### 1. Install OpenAI Client
```bash
pip install openai
```

### 2. Replace Simulation Functions
```python
from openai import OpenAI

def get_completion(messages, model, temperature=0.7):
    """Real OpenAI API call."""
    client = OpenAI()
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    
    return response.choices[0].message.content
```

### 3. Update Analysis Functions
```python
def real_cot_analysis(request: ChainOfThoughtRequest) -> str:
    """Real CoT analysis using OpenAI API."""
    messages = [
        {"role": "system", "content": request.system_prompt},
        {"role": "user", "content": request.user_prompt}
    ]
    
    return get_completion(messages, request.model)
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**
   - Ensure virtual environment is activated
   - Install all requirements: `pip install -r requirements.txt`

2. **Streamlit Port Issues**
   - Use different port: `streamlit run app.py --server.port 8502`
   - Check for conflicting applications

3. **Data Loading Errors**
   - Verify sample data format
   - Check file permissions
   - Ensure proper JSON/CSV structure

4. **API Connection Issues**
   - Verify API key in .env file
   - Check network connectivity
   - Validate API endpoint URL

### Performance Optimization

1. **Caching**
   - Use `@st.cache_data` for expensive operations
   - Cache API responses when possible
   - Store processed data efficiently

2. **Memory Management**
   - Limit data size for large datasets
   - Use pagination for extensive results
   - Clear unused session state variables

3. **UI Responsiveness**
   - Use `st.spinner()` for long operations
   - Implement progress bars for multi-step processes
   - Optimize chart rendering with sampling

## Development Guidelines

### Code Style
- Follow PEP 8 conventions
- Use type hints consistently
- Document functions with docstrings
- Implement error handling

### Testing
```python
# Example test structure
def test_sales_data_validation():
    """Test sales data model validation."""
    data = SalesDataPoint(
        date=date(2024, 1, 10),
        product_id="P001",
        product_name="Product 1",
        quantity=100,
        revenue=1000.0
    )
    assert data.quantity == 100
    assert data.revenue == 1000.0
```

### Contributing
1. Follow existing code patterns
2. Add type hints to new functions
3. Update documentation for changes
4. Test thoroughly before deployment

## Advanced Features

### Custom Analysis Workflows
- Create analysis pipelines
- Chain multiple prompting techniques
- Implement result validation

### Integration Capabilities
- Database connections
- External API integration
- File import/export functionality

### Scalability Considerations
- Async processing for large datasets
- Batch analysis capabilities
- Result caching strategies

## Support and Resources

### Documentation
- Pydantic: https://docs.pydantic.dev/
- Streamlit: https://docs.streamlit.io/
- OpenAI API: https://platform.openai.com/docs

### Community
- Streamlit Community: https://discuss.streamlit.io/
- Pydantic GitHub: https://github.com/pydantic/pydantic

This implementation guide provides a comprehensive foundation for building and extending the CoT and ReACT prompting application. The modular design allows for easy customization and integration with real AI services.