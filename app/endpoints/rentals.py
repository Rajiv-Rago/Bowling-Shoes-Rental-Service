from fastapi import APIRouter, Request
from ..database import *
from ..tools.base import ToolContext
from ..tools.discount_tools import GetBestDiscountTool
import json

router = APIRouter()
table = "rentals"


@router.post("/add")
async def add_record(
    name: str,
    rental_date: str,
    shoe_size: float,
    rental_fee: float,
):
    """Create a new rental with automatic discount calculation.

    The discount is calculated deterministically using the tools system
    based on customer age, disability status, and medical conditions.
    """
    customer = get({"name": name}, "customers")[0]

    # Use the discount tool to calculate the best discount
    discount_tool = GetBestDiscountTool()
    context = ToolContext()

    discount_result = await discount_tool.execute(
        context,
        age=customer["age"],
        is_disabled=customer.get("is_disabled", False),
        medical_conditions=customer.get("medical_conditions", "")
    )

    discount = discount_result["best_discount"]

    data = {
        "customer_id": customer["id"],
        "rental_date": rental_date,
        "shoe_size": shoe_size,
        "rental_fee": rental_fee,
        "discount": discount,
        "total_fee": rental_fee - (rental_fee * discount)
    }

    response = add(table, data)

    return json.dumps({
        **response[0],
        "discount_explanation": discount_result["explanation"]
    })


@router.post("/remove")
async def remove_record(request: Request):
    response = delete(request, table)
    return json.dumps({"message": "Rental record removed successfully"})


@router.get("/get")
async def get_records(request: Request):
    response = get(request, table)
    return json.dumps(response)


@router.post("/update")
async def update_record(request: Request, id: int):
    response = update(request, table, id)
    return json.dumps(response)
