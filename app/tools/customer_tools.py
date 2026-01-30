from typing import Any, Dict, List, Optional

from .base import Tool, ToolContext
from ..schemas.tools import (
    ToolParameter,
    CustomerInfo,
    CustomerLookupResult,
    CustomerListResult
)
from ..database import get as db_get, add as db_add, update as db_update


class LookupCustomerTool(Tool):
    """Look up a customer by name or ID."""

    name = "lookup_customer"
    description = """Find a customer in the system by their name or ID.
    Use this to retrieve customer information before creating a rental
    or to check if a customer already exists."""

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="name",
                type="string",
                description="Customer name to search for",
                required=False
            ),
            ToolParameter(
                name="customer_id",
                type="integer",
                description="Customer ID to look up",
                required=False
            )
        ]

    async def execute(
        self,
        context: ToolContext,
        name: Optional[str] = None,
        customer_id: Optional[int] = None
    ) -> Dict[str, Any]:
        if not name and not customer_id:
            return CustomerLookupResult(
                found=False,
                customer=None,
                message="Please provide either a name or customer ID to search"
            ).model_dump()

        query = {}
        if customer_id:
            query["id"] = customer_id
        if name:
            query["name"] = name

        try:
            results = db_get(query, "customers")

            if results and len(results) > 0:
                customer_data = results[0]
                customer = CustomerInfo(
                    id=customer_data.get("id"),
                    name=customer_data.get("name"),
                    age=customer_data.get("age"),
                    contact_info=customer_data.get("contact_info"),
                    is_disabled=customer_data.get("is_disabled", False),
                    medical_conditions=customer_data.get("medical_conditions", "")
                )
                return CustomerLookupResult(
                    found=True,
                    customer=customer,
                    message=f"Found customer: {customer.name}"
                ).model_dump()
            else:
                search_term = name if name else f"ID {customer_id}"
                return CustomerLookupResult(
                    found=False,
                    customer=None,
                    message=f"No customer found matching: {search_term}"
                ).model_dump()
        except Exception as e:
            return CustomerLookupResult(
                found=False,
                customer=None,
                message=f"Error searching for customer: {str(e)}"
            ).model_dump()


class CreateCustomerTool(Tool):
    """Create a new customer record."""

    name = "create_customer"
    description = """Create a new customer in the system.
    Use this when a customer wants to rent shoes but doesn't have an account yet."""

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="name",
                type="string",
                description="Customer's full name",
                required=True
            ),
            ToolParameter(
                name="age",
                type="integer",
                description="Customer's age in years",
                required=True
            ),
            ToolParameter(
                name="contact_info",
                type="string",
                description="Customer's contact information (phone or email)",
                required=True
            ),
            ToolParameter(
                name="is_disabled",
                type="boolean",
                description="Whether the customer has a disability",
                required=False,
                default=False
            ),
            ToolParameter(
                name="medical_conditions",
                type="string",
                description="Any medical conditions (comma-separated)",
                required=False,
                default=""
            )
        ]

    async def execute(
        self,
        context: ToolContext,
        name: str,
        age: int,
        contact_info: str,
        is_disabled: bool = False,
        medical_conditions: str = ""
    ) -> Dict[str, Any]:
        # Check if customer already exists
        lookup_tool = LookupCustomerTool()
        existing = await lookup_tool.execute(context, name=name)

        if existing["found"]:
            return {
                "success": False,
                "customer": existing["customer"],
                "message": f"Customer '{name}' already exists. Use update_customer to modify their info."
            }

        data = {
            "name": name,
            "age": age,
            "contact_info": contact_info,
            "is_disabled": is_disabled,
            "medical_conditions": medical_conditions
        }

        try:
            result = db_add("customers", data)
            if result and len(result) > 0:
                customer = CustomerInfo(
                    id=result[0].get("id"),
                    name=result[0].get("name"),
                    age=result[0].get("age"),
                    contact_info=result[0].get("contact_info"),
                    is_disabled=result[0].get("is_disabled", False),
                    medical_conditions=result[0].get("medical_conditions", "")
                )
                return {
                    "success": True,
                    "customer": customer.model_dump(),
                    "message": f"Successfully created customer: {name}"
                }
            else:
                return {
                    "success": False,
                    "customer": None,
                    "message": "Failed to create customer - no result returned"
                }
        except Exception as e:
            return {
                "success": False,
                "customer": None,
                "message": f"Error creating customer: {str(e)}"
            }


class UpdateCustomerTool(Tool):
    """Update an existing customer's information."""

    name = "update_customer"
    description = """Update a customer's information in the system.
    Use this to modify contact info, medical conditions, or other details."""

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="customer_id",
                type="integer",
                description="ID of the customer to update",
                required=True
            ),
            ToolParameter(
                name="name",
                type="string",
                description="New name (optional)",
                required=False
            ),
            ToolParameter(
                name="age",
                type="integer",
                description="New age (optional)",
                required=False
            ),
            ToolParameter(
                name="contact_info",
                type="string",
                description="New contact info (optional)",
                required=False
            ),
            ToolParameter(
                name="is_disabled",
                type="boolean",
                description="New disability status (optional)",
                required=False
            ),
            ToolParameter(
                name="medical_conditions",
                type="string",
                description="New medical conditions (optional)",
                required=False
            )
        ]

    async def execute(
        self,
        context: ToolContext,
        customer_id: int,
        name: Optional[str] = None,
        age: Optional[int] = None,
        contact_info: Optional[str] = None,
        is_disabled: Optional[bool] = None,
        medical_conditions: Optional[str] = None
    ) -> Dict[str, Any]:
        # Build update dict with only provided fields
        updates = {}
        if name is not None:
            updates["name"] = name
        if age is not None:
            updates["age"] = age
        if contact_info is not None:
            updates["contact_info"] = contact_info
        if is_disabled is not None:
            updates["is_disabled"] = is_disabled
        if medical_conditions is not None:
            updates["medical_conditions"] = medical_conditions

        if not updates:
            return {
                "success": False,
                "message": "No fields to update were provided"
            }

        try:
            result = db_update(updates, "customers", customer_id)
            if result and len(result) > 0:
                return {
                    "success": True,
                    "customer": result[0],
                    "message": f"Successfully updated customer ID {customer_id}"
                }
            else:
                return {
                    "success": False,
                    "message": f"Customer ID {customer_id} not found"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error updating customer: {str(e)}"
            }


class ListCustomersTool(Tool):
    """List all customers or filter by criteria."""

    name = "list_customers"
    description = """List customers in the system. Can filter by name pattern or other criteria.
    Use this to see all customers or find customers matching certain criteria."""

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="name_filter",
                type="string",
                description="Filter by name (partial match)",
                required=False
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="Maximum number of results to return",
                required=False,
                default=20
            )
        ]

    async def execute(
        self,
        context: ToolContext,
        name_filter: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        try:
            query = {}
            if name_filter:
                query["name"] = name_filter

            results = db_get(query, "customers")

            customers = []
            for row in results[:limit]:
                customers.append(CustomerInfo(
                    id=row.get("id"),
                    name=row.get("name"),
                    age=row.get("age"),
                    contact_info=row.get("contact_info"),
                    is_disabled=row.get("is_disabled", False),
                    medical_conditions=row.get("medical_conditions", "")
                ).model_dump())

            return CustomerListResult(
                customers=customers,
                count=len(customers)
            ).model_dump()
        except Exception as e:
            return {
                "customers": [],
                "count": 0,
                "error": f"Error listing customers: {str(e)}"
            }
