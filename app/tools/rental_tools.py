from typing import Any, Dict, List, Optional

from .base import Tool, ToolContext
from .discount_tools import GetBestDiscountTool
from .customer_tools import LookupCustomerTool
from ..schemas.tools import (
    ToolParameter,
    RentalInfo,
    CreateRentalResult,
    RentalHistoryResult
)
from ..database import get as db_get, add as db_add, delete as db_delete


class CreateRentalTool(Tool):
    """Create a new rental with automatic discount calculation."""

    name = "create_rental"
    description = """Create a new shoe rental for a customer.
    This tool automatically calculates and applies the best discount based on
    the customer's age, disability status, and medical conditions.
    The customer must already exist in the system."""

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="customer_name",
                type="string",
                description="Name of the customer renting shoes",
                required=True
            ),
            ToolParameter(
                name="rental_date",
                type="string",
                description="Date of rental (YYYY-MM-DD format)",
                required=True
            ),
            ToolParameter(
                name="shoe_size",
                type="number",
                description="Shoe size (e.g., 9.5)",
                required=True
            ),
            ToolParameter(
                name="rental_fee",
                type="number",
                description="Base rental fee before discount",
                required=False,
                default=5.00
            )
        ]

    async def execute(
        self,
        context: ToolContext,
        customer_name: str,
        rental_date: str,
        shoe_size: float,
        rental_fee: float = 5.00
    ) -> Dict[str, Any]:
        # Look up the customer
        lookup_tool = LookupCustomerTool()
        customer_result = await lookup_tool.execute(context, name=customer_name)

        if not customer_result["found"]:
            return CreateRentalResult(
                success=False,
                rental=None,
                message=f"Customer '{customer_name}' not found. Please create the customer first.",
                discount_explanation=None
            ).model_dump()

        customer = customer_result["customer"]

        # Calculate best discount
        discount_tool = GetBestDiscountTool()
        discount_result = await discount_tool.execute(
            context,
            age=customer["age"],
            is_disabled=customer["is_disabled"],
            medical_conditions=customer.get("medical_conditions", "")
        )

        best_discount = discount_result["best_discount"]
        discount_explanation = discount_result["explanation"]

        # Calculate total fee
        total_fee = rental_fee - (rental_fee * best_discount)

        # Create the rental record
        data = {
            "customer_id": customer["id"],
            "rental_date": rental_date,
            "shoe_size": shoe_size,
            "rental_fee": rental_fee,
            "discount": best_discount,
            "total_fee": round(total_fee, 2)
        }

        try:
            result = db_add("rentals", data)
            if result and len(result) > 0:
                rental = RentalInfo(
                    id=result[0].get("id"),
                    customer_id=result[0].get("customer_id"),
                    rental_date=result[0].get("rental_date"),
                    shoe_size=result[0].get("shoe_size"),
                    rental_fee=result[0].get("rental_fee"),
                    discount=result[0].get("discount"),
                    total_fee=result[0].get("total_fee")
                )
                return CreateRentalResult(
                    success=True,
                    rental=rental,
                    message=f"Rental created for {customer_name}. Total: ${rental.total_fee:.2f} (saved ${(rental_fee - rental.total_fee):.2f})",
                    discount_explanation=discount_explanation
                ).model_dump()
            else:
                return CreateRentalResult(
                    success=False,
                    rental=None,
                    message="Failed to create rental - no result returned",
                    discount_explanation=None
                ).model_dump()
        except Exception as e:
            return CreateRentalResult(
                success=False,
                rental=None,
                message=f"Error creating rental: {str(e)}",
                discount_explanation=None
            ).model_dump()


class GetRentalHistoryTool(Tool):
    """Get rental history for a customer."""

    name = "get_rental_history"
    description = """Retrieve the rental history for a customer.
    Shows all past rentals with dates, sizes, fees, and discounts applied."""

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="customer_name",
                type="string",
                description="Name of the customer",
                required=False
            ),
            ToolParameter(
                name="customer_id",
                type="integer",
                description="ID of the customer",
                required=False
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="Maximum number of rentals to return",
                required=False,
                default=10
            )
        ]

    async def execute(
        self,
        context: ToolContext,
        customer_name: Optional[str] = None,
        customer_id: Optional[int] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        # Get customer ID if only name provided
        if customer_name and not customer_id:
            lookup_tool = LookupCustomerTool()
            customer_result = await lookup_tool.execute(context, name=customer_name)
            if not customer_result["found"]:
                return RentalHistoryResult(
                    rentals=[],
                    count=0,
                    total_spent=0.0
                ).model_dump()
            customer_id = customer_result["customer"]["id"]

        if not customer_id:
            return RentalHistoryResult(
                rentals=[],
                count=0,
                total_spent=0.0
            ).model_dump()

        try:
            results = db_get({"customer_id": customer_id}, "rentals")

            rentals = []
            total_spent = 0.0

            for row in results[:limit]:
                rental = RentalInfo(
                    id=row.get("id"),
                    customer_id=row.get("customer_id"),
                    rental_date=row.get("rental_date"),
                    shoe_size=row.get("shoe_size"),
                    rental_fee=row.get("rental_fee"),
                    discount=row.get("discount"),
                    total_fee=row.get("total_fee")
                )
                rentals.append(rental.model_dump())
                total_spent += rental.total_fee

            return RentalHistoryResult(
                rentals=rentals,
                count=len(rentals),
                total_spent=round(total_spent, 2)
            ).model_dump()
        except Exception as e:
            return {
                "rentals": [],
                "count": 0,
                "total_spent": 0.0,
                "error": f"Error retrieving rental history: {str(e)}"
            }


class CancelRentalTool(Tool):
    """Cancel a rental."""

    name = "cancel_rental"
    description = """Cancel an existing rental by its ID.
    Use this if a customer needs to cancel their shoe rental."""

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="rental_id",
                type="integer",
                description="ID of the rental to cancel",
                required=True
            )
        ]

    async def execute(self, context: ToolContext, rental_id: int) -> Dict[str, Any]:
        try:
            # First check if rental exists
            results = db_get({"id": rental_id}, "rentals")
            if not results or len(results) == 0:
                return {
                    "success": False,
                    "message": f"Rental ID {rental_id} not found"
                }

            # Delete the rental
            db_delete({"id": rental_id}, "rentals")

            return {
                "success": True,
                "message": f"Rental ID {rental_id} has been cancelled"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error cancelling rental: {str(e)}"
            }
