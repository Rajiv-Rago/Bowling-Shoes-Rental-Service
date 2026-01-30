from typing import Any, Dict, List

from .base import Tool, ToolContext
from ..schemas.tools import ToolParameter, PricingInfo, ServiceInfo


class GetPricingInfoTool(Tool):
    """Get pricing and discount policy information."""

    name = "get_pricing_info"
    description = """Get information about rental pricing and discount policies.
    Use this when a customer asks about prices, discounts, or how much rentals cost."""

    @property
    def parameters(self) -> List[ToolParameter]:
        return []  # No parameters needed

    async def execute(self, context: ToolContext) -> Dict[str, Any]:
        return PricingInfo(
            base_rental_fee=5.00,
            discount_policies={
                "age_child": "Children (age 0-12): 20% discount",
                "age_youth": "Youth (age 13-18): 10% discount",
                "age_senior": "Seniors (age 65+): 15% discount",
                "disability": "Customers with disabilities: 25% discount",
                "medical_diabetes": "Diabetes: 10% discount",
                "medical_hypertension": "Hypertension: 10% discount",
                "medical_chronic": "Chronic conditions: 10% discount",
                "stacking": "Note: Medical discounts can stack up to 30%. The highest single discount is applied."
            }
        ).model_dump()


class GetServiceInfoTool(Tool):
    """Get general service information."""

    name = "get_service_info"
    description = """Get general information about the bowling shoe rental service.
    Use this when customers ask about available sizes, hours, or general information."""

    @property
    def parameters(self) -> List[ToolParameter]:
        return []  # No parameters needed

    async def execute(self, context: ToolContext) -> Dict[str, Any]:
        return ServiceInfo(
            name="Bowling Shoes Rental Service",
            description="We provide quality bowling shoe rentals for all ages. "
                        "Our service includes automatic discount calculations based on "
                        "age, disability status, and medical conditions to ensure everyone "
                        "can enjoy bowling at an affordable price.",
            available_sizes=[
                5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5,
                9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 13.0
            ],
            operating_hours="Monday - Sunday: 10:00 AM - 10:00 PM"
        ).model_dump()
