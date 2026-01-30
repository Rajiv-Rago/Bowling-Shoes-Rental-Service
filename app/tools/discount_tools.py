from typing import Any, Dict, List

from .base import Tool, ToolContext
from ..schemas.tools import ToolParameter, DiscountResult, BestDiscountResult


class CalculateAgeDiscountTool(Tool):
    """Calculate discount based on customer age."""

    name = "calculate_age_discount"
    description = """Calculate the age-based discount for a customer.
    - Age 0-12: 20% discount
    - Age 13-18: 10% discount
    - Age 19-64: No discount
    - Age 65+: 15% discount (senior discount)"""

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="age",
                type="integer",
                description="The customer's age in years",
                required=True
            )
        ]

    async def execute(self, context: ToolContext, age: int) -> Dict[str, Any]:
        if age < 0:
            return DiscountResult(
                discount=0.0,
                reason="Invalid age provided"
            ).model_dump()

        if age <= 12:
            return DiscountResult(
                discount=0.20,
                reason=f"Child discount (age {age}): 20% off"
            ).model_dump()
        elif age <= 18:
            return DiscountResult(
                discount=0.10,
                reason=f"Youth discount (age {age}): 10% off"
            ).model_dump()
        elif age >= 65:
            return DiscountResult(
                discount=0.15,
                reason=f"Senior discount (age {age}): 15% off"
            ).model_dump()
        else:
            return DiscountResult(
                discount=0.0,
                reason=f"No age-based discount applies (age {age})"
            ).model_dump()


class CalculateDisabilityDiscountTool(Tool):
    """Calculate discount based on disability status."""

    name = "calculate_disability_discount"
    description = """Calculate the disability discount for a customer.
    Customers with disabilities receive a 25% discount."""

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="is_disabled",
                type="boolean",
                description="Whether the customer has a disability",
                required=True
            )
        ]

    async def execute(self, context: ToolContext, is_disabled: bool) -> Dict[str, Any]:
        if is_disabled:
            return DiscountResult(
                discount=0.25,
                reason="Disability discount: 25% off"
            ).model_dump()
        else:
            return DiscountResult(
                discount=0.0,
                reason="No disability discount applies"
            ).model_dump()


class CalculateMedicalDiscountTool(Tool):
    """Calculate discount based on medical conditions."""

    name = "calculate_medical_discount"
    description = """Calculate the medical condition discount for a customer.
    Each qualifying condition provides a 10% discount:
    - Diabetes: 10%
    - Hypertension: 10%
    - Chronic conditions: 10%
    Multiple conditions stack (e.g., diabetes + hypertension = 20%)."""

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="medical_conditions",
                type="string",
                description="Comma-separated list of medical conditions (e.g., 'diabetes, hypertension')",
                required=True
            )
        ]

    async def execute(self, context: ToolContext, medical_conditions: str) -> Dict[str, Any]:
        if not medical_conditions or medical_conditions.strip() == "":
            return DiscountResult(
                discount=0.0,
                reason="No medical conditions specified"
            ).model_dump()

        conditions_lower = medical_conditions.lower()
        discount = 0.0
        reasons = []

        qualifying_conditions = {
            "diabetes": 0.10,
            "hypertension": 0.10,
            "chronic": 0.10,
        }

        for condition, rate in qualifying_conditions.items():
            if condition in conditions_lower:
                discount += rate
                reasons.append(f"{condition.capitalize()}: {int(rate * 100)}%")

        # Cap at 30% for medical conditions
        discount = min(discount, 0.30)

        if discount > 0:
            return DiscountResult(
                discount=discount,
                reason=f"Medical discount ({', '.join(reasons)}): {int(discount * 100)}% off"
            ).model_dump()
        else:
            return DiscountResult(
                discount=0.0,
                reason="No qualifying medical conditions found"
            ).model_dump()


class GetBestDiscountTool(Tool):
    """Get the best applicable discount for a customer."""

    name = "get_best_discount"
    description = """Determine the best discount for a customer based on all their attributes.
    Evaluates age, disability status, and medical conditions, then returns
    the highest applicable discount. This tool should be used when creating
    a rental to ensure the customer gets the best deal."""

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="age",
                type="integer",
                description="The customer's age in years",
                required=True
            ),
            ToolParameter(
                name="is_disabled",
                type="boolean",
                description="Whether the customer has a disability",
                required=True
            ),
            ToolParameter(
                name="medical_conditions",
                type="string",
                description="Comma-separated list of medical conditions",
                required=False,
                default=""
            )
        ]

    async def execute(
        self,
        context: ToolContext,
        age: int,
        is_disabled: bool,
        medical_conditions: str = ""
    ) -> Dict[str, Any]:
        discounts = []

        # Calculate age discount
        age_tool = CalculateAgeDiscountTool()
        age_result = await age_tool.execute(context, age=age)
        if age_result["discount"] > 0:
            discounts.append(DiscountResult(**age_result))

        # Calculate disability discount
        disability_tool = CalculateDisabilityDiscountTool()
        disability_result = await disability_tool.execute(context, is_disabled=is_disabled)
        if disability_result["discount"] > 0:
            discounts.append(DiscountResult(**disability_result))

        # Calculate medical discount
        medical_tool = CalculateMedicalDiscountTool()
        medical_result = await medical_tool.execute(context, medical_conditions=medical_conditions)
        if medical_result["discount"] > 0:
            discounts.append(DiscountResult(**medical_result))

        # Find the best discount
        if not discounts:
            return BestDiscountResult(
                best_discount=0.0,
                explanation="No discounts apply to this customer.",
                applied_discounts=[]
            ).model_dump()

        best = max(discounts, key=lambda d: d.discount)

        # Build explanation
        all_reasons = [d.reason for d in discounts]
        explanation = (
            f"Applicable discounts: {'; '.join(all_reasons)}. "
            f"Best discount selected: {int(best.discount * 100)}% ({best.reason})"
        )

        return BestDiscountResult(
            best_discount=best.discount,
            explanation=explanation,
            applied_discounts=[d.model_dump() for d in discounts]
        ).model_dump()
