import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class OpenAIModels(str, Enum):
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_41_MINI = "gpt-4.1-mini"
    GPT_41_NANO = "gpt-4.1-nano"


def get_sales_data(products: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Get sales data for analysis. Optionally filter by product IDs.
    
    Args:
        products: Optional list of product IDs to filter by
        
    Returns:
        List of sales data dictionaries
    """
    data = [
        {
            "date": datetime.date(2024, 1, 10),
            "product_id": "P001",
            "product_name": "Product 1",
            "quantity": 255,
            "revenue": 15547.35,
        },
        {
            "date": datetime.date(2024, 1, 10),
            "product_id": "P002",
            "product_name": "Product 2",
            "quantity": 65,
            "revenue": 2297.1,
        },
        {
            "date": datetime.date(2024, 1, 10),
            "product_id": "P003",
            "product_name": "Product 3",
            "quantity": 90,
            "revenue": 7301.7,
        },
        {
            "date": datetime.date(2024, 1, 10),
            "product_id": "P004",
            "product_name": "Product 4",
            "quantity": 171,
            "revenue": 8296.92,
        },
        {
            "date": datetime.date(2024, 1, 10),
            "product_id": "P005",
            "product_name": "Product 5",
            "quantity": 96,
            "revenue": 2587.2,
        },
        {
            "date": datetime.date(2024, 1, 11),
            "product_id": "P001",
            "product_name": "Product 1",
            "quantity": 235,
            "revenue": 14327.95,
        },
        {
            "date": datetime.date(2024, 1, 11),
            "product_id": "P002",
            "product_name": "Product 2",
            "quantity": 86,
            "revenue": 3039.24,
        },
        {
            "date": datetime.date(2024, 1, 11),
            "product_id": "P003",
            "product_name": "Product 3",
            "quantity": 79,
            "revenue": 6409.27,
        },
        {
            "date": datetime.date(2024, 1, 11),
            "product_id": "P004",
            "product_name": "Product 4",
            "quantity": 145,
            "revenue": 7035.4,
        },
        {
            "date": datetime.date(2024, 1, 11),
            "product_id": "P005",
            "product_name": "Product 5",
            "quantity": 114,
            "revenue": 3072.3,
        },
        {
            "date": datetime.date(2024, 1, 12),
            "product_id": "P001",
            "product_name": "Product 1",
            "quantity": 310,
            "revenue": 18900.7,
        },
        {
            "date": datetime.date(2024, 1, 12),
            "product_id": "P002",
            "product_name": "Product 2",
            "quantity": 80,
            "revenue": 2827.2,
        },
        {
            "date": datetime.date(2024, 1, 12),
            "product_id": "P003",
            "product_name": "Product 3",
            "quantity": 108,
            "revenue": 8762.04,
        },
        {
            "date": datetime.date(2024, 1, 12),
            "product_id": "P004",
            "product_name": "Product 4",
            "quantity": 143,
            "revenue": 6938.36,
        },
        {
            "date": datetime.date(2024, 1, 12),
            "product_id": "P005",
            "product_name": "Product 5",
            "quantity": 342,
            "revenue": 9216.9,
        },
        {
            "date": datetime.date(2024, 1, 13),
            "product_id": "P001",
            "product_name": "Product 1",
            "quantity": 302,
            "revenue": 18412.94,
        },
        {
            "date": datetime.date(2024, 1, 13),
            "product_id": "P002",
            "product_name": "Product 2",
            "quantity": 68,
            "revenue": 2403.12,
        },
        {
            "date": datetime.date(2024, 1, 13),
            "product_id": "P003",
            "product_name": "Product 3",
            "quantity": 96,
            "revenue": 7788.48,
        },
        {
            "date": datetime.date(2024, 1, 13),
            "product_id": "P004",
            "product_name": "Product 4",
            "quantity": 130,
            "revenue": 6307.6,
        },
        {
            "date": datetime.date(2024, 1, 13),
            "product_id": "P005",
            "product_name": "Product 5",
            "quantity": 103,
            "revenue": 2775.85,
        },
        {
            "date": datetime.date(2024, 1, 14),
            "product_id": "P001",
            "product_name": "Product 1",
            "quantity": 305,
            "revenue": 18595.85,
        },
        {
            "date": datetime.date(2024, 1, 14),
            "product_id": "P002",
            "product_name": "Product 2",
            "quantity": 84,
            "revenue": 2968.56,
        },
        {
            "date": datetime.date(2024, 1, 14),
            "product_id": "P003",
            "product_name": "Product 3",
            "quantity": 99,
            "revenue": 8031.87,
        },
        {
            "date": datetime.date(2024, 1, 14),
            "product_id": "P004",
            "product_name": "Product 4",
            "quantity": 167,
            "revenue": 8102.84,
        },
        {
            "date": datetime.date(2024, 1, 14),
            "product_id": "P005",
            "product_name": "Product 5",
            "quantity": 104,
            "revenue": 2802.8,
        },
        {
            "date": datetime.date(2024, 1, 15),
            "product_id": "P001",
            "product_name": "Product 1",
            "quantity": 301,
            "revenue": 18351.97,
        },
        {
            "date": datetime.date(2024, 1, 15),
            "product_id": "P002",
            "product_name": "Product 2",
            "quantity": 73,
            "revenue": 2579.82,
        },
        {
            "date": datetime.date(2024, 1, 15),
            "product_id": "P003",
            "product_name": "Product 3",
            "quantity": 89,
            "revenue": 7220.57,
        },
        {
            "date": datetime.date(2024, 1, 15),
            "product_id": "P004",
            "product_name": "Product 4",
            "quantity": 126,
            "revenue": 6113.52,
        },
        {
            "date": datetime.date(2024, 1, 15),
            "product_id": "P005",
            "product_name": "Product 5",
            "quantity": 100,
            "revenue": 2695.0,
        },
        {
            "date": datetime.date(2024, 1, 16),
            "product_id": "P001",
            "product_name": "Product 1",
            "quantity": 226,
            "revenue": 13779.22,
        },
        {
            "date": datetime.date(2024, 1, 16),
            "product_id": "P002",
            "product_name": "Product 2",
            "quantity": 80,
            "revenue": 2827.2,
        },
        {
            "date": datetime.date(2024, 1, 16),
            "product_id": "P003",
            "product_name": "Product 3",
            "quantity": 83,
            "revenue": 6733.79,
        },
        {
            "date": datetime.date(2024, 1, 16),
            "product_id": "P004",
            "product_name": "Product 4",
            "quantity": 175,
            "revenue": 8491.0,
        },
        {
            "date": datetime.date(2024, 1, 16),
            "product_id": "P005",
            "product_name": "Product 5",
            "quantity": 125,
            "revenue": 3368.75,
        },
    ]
    if products:
        return [item for item in data if item["product_id"] in products]
    return data


def get_promotions_data() -> List[Dict[str, Any]]:
    """Get promotional campaign data."""
    data = [
        {
            "promotion_id": "PROMO001",
            "name": "Weekend Special",
            "discount": "10% off",
            "products": ["P002"],
            "start_date": datetime.date(2024, 1, 12),
            "end_date": datetime.date(2024, 1, 14),
        },
        {
            "promotion_id": "PROMO002",
            "name": "Flash Sale",
            "discount": "15% off",
            "products": ["P001", "P003", "P005"],
            "start_date": datetime.date(2024, 1, 15),
            "end_date": datetime.date(2024, 1, 16),
        },
    ]
    return data


def get_weather_data() -> List[Dict[str, Any]]:
    """Get weather data for analysis."""
    data = [
        {
            "date": "2024-01-10",
            "temperature": {"fahrenheit": 23.4, "celsius": -4.8},
            "conditions": {
                "main": "Clear",
                "precipitation": "None",
                "precipitation_amount": 0,
                "special_event": None,
            },
        },
        {
            "date": "2024-01-11",
            "temperature": {"fahrenheit": 39.3, "celsius": 4.1},
            "conditions": {
                "main": "Clear",
                "precipitation": "None",
                "precipitation_amount": 0,
                "special_event": None,
            },
        },
        {
            "date": "2024-01-12",
            "temperature": {"fahrenheit": 41.1, "celsius": 5.1},
            "conditions": {
                "main": "Heavy Rain",
                "precipitation": "Heavy Rain",
                "precipitation_amount": 2.7,
                "special_event": "Flood Warning",
            },
        },
        {
            "date": "2024-01-13",
            "temperature": {"fahrenheit": 27.2, "celsius": -2.6},
            "conditions": {
                "main": "Clear",
                "precipitation": "None",
                "precipitation_amount": 0,
                "special_event": None,
            },
        },
        {
            "date": "2024-01-14",
            "temperature": {"fahrenheit": 22.9, "celsius": -5.1},
            "conditions": {
                "main": "Clear",
                "precipitation": "None",
                "precipitation_amount": 0,
                "special_event": None,
            },
        },
        {
            "date": "2024-01-15",
            "temperature": {"fahrenheit": 33.2, "celsius": 0.7},
            "conditions": {
                "main": "Clear",
                "precipitation": "None",
                "precipitation_amount": 0,
                "special_event": "High Winds",
            },
        },
        {
            "date": "2024-01-16",
            "temperature": {"fahrenheit": 23.3, "celsius": -4.8},
            "conditions": {
                "main": "Clear",
                "precipitation": "None",
                "precipitation_amount": 0,
                "special_event": None,
            },
        },
    ]
    return data


def get_competitor_pricing_data() -> List[Dict[str, Any]]:
    """Get competitor pricing data for analysis."""
    data = [
        {
            "product": "Product 1",
            "date": "2024-01-10",
            "our_price": 60.97,
            "competitor_sales": {},
            "competitor_a_price": 56.88,
            "competitor_b_price": 62.23,
            "competitor_c_price": 51.8,
        },
        {
            "product": "Product 1",
            "date": "2024-01-11",
            "our_price": 60.97,
            "competitor_sales": {},
            "competitor_a_price": 59.65,
            "competitor_b_price": 72.47,
            "competitor_c_price": 72.5,
        },
        {
            "product": "Product 1",
            "date": "2024-01-12",
            "our_price": 60.97,
            "competitor_sales": {
                "CompetitorB": {
                    "original_price": 69.24,
                    "sale_price": 50.55,
                    "discount_percentage": 27,
                },
                "CompetitorC": {
                    "original_price": 49.92,
                    "sale_price": 39.44,
                    "discount_percentage": 21,
                },
            },
            "competitor_a_price": 65.4,
            "competitor_b_price": 50.55,
            "competitor_c_price": 39.44,
        },
        {
            "product": "Product 5",
            "date": "2024-01-10",
            "our_price": 26.95,
            "competitor_sales": {},
            "competitor_a_price": 31.99,
            "competitor_b_price": 30.96,
            "competitor_c_price": 26.98,
        },
        {
            "product": "Product 5",
            "date": "2024-01-11",
            "our_price": 26.95,
            "competitor_sales": {},
            "competitor_a_price": 30.29,
            "competitor_b_price": 26.36,
            "competitor_c_price": 32.28,
        },
        {
            "product": "Product 5",
            "date": "2024-01-12",
            "our_price": 26.95,
            "competitor_sales": {
                "CompetitorA": {
                    "original_price": 23.8,
                    "sale_price": 19.75,
                    "discount_percentage": 17,
                }
            },
            "competitor_a_price": 19.75,
            "competitor_b_price": 25.5,
            "competitor_c_price": 31.17,
        },
    ]
    return data


def call_weather_api(date: str) -> Dict[str, Any]:
    """
    Simulated weather API call for specific date.
    
    Args:
        date: Date string in YYYY-MM-DD format
        
    Returns:
        Weather data dictionary for the specified date
    """
    data = get_weather_data()
    data_dict = {item["date"]: item for item in data}
    return data_dict.get(date, {})


# Data for Prompt Instruction Refinement case
def get_email_data() -> List[Dict[str, Any]]:
    """Get sample email data for prompt instruction refinement exercises."""
    return [
        {
            "id": 1,
            "subject": "Q4 Budget Review Meeting - URGENT",
            "from": "finance@company.com",
            "to": "team@company.com",
            "date": "2024-01-15",
            "content": "Please review the attached Q4 budget spreadsheet before tomorrow's meeting at 2 PM. We need to discuss the 15% overage in marketing expenses and the proposed cuts to the training budget. Your input on reallocating funds is crucial.",
            "priority": "high",
            "attachments": ["Q4_Budget_Review.xlsx"],
            "category": "business"
        },
        {
            "id": 2,
            "subject": "Team Building Event - Pizza Party!",
            "from": "hr@company.com",
            "to": "all-staff@company.com",
            "date": "2024-01-14",
            "content": "Join us this Friday at 5 PM in the main conference room for our monthly team building pizza party! We'll have vegetarian and gluten-free options available. Please RSVP by Wednesday so we can order enough food for everyone.",
            "priority": "low",
            "attachments": [],
            "category": "social"
        },
        {
            "id": 3,
            "subject": "Security Alert: Password Reset Required",
            "from": "security@company.com",
            "to": "john.doe@company.com",
            "date": "2024-01-16",
            "content": "We've detected unusual login activity on your account from an unrecognized location. As a precautionary measure, please reset your password immediately using the link below. If you did not attempt to log in, please contact IT security immediately.",
            "priority": "critical",
            "attachments": [],
            "category": "security"
        },
        {
            "id": 4,
            "subject": "New Feature Release - CRM Updates",
            "from": "product@company.com",
            "to": "development@company.com",
            "date": "2024-01-13",
            "content": "We're excited to announce the release of new CRM features including automated lead scoring, custom dashboard widgets, and enhanced reporting capabilities. The update will be deployed this weekend. Please review the documentation and prepare for Monday's training session.",
            "priority": "medium",
            "attachments": ["CRM_Feature_Guide.pdf", "Training_Schedule.pdf"],
            "category": "product"
        },
        {
            "id": 5,
            "subject": "Lunch Plans",
            "from": "jane.smith@company.com",
            "to": "john.doe@company.com",
            "date": "2024-01-12",
            "content": "Hey! Want to grab lunch at that new sushi place down the street today? I heard they have great reviews. Let me know if you're free around 12:30.",
            "priority": "low",
            "attachments": [],
            "category": "personal"
        },
        {
            "id": 6,
            "subject": "Server Maintenance Tonight - Action Required",
            "from": "infrastructure@company.com",
            "to": "developers@company.com",
            "date": "2024-01-17",
            "content": "Scheduled server maintenance will begin at 11 PM tonight and last approximately 4 hours. Please ensure all critical processes are shut down gracefully by 10:45 PM. The customer portal and internal systems will be unavailable during this time. Emergency contact: on-call engineer at ext. 9999.",
            "priority": "high",
            "attachments": ["Maintenance_Checklist.pdf"],
            "category": "infrastructure"
        }
    ]


def get_customer_feedback_data() -> List[Dict[str, Any]]:
    """Get sample customer feedback data for sentiment analysis exercises."""
    return [
        {
            "id": 1,
            "customer_name": "Alice Johnson",
            "email": "alice.j@email.com",
            "product": "Product 1",
            "rating": 5,
            "feedback": "Absolutely fantastic product! The quality exceeded my expectations and the customer service was outstanding. I've already recommended it to three friends. Will definitely be ordering again soon!",
            "date": "2024-01-15",
            "channel": "website"
        },
        {
            "id": 2,
            "customer_name": "Bob Smith",
            "email": "bob.smith@email.com",
            "product": "Product 3",
            "rating": 2,
            "feedback": "Very disappointed with this purchase. The product arrived damaged and the return process was extremely complicated. It took three phone calls and two weeks to get a refund. Not impressed with the overall experience.",
            "date": "2024-01-14",
            "channel": "phone"
        },
        {
            "id": 3,
            "customer_name": "Carol Wilson",
            "email": "c.wilson@email.com",
            "product": "Product 2",
            "rating": 4,
            "feedback": "Good product overall, works as advertised. The setup was a bit more complex than expected, but customer support helped me through it. Would be nice if the instructions were clearer, but I'm satisfied with the purchase.",
            "date": "2024-01-13",
            "channel": "email"
        },
        {
            "id": 4,
            "customer_name": "David Lee",
            "email": "d.lee@email.com",
            "product": "Product 4",
            "rating": 1,
            "feedback": "Terrible experience from start to finish. Product stopped working after just two days and customer service was completely unhelpful. They kept transferring me to different departments. I want a full refund immediately!",
            "date": "2024-01-16",
            "channel": "chat"
        },
        {
            "id": 5,
            "customer_name": "Emma Davis",
            "email": "emma.davis@email.com",
            "product": "Product 5",
            "rating": 3,
            "feedback": "It's okay, nothing special. Does what it's supposed to do but doesn't really stand out from competitors. The price is fair but I was expecting something more innovative based on the marketing materials.",
            "date": "2024-01-12",
            "channel": "website"
        },
        {
            "id": 6,
            "customer_name": "Frank Garcia",
            "email": "f.garcia@email.com",
            "product": "Product 1",
            "rating": 5,
            "feedback": "Love this product! It has made my daily routine so much easier. The quality is top-notch and it looks great too. My only minor complaint is that shipping took a bit longer than expected, but the product itself is perfect.",
            "date": "2024-01-17",
            "channel": "website"
        }
    ]


def get_prompt_templates() -> Dict[str, str]:
    """Get various prompt templates for instruction refinement exercises."""
    return {
        "basic_email_summary": "Summarize this email:",
        "detailed_email_analysis": """
        Analyze the following email and provide:
        1. A concise summary
        2. Priority level assessment
        3. Key action items
        4. Recommended next steps
        
        Email content:
        """,
        "sentiment_analysis_basic": "What is the sentiment of this customer feedback?",
        "sentiment_analysis_detailed": """
        Analyze the customer feedback below and provide:
        1. Overall sentiment (positive/negative/neutral)
        2. Sentiment score (1-10 scale)
        3. Key themes mentioned
        4. Specific issues or praise points
        5. Recommended business actions
        
        Customer feedback:
        """,
        "professional_email_composer": """
        Compose a professional email response with the following requirements:
        - Professional but friendly tone
        - Clear structure with greeting, body, and closing
        - Address all key points mentioned
        - Include appropriate call-to-action
        - Maximum 200 words
        
        Context:
        """
    }