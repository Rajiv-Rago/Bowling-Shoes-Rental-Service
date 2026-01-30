from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from enum import Enum


class ToolParameter(BaseModel):
    """Schema for a tool parameter."""
    name: str
    type: str
    description: str
    required: bool = True
    enum: Optional[List[str]] = None
    default: Optional[Any] = None


class ToolDefinition(BaseModel):
    """Schema for a tool definition that gets sent to the LLM."""
    name: str
    description: str
    parameters: List[ToolParameter]

    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        properties = {}
        required = []

        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic tool use format."""
        properties = {}
        required = []

        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }


class ToolCallRequest(BaseModel):
    """A request to call a tool."""
    tool_name: str
    tool_call_id: str
    arguments: Dict[str, Any]


class ToolCallResult(BaseModel):
    """Result from executing a tool."""
    tool_call_id: str
    tool_name: str
    result: Any
    success: bool = True
    error: Optional[str] = None


# Discount tool schemas
class DiscountResult(BaseModel):
    """Result from a discount calculation."""
    discount: float = Field(..., ge=0, le=1, description="Discount as decimal (0-1)")
    reason: str = Field(..., description="Explanation for the discount")


class BestDiscountResult(BaseModel):
    """Result from getting the best discount."""
    best_discount: float = Field(..., ge=0, le=1, description="Best applicable discount")
    explanation: str = Field(..., description="Explanation of all applicable discounts")
    applied_discounts: List[DiscountResult] = Field(default_factory=list)


# Customer tool schemas
class CustomerInfo(BaseModel):
    """Customer information."""
    id: Optional[int] = None
    name: str
    age: int
    contact_info: str
    is_disabled: bool = False
    medical_conditions: str = ""


class CustomerLookupResult(BaseModel):
    """Result from customer lookup."""
    found: bool
    customer: Optional[CustomerInfo] = None
    message: str


class CustomerListResult(BaseModel):
    """Result from listing customers."""
    customers: List[CustomerInfo]
    count: int


# Rental tool schemas
class RentalInfo(BaseModel):
    """Rental information."""
    id: Optional[int] = None
    customer_id: int
    rental_date: str
    shoe_size: float
    rental_fee: float
    discount: float
    total_fee: float


class CreateRentalResult(BaseModel):
    """Result from creating a rental."""
    success: bool
    rental: Optional[RentalInfo] = None
    message: str
    discount_explanation: Optional[str] = None


class RentalHistoryResult(BaseModel):
    """Result from getting rental history."""
    rentals: List[RentalInfo]
    count: int
    total_spent: float


# Info tool schemas
class PricingInfo(BaseModel):
    """Pricing and discount policy information."""
    base_rental_fee: float = 5.00
    discount_policies: Dict[str, str]


class ServiceInfo(BaseModel):
    """General service information."""
    name: str = "Bowling Shoes Rental Service"
    description: str
    available_sizes: List[float]
    operating_hours: str
