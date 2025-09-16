from pydantic import BaseModel, Field
from typing import Optional, List

# Now, we define our model as a Python class
class Order(BaseModel):
    """A model to hold structured information about a user."""

    # This is a required field of type integer.
    # The `Field` function lets us add a description.
    order_id: int = Field(..., description="The unique identifier for the order.")

    # This is a required field of type float.
    total_amount: float = Field(..., description="The total amount for the order.")

    # items is a list of strings, and it's required.
    items: List[str] = Field(..., description="The items included in the order.")

    # This is an optional field. If it's not present, its value will be None.
    customer_email: Optional[str] = Field(None, description="The customer's email address, if available.")


class OrderItem(BaseModel):
    """A model to hold structured information about an order item."""

    sku: str = Field(..., description="the Stock Keeping Unit.")
    quantity: int = Field(..., description="The quantity of the item ordered.")
    item_name: str = Field(..., description="The name of the item.")